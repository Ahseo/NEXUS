from __future__ import annotations

from unittest.mock import AsyncMock

import pytest

from app.agents.connect import (
    RICHNESS_THRESHOLD,
    ConnectAgent,
)
from app.integrations.reka_client import RekaVisionResult
from app.integrations.tavily_client import TavilySearchResult
from app.integrations.yutori_client import YutoriTask


@pytest.fixture
def mock_tavily() -> AsyncMock:
    return AsyncMock()


@pytest.fixture
def mock_yutori() -> AsyncMock:
    return AsyncMock()


@pytest.fixture
def mock_reka() -> AsyncMock:
    return AsyncMock()


@pytest.fixture
def agent(
    mock_tavily: AsyncMock, mock_yutori: AsyncMock, mock_reka: AsyncMock
) -> ConnectAgent:
    return ConnectAgent(
        _tavily=mock_tavily, _yutori=mock_yutori, _reka=mock_reka
    )


@pytest.fixture
def agent_no_clients() -> ConnectAgent:
    return ConnectAgent()


def _make_search_result(items: list[dict]) -> TavilySearchResult:
    return TavilySearchResult(
        query="test",
        answer=None,
        results=items,
        raw_content=[],
    )


def _make_yutori_task(attendees: list[dict]) -> YutoriTask:
    return YutoriTask(
        task_id="task-1",
        status="completed",
        result=attendees,
    )


def _full_profile() -> dict:
    return {
        "name": "Alice Smith",
        "current_role": "VP Engineering",
        "company": "TechCorp",
        "bio": "Experienced engineering leader with 15 years in tech.",
        "linkedin": "https://linkedin.com/in/alicesmith",
        "twitter": "https://x.com/alicesmith",
        "recent_work": "Published a paper on distributed systems at SIGMOD 2024",
        "interests": ["distributed systems", "AI", "leadership"],
        "mutual_connections": ["Bob Jones"],
        "conversation_hooks": ["SIGMOD paper", "distributed systems"],
    }


# ── scrape_attendees ───────────────────────────────────────────────────────


class TestScrapeAttendees:
    async def test_scrape_attendees_with_yutori(
        self,
        agent: ConnectAgent,
        mock_yutori: AsyncMock,
        sample_raw_event: dict,
    ) -> None:
        attendees = [
            {"name": "Sarah Chen", "role": "Partner", "company": "Sequoia"},
            {"name": "James Liu", "role": "Partner", "company": "a16z"},
        ]
        mock_yutori.browsing_create.return_value = _make_yutori_task(attendees)

        result = await agent.scrape_attendees(sample_raw_event)
        assert len(result) == 2
        assert result[0]["name"] == "Sarah Chen"
        mock_yutori.browsing_create.assert_called_once()

    async def test_scrape_attendees_no_client(
        self,
        agent_no_clients: ConnectAgent,
        sample_raw_event: dict,
    ) -> None:
        result = await agent_no_clients.scrape_attendees(sample_raw_event)
        assert result == []


# ── deep_research_person ───────────────────────────────────────────────────


class TestDeepResearchPerson:
    async def test_deep_research_stops_at_threshold(
        self,
        agent: ConnectAgent,
        mock_tavily: AsyncMock,
        test_user_profile: dict,
    ) -> None:
        """If profile already meets richness threshold, no searches happen."""
        rich_attendee = _full_profile()
        result = await agent.deep_research_person(rich_attendee, test_user_profile)
        assert result["richness_score"] >= RICHNESS_THRESHOLD
        mock_tavily.search.assert_not_called()

    async def test_deep_research_max_iterations(
        self,
        agent: ConnectAgent,
        mock_tavily: AsyncMock,
        test_user_profile: dict,
    ) -> None:
        """Stops after max_iterations even if below threshold."""
        sparse_attendee = {"name": "Unknown Person"}
        mock_tavily.search.return_value = _make_search_result(
            [{"title": "Some result", "url": "https://example.com", "content": "Short"}]
        )

        result = await agent.deep_research_person(
            sparse_attendee, test_user_profile, max_iterations=3
        )
        assert mock_tavily.search.call_count <= 3
        assert "richness_score" in result


# ── resolve_social_accounts ────────────────────────────────────────────────


class TestResolveSocialAccounts:
    async def test_resolve_social_uses_tavily(
        self,
        agent: ConnectAgent,
        mock_tavily: AsyncMock,
    ) -> None:
        mock_tavily.search.return_value = _make_search_result(
            [{"title": "Alice on LinkedIn", "url": "https://linkedin.com/in/alice", "content": ""}]
        )
        profile = {"name": "Alice Smith", "company": "TechCorp"}
        socials = await agent.resolve_social_accounts(profile)
        assert "linkedin" in socials
        assert mock_tavily.search.call_count >= 1


# ── cross_verify_profiles_reka ─────────────────────────────────────────────


class TestCrossVerify:
    async def test_cross_verify_no_reka(
        self,
        agent_no_clients: ConnectAgent,
    ) -> None:
        result = await agent_no_clients.cross_verify_profiles_reka(
            "https://linkedin.com/in/alice",
            "https://x.com/alice",
        )
        assert result is True


# ── calculate_profile_richness ─────────────────────────────────────────────


class TestCalculateProfileRichness:
    def test_calculate_richness_empty_profile(
        self,
        agent: ConnectAgent,
    ) -> None:
        assert agent.calculate_profile_richness({}) == 0.0

    def test_calculate_richness_full_profile(
        self,
        agent: ConnectAgent,
    ) -> None:
        profile = _full_profile()
        richness = agent.calculate_profile_richness(profile)
        assert richness >= 0.95


# ── identify_gaps ──────────────────────────────────────────────────────────


class TestIdentifyGaps:
    def test_identify_gaps_empty_profile(
        self,
        agent: ConnectAgent,
    ) -> None:
        gaps = agent.identify_gaps({})
        from app.agents.connect import RICHNESS_WEIGHTS

        assert set(gaps) == set(RICHNESS_WEIGHTS.keys())

    def test_identify_gaps_full_profile(
        self,
        agent: ConnectAgent,
    ) -> None:
        profile = _full_profile()
        gaps = agent.identify_gaps(profile)
        assert gaps == []


# ── build_research_query ───────────────────────────────────────────────────


class TestBuildResearchQuery:
    def test_build_research_query_iteration_1(
        self,
        agent: ConnectAgent,
    ) -> None:
        attendee = {"name": "Alice Smith", "company": "TechCorp"}
        query = agent.build_research_query(attendee, {}, ["bio", "linkedin"], 1)
        assert "Alice Smith" in query
        assert "TechCorp" in query

    def test_build_research_query_iteration_3(
        self,
        agent: ConnectAgent,
    ) -> None:
        attendee = {"name": "Alice Smith"}
        query = agent.build_research_query(attendee, {}, ["linkedin"], 3)
        assert "linkedin" in query.lower()
        assert "OR" in query


# ── check_target_matches ──────────────────────────────────────────────────


class TestCheckTargetMatches:
    def test_check_target_matches_found(
        self,
        agent: ConnectAgent,
        sample_raw_event: dict,
    ) -> None:
        attendees = [
            {"name": "Sarah Chen", "role": "Partner", "company": "Sequoia"},
        ]
        user_profile = {
            "target_people": [
                {"name": "Sarah Chen", "company": "Sequoia", "reason": "fundraising"},
            ],
        }
        matches = agent.check_target_matches(attendees, sample_raw_event, user_profile)
        assert len(matches) == 1
        assert matches[0]["matched_attendee"]["name"] == "Sarah Chen"

    def test_check_target_matches_none(
        self,
        agent: ConnectAgent,
        sample_raw_event: dict,
    ) -> None:
        attendees = [{"name": "Random Person"}]
        user_profile = {
            "target_people": [{"name": "Sarah Chen", "reason": "fundraising"}],
        }
        matches = agent.check_target_matches(attendees, sample_raw_event, user_profile)
        assert matches == []


# ── find_best_connections ─────────────────────────────────────────────────


class TestFindBestConnections:
    async def test_find_best_connections(
        self,
        agent: ConnectAgent,
        test_user_profile: dict,
    ) -> None:
        attendees = [
            {
                "name": "Low Match",
                "role": "Barista",
                "company": "CoffeeShop",
                "interests": [],
            },
            {
                "name": "High Match",
                "role": "VC Partner",
                "company": "Sequoia",
                "interests": ["AI agents"],
                "current_role": "VC Partner",
                "bio": "Investor",
                "linkedin": "https://linkedin.com/in/high",
                "twitter": "https://x.com/high",
                "recent_work": "Led Series A for AI startup",
                "mutual_connections": ["Someone"],
                "conversation_hooks": ["AI investing"],
            },
        ]
        result = await agent.find_best_connections(attendees, test_user_profile)
        assert len(result) == 2
        assert result[0]["name"] == "High Match"
        assert result[0]["connection_score"] > result[1]["connection_score"]
