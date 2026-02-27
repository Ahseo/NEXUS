from __future__ import annotations

import uuid

from fastapi import APIRouter, Request
from fastapi.responses import RedirectResponse
from google_auth_oauthlib.flow import Flow
from sqlalchemy import select

from app.core.auth import create_access_token, decode_access_token, get_token_from_cookie
from app.core.config import settings
from app.core.deps import CurrentUser, DbSession
from app.core.google_auth import SCOPES
from app.models.profile import UserProfileDB

router = APIRouter(prefix="/api/auth", tags=["auth"])

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
    return RedirectResponse(authorization_url)


@router.get("/google/callback")
async def google_callback(request: Request, db: DbSession) -> RedirectResponse:
    """Handle Google OAuth callback.

    - Exchange code for tokens
    - Upsert user in DB
    - Set JWT cookie
    - Redirect: new user -> /onboarding, existing user -> /
    """
    flow = _build_flow()
    flow.fetch_token(code=request.query_params.get("code"))

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
    response.set_cookie(
        key="access_token",
        value=token,
        httponly=True,
        samesite="lax",
        max_age=settings.jwt_expire_minutes * 60,
        secure=False,  # Set True in production with HTTPS
    )
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
