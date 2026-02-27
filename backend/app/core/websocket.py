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
        text = json.dumps(message)
        disconnected: list[str] = []
        for user_id, ws in self._connections.items():
            try:
                await ws.send_text(text)
            except Exception:
                disconnected.append(user_id)
        for uid in disconnected:
            self.disconnect(uid)


# Global instance
manager = ConnectionManager()
