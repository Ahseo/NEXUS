from fastapi import APIRouter, Depends, HTTPException

from app.core.deps import get_current_user

router = APIRouter(
    prefix="/api/messages",
    tags=["messages"],
    dependencies=[Depends(get_current_user)],
)

_messages: dict[str, dict] = {}


@router.get("")
async def list_messages(
    status: str | None = None,
    limit: int = 20,
) -> list[dict]:
    msgs = list(_messages.values())
    if status:
        msgs = [m for m in msgs if m.get("status") == status]
    return msgs[:limit]


@router.get("/{message_id}")
async def get_message(message_id: str) -> dict:
    if message_id not in _messages:
        raise HTTPException(status_code=404, detail="Message not found")
    return _messages[message_id]


@router.post("/{message_id}/approve", status_code=200)
async def approve_message(message_id: str) -> dict:
    if message_id not in _messages:
        raise HTTPException(status_code=404, detail="Message not found")
    _messages[message_id]["status"] = "approved"
    return {"status": "approved", "message_id": message_id}


@router.post("/{message_id}/edit", status_code=200)
async def edit_message(message_id: str, body: dict) -> dict:
    if message_id not in _messages:
        raise HTTPException(status_code=404, detail="Message not found")
    _messages[message_id]["content"] = body.get("content", "")
    _messages[message_id]["status"] = "edited"
    return {"status": "edited", "message_id": message_id}


@router.post("/{message_id}/reject", status_code=200)
async def reject_message(message_id: str) -> dict:
    if message_id not in _messages:
        raise HTTPException(status_code=404, detail="Message not found")
    _messages[message_id]["status"] = "rejected"
    return {"status": "rejected", "message_id": message_id}
