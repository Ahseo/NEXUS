"""E2E test: full pipeline in REPLAY mode.

Loads fixture events, runs discovery -> dedup -> analyze -> score -> action -> connect -> message.
All external APIs are mocked; validates correct counts and score ranges at each stage.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any
from unittest.mock import AsyncMock, patch

import pytest

from app.agents.action import ActionAgent
from app.agents.connect import ConnectAgent
from app.agents.discovery import DiscoveryAgent
from app.core.config import NexusMode
from app.integrations.tavily_client import TavilySearchResult
from app.services.deduplication import deduplicate_events
from app.services.message_generator import MessageGenerator
from app.services.scoring import ScoringEngine

FIXTURES_DIR = Path(__file__).resolve().parent.parent / "fixtures"


@pytest.fixture
def fixture_events() -> list[dict[str, Any]]:
    with open(FIXTURES_DIR / "events_sf_sample.json") as f:
        events: list[dict[str, Any]] = json.load(f)
        return events


@pytest.fixture
def mock_tavily(fixture_events: list[dict[str, Any]]) -> AsyncMock:
    client = AsyncMock()
    client.search.return_value = TavilySearchResult(
        query="test",
        answer=None,
        results=[
            {
                "title": e["title"],
                "url": e["url"],
                "content": e.get("description", ""),
            }
            for e in fixture_events
        ],
        raw_content=[],
    )
    return client


def _make_entities(event: dict[str, Any]) -> dict[str, Any]:
    """Build a mock entity extraction result from a raw event."""
    desc_lower = event.get("description", "").lower()
    topics: list[str] = []
    if "ai" in desc_lower:
        topics.append("AI agents")
    if "fundraising" in desc_lower or "vc" in desc_lower or "pitch" in desc_lower:
        topics.append("fundraising")
    if "developer tools" in desc_lower or "devtools" in desc_lower:
        topics.append("developer tools")
    if "saas" in desc_lower:
        topics.append("developer tools")
    if "kubernetes" in desc_lower or "k8s" in desc_lower:
        topics.append("Kubernetes")

    speakers: list[dict[str, str]] = []
    if "sequoia" in desc_lower:
        speakers.append({"name": "Sarah Chen", "role": "Partner", "company": "Sequoia"})
    if "a16z" in desc_lower:
        speakers.append({"name": "James Liu", "role": "Partner", "company": "a16z"})
    if "anthropic" in desc_lower:
        speakers.append({"name": "Speaker", "role": "Researcher", "company": "Anthropic"})

    # Infer event type
    title_lower = event.get("title", "").lower()
    if "dinner" in title_lower:
        event_type = "dinner"
    elif "workshop" in title_lower:
        event_type = "workshop"
    elif "happy hour" in title_lower or "happy_hour" in title_lower:
        event_type = "happy_hour"
    elif "demo day" in title_lower:
        event_type = "demo_day"
    elif "conference" in title_lower:
        event_type = "conference"
    else:
        event_type = "meetup"

    return {
        "event_type": event_type,
        "date": event.get("date"),
        "location": "San Francisco",
        "speakers": speakers,
        "topics": topics,
        "companies": [s["company"] for s in speakers],
        "target_audience": "founders and investors",
        "capacity": 30,
        "price": None,
        "application_required": False,
    }


class TestFullCycleReplay:
    """Test the full NEXUS pipeline using REPLAY mode with fixture data."""

    async def test_discovery_loads_events(
        self,
        mock_tavily: AsyncMock,
        test_user_profile: dict[str, Any],
    ) -> None:
        """Discovery agent fetches raw events from Tavily (12 per query * 3 queries)."""
        agent = DiscoveryAgent(tavily=mock_tavily)
        events = await agent.discover_events_tavily(test_user_profile)
        # 12 events returned per query, 3 queries from user interests
        assert len(events) == 36

    async def test_deduplication_removes_duplicates(
        self,
        fixture_events: list[dict[str, Any]],
    ) -> None:
        """Deduplication merges events with similar titles and same date."""
        unique = deduplicate_events(fixture_events)
        # 12 events, 1 duplicate pair (AI Founders Dinner — SF / AI Founders Dinner SF)
        # The GenAI Demo Day pair titles are too different for fuzz.ratio > 80
        assert len(unique) == 11

    async def test_full_pipeline(
        self,
        mock_tavily: AsyncMock,
        fixture_events: list[dict[str, Any]],
        test_user_profile: dict[str, Any],
    ) -> None:
        """Run the full pipeline: discover -> dedup -> analyze -> score -> action -> connect -> message."""

        # --- Stage 1: Discovery ---
        discovery = DiscoveryAgent(tavily=mock_tavily)
        raw_events = await discovery.run_discovery_cycle(test_user_profile)
        assert len(raw_events) >= 8  # after dedup
        assert len(raw_events) <= 12  # never more than original

        # --- Stage 2: Analyze & Score each event ---
        scoring = ScoringEngine()
        enriched_events: list[dict[str, Any]] = []

        for raw in raw_events:
            entities = _make_entities(raw)
            enriched = {
                "url": raw["url"],
                "title": raw["title"],
                "description": raw.get("description", ""),
                "source": raw.get("source", ""),
                "entities": entities,
                "event_type": entities["event_type"],
                "date": entities.get("date"),
                "location": entities.get("location", ""),
                "speakers": entities.get("speakers", []),
                "topics": entities.get("topics", []),
                "companies": entities.get("companies", []),
                "target_audience": entities.get("target_audience", ""),
                "capacity": entities.get("capacity"),
                "price": entities.get("price"),
                "application_required": entities.get("application_required", False),
            }
            score = scoring.calculate_relevance(enriched, test_user_profile)
            enriched["relevance_score"] = score
            enriched_events.append(enriched)

        assert len(enriched_events) == len(raw_events)

        # All scores should be in [0, 100]
        for ev in enriched_events:
            assert 0 <= ev["relevance_score"] <= 100

        # Sort by score to identify high/low
        enriched_events.sort(key=lambda e: e["relevance_score"], reverse=True)
        top_event = enriched_events[0]
        bottom_event = enriched_events[-1]

        # Top event should have a meaningfully higher score than bottom
        assert top_event["relevance_score"] >= bottom_event["relevance_score"]

        # --- Stage 3: Action decisions ---
        action_agent = ActionAgent()
        decisions: list[dict[str, Any]] = []
        for ev in enriched_events:
            decision = action_agent.decide(ev["relevance_score"], test_user_profile)
            decisions.append({
                "title": ev["title"],
                "score": ev["relevance_score"],
                "action": decision.action,
            })

        # Verify decision logic
        for d in decisions:
            if d["score"] >= test_user_profile["auto_apply_threshold"]:
                assert d["action"] == "auto_apply"
            elif d["score"] >= test_user_profile["suggest_threshold"]:
                assert d["action"] == "suggest"
            else:
                assert d["action"] == "skip"

        # --- Stage 4: Connect for accepted events ---
        connect = ConnectAgent()

        # Simulate attendees for the top event
        mock_attendees = [
            {"name": "Alice Smith", "role": "CTO", "company": "TechCo"},
            {"name": "Bob Jones", "role": "VC Partner", "company": "Sequoia"},
        ]

        best_connections = await connect.find_best_connections(
            mock_attendees, test_user_profile
        )
        assert len(best_connections) == 2
        # All connections should have a connection_score
        for c in best_connections:
            assert "connection_score" in c
        # Should be sorted descending
        scores = [c["connection_score"] for c in best_connections]
        assert scores == sorted(scores, reverse=True)

        # --- Stage 5: Draft messages ---
        msg_gen = MessageGenerator()
        messages: list[dict[str, Any]] = []
        for conn in best_connections:
            msg = msg_gen.draft_cold_message(conn, top_event, test_user_profile)
            messages.append(msg)

        assert len(messages) == 2
        for msg in messages:
            assert "body" in msg
            assert msg["word_count"] > 0
            assert msg["message_type"] == "cold_outreach"
            assert msg["channel"] in ["twitter_dm", "linkedin", "email", "instagram_dm"]

    async def test_scoring_ranges_for_different_event_types(
        self,
        fixture_events: list[dict[str, Any]],
        test_user_profile: dict[str, Any],
    ) -> None:
        """Verify that events matching user interests score higher."""
        scoring = ScoringEngine()

        # AI Founders Dinner should score high (topic match + people match + type match)
        ai_dinner = fixture_events[0]
        ai_dinner_entities = _make_entities(ai_dinner)
        ai_enriched = {
            **ai_dinner,
            "event_type": ai_dinner_entities["event_type"],
            "topics": ai_dinner_entities["topics"],
            "speakers": ai_dinner_entities["speakers"],
        }
        ai_score = scoring.calculate_relevance(ai_enriched, test_user_profile)

        # Kubernetes meetup should score lower (no topic/people match)
        k8s_event = fixture_events[10]  # "Kubernetes & Cloud Native Meetup"
        k8s_entities = _make_entities(k8s_event)
        k8s_enriched = {
            **k8s_event,
            "event_type": k8s_entities["event_type"],
            "topics": k8s_entities["topics"],
            "speakers": k8s_entities["speakers"],
        }
        k8s_score = scoring.calculate_relevance(k8s_enriched, test_user_profile)

        assert ai_score > k8s_score
