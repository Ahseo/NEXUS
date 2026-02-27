from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select

from app.core.agent_manager import agent_manager
from app.core.deps import DbSession, get_current_user
from app.models.agent_event import AgentEventDB

router = APIRouter(
    prefix="/api/agent",
    tags=["agent"],
    dependencies=[Depends(get_current_user)],
)


@router.get("/status")
async def get_agent_status() -> dict[str, Any]:
    return agent_manager.get_status()


@router.get("/events")
async def get_agent_events(
    db: DbSession,
    limit: int = Query(200, ge=1, le=1000),
    source: str | None = Query(None),
) -> list[dict[str, Any]]:
    """Return persisted agent events (newest first)."""
    stmt = select(AgentEventDB).order_by(AgentEventDB.created_at.desc())
    if source:
        stmt = stmt.where(AgentEventDB.source == source)
    stmt = stmt.limit(limit)
    result = await db.execute(stmt)
    rows = result.scalars().all()
    return [
        {
            "id": r.id,
            "type": r.event_type,
            "source": r.source,
            "message": r.message,
            "detail": r.detail,
            "data": r.data,
            "time": r.created_at.isoformat() if r.created_at else "",
        }
        for r in rows
    ]


@router.post("/pause", status_code=200)
async def pause_agent() -> dict[str, str]:
    agent_manager.pause()
    return {"status": "paused"}


@router.post("/resume", status_code=200)
async def resume_agent() -> dict[str, str]:
    await agent_manager.resume()
    return {"status": "running"}


@router.post("/run-now", status_code=200)
async def run_now() -> dict[str, str]:
    await agent_manager.run_now()
    return {"status": "triggered", "message": "Agent cycle started"}
