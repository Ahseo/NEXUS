from __future__ import annotations

from unittest.mock import AsyncMock

import pytest

from app.agents.discovery import DiscoveryAgent, _build_queries, _source_from_url
from app.integrations.tavily_client import TavilySearchResult
from app.models.event import EventSource


@pytest.fixture
def mock_tavily() -> AsyncMock:
    return AsyncMock()


@pytest.fixture
def agent(mock_tavily: AsyncMock) -> DiscoveryAgent:
    return DiscoveryAgent(tavily=mock_tavily)


def _make_search_result(items: list[dict]) -> TavilySearchResult:
    return TavilySearchResult(
        query="test",
        answer=None,
        results=items,
        raw_content=[],
    )


# ── _source_from_url ────────────────────────────────────────────────────────


class TestSourceFromUrl:
    def test_luma(self) -> None:
        assert _source_from_url("https://lu.ma/ai-dinner") == EventSource.LUMA

    def test_luma_cal(self) -> None:
        assert _source_from_url("https://luma-cal.com/event/123") == EventSource.LUMA

    def test_eventbrite(self) -> None:
        assert (
            _source_from_url("https://www.eventbrite.com/e/123") == EventSource.EVENTBRITE
        )

    def test_meetup(self) -> None:
        assert _source_from_url("https://www.meetup.com/group/events") == EventSource.MEETUP

    def test_partiful(self) -> None:
        assert _source_from_url("https://partiful.com/e/xyz") == EventSource.PARTIFUL

    def test_unknown_domain(self) -> None:
        assert _source_from_url("https://random-site.com/event") == EventSource.OTHER


# ── _build_queries ──────────────────────────────────────────────────────────


class TestBuildQueries:
    def test_uses_interests(self, test_user_profile: dict) -> None:
        queries = _build_queries(test_user_profile)
        assert len(queries) <= 3
        assert any("AI agents" in q for q in queries)

    def test_fallback_for_empty_profile(self) -> None:
        queries = _build_queries({})
        assert queries == ["SF tech events this week"]

    def test_deduplicates_terms(self) -> None:
        profile = {"interests": ["AI", "ai"], "target_industries": ["AI"]}
        queries = _build_queries(profile)
        assert len(queries) == 1


# ── discover_events_tavily ──────────────────────────────────────────────────


class TestDiscoverEventsTavily:
    async def test_returns_events_from_search(
        self,
        agent: DiscoveryAgent,
        mock_tavily: AsyncMock,
        test_user_profile: dict,
    ) -> None:
        mock_tavily.search.return_value = _make_search_result(
            [
                {
                    "title": "AI Dinner",
                    "url": "https://lu.ma/ai-dinner",
                    "content": "A great dinner for AI folks.",
                },
                {
                    "title": "Startup Pitch Night",
                    "url": "https://www.eventbrite.com/e/pitch-night",
                    "content": "10 startups pitch to VCs.",
                },
            ]
        )
        events = await agent.discover_events_tavily(test_user_profile)
        assert len(events) >= 2
        luma_event = next(e for e in events if "Dinner" in e["title"])
        assert luma_event["source"] == "luma"
        eb_event = next(e for e in events if "Pitch" in e["title"])
        assert eb_event["source"] == "eventbrite"

    async def test_source_correctly_determined(
        self,
        agent: DiscoveryAgent,
        mock_tavily: AsyncMock,
        test_user_profile: dict,
    ) -> None:
        mock_tavily.search.return_value = _make_search_result(
            [
                {"title": "ML Meetup", "url": "https://www.meetup.com/ml", "content": ""},
                {"title": "Party", "url": "https://partiful.com/e/party", "content": ""},
            ]
        )
        events = await agent.discover_events_tavily(test_user_profile)
        sources = {e["source"] for e in events}
        assert "meetup" in sources
        assert "partiful" in sources

    async def test_empty_search_results(
        self,
        agent: DiscoveryAgent,
        mock_tavily: AsyncMock,
        test_user_profile: dict,
    ) -> None:
        mock_tavily.search.return_value = _make_search_result([])
        events = await agent.discover_events_tavily(test_user_profile)
        assert events == []

    async def test_queries_include_user_interests(
        self,
        agent: DiscoveryAgent,
        mock_tavily: AsyncMock,
        test_user_profile: dict,
    ) -> None:
        mock_tavily.search.return_value = _make_search_result([])
        await agent.discover_events_tavily(test_user_profile)
        calls = mock_tavily.search.call_args_list
        queries = [call.args[0] for call in calls]
        assert any("AI agents" in q for q in queries)

    async def test_skips_items_without_title_or_url(
        self,
        agent: DiscoveryAgent,
        mock_tavily: AsyncMock,
        test_user_profile: dict,
    ) -> None:
        items_result = _make_search_result(
            [
                {"title": "", "url": "https://lu.ma/x", "content": ""},
                {"title": "Valid", "url": "", "content": ""},
                {"title": "Good Event", "url": "https://lu.ma/good", "content": "desc"},
            ]
        )
        empty_result = _make_search_result([])
        mock_tavily.search.side_effect = [items_result, empty_result, empty_result]
        events = await agent.discover_events_tavily(test_user_profile)
        assert len(events) == 1
        assert events[0]["title"] == "Good Event"

    async def test_handles_search_exception(
        self,
        agent: DiscoveryAgent,
        mock_tavily: AsyncMock,
        test_user_profile: dict,
    ) -> None:
        mock_tavily.search.side_effect = RuntimeError("API error")
        events = await agent.discover_events_tavily(test_user_profile)
        assert events == []


# ── run_discovery_cycle ─────────────────────────────────────────────────────


class TestRunDiscoveryCycle:
    async def test_deduplicates_results(
        self,
        agent: DiscoveryAgent,
        mock_tavily: AsyncMock,
        test_user_profile: dict,
    ) -> None:
        mock_tavily.search.return_value = _make_search_result(
            [
                {
                    "title": "AI Founders Dinner — SF",
                    "url": "https://lu.ma/ai-dinner",
                    "content": "Long description of the dinner event with many details.",
                },
                {
                    "title": "AI Founders Dinner SF",
                    "url": "https://www.eventbrite.com/e/ai-dinner",
                    "content": "Short desc.",
                },
            ]
        )
        events = await agent.run_discovery_cycle(test_user_profile)
        titles = [e["title"] for e in events]
        assert len(titles) == 1
        assert events[0]["description"] == "Long description of the dinner event with many details."
