from __future__ import annotations

from google.oauth2.credentials import Credentials

from app.core.config import settings

SCOPES = [
    "openid",
    "https://www.googleapis.com/auth/userinfo.email",
    "https://www.googleapis.com/auth/userinfo.profile",
    "https://www.googleapis.com/auth/calendar.events",
]


def build_credentials_from_refresh_token(refresh_token: str) -> Credentials:
    """Build Google API credentials from a stored refresh token.

    Used to make Calendar API calls on behalf of the user.
    """
    return Credentials(
        token=None,
        refresh_token=refresh_token,
        token_uri="https://oauth2.googleapis.com/token",
        client_id=settings.google_client_id,
        client_secret=settings.google_client_secret,
        scopes=SCOPES,
    )
