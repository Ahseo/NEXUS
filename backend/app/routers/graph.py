from __future__ import annotations

import logging
import uuid
from datetime import datetime, timedelta, timezone
from typing import Any

from fastapi import APIRouter, Query, Request
from pydantic import BaseModel

from app.core.database import async_session_factory
from app.models.agent_event import AgentEventDB
from app.services.graph_service import (
    add_person_to_graph,
    bulk_import_participants,
    enrich_all_people_sns,
    get_event_participants,
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


class AddPersonRequest(BaseModel):
    name: str
    title: str = ""
    company: str = ""
    role: str = "participant"
    linkedin: str = ""
    twitter: str = ""
    github: str = ""
    avatar_url: str = ""
    topics: list[str] = []
    event_url: str = "https://autonomous-agents-hackathon.devpost.com"


class BulkImportRequest(BaseModel):
    participants: list[dict[str, Any]]
    event_url: str = "https://autonomous-agents-hackathon.devpost.com"


@router.post("/add-person")
async def add_person(body: AddPersonRequest) -> dict[str, Any]:
    """Add a single person to the graph."""
    try:
        return await add_person_to_graph(
            name=body.name,
            title=body.title,
            company=body.company,
            role=body.role,
            linkedin=body.linkedin,
            twitter=body.twitter,
            github=body.github,
            avatar_url=body.avatar_url,
            topics=body.topics,
            event_url=body.event_url,
        )
    except Exception as e:
        logger.exception("Failed to add person: %s", e)
        return {"error": str(e)}


@router.post("/bulk-import")
async def bulk_import(body: BulkImportRequest) -> dict[str, Any]:
    """Bulk import participants from JSON array."""
    try:
        return await bulk_import_participants(
            participants=body.participants,
            event_url=body.event_url,
        )
    except Exception as e:
        logger.exception("Failed to bulk import: %s", e)
        return {"error": str(e)}


@router.post("/seed-demo")
async def seed_demo(request: Request) -> dict[str, Any]:
    """Seed demo data: AgentEvent rows in Postgres + Neo4j graph."""
    email = _get_email(request)

    HACKATHON_URL = "https://autonomous-agents-hackathon.devpost.com"
    HACKATHON_TITLE = "Autonomous Agents Hackathon"

    # 1. Seed Neo4j graph (event + participants + relationships)
    try:
        graph_result = await seed_hackathon_event(
            event_url=HACKATHON_URL,
            event_title=HACKATHON_TITLE,
            user_email=email,
        )
    except Exception as e:
        logger.exception("Neo4j seed failed: %s", e)
        graph_result = {"error": str(e)}

    # 2. Seed AgentEventDB rows so the event shows up in Events page
    now = datetime.now(timezone.utc)
    event_data = {
        "event": {
            "title": HACKATHON_TITLE,
            "url": HACKATHON_URL,
            "date": "2026-02-27",
            "start_date": "2026-02-27T09:00:00",
            "location": "AWS Builder Loft, 525 Market St, SF",
            "description": "Build autonomous agents in 24 hours. $10K+ in prizes. Speakers from Anthropic, Render, Yutori, Numeric.",
            "source": "devpost",
            "price": 0,
            "topics": ["AI Agents", "LLM", "Autonomous Systems", "Hackathon"],
            "speakers": ["Carter Huffman", "Dhruv Batra", "Ojus Save", "Andrew Bihl"],
        },
        "score": 94,
        "why": "Directly aligned with your interests in AI agents and autonomous systems. High-value networking with founders, engineers, and investors in the AI space.",
    }

    agent_events = [
        {
            "event_type": "event:discovered",
            "message": f"Found event: {HACKATHON_TITLE}",
            "detail": HACKATHON_URL,
            "data": {**event_data, "count": 1},
            "created_at": now - timedelta(hours=6),
        },
        {
            "event_type": "event:analyzed",
            "message": f"Recommended: {HACKATHON_TITLE}",
            "detail": f"Score: {event_data['score']}",
            "data": event_data,
            "created_at": now - timedelta(hours=5),
        },
        {
            "event_type": "event:applied",
            "message": f"Applied to: {HACKATHON_TITLE}",
            "detail": HACKATHON_URL,
            "data": {**event_data, "status": "applied", "application_status": "confirmed"},
            "created_at": now - timedelta(hours=4),
        },
    ]

    inserted = 0
    try:
        async with async_session_factory() as session:
            for ae in agent_events:
                session.add(AgentEventDB(
                    id=str(uuid.uuid4()),
                    event_type=ae["event_type"],
                    source="nexus",
                    message=ae["message"],
                    detail=ae["detail"],
                    data=ae["data"],
                    created_at=ae["created_at"],
                ))
            await session.commit()
            inserted = len(agent_events)
    except Exception as e:
        logger.exception("Failed to seed agent events: %s", e)

    return {
        "status": "ok",
        "agent_events_inserted": inserted,
        "graph": graph_result,
    }


@router.get("/event-participants")
async def event_participants(url: str = Query(...)) -> list[dict[str, Any]]:
    """Get all participants for an event by its URL from Neo4j."""
    try:
        return await get_event_participants(url)
    except Exception as e:
        logger.error("Failed to get event participants: %s", e)
        return []
