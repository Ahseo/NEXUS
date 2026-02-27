from __future__ import annotations

import json
import logging
from collections.abc import AsyncGenerator
from typing import Any

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

# ── Tools available to the chat agent ─────────────────────────────────────────

CHAT_TOOLS: list[dict[str, Any]] = [
    {
        "name": "tavily_search",
        "description": (
            "Search the web for events, people, companies, or any information. "
            "Use this to find upcoming events on Eventbrite, Luma, Meetup, etc. "
            "Also use this to research attendees, speakers, and companies."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "Search query"},
                "search_depth": {
                    "type": "string",
                    "enum": ["basic", "advanced"],
                    "default": "advanced",
                },
                "max_results": {"type": "integer", "default": 5},
                "include_domains": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Limit search to these domains (e.g. eventbrite.com, lu.ma)",
                },
                "time_range": {
                    "type": "string",
                    "enum": ["day", "week", "month"],
                    "description": "How recent the results should be",
                },
            },
            "required": ["query"],
        },
    },
]


SYSTEM_PROMPT = """You are NEXUS, an autonomous networking agent for SF tech professionals.
You help the user discover events, research people, and build connections.

Current user profile:
- Name: {name}
- Role: {role} at {company}
- Interests: {interests}
- Networking goals: {goals}

You have access to web search via the tavily_search tool. USE IT to find real events,
research real people, and get up-to-date information. Do NOT say you can't search the web
— you CAN. When the user asks you to find events or people, actually search for them.

When searching for events:
1. Use tavily_search with relevant keywords + city (SF, San Francisco)
2. Include domains like eventbrite.com, lu.ma, meetup.com for better results
3. Use time_range "week" or "month" to get upcoming events
4. Present results clearly with title, date, location, link

Be concise and actionable. Use the user's interests and goals to personalize your responses.
"""


class ChatMessage(BaseModel):
    message: str


# In-memory chat history per user (hackathon)
_chat_histories: dict[str, list[dict[str, Any]]] = {}


async def _execute_chat_tool(
    tool_name: str, tool_input: dict[str, Any]
) -> dict[str, Any]:
    """Execute a chat tool and return the result."""
    if tool_name == "tavily_search":
        if not settings.tavily_api_key:
            return {"error": "Tavily API key not configured"}

        from app.integrations.tavily_client import TavilyClient

        try:
            client = TavilyClient(api_key=settings.tavily_api_key)
            result = await client.search(
                query=tool_input["query"],
                search_depth=tool_input.get("search_depth", "advanced"),
                max_results=tool_input.get("max_results", 5),
                include_domains=tool_input.get("include_domains"),
                time_range=tool_input.get("time_range"),
                include_answer=True,
            )
            return {
                "query": result.query,
                "answer": result.answer,
                "results": [
                    {
                        "title": r.get("title", ""),
                        "url": r.get("url", ""),
                        "content": r.get("content", "")[:500],
                    }
                    for r in result.results
                ],
            }
        except Exception as e:
            logger.error("Tavily search error: %s", e)
            return {"error": str(e)}

    return {"error": f"Unknown tool: {tool_name}"}


def _sse(event_type: str, data: Any) -> str:
    return f"data: {json.dumps({'type': event_type, **data} if isinstance(data, dict) else {'type': event_type, 'content': data})}\n\n"


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
    await manager.broadcast(
        {
            "type": "agent:status",
            "data": {"status": "thinking", "agent": "chat"},
        }
    )

    async def generate() -> AsyncGenerator[str, None]:
        client = anthropic.AsyncAnthropic(api_key=settings.anthropic_api_key)
        full_response = ""

        # Build messages for this round (may include tool results)
        round_messages: list[dict[str, Any]] = list(history)

        try:
            # Tool use loop: up to 5 rounds of tool calls
            for _round in range(5):
                # Stream the response
                round_text = ""

                async with client.messages.stream(
                    model="claude-sonnet-4-20250514",
                    max_tokens=2048,
                    system=system,
                    tools=CHAT_TOOLS,  # type: ignore[arg-type]
                    messages=round_messages,  # type: ignore[arg-type]
                ) as stream:
                    async for text in stream.text_stream:
                        round_text += text
                        yield _sse("text", text)

                    # Get the full message to check for tool use
                    final_msg = await stream.get_final_message()

                full_response += round_text

                # Check for tool use blocks
                tool_blocks = [
                    b for b in final_msg.content if b.type == "tool_use"
                ]

                if not tool_blocks:
                    # No tools — we're done
                    break

                # Execute tools and send status events
                round_messages.append(
                    {
                        "role": "assistant",
                        "content": [
                            b.model_dump() for b in final_msg.content
                        ],
                    }
                )
                tool_results: list[dict[str, Any]] = []
                for block in tool_blocks:
                    # Tell frontend which tool is being used
                    yield _sse(
                        "tool_use",
                        {"tool": block.name, "input": {"query": block.input.get("query", "")} if isinstance(block.input, dict) else {}},  # type: ignore[union-attr]
                    )

                    result = await _execute_chat_tool(
                        block.name,
                        block.input if isinstance(block.input, dict) else {},  # type: ignore[arg-type]
                    )
                    tool_results.append(
                        {
                            "type": "tool_result",
                            "tool_use_id": block.id,
                            "content": json.dumps(result),
                        }
                    )

                round_messages.append(
                    {"role": "user", "content": tool_results}
                )

            # Save assistant response to history (text only for simplicity)
            history.append({"role": "assistant", "content": full_response})

            yield _sse("done", {})

        except Exception as e:
            logger.exception("Chat stream error")
            yield _sse("error", str(e))

        # Broadcast agent done
        await manager.broadcast(
            {
                "type": "agent:status",
                "data": {"status": "idle", "agent": "chat"},
            }
        )

    return StreamingResponse(generate(), media_type="text/event-stream")


@router.get("/history")
async def get_history(user: CurrentUser) -> list[dict[str, Any]]:
    """Return chat history for current user."""
    return _chat_histories.get(user["user_id"], [])


@router.delete("/history")
async def clear_history(user: CurrentUser) -> dict[str, str]:
    """Clear chat history for current user."""
    _chat_histories.pop(user["user_id"], None)
    return {"status": "cleared"}
