from fastapi import APIRouter, Depends, HTTPException

from app.core.deps import get_current_user
from app.models.event import EventResponse, EventStatus
from app.services.linkedin_analyzer import analyze_linkedin_profile
from app.services.message_generator import MessageGenerator

_msg_gen = MessageGenerator()

router = APIRouter(
    prefix="/api/events",
    tags=["events"],
    dependencies=[Depends(get_current_user)],
)

# In-memory store for hackathon MVP
_events: dict[str, dict] = {}


@router.get("")
async def list_events(
    status: EventStatus | None = None,
    limit: int = 20,
    offset: int = 0,
) -> list[dict]:
    events = list(_events.values())
    if status:
        events = [e for e in events if e.get("status") == status]
    return events[offset : offset + limit]


@router.get("/{event_id}")
async def get_event(event_id: str) -> dict:
    if event_id not in _events:
        raise HTTPException(status_code=404, detail="Event not found")
    return _events[event_id]


@router.post("/{event_id}/accept", status_code=200)
async def accept_event(event_id: str) -> dict:
    if event_id not in _events:
        raise HTTPException(status_code=404, detail="Event not found")
    _events[event_id]["status"] = "accepted"
    return {"status": "accepted", "event_id": event_id}


@router.post("/{event_id}/reject", status_code=200)
async def reject_event(event_id: str, body: dict) -> dict:
    if event_id not in _events:
        raise HTTPException(status_code=404, detail="Event not found")
    _events[event_id]["status"] = "rejected"
    _events[event_id]["rejection_reason"] = body.get("reason", "")
    return {"status": "rejected", "event_id": event_id}


@router.post("/{event_id}/apply", status_code=200)
async def apply_to_event(event_id: str) -> dict:
    if event_id not in _events:
        raise HTTPException(status_code=404, detail="Event not found")
    _events[event_id]["status"] = "applied"
    return {"status": "applied", "event_id": event_id}


@router.get("/{event_id}/people")
async def get_event_people(event_id: str) -> list[dict]:
    if event_id not in _events:
        raise HTTPException(status_code=404, detail="Event not found")
    return _events[event_id].get("speakers", [])


@router.post("/{event_id}/attend", status_code=200)
async def attend_event(event_id: str) -> dict:
    if event_id not in _events:
        _events[event_id] = {"id": event_id}
    _events[event_id]["status"] = "attended"
    return {"status": "attended", "event_id": event_id}


@router.post("/{event_id}/skip-attend", status_code=200)
async def skip_attend_event(event_id: str) -> dict:
    if event_id not in _events:
        _events[event_id] = {"id": event_id}
    _events[event_id]["status"] = "skipped"
    return {"status": "skipped", "event_id": event_id}


@router.post("/{event_id}/connections", status_code=200)
async def add_event_connections(event_id: str, body: dict) -> dict:
    """Save people you met at an event. Body: { connections: [{ name, linkedin_url, notes? }] }"""
    connections = body.get("connections", [])
    if event_id not in _events:
        _events[event_id] = {"id": event_id}
    _events[event_id].setdefault("connections", []).extend(connections)
    return {"status": "ok", "event_id": event_id, "connections_added": len(connections)}


@router.get("/{event_id}/connections")
async def get_event_connections(event_id: str) -> list[dict]:
    if event_id not in _events:
        return []
    return _events[event_id].get("connections", [])


@router.post("/{event_id}/analyze-connections", status_code=200)
async def analyze_event_connections(event_id: str) -> list[dict]:
    """Analyze all connections for an event using REKA API."""
    if event_id not in _events:
        return []
    connections = _events[event_id].get("connections", [])
    results = []
    for conn in connections:
        profile = await analyze_linkedin_profile(
            name=conn.get("name", ""),
            linkedin_url=conn.get("linkedin_url", ""),
            notes=conn.get("notes", ""),
        )
        results.append(profile)
    _events[event_id]["analyzed_connections"] = results
    return results


@router.post("/{event_id}/draft-messages", status_code=200)
async def draft_connection_messages(event_id: str, body: dict) -> list[dict]:
    """Draft follow-up messages for connections at an event.

    Body: { user_profile: { name, role, company, ... } }
    """
    if event_id not in _events:
        return []
    user_profile = body.get("user_profile", {})
    event_data = _events[event_id]
    analyzed = event_data.get("analyzed_connections", event_data.get("connections", []))
    messages = []
    for person in analyzed:
        msg = _msg_gen.generate_followup_message(
            person=person,
            event={"title": event_data.get("title", "the event"), "id": event_id},
            user_profile=user_profile,
            met=True,
        )
        msg["linkedin_url"] = person.get("linkedin_url", "")
        messages.append(msg)
    return messages


@router.post("/{event_id}/rate", status_code=200)
async def rate_event(event_id: str, body: dict) -> dict:
    if event_id not in _events:
        raise HTTPException(status_code=404, detail="Event not found")
    rating = body.get("rating", 0)
    if not 1 <= rating <= 5:
        raise HTTPException(status_code=400, detail="Rating must be 1-5")
    _events[event_id]["user_rating"] = rating
    return {"status": "rated", "event_id": event_id, "rating": rating}
