from __future__ import annotations

import logging
from typing import Any

from fastapi import APIRouter, Query, Request
from pydantic import BaseModel

from app.services.graph_service import (
    enrich_all_people_sns,
    get_network_graph,
    get_ranked_people,
    search_people_tavily,
    seed_hackathon_event,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/graph", tags=["graph"])


def _get_email(request: Request) -> str | None:
    """Try to extract user email from JWT cookie, return None if not logged in."""
    try:
        from app.core.auth import decode_access_token
        token = request.cookies.get("access_token")
        if token:
            payload = decode_access_token(token)
            return payload.get("email")
    except Exception:
        pass
    return None


class SeedEventRequest(BaseModel):
    url: str
    title: str


@router.get("/network")
async def get_network(request: Request) -> dict[str, Any]:
    try:
        email = _get_email(request)
        return await get_network_graph(user_email=email)
    except Exception as e:
        logger.error("Failed to get network graph: %s", e)
        return {"nodes": [], "edges": [], "events": [], "user": None, "stats": {"total_people": 0, "total_connections": 0, "total_events": 0}}


@router.get("/ranked")
async def get_ranked(
    request: Request,
    role: str | None = Query(None),
    topic: str | None = Query(None),
    limit: int = Query(50, ge=1, le=200),
) -> list[dict[str, Any]]:
    try:
        email = _get_email(request)
        return await get_ranked_people(
            user_email=email,
            role_filter=role,
            topic_filter=topic,
            limit=limit,
        )
    except Exception as e:
        logger.error("Failed to get ranked people: %s", e)
        return []


@router.post("/seed-event")
async def seed_event(body: SeedEventRequest, request: Request) -> dict[str, Any]:
    try:
        email = _get_email(request)
        return await seed_hackathon_event(
            event_url=body.url,
            event_title=body.title,
            user_email=email,
        )
    except Exception as e:
        logger.exception("Failed to seed event: %s", e)
        return {"error": str(e)}


@router.get("/search")
async def search_people(q: str = Query(...)) -> list[dict[str, Any]]:
    try:
        return await search_people_tavily(q)
    except Exception as e:
        logger.error("Tavily search failed: %s", e)
        return []


@router.post("/enrich-sns")
async def enrich_sns() -> dict[str, Any]:
    """Run Tavily+Reka pipeline to discover SNS accounts for all people."""
    try:
        return await enrich_all_people_sns()
    except Exception as e:
        logger.exception("SNS enrichment failed: %s", e)
        return {"error": str(e)}


@router.get("/suggestions")
async def get_graph_suggestions(request: Request) -> list[dict[str, Any]]:
    try:
        email = _get_email(request)
        return await get_ranked_people(user_email=email, limit=5)
    except Exception:
        return []
