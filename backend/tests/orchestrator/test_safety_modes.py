"""Tests for NexusAgent safety modes.

Verifies that DRY_RUN, REPLAY, CANARY, and LIVE modes enforce
correct tool blocking, rate limiting, and permission rules.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any
from unittest.mock import AsyncMock

import pytest

from app.agents.orchestrator import NexusAgent, _SIDE_EFFECT_TOOLS
from app.core.config import NexusMode
from app.integrations.tavily_client import TavilySearchResult
from app.integrations.yutori_client import YutoriTask


def _today_str() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%d")


# ── Fixtures ────────────────────────────────────────────────────────────────


@pytest.fixture
def mock_tavily() -> AsyncMock:
    client = AsyncMock()
    client.search.return_value = TavilySearchResult(
        query="test",
        answer="answer",
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


SIDE_EFFECT_TOOLS = list(_SIDE_EFFECT_TOOLS)
READ_ONLY_TOOLS = [
    "tavily_search",
    "neo4j_query",
    "neo4j_write",
    "reka_vision",
    "resolve_social_accounts",
    "draft_message",
    "get_user_feedback",
    "wait",
]


# ── DRY_RUN mode ────────────────────────────────────────────────────────────


class TestDryRunMode:
    """DRY_RUN blocks all side-effect tools, allows read-only tools."""

    @pytest.fixture
    def agent(self, test_user_profile: dict[str, Any]) -> NexusAgent:
        return NexusAgent(
            user_profile=test_user_profile,
            mode=NexusMode.DRY_RUN,
        )

    def test_allow_side_effects_is_false(self, agent: NexusAgent) -> None:
        assert agent.allow_side_effects is False

    @pytest.mark.parametrize("tool_name", SIDE_EFFECT_TOOLS)
    async def test_blocks_all_side_effect_tools(
        self, agent: NexusAgent, tool_name: str
    ) -> None:
        result = await agent.execute_tool(tool_name, {})
        assert result["status"] == "blocked"
        assert "dry_run" in result["reason"]

    async def test_allows_tavily_search(self, agent: NexusAgent) -> None:
        result = await agent.execute_tool("tavily_search", {"query": "test"})
        # Not blocked by mode — fails on missing client
        assert "blocked" not in result.get("status", "")

    async def test_allows_wait_tool(self, agent: NexusAgent) -> None:
        result = await agent.execute_tool("wait", {"hours": 1, "reason": "test"})
        assert result["status"] == "waited"


# ── REPLAY mode ─────────────────────────────────────────────────────────────


class TestReplayMode:
    """REPLAY mode blocks side effects, same as DRY_RUN."""

    @pytest.fixture
    def agent(self, test_user_profile: dict[str, Any]) -> NexusAgent:
        return NexusAgent(
            user_profile=test_user_profile,
            mode=NexusMode.REPLAY,
        )

    def test_allow_side_effects_is_false(self, agent: NexusAgent) -> None:
        assert agent.allow_side_effects is False

    @pytest.mark.parametrize("tool_name", SIDE_EFFECT_TOOLS)
    async def test_blocks_all_side_effect_tools(
        self, agent: NexusAgent, tool_name: str
    ) -> None:
        result = await agent.execute_tool(tool_name, {})
        assert result["status"] == "blocked"
        assert "replay" in result["reason"]

    async def test_allows_read_only_tools(self, agent: NexusAgent) -> None:
        """Read-only tools pass mode guard (may fail on missing clients)."""
        result = await agent.execute_tool("tavily_search", {"query": "test"})
        assert result.get("status") != "blocked"

    async def test_allows_draft_message(self, agent: NexusAgent) -> None:
        result = await agent.execute_tool(
            "draft_message",
            {"recipient": {"name": "Test"}, "message_type": "cold_pre_event", "channel": "email"},
        )
        assert result["status"] == "drafted"


# ── CANARY mode ─────────────────────────────────────────────────────────────


class TestCanaryMode:
    """CANARY mode allows side effects but enforces daily limits."""

    @pytest.fixture
    def agent(
        self,
        test_user_profile: dict[str, Any],
        mock_tavily: AsyncMock,
        mock_yutori: AsyncMock,
    ) -> NexusAgent:
        return NexusAgent(
            user_profile=test_user_profile,
            mode=NexusMode.CANARY,
            tavily=mock_tavily,
            yutori=mock_yutori,
        )

    def test_allow_side_effects_is_true(self, agent: NexusAgent) -> None:
        assert agent.allow_side_effects is True

    async def test_allows_side_effects_within_limits(
        self, agent: NexusAgent
    ) -> None:
        """Side-effect tools work when under daily limits."""
        result = await agent.execute_tool(
            "yutori_browse",
            {"task": "Apply to event", "start_url": "https://lu.ma/event"},
        )
        assert result["status"] != "blocked"
        assert result["task_id"] == "task-1"

    async def test_blocks_yutori_browse_over_apply_limit(
        self, agent: NexusAgent
    ) -> None:
        """After max daily applies, yutori_browse is blocked."""
        agent._applies_today = 10
        agent._last_reset_date = _today_str()

        result = await agent.execute_tool(
            "yutori_browse",
            {"task": "Apply", "start_url": "https://lu.ma/event"},
        )
        assert result["status"] == "blocked"
        assert "Daily limit" in result["reason"]

    async def test_blocks_notify_user_over_message_limit(
        self, agent: NexusAgent
    ) -> None:
        """After max daily messages, notify_user is blocked."""
        agent._messages_today = 5
        agent._last_reset_date = _today_str()

        result = await agent.execute_tool(
            "notify_user",
            {"type": "event_suggested", "data": {}},
        )
        assert result["status"] == "blocked"
        assert "Daily limit" in result["reason"]

    async def test_increments_apply_counter(
        self, agent: NexusAgent
    ) -> None:
        """Successful yutori_browse increments _applies_today."""
        initial = agent._applies_today
        await agent.execute_tool(
            "yutori_browse",
            {"task": "Apply", "start_url": "https://lu.ma/event"},
        )
        assert agent._applies_today == initial + 1

    async def test_allows_read_tools_regardless_of_limits(
        self, agent: NexusAgent
    ) -> None:
        """Read-only tools are never limited by canary counters."""
        agent._applies_today = 100
        agent._messages_today = 100
        agent._last_reset_date = _today_str()

        result = await agent.execute_tool("tavily_search", {"query": "test"})
        assert result.get("status") != "blocked"

    def test_daily_counter_resets_on_new_day(self, agent: NexusAgent) -> None:
        """Canary counters reset when date changes."""
        agent._applies_today = 10
        agent._messages_today = 5
        agent._last_reset_date = "2020-01-01"

        allowed = agent._check_canary_limits("yutori_browse")
        assert allowed is True
        assert agent._applies_today == 0
        assert agent._messages_today == 0


# ── LIVE mode ───────────────────────────────────────────────────────────────


class TestLiveMode:
    """LIVE mode allows all tools with no canary limits."""

    @pytest.fixture
    def agent(
        self,
        test_user_profile: dict[str, Any],
        mock_tavily: AsyncMock,
        mock_yutori: AsyncMock,
    ) -> NexusAgent:
        return NexusAgent(
            user_profile=test_user_profile,
            mode=NexusMode.LIVE,
            tavily=mock_tavily,
            yutori=mock_yutori,
        )

    def test_allow_side_effects_is_true(self, agent: NexusAgent) -> None:
        assert agent.allow_side_effects is True

    async def test_allows_yutori_browse(self, agent: NexusAgent) -> None:
        result = await agent.execute_tool(
            "yutori_browse",
            {"task": "Apply to event", "start_url": "https://lu.ma/event"},
        )
        assert result["status"] != "blocked"
        assert result["task_id"] == "task-1"

    async def test_allows_yutori_scout(self, agent: NexusAgent) -> None:
        result = await agent.execute_tool(
            "yutori_scout",
            {"task": "Monitor", "start_url": "https://lu.ma"},
        )
        assert result["task_id"] == "scout-1"
        assert result["status"] == "running"

    async def test_allows_notify_user(self, agent: NexusAgent) -> None:
        result = await agent.execute_tool(
            "notify_user",
            {"type": "event_suggested", "data": {"event": "test"}},
        )
        assert result["status"] == "notified"

    async def test_allows_google_calendar(self, agent: NexusAgent) -> None:
        result = await agent.execute_tool(
            "google_calendar", {"action": "list_upcoming"}
        )
        # Passes mode guard — returns not_connected (no OAuth yet)
        assert result["status"] == "not_connected"

    async def test_no_canary_limits_applied(self, agent: NexusAgent) -> None:
        """LIVE mode doesn't enforce canary daily limits."""
        # _check_canary_limits only applies in CANARY mode
        assert agent._check_canary_limits("yutori_browse") is True
        assert agent._check_canary_limits("notify_user") is True

    async def test_allows_all_tools(
        self, agent: NexusAgent
    ) -> None:
        """Every tool should not be blocked by mode guard in LIVE."""
        for tool_name in SIDE_EFFECT_TOOLS:
            result = await agent.execute_tool(tool_name, _minimal_input(tool_name))
            assert result.get("status") != "blocked", f"{tool_name} was blocked in LIVE mode"


# ── Cross-mode comparison ───────────────────────────────────────────────────


class TestCrossModeComparison:
    """Compare behavior across all modes."""

    @pytest.mark.parametrize(
        "mode,expected_side_effects",
        [
            (NexusMode.DRY_RUN, False),
            (NexusMode.REPLAY, False),
            (NexusMode.CANARY, True),
            (NexusMode.LIVE, True),
        ],
    )
    def test_allow_side_effects_per_mode(
        self,
        test_user_profile: dict[str, Any],
        mode: NexusMode,
        expected_side_effects: bool,
    ) -> None:
        agent = NexusAgent(user_profile=test_user_profile, mode=mode)
        assert agent.allow_side_effects is expected_side_effects

    @pytest.mark.parametrize("mode", [NexusMode.DRY_RUN, NexusMode.REPLAY])
    async def test_side_effect_tools_blocked_in_safe_modes(
        self, test_user_profile: dict[str, Any], mode: NexusMode
    ) -> None:
        agent = NexusAgent(user_profile=test_user_profile, mode=mode)
        for tool_name in SIDE_EFFECT_TOOLS:
            result = await agent.execute_tool(tool_name, {})
            assert result["status"] == "blocked", (
                f"{tool_name} not blocked in {mode.value}"
            )


def _minimal_input(tool_name: str) -> dict[str, Any]:
    """Return minimal valid input for a given tool."""
    inputs: dict[str, dict[str, Any]] = {
        "yutori_browse": {"task": "test", "start_url": "https://example.com"},
        "yutori_scout": {"task": "test", "start_url": "https://example.com"},
        "google_calendar": {"action": "list_upcoming"},
        "notify_user": {"type": "status_update", "data": {}},
    }
    return inputs.get(tool_name, {})
