from __future__ import annotations

import pytest

from app.agents.connect import RICHNESS_WEIGHTS, ConnectAgent


@pytest.fixture
def agent() -> ConnectAgent:
    return ConnectAgent()


def _full_profile() -> dict:
    return {
        "current_role": "VP Engineering",
        "company": "TechCorp",
        "bio": "Experienced engineering leader.",
        "linkedin": "https://linkedin.com/in/alicesmith",
        "twitter": "https://x.com/alicesmith",
        "recent_work": "Published a paper on distributed systems",
        "interests": ["distributed systems", "AI"],
        "mutual_connections": ["Bob Jones"],
        "conversation_hooks": ["SIGMOD paper"],
    }


class TestProfileRichness:
    def test_empty_profile_richness_zero(self, agent: ConnectAgent) -> None:
        assert agent.calculate_profile_richness({}) == 0.0

    def test_full_profile_richness_near_one(self, agent: ConnectAgent) -> None:
        richness = agent.calculate_profile_richness(_full_profile())
        assert richness >= 0.95
        assert richness <= 1.0

    def test_partial_profile_richness(self, agent: ConnectAgent) -> None:
        partial = {
            "current_role": "Engineer",
            "company": "Acme",
            "linkedin": "https://linkedin.com/in/someone",
        }
        richness = agent.calculate_profile_richness(partial)
        expected = RICHNESS_WEIGHTS["current_role"] + RICHNESS_WEIGHTS["company"] + RICHNESS_WEIGHTS["linkedin"]
        assert abs(richness - expected) < 0.01

    def test_weights_sum_to_one(self) -> None:
        total = sum(RICHNESS_WEIGHTS.values())
        assert abs(total - 1.0) < 0.001

    def test_individual_weights_match_spec(self) -> None:
        assert RICHNESS_WEIGHTS["current_role"] == 0.15
        assert RICHNESS_WEIGHTS["company"] == 0.10
        assert RICHNESS_WEIGHTS["bio"] == 0.10
        assert RICHNESS_WEIGHTS["linkedin"] == 0.15
        assert RICHNESS_WEIGHTS["twitter"] == 0.10
        assert RICHNESS_WEIGHTS["recent_work"] == 0.15
        assert RICHNESS_WEIGHTS["interests"] == 0.10
        assert RICHNESS_WEIGHTS["mutual_connections"] == 0.05
        assert RICHNESS_WEIGHTS["conversation_hooks"] == 0.10
