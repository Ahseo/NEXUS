from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException, Query, Request

from app.services.graph_service import get_ranked_people

router = APIRouter(prefix="/api/people", tags=["people"])


def _get_email(request: Request) -> str | None:
    try:
        from app.core.auth import decode_access_token
        token = request.cookies.get("access_token")
        if token:
            return decode_access_token(token).get("email")
    except Exception:
        pass
    return None


@router.get("")
async def list_people(
    request: Request,
    role: str | None = Query(None),
    topic: str | None = Query(None),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
) -> list[dict[str, Any]]:
    try:
        email = _get_email(request)
        people = await get_ranked_people(
            user_email=email,
            role_filter=role,
            topic_filter=topic,
            limit=limit + offset,
        )
        return people[offset:]
    except Exception:
        return []


@router.get("/{person_id}")
async def get_person(person_id: str) -> dict[str, Any]:
    people = await get_ranked_people(limit=200)
    for p in people:
        if p["id"] == person_id:
            return p
    raise HTTPException(status_code=404, detail="Person not found")


@router.get("/{person_id}/graph")
async def get_person_graph(person_id: str) -> dict[str, Any]:
    people = await get_ranked_people(limit=200)
    person = None
    for p in people:
        if p["id"] == person_id:
            person = p
            break
    if not person:
        raise HTTPException(status_code=404, detail="Person not found")
    return {
        "person": person,
        "connections": [],
        "shared_topics": person.get("topics", []),
    }


@router.post("/{person_id}/mark", status_code=200)
async def mark_person(person_id: str, body: dict[str, Any]) -> dict[str, Any]:
    action = body.get("action", "want_to_meet")
    return {"person_id": person_id, "action": action}
