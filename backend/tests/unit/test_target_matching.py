from __future__ import annotations

import pytest

from app.agents.connect import TARGET_MATCH_THRESHOLD, TARGET_SCORE_BOOST, ConnectAgent


@pytest.fixture
def agent() -> ConnectAgent:
    return ConnectAgent()


@pytest.fixture
def sample_event() -> dict:
    return {
        "title": "AI Founders Dinner — SF",
        "url": "https://lu.ma/ai-dinner-sf",
        "relevance_score": 75,
    }


class TestTargetMatching:
    def test_exact_name_match(self, agent: ConnectAgent, sample_event: dict) -> None:
        attendees = [{"name": "Sarah Chen"}]
        user_profile = {
            "target_people": [{"name": "Sarah Chen", "reason": "fundraising"}],
        }
        matches = agent.check_target_matches(attendees, sample_event, user_profile)
        assert len(matches) == 1
        assert matches[0]["match_score"] == 100

    def test_fuzzy_match_above_85(self, agent: ConnectAgent, sample_event: dict) -> None:
        attendees = [{"name": "Sarah M. Chen"}]
        user_profile = {
            "target_people": [{"name": "Sarah Chen", "reason": "fundraising"}],
        }
        matches = agent.check_target_matches(attendees, sample_event, user_profile)
        # "Sarah M. Chen" vs "Sarah Chen" should have fuzz.ratio > 85
        assert len(matches) >= 1

    def test_no_match_below_85(self, agent: ConnectAgent, sample_event: dict) -> None:
        attendees = [{"name": "John Totally Different"}]
        user_profile = {
            "target_people": [{"name": "Sarah Chen", "reason": "fundraising"}],
        }
        matches = agent.check_target_matches(attendees, sample_event, user_profile)
        assert matches == []

    def test_score_boost_capped_at_100(
        self, agent: ConnectAgent
    ) -> None:
        event = {"title": "Test", "relevance_score": 90}
        attendees = [{"name": "Sarah Chen"}]
        user_profile = {
            "target_people": [{"name": "Sarah Chen", "reason": "fundraising"}],
        }
        agent.check_target_matches(attendees, event, user_profile)
        # 90 + 30 = 120, should be capped at 100
        assert event["relevance_score"] == 100

    def test_empty_targets_no_matches(
        self, agent: ConnectAgent, sample_event: dict
    ) -> None:
        attendees = [{"name": "Anyone"}]
        user_profile: dict = {"target_people": []}
        matches = agent.check_target_matches(attendees, sample_event, user_profile)
        assert matches == []

    def test_multiple_targets_multiple_matches(
        self, agent: ConnectAgent, sample_event: dict
    ) -> None:
        attendees = [
            {"name": "Sarah Chen"},
            {"name": "James Liu"},
            {"name": "Random Person"},
        ]
        user_profile = {
            "target_people": [
                {"name": "Sarah Chen", "reason": "fundraising"},
                {"name": "James Liu", "reason": "partnership"},
            ],
        }
        matches = agent.check_target_matches(attendees, sample_event, user_profile)
        assert len(matches) == 2
        matched_names = {m["matched_attendee"]["name"] for m in matches}
        assert "Sarah Chen" in matched_names
        assert "James Liu" in matched_names
