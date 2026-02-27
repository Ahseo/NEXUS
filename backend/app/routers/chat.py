from __future__ import annotations

import json
import logging
from collections.abc import AsyncGenerator

from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from app.core.config import settings
from app.core.deps import CurrentUser, DbSession, get_current_user
from app.core.websocket import manager
from app.models.profile import UserProfileDB

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/chat",
    tags=["chat"],
    dependencies=[Depends(get_current_user)],
)

SYSTEM_PROMPT = """You are NEXUS, an autonomous networking agent for SF tech professionals.
You help the user discover events, research people, and build connections.

Current user profile:
- Name: {name}
- Role: {role} at {company}
- Interests: {interests}
- Networking goals: {goals}

You can:
1. Search for upcoming events matching user interests
2. Analyze events and score their relevance
3. Research attendees and speakers
4. Draft cold messages
5. Check calendar conflicts

When the user asks you to find events or people, describe what you would do step by step.
Be concise and actionable. Use the user's interests and goals to personalize your responses.
"""


class ChatMessage(BaseModel):
    message: str


class ChatHistory(BaseModel):
    messages: list[dict[str, str]]


# In-memory chat history per user (hackathon)
_chat_histories: dict[str, list[dict[str, str]]] = {}


@router.post("/send")
async def send_message(
    body: ChatMessage,
    user: CurrentUser,
    db: DbSession,
) -> StreamingResponse:
    """Send a message to the NEXUS agent and stream the response."""
    import anthropic

    user_id = user["user_id"]

    # Load user profile for context
    profile = await db.get(UserProfileDB, user_id)
    profile_context = {
        "name": profile.name if profile else "User",
        "role": profile.role if profile else "",
        "company": profile.company if profile else "",
        "interests": ", ".join(profile.interests or []) if profile else "",
        "goals": ", ".join(profile.networking_goals or []) if profile else "",
    }

    system = SYSTEM_PROMPT.format(**profile_context)

    # Get or init history
    if user_id not in _chat_histories:
        _chat_histories[user_id] = []
    history = _chat_histories[user_id]

    # Add user message
    history.append({"role": "user", "content": body.message})

    # Keep last 20 messages
    if len(history) > 20:
        history[:] = history[-20:]

    # Broadcast to websocket that agent is working
    await manager.broadcast({
        "type": "agent:status",
        "data": {"status": "thinking", "agent": "chat"},
    })

    async def generate() -> AsyncGenerator[str, None]:
        client = anthropic.AsyncAnthropic(api_key=settings.anthropic_api_key)
        full_response = ""

        try:
            async with client.messages.stream(
                model="claude-sonnet-4-20250514",
                max_tokens=1024,
                system=system,
                messages=history,  # type: ignore[arg-type]
            ) as stream:
                async for text in stream.text_stream:
                    full_response += text
                    yield f"data: {json.dumps({'type': 'text', 'content': text})}\n\n"

            # Save assistant response to history
            history.append({"role": "assistant", "content": full_response})

            yield f"data: {json.dumps({'type': 'done'})}\n\n"

        except Exception as e:
            logger.exception("Chat stream error")
            yield f"data: {json.dumps({'type': 'error', 'content': str(e)})}\n\n"

        # Broadcast agent done
        await manager.broadcast({
            "type": "agent:status",
            "data": {"status": "idle", "agent": "chat"},
        })

    return StreamingResponse(generate(), media_type="text/event-stream")


@router.get("/history")
async def get_history(user: CurrentUser) -> list[dict[str, str]]:
    """Return chat history for current user."""
    return _chat_histories.get(user["user_id"], [])


@router.delete("/history")
async def clear_history(user: CurrentUser) -> dict[str, str]:
    """Clear chat history for current user."""
    _chat_histories.pop(user["user_id"], None)
    return {"status": "cleared"}
