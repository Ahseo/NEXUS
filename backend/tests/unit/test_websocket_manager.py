"""Tests for WebSocket ConnectionManager."""

from __future__ import annotations

import json
from unittest.mock import AsyncMock, MagicMock

import pytest

from app.core.websocket import ConnectionManager


@pytest.fixture
def mgr() -> ConnectionManager:
    return ConnectionManager()


def _make_ws(accept: bool = True) -> MagicMock:
    ws = AsyncMock()
    ws.accept = AsyncMock()
    ws.send_text = AsyncMock()
    return ws


class TestConnect:
    @pytest.mark.asyncio
    async def test_connect_accepts_websocket(self, mgr: ConnectionManager) -> None:
        ws = _make_ws()
        await mgr.connect("user-1", ws)
        ws.accept.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_connect_tracks_connection(self, mgr: ConnectionManager) -> None:
        ws = _make_ws()
        await mgr.connect("user-1", ws)
        assert mgr.active_count == 1

    @pytest.mark.asyncio
    async def test_connect_multiple_users(self, mgr: ConnectionManager) -> None:
        await mgr.connect("user-1", _make_ws())
        await mgr.connect("user-2", _make_ws())
        assert mgr.active_count == 2


class TestDisconnect:
    @pytest.mark.asyncio
    async def test_disconnect_removes_connection(self, mgr: ConnectionManager) -> None:
        ws = _make_ws()
        await mgr.connect("user-1", ws)
        mgr.disconnect("user-1")
        assert mgr.active_count == 0

    def test_disconnect_unknown_user(self, mgr: ConnectionManager) -> None:
        # Should not raise
        mgr.disconnect("nonexistent")
        assert mgr.active_count == 0


class TestSendPersonal:
    @pytest.mark.asyncio
    async def test_sends_to_correct_user(self, mgr: ConnectionManager) -> None:
        ws1 = _make_ws()
        ws2 = _make_ws()
        await mgr.connect("user-1", ws1)
        await mgr.connect("user-2", ws2)

        await mgr.send_personal("user-1", {"type": "event:discovered"})

        ws1.send_text.assert_awaited_once()
        ws2.send_text.assert_not_awaited()

    @pytest.mark.asyncio
    async def test_sends_json_string(self, mgr: ConnectionManager) -> None:
        ws = _make_ws()
        await mgr.connect("user-1", ws)

        msg = {"type": "event:analyzed", "data": {"id": "e-1"}}
        await mgr.send_personal("user-1", msg)

        ws.send_text.assert_awaited_once_with(json.dumps(msg))

    @pytest.mark.asyncio
    async def test_send_to_nonexistent_user(self, mgr: ConnectionManager) -> None:
        # Should not raise
        await mgr.send_personal("ghost", {"type": "test"})

    @pytest.mark.asyncio
    async def test_disconnects_on_error(self, mgr: ConnectionManager) -> None:
        ws = _make_ws()
        ws.send_text = AsyncMock(side_effect=RuntimeError("closed"))
        await mgr.connect("user-1", ws)

        await mgr.send_personal("user-1", {"type": "test"})
        assert mgr.active_count == 0


class TestBroadcast:
    @pytest.mark.asyncio
    async def test_broadcast_sends_to_all(self, mgr: ConnectionManager) -> None:
        ws1 = _make_ws()
        ws2 = _make_ws()
        await mgr.connect("user-1", ws1)
        await mgr.connect("user-2", ws2)

        msg = {"type": "agent:status", "data": {"status": "running"}}
        await mgr.broadcast(msg)

        text = json.dumps(msg)
        ws1.send_text.assert_awaited_once_with(text)
        ws2.send_text.assert_awaited_once_with(text)

    @pytest.mark.asyncio
    async def test_broadcast_to_empty(self, mgr: ConnectionManager) -> None:
        # Should not raise
        await mgr.broadcast({"type": "test"})

    @pytest.mark.asyncio
    async def test_broadcast_removes_failed_connections(
        self, mgr: ConnectionManager
    ) -> None:
        ws_good = _make_ws()
        ws_bad = _make_ws()
        ws_bad.send_text = AsyncMock(side_effect=RuntimeError("closed"))

        await mgr.connect("good", ws_good)
        await mgr.connect("bad", ws_bad)

        await mgr.broadcast({"type": "test"})

        assert mgr.active_count == 1
        ws_good.send_text.assert_awaited_once()


class TestWSEventTypes:
    """Verify all event types from README are valid JSON."""

    EVENT_TYPES = [
        "event:discovered",
        "event:analyzed",
        "event:applied",
        "event:scheduled",
        "person:discovered",
        "message:drafted",
        "message:sent",
        "agent:status",
        "target:found",
        "target:updated",
    ]

    @pytest.mark.asyncio
    async def test_all_event_types_serializable(
        self, mgr: ConnectionManager
    ) -> None:
        ws = _make_ws()
        await mgr.connect("user-1", ws)

        for event_type in self.EVENT_TYPES:
            msg = {"type": event_type, "data": {}, "priority": "medium"}
            await mgr.send_personal("user-1", msg)

        assert ws.send_text.await_count == len(self.EVENT_TYPES)
