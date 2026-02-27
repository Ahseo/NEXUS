"""WebSocket connection manager for real-time UI updates."""

from __future__ import annotations

import json
import logging
from typing import Any

from fastapi import WebSocket

logger = logging.getLogger(__name__)


class ConnectionManager:
    """Manages WebSocket connections for real-time event broadcasting."""

    def __init__(self) -> None:
        self._connections: dict[str, WebSocket] = {}

    @property
    def active_count(self) -> int:
        return len(self._connections)

    async def connect(self, user_id: str, websocket: WebSocket) -> None:
        await websocket.accept()
        self._connections[user_id] = websocket
        logger.info("WebSocket connected: %s (total: %d)", user_id, self.active_count)

    def disconnect(self, user_id: str) -> None:
        self._connections.pop(user_id, None)
        logger.info("WebSocket disconnected: %s (total: %d)", user_id, self.active_count)

    async def send_personal(self, user_id: str, message: dict[str, Any]) -> None:
        ws = self._connections.get(user_id)
        if ws:
            try:
                await ws.send_text(json.dumps(message))
            except Exception:
                self.disconnect(user_id)

    async def broadcast(self, message: dict[str, Any]) -> None:
        """Broadcast to all connected clients AND persist to DB."""
        text = json.dumps(message)
        disconnected: list[str] = []
        for user_id, ws in self._connections.items():
            try:
                await ws.send_text(text)
            except Exception:
                disconnected.append(user_id)
        for uid in disconnected:
            self.disconnect(uid)

        # Persist event to DB (fire-and-forget, don't block broadcast)
        await self._persist_event(message)

    async def _persist_event(self, message: dict[str, Any]) -> None:
        """Store the event in the agent_events table."""
        try:
            from app.core.database import async_session_factory
            from app.models.agent_event import AgentEventDB

            event_type = message.get("type", "unknown")
            data = message.get("data", {})
            source = data.get("agent", "nexus") if isinstance(data, dict) else "nexus"

            # Build a human-readable message
            msg, detail = _format_event(event_type, data)

            async with async_session_factory() as session:
                event = AgentEventDB(
                    event_type=event_type,
                    source=source,
                    message=msg,
                    detail=detail,
                    data=data if isinstance(data, dict) else None,
                )
                session.add(event)
                await session.commit()
        except Exception:
            logger.debug("Failed to persist agent event", exc_info=True)


def _format_event(event_type: str, data: Any) -> tuple[str, str]:
    """Return (message, detail) for an event."""
    if not isinstance(data, dict):
        return (event_type, "")

    formatters: dict[str, Any] = {
        "event:discovered": lambda d: (
            f"Found event: {_nested(d, 'event', 'title', 'unknown')}",
            f"Count: {d.get('count', '-')}",
        ),
        "event:analyzed": lambda d: (
            f"Recommended: {_nested(d, 'event', 'title', 'event')} (Score: {d.get('score', '-')})",
            d.get("why", ""),
        ),
        "event:applied": lambda d: (
            (
                f"Payment required: {_nested(d, 'event', 'title', 'event')}"
                if d.get("payment_required")
                else f"Applied to: {_nested(d, 'event', 'title', 'event')}"
            ),
            f"Amount: ${d['payment_amount']}" if d.get("payment_amount") else "",
        ),
        "event:scheduled": lambda d: (
            f"Scheduled: {_nested(d, 'event', 'title', 'event')}",
            "",
        ),
        "person:discovered": lambda d: (
            f"Discovered person: {_nested(d, 'person', 'name', 'unknown')}",
            "",
        ),
        "message:drafted": lambda d: (
            "Drafted a message",
            f"Channel: {d.get('channel', '-')}, Type: {d.get('type', '-')}",
        ),
        "message:sent": lambda _d: ("Sent a message", ""),
        "agent:status": lambda d: (
            f"Tool: {d['tool']}" if d.get("tool") else f"Agent {d.get('status', 'unknown')}",
            d.get("detail", "") if d.get("detail") else (f"Status: {d.get('status')}" if d.get("tool") else ""),
        ),
        "target:found": lambda d: (
            f"Target person matched: {_nested(d, 'target', 'name', '')}",
            "",
        ),
        "target:updated": lambda d: (
            f"Target updated: {_nested(d, 'target', 'name', '')}",
            "",
        ),
    }

    fn = formatters.get(event_type)
    if fn:
        return fn(data)
    return (event_type, json.dumps(data)[:200] if data else "")


def _nested(d: dict[str, Any], key: str, sub: str, default: str) -> str:
    obj = d.get(key)
    if isinstance(obj, dict):
        return str(obj.get(sub, default))
    return default


# Global instance
manager = ConnectionManager()
