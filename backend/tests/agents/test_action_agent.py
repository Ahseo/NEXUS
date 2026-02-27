from __future__ import annotations

from unittest.mock import AsyncMock, patch

import pytest

from app.agents.action import ActionAgent, ActionDecision
from app.integrations.yutori_client import YutoriTask


@pytest.fixture
def mock_yutori() -> AsyncMock:
    client = AsyncMock()
    client.browsing_create.return_value = YutoriTask(
        task_id="yut-task-001",
        status="running",
        result=None,
    )
    return client


@pytest.fixture
def agent(mock_yutori: AsyncMock) -> ActionAgent:
    return ActionAgent(yutori=mock_yutori)


@pytest.fixture
def sample_enriched_event() -> dict:
    return {
        "id": "evt-001",
        "url": "https://lu.ma/ai-dinner-sf",
        "title": "AI Founders Dinner -- SF",
        "description": "Intimate gathering of 30 founders and investors.",
        "source": "luma",
        "event_type": "dinner",
        "date": "2026-03-15T18:00:00Z",
        "location": "San Francisco, CA",
        "relevance_score": 90,
        "status": "analyzed",
    }


# -- decide ---------------------------------------------------------------


class TestDecide:
    def test_decide_auto_apply(self, agent: ActionAgent, test_user_profile: dict) -> None:
        decision = agent.decide(90, test_user_profile)
        assert decision.action == "auto_apply"
        assert decision.should_schedule is True

    def test_decide_suggest(self, agent: ActionAgent, test_user_profile: dict) -> None:
        decision = agent.decide(65, test_user_profile)
        assert decision.action == "suggest"
        assert decision.should_schedule is False

    def test_decide_skip(self, agent: ActionAgent, test_user_profile: dict) -> None:
        decision = agent.decide(30, test_user_profile)
        assert decision.action == "skip"
        assert decision.should_schedule is False


# -- apply_to_event -------------------------------------------------------


class TestApplyToEvent:
    async def test_apply_to_event_calls_yutori(
        self,
        agent: ActionAgent,
        mock_yutori: AsyncMock,
        sample_enriched_event: dict,
        test_user_profile: dict,
    ) -> None:
        with patch("app.agents.action.settings") as mock_settings:
            mock_settings.allow_side_effects = True
            mock_settings.max_auto_applies_per_day = 10
            mock_settings.backend_url = "http://localhost:8000"

            result = await agent.apply_to_event(sample_enriched_event, test_user_profile)

        assert result["status"] == "applied"
        assert result["yutori_task_id"] == "yut-task-001"
        mock_yutori.browsing_create.assert_called_once()
        call_kwargs = mock_yutori.browsing_create.call_args
        assert "John Park" in call_kwargs.kwargs["task"]
        assert "john@buildai.com" in call_kwargs.kwargs["task"]

    async def test_apply_to_event_no_client(
        self,
        sample_enriched_event: dict,
        test_user_profile: dict,
    ) -> None:
        agent = ActionAgent(yutori=None)
        result = await agent.apply_to_event(sample_enriched_event, test_user_profile)
        assert result["status"] == "error"
        assert "not_configured" in result["reason"]


# -- check_calendar_conflicts ---------------------------------------------


class TestCalendarConflicts:
    def test_calendar_conflict_detected(self, agent: ActionAgent) -> None:
        busy_periods = [
            {"start": "2026-03-15T17:00:00Z", "end": "2026-03-15T19:00:00Z"},
        ]
        assert agent.check_calendar_conflicts("2026-03-15T18:00:00Z", busy_periods) is True

    def test_calendar_no_conflict(self, agent: ActionAgent) -> None:
        busy_periods = [
            {"start": "2026-03-15T10:00:00Z", "end": "2026-03-15T11:00:00Z"},
        ]
        assert agent.check_calendar_conflicts("2026-03-15T18:00:00Z", busy_periods) is False


# -- apply_with_retry -----------------------------------------------------


class TestApplyWithRetry:
    async def test_apply_with_retry_succeeds(
        self,
        agent: ActionAgent,
        sample_enriched_event: dict,
        test_user_profile: dict,
    ) -> None:
        with patch("app.agents.action.settings") as mock_settings:
            mock_settings.allow_side_effects = True
            mock_settings.max_auto_applies_per_day = 10
            mock_settings.backend_url = "http://localhost:8000"

            result = await agent.apply_with_retry(sample_enriched_event, test_user_profile)

        assert result["status"] == "applied"

    async def test_apply_with_retry_fails(
        self,
        sample_enriched_event: dict,
        test_user_profile: dict,
    ) -> None:
        agent = ActionAgent(yutori=None)
        result = await agent.apply_with_retry(
            sample_enriched_event, test_user_profile, max_retries=2
        )
        assert result["status"] == "manual_required"
        assert result["url"] == sample_enriched_event["url"]


# -- process_event --------------------------------------------------------


class TestProcessEvent:
    async def test_process_event_auto_apply(
        self,
        agent: ActionAgent,
        sample_enriched_event: dict,
        test_user_profile: dict,
    ) -> None:
        sample_enriched_event["relevance_score"] = 90
        with patch("app.agents.action.settings") as mock_settings:
            mock_settings.allow_side_effects = True
            mock_settings.max_auto_applies_per_day = 10
            mock_settings.backend_url = "http://localhost:8000"
            mock_settings.auto_apply_threshold = 80
            mock_settings.suggest_threshold = 50

            result = await agent.process_event(sample_enriched_event, test_user_profile)

        assert result["action"] == "auto_apply"
        assert "application" in result
        assert "schedule" in result

    async def test_process_event_skip(
        self,
        agent: ActionAgent,
        sample_enriched_event: dict,
        test_user_profile: dict,
    ) -> None:
        sample_enriched_event["relevance_score"] = 30
        result = await agent.process_event(sample_enriched_event, test_user_profile)
        assert result["action"] == "skip"
        assert "application" not in result
