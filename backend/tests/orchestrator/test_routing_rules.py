"""Tests for NexusAgent tool routing.

Verifies that execute_tool dispatches each of the 12 tools to the correct
integration client method and that unknown tools return an error dict.
"""

from __future__ import annotations

from typing import Any
from unittest.mock import AsyncMock, MagicMock

import pytest

from app.agents.orchestrator import NexusAgent
from app.core.config import NexusMode
from app.integrations.reka_client import RekaVisionResult
from app.integrations.tavily_client import TavilySearchResult
from app.integrations.yutori_client import YutoriTask


# ── Fixtures ──────────────────────────────────────────────────────────────────


@pytest.fixture
def mock_tavily() -> AsyncMock:
    client = AsyncMock()
    client.search.return_value = TavilySearchResult(
        query="test",
        answer="test answer",
        results=[{"title": "T", "url": "https://example.com", "content": "C"}],
        raw_content=[],
    )
    return client


@pytest.fixture
def mock_yutori() -> AsyncMock:
    client = AsyncMock()
    client.browsing_create.return_value = YutoriTask(
        task_id="task-1", status="completed", result={"output": "done"}
    )
    client.scouting_create.return_value = YutoriTask(
        task_id="scout-1", status="running", result=None
    )
    return client


@pytest.fixture
def mock_neo4j() -> AsyncMock:
    client = AsyncMock()
    client.execute_query.return_value = [{"n": "node"}]
    client.execute_write.return_value = [{"n": "written"}]
    return client


@pytest.fixture
def mock_reka() -> AsyncMock:
    client = AsyncMock()
    result = RekaVisionResult(
        analysis="Person detected",
        conversation_hooks=["Likes AI"],
        raw={},
    )
    client.analyze.return_value = result
    client.compare.return_value = result
    return client


@pytest.fixture
def agent(
    test_user_profile: dict,
    mock_tavily: AsyncMock,
    mock_yutori: AsyncMock,
    mock_neo4j: AsyncMock,
    mock_reka: AsyncMock,
) -> NexusAgent:
    return NexusAgent(
        user_profile=test_user_profile,
        tavily=mock_tavily,
        yutori=mock_yutori,
        neo4j=mock_neo4j,
        reka=mock_reka,
        mode=NexusMode.LIVE,
    )


# ── Routing Tests ─────────────────────────────────────────────────────────────


class TestTavilyRouting:
    @pytest.mark.asyncio
    async def test_tavily_search_calls_client(
        self, agent: NexusAgent, mock_tavily: AsyncMock
    ) -> None:
        result = await agent.execute_tool(
            "tavily_search", {"query": "AI events SF"}
        )
        mock_tavily.search.assert_awaited_once()
        assert "query" in result
        assert "answer" in result
        assert "results" in result


class TestYutoriRouting:
    @pytest.mark.asyncio
    async def test_yutori_browse_calls_browsing_create(
        self, agent: NexusAgent, mock_yutori: AsyncMock
    ) -> None:
        result = await agent.execute_tool(
            "yutori_browse",
            {"task": "Apply to event", "start_url": "https://lu.ma/event"},
        )
        mock_yutori.browsing_create.assert_awaited_once()
        assert result["task_id"] == "task-1"
        assert result["status"] == "completed"

    @pytest.mark.asyncio
    async def test_yutori_scout_calls_scouting_create(
        self, agent: NexusAgent, mock_yutori: AsyncMock
    ) -> None:
        result = await agent.execute_tool(
            "yutori_scout",
            {"task": "Monitor luma", "start_url": "https://lu.ma"},
        )
        mock_yutori.scouting_create.assert_awaited_once()
        assert result["task_id"] == "scout-1"


class TestRekaRouting:
    @pytest.mark.asyncio
    async def test_reka_vision_analyze(
        self, agent: NexusAgent, mock_reka: AsyncMock
    ) -> None:
        result = await agent.execute_tool(
            "reka_vision",
            {"url": "https://img.example.com/photo.jpg", "prompt": "Who is this?"},
        )
        mock_reka.analyze.assert_awaited_once()
        assert result["analysis"] == "Person detected"
        assert result["conversation_hooks"] == ["Likes AI"]

    @pytest.mark.asyncio
    async def test_reka_vision_compare(
        self, agent: NexusAgent, mock_reka: AsyncMock
    ) -> None:
        result = await agent.execute_tool(
            "reka_vision",
            {
                "url": "https://img.example.com/a.jpg",
                "prompt": "Same person?",
                "compare_urls": [
                    "https://img.example.com/a.jpg",
                    "https://img.example.com/b.jpg",
                ],
            },
        )
        mock_reka.compare.assert_awaited_once()
        assert "analysis" in result


class TestNeo4jRouting:
    @pytest.mark.asyncio
    async def test_neo4j_query_calls_execute_query(
        self, agent: NexusAgent, mock_neo4j: AsyncMock
    ) -> None:
        result = await agent.execute_tool(
            "neo4j_query", {"cypher": "MATCH (n) RETURN n LIMIT 1"}
        )
        mock_neo4j.execute_query.assert_awaited_once_with(
            "MATCH (n) RETURN n LIMIT 1", None
        )
        assert result["records"] == [{"n": "node"}]
        assert result["count"] == 1

    @pytest.mark.asyncio
    async def test_neo4j_write_calls_execute_write(
        self, agent: NexusAgent, mock_neo4j: AsyncMock
    ) -> None:
        result = await agent.execute_tool(
            "neo4j_write",
            {"cypher": "CREATE (n:Test {name: $name})", "params": {"name": "test"}},
        )
        mock_neo4j.execute_write.assert_awaited_once_with(
            "CREATE (n:Test {name: $name})", {"name": "test"}
        )
        assert result["status"] == "written"


class TestGoogleCalendarRouting:
    @pytest.mark.asyncio
    async def test_google_calendar_returns_not_connected(
        self, agent: NexusAgent
    ) -> None:
        result = await agent.execute_tool(
            "google_calendar", {"action": "list_upcoming"}
        )
        assert result["status"] == "not_connected"
        assert result["action"] == "list_upcoming"


class TestResolveSocialRouting:
    @pytest.mark.asyncio
    async def test_resolve_social_accounts(
        self, agent: NexusAgent, mock_tavily: AsyncMock
    ) -> None:
        result = await agent.execute_tool(
            "resolve_social_accounts",
            {"name": "John Doe", "company": "Acme"},
        )
        assert result["name"] == "John Doe"
        assert "social_links" in result
        # Should have called tavily search at least once (LinkedIn + Twitter)
        assert mock_tavily.search.await_count >= 1


class TestDraftMessageRouting:
    @pytest.mark.asyncio
    async def test_draft_message(self, agent: NexusAgent) -> None:
        result = await agent.execute_tool(
            "draft_message",
            {
                "recipient": {"name": "Jane"},
                "message_type": "cold_pre_event",
                "channel": "linkedin",
            },
        )
        assert result["status"] == "drafted"
        assert result["message_type"] == "cold_pre_event"
        assert result["channel"] == "linkedin"


class TestGetUserFeedbackRouting:
    @pytest.mark.asyncio
    async def test_get_user_feedback(self, agent: NexusAgent) -> None:
        result = await agent.execute_tool(
            "get_user_feedback", {"since": "2025-01-01T00:00:00Z"}
        )
        assert "feedback" in result
        assert result["feedback"] == []


class TestNotifyUserRouting:
    @pytest.mark.asyncio
    async def test_notify_user(self, agent: NexusAgent) -> None:
        result = await agent.execute_tool(
            "notify_user",
            {"type": "event_suggested", "data": {"event": "AI meetup"}},
        )
        assert result["status"] == "notified"
        assert result["type"] == "event_suggested"

    @pytest.mark.asyncio
    async def test_notify_user_with_ws_broadcast(
        self, test_user_profile: dict
    ) -> None:
        ws_broadcast = AsyncMock()
        agent = NexusAgent(
            user_profile=test_user_profile,
            mode=NexusMode.LIVE,
            ws_broadcast=ws_broadcast,
        )
        result = await agent.execute_tool(
            "notify_user",
            {
                "type": "status_update",
                "data": {"msg": "hi"},
                "priority": "high",
            },
        )
        ws_broadcast.assert_awaited_once()
        assert result["status"] == "notified"
        assert result["priority"] == "high"


class TestWaitRouting:
    @pytest.mark.asyncio
    async def test_wait(self, agent: NexusAgent) -> None:
        result = await agent.execute_tool(
            "wait", {"hours": 2, "reason": "cycle done"}
        )
        assert result["status"] == "waited"
        assert result["hours"] == 2


class TestUnknownTool:
    @pytest.mark.asyncio
    async def test_unknown_tool_returns_error(self, agent: NexusAgent) -> None:
        result = await agent.execute_tool(
            "nonexistent_tool", {"foo": "bar"}
        )
        assert "error" in result
        assert "Unknown tool" in result["error"]


class TestClientNotConfigured:
    """When a client is None, the tool should return an error."""

    @pytest.mark.asyncio
    async def test_tavily_not_configured(
        self, test_user_profile: dict
    ) -> None:
        agent = NexusAgent(
            user_profile=test_user_profile, mode=NexusMode.LIVE
        )
        result = await agent.execute_tool(
            "tavily_search", {"query": "test"}
        )
        assert result == {"error": "Tavily client not configured"}

    @pytest.mark.asyncio
    async def test_yutori_not_configured(
        self, test_user_profile: dict
    ) -> None:
        agent = NexusAgent(
            user_profile=test_user_profile, mode=NexusMode.LIVE
        )
        result = await agent.execute_tool(
            "yutori_browse",
            {"task": "test", "start_url": "https://example.com"},
        )
        assert result == {"error": "Yutori client not configured"}

    @pytest.mark.asyncio
    async def test_neo4j_not_configured(
        self, test_user_profile: dict
    ) -> None:
        agent = NexusAgent(
            user_profile=test_user_profile, mode=NexusMode.LIVE
        )
        result = await agent.execute_tool(
            "neo4j_query", {"cypher": "MATCH (n) RETURN n"}
        )
        assert result == {"error": "Neo4j client not configured"}

    @pytest.mark.asyncio
    async def test_reka_not_configured(
        self, test_user_profile: dict
    ) -> None:
        agent = NexusAgent(
            user_profile=test_user_profile, mode=NexusMode.LIVE
        )
        result = await agent.execute_tool(
            "reka_vision",
            {"url": "https://example.com/img.jpg", "prompt": "analyze"},
        )
        assert result == {"error": "Reka client not configured"}
