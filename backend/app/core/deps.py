from __future__ import annotations

from collections.abc import AsyncGenerator
from typing import Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth import verify_api_key
from app.core.database import async_session_factory


async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """Yield an async SQLAlchemy session, auto-closing on exit."""
    async with async_session_factory() as session:
        yield session


async def get_neo4j_session() -> AsyncGenerator[None, None]:
    """Placeholder for Neo4j session injection.

    Will be implemented when the Neo4j integration client is ready.
    """
    yield None


async def get_current_user(api_key: str = Depends(verify_api_key)) -> str:
    """Return the authenticated user identifier.

    For the initial API-key auth scheme the key itself is the identity.
    Will be replaced with proper user lookup once OAuth is wired.
    """
    return api_key


# Annotated shortcuts for router signatures
DbSession = Annotated[AsyncSession, Depends(get_db_session)]
CurrentUser = Annotated[str, Depends(get_current_user)]
