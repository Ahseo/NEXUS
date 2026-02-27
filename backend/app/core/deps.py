from __future__ import annotations

from collections.abc import AsyncGenerator
from typing import Annotated

from fastapi import Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth import decode_access_token, get_token_from_cookie
from app.core.database import async_session_factory


async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """Yield an async SQLAlchemy session, auto-closing on exit."""
    async with async_session_factory() as session:
        yield session


async def get_neo4j_session() -> AsyncGenerator[None, None]:
    """Placeholder for Neo4j session injection."""
    yield None


async def get_current_user(request: Request) -> dict[str, str]:
    """Extract user_id and email from the JWT cookie.

    Returns {"user_id": "...", "email": "..."}.
    """
    token = get_token_from_cookie(request)
    return decode_access_token(token)


# Annotated shortcuts for router signatures
DbSession = Annotated[AsyncSession, Depends(get_db_session)]
CurrentUser = Annotated[dict[str, str], Depends(get_current_user)]
