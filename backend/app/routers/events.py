from fastapi import APIRouter, HTTPException

from app.models.event import EventResponse, EventStatus

router = APIRouter(prefix="/api/events", tags=["events"])

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


@router.post("/{event_id}/rate", status_code=200)
async def rate_event(event_id: str, body: dict) -> dict:
    if event_id not in _events:
        raise HTTPException(status_code=404, detail="Event not found")
    rating = body.get("rating", 0)
    if not 1 <= rating <= 5:
        raise HTTPException(status_code=400, detail="Rating must be 1-5")
    _events[event_id]["user_rating"] = rating
    return {"status": "rated", "event_id": event_id, "rating": rating}
