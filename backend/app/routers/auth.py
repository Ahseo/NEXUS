from __future__ import annotations

import asyncio
import logging
import os
import uuid

# Allow OAuth over HTTP for local development
os.environ["OAUTHLIB_INSECURE_TRANSPORT"] = "1"
# Accept when Google grants fewer scopes than requested (e.g. calendar not approved)
os.environ["OAUTHLIB_RELAX_TOKEN_SCOPE"] = "1"

import bcrypt  # type: ignore[import-untyped]
from fastapi import APIRouter, HTTPException, Request, status
from fastapi.responses import JSONResponse, RedirectResponse
from google_auth_oauthlib.flow import Flow  # type: ignore[import-untyped]
from pydantic import BaseModel, EmailStr
from sqlalchemy import select

from app.core.auth import create_access_token
from app.core.config import settings
from app.core.deps import CurrentUser, DbSession
from app.core.google_auth import SCOPES
from app.models.profile import UserProfileDB

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/auth", tags=["auth"])


def _hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()


def _verify_password(password: str, hashed: str) -> bool:
    return bcrypt.checkpw(password.encode(), hashed.encode())


class SignupRequest(BaseModel):
    name: str
    email: EmailStr
    password: str


class LoginRequest(BaseModel):
    email: EmailStr
    password: str

def _set_auth_cookie(response: JSONResponse | RedirectResponse, token: str) -> None:
    response.set_cookie(
        key="access_token",
        value=token,
        httponly=True,
        samesite="lax",
        max_age=settings.jwt_expire_minutes * 60,
        secure=False,  # Set True in production with HTTPS
    )


# ── Email/Password Auth ──────────────────────────────────────────────────────


@router.post("/signup")
async def signup(body: SignupRequest, db: DbSession) -> JSONResponse:
    """Register a new user with email and password."""
    result = await db.execute(
        select(UserProfileDB).where(UserProfileDB.email == body.email)
    )
    if result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email already registered",
        )

    user = UserProfileDB(
        id=str(uuid.uuid4()),
        name=body.name,
        email=body.email,
        password_hash=_hash_password(body.password),
        onboarding_completed=False,
        role="",
        company="",
        product_description="",
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)

    token = create_access_token(user.id, user.email)
    response = JSONResponse(
        content={"user_id": user.id, "email": user.email, "onboarding_completed": False}
    )
    _set_auth_cookie(response, token)
    return response


@router.post("/login")
async def login(body: LoginRequest, db: DbSession) -> JSONResponse:
    """Login with email and password."""
    result = await db.execute(
        select(UserProfileDB).where(UserProfileDB.email == body.email)
    )
    user = result.scalar_one_or_none()

    if not user or not user.password_hash or not _verify_password(body.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )

    token = create_access_token(user.id, user.email)
    response = JSONResponse(
        content={
            "user_id": user.id,
            "email": user.email,
            "onboarding_completed": user.onboarding_completed,
        }
    )
    _set_auth_cookie(response, token)
    return response


# ── Google OAuth ──────────────────────────────────────────────────────────────


_CLIENT_CONFIG = {
    "web": {
        "client_id": settings.google_client_id,
        "client_secret": settings.google_client_secret,
        "auth_uri": "https://accounts.google.com/o/oauth2/auth",
        "token_uri": "https://oauth2.googleapis.com/token",
        "redirect_uris": [settings.google_redirect_uri],
    }
}


def _build_flow() -> Flow:
    flow = Flow.from_client_config(_CLIENT_CONFIG, scopes=SCOPES)
    flow.redirect_uri = settings.google_redirect_uri
    return flow


@router.get("/google")
async def google_login() -> RedirectResponse:
    """Redirect user to Google OAuth consent screen."""
    flow = _build_flow()
    authorization_url, _ = flow.authorization_url(
        access_type="offline",
        prompt="consent",
        include_granted_scopes="true",
    )
    response = RedirectResponse(authorization_url)
    # Store PKCE code_verifier so the callback can use it
    if flow.code_verifier:
        response.set_cookie(
            key="oauth_cv",
            value=flow.code_verifier,
            httponly=True,
            samesite="lax",
            max_age=600,
            secure=False,
        )
    return response


@router.get("/google/callback")
async def google_callback(request: Request, db: DbSession) -> RedirectResponse:
    """Handle Google OAuth callback.

    - Exchange code for tokens
    - Upsert user in DB
    - Set JWT cookie
    - Redirect: new user -> /onboarding, existing user -> /
    """
    code = request.query_params.get("code")
    if not code:
        logger.error("OAuth callback missing code parameter")
        return RedirectResponse(f"{settings.frontend_url}/login?error=missing_code")

    flow = _build_flow()

    # Restore PKCE code_verifier from cookie (set during /google redirect)
    code_verifier = request.cookies.get("oauth_cv")

    try:
        # fetch_token is synchronous — run in thread to avoid blocking
        await asyncio.to_thread(
            flow.fetch_token, code=code, code_verifier=code_verifier
        )
    except Exception as e:
        logger.exception("OAuth token exchange failed: %s", e)
        return RedirectResponse(f"{settings.frontend_url}/login?error=token_exchange")

    credentials = flow.credentials
    # Get user info from Google
    import httpx

    async with httpx.AsyncClient() as client:
        resp = await client.get(
            "https://www.googleapis.com/oauth2/v3/userinfo",
            headers={"Authorization": f"Bearer {credentials.token}"},
        )
        resp.raise_for_status()
        user_info = resp.json()

    google_sub = user_info["sub"]
    email = user_info.get("email", "")
    name = user_info.get("name", "")

    # Look up existing user by google_sub
    result = await db.execute(
        select(UserProfileDB).where(UserProfileDB.google_sub == google_sub)
    )
    user = result.scalar_one_or_none()

    is_new = user is None

    if is_new:
        user = UserProfileDB(
            id=str(uuid.uuid4()),
            name=name,
            email=email,
            google_sub=google_sub,
            google_refresh_token=credentials.refresh_token,
            onboarding_completed=False,
            role="",
            company="",
            product_description="",
        )
        db.add(user)
    else:
        # Update refresh token if a new one was issued
        if credentials.refresh_token:
            user.google_refresh_token = credentials.refresh_token
        user.email = email
        user.name = name

    await db.commit()
    await db.refresh(user)

    # Create JWT
    token = create_access_token(user.id, user.email)

    # Redirect based on onboarding status
    redirect_path = "/onboarding" if is_new or not user.onboarding_completed else "/"
    response = RedirectResponse(f"{settings.frontend_url}{redirect_path}")
    _set_auth_cookie(response, token)
    response.delete_cookie("oauth_cv")  # Clean up PKCE cookie
    return response


@router.get("/me")
async def get_me(user: CurrentUser) -> dict:
    """Return the current authenticated user's info from JWT."""
    return {"user_id": user["user_id"], "email": user["email"]}


@router.post("/logout")
async def logout() -> RedirectResponse:
    """Clear the auth cookie and redirect to login."""
    response = RedirectResponse(f"{settings.frontend_url}/login")
    response.delete_cookie("access_token")
    return response
