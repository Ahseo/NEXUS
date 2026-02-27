from fastapi import APIRouter, Depends, HTTPException

from app.core.deps import get_current_user

router = APIRouter(
    prefix="/api/people",
    tags=["people"],
    dependencies=[Depends(get_current_user)],
)

_people: dict[str, dict] = {}


@router.get("")
async def list_people(limit: int = 20, offset: int = 0) -> list[dict]:
    return list(_people.values())[offset : offset + limit]


@router.get("/{person_id}")
async def get_person(person_id: str) -> dict:
    if person_id not in _people:
        raise HTTPException(status_code=404, detail="Person not found")
    return _people[person_id]


@router.get("/{person_id}/graph")
async def get_person_graph(person_id: str) -> dict:
    if person_id not in _people:
        raise HTTPException(status_code=404, detail="Person not found")
    return {
        "person": _people[person_id],
        "connections": [],
        "shared_topics": [],
    }


@router.post("/{person_id}/mark", status_code=200)
async def mark_person(person_id: str, body: dict) -> dict:
    action = body.get("action", "want_to_meet")
    return {"person_id": person_id, "action": action}
