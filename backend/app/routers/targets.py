import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException

from app.core.deps import get_current_user

router = APIRouter(
    prefix="/api/targets",
    tags=["targets"],
    dependencies=[Depends(get_current_user)],
)

_targets: dict[str, dict] = {}


@router.get("")
async def list_targets() -> list[dict]:
    return list(_targets.values())


@router.post("", status_code=201)
async def create_target(body: dict) -> dict:
    target_id = str(uuid.uuid4())[:8]
    target = {
        "id": target_id,
        "name": body["name"],
        "company": body.get("company"),
        "role": body.get("role"),
        "reason": body.get("reason", ""),
        "priority": body.get("priority", "medium"),
        "status": "searching",
        "added_at": datetime.now(timezone.utc).isoformat(),
        "matched_events": [],
    }
    _targets[target_id] = target
    return target


@router.put("/{target_id}")
async def update_target(target_id: str, body: dict) -> dict:
    if target_id not in _targets:
        raise HTTPException(status_code=404, detail="Target not found")
    _targets[target_id].update(body)
    return _targets[target_id]


@router.delete("/{target_id}", status_code=204)
async def delete_target(target_id: str) -> None:
    if target_id not in _targets:
        raise HTTPException(status_code=404, detail="Target not found")
    del _targets[target_id]


@router.get("/{target_id}/matches")
async def get_target_matches(target_id: str) -> list[dict]:
    if target_id not in _targets:
        raise HTTPException(status_code=404, detail="Target not found")
    return _targets[target_id].get("matched_events", [])
