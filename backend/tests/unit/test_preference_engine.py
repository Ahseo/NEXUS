"""Tests for the PreferenceEngine feedback learning system."""

from __future__ import annotations

import pytest

from app.services.preference_engine import (
    ACCEPT_DELTA,
    INITIAL_WEIGHTS,
    REJECT_DELTA,
    PreferenceEngine,
)


@pytest.fixture
def engine() -> PreferenceEngine:
    return PreferenceEngine()


class TestInitialState:
    def test_initial_weights_match_spec(self, engine: PreferenceEngine) -> None:
        assert engine.weights == {
            "topic": 30,
            "people": 25,
            "event_type": 15,
            "time": 15,
            "historical": 15,
        }

    def test_initial_weights_sum_to_100(self, engine: PreferenceEngine) -> None:
        assert sum(engine.weights.values()) == 100

    def test_no_topic_affinities(self, engine: PreferenceEngine) -> None:
        assert engine.topic_affinities == {}

    def test_no_avoided_topics(self, engine: PreferenceEngine) -> None:
        assert engine.avoided_topics == set()


class TestTopicAffinity:
    def test_accept_increases_affinity(self, engine: PreferenceEngine) -> None:
        engine.process_feedback(
            {"action": "accept", "topics": ["AI"]}
        )
        assert engine.get_topic_affinity("AI") == pytest.approx(ACCEPT_DELTA)

    def test_reject_decreases_affinity(self, engine: PreferenceEngine) -> None:
        engine.process_feedback(
            {"action": "reject", "topics": ["Web3"]}
        )
        assert engine.get_topic_affinity("Web3") == pytest.approx(REJECT_DELTA)

    def test_multiple_rejects_compound(self, engine: PreferenceEngine) -> None:
        for _ in range(3):
            engine.process_feedback(
                {"action": "reject", "topics": ["Web3"]}
            )
        expected = max(-1.0, REJECT_DELTA * 3)
        assert engine.get_topic_affinity("Web3") == pytest.approx(expected)

    def test_three_rejects_avoids_topic(self, engine: PreferenceEngine) -> None:
        for _ in range(3):
            engine.process_feedback(
                {"action": "reject", "topics": ["Web3"]}
            )
        assert engine.is_topic_avoided("Web3")

    def test_accept_ai_increases(self, engine: PreferenceEngine) -> None:
        engine.process_feedback(
            {"action": "accept", "topics": ["AI", "machine learning"]}
        )
        assert engine.get_topic_affinity("AI") > 0
        assert engine.get_topic_affinity("machine learning") > 0

    def test_affinity_clamped_at_positive_one(
        self, engine: PreferenceEngine
    ) -> None:
        for _ in range(10):
            engine.process_feedback(
                {"action": "accept", "topics": ["AI"]}
            )
        assert engine.get_topic_affinity("AI") == pytest.approx(1.0)

    def test_affinity_clamped_at_negative_one(
        self, engine: PreferenceEngine
    ) -> None:
        for _ in range(10):
            engine.process_feedback(
                {"action": "reject", "topics": ["spam"]}
            )
        assert engine.get_topic_affinity("spam") == pytest.approx(-1.0)

    def test_unknown_topic_returns_zero(
        self, engine: PreferenceEngine
    ) -> None:
        assert engine.get_topic_affinity("never_seen") == 0.0


class TestRejectionReasons:
    def test_not_my_industry_double_penalty(
        self, engine: PreferenceEngine
    ) -> None:
        engine.process_feedback(
            {
                "action": "reject",
                "topics": ["crypto"],
                "reason": "not_my_industry",
            }
        )
        # Two reject deltas applied (one for reject, one for not_my_industry)
        assert engine.get_topic_affinity("crypto") == pytest.approx(
            REJECT_DELTA * 2
        )

    def test_bad_timing_updates_time_preferences(
        self, engine: PreferenceEngine
    ) -> None:
        engine.process_feedback(
            {
                "action": "reject",
                "topics": [],
                "reason": "bad_timing",
                "event_time": "2026-02-27T09:00:00",  # Friday
            }
        )
        assert "friday" in engine.preferred_times
        assert engine.preferred_times["friday"] < 0

    def test_too_expensive_logs(self, engine: PreferenceEngine) -> None:
        # Should not raise
        engine.process_feedback(
            {
                "action": "reject",
                "topics": [],
                "reason": "too_expensive",
                "price": 100.0,
            }
        )


class TestRating:
    def test_high_rating_increases_affinity(
        self, engine: PreferenceEngine
    ) -> None:
        engine.process_feedback(
            {"action": "rate", "rating": 5, "topics": ["AI"]}
        )
        assert engine.get_topic_affinity("AI") > 0

    def test_low_rating_decreases_affinity(
        self, engine: PreferenceEngine
    ) -> None:
        engine.process_feedback(
            {"action": "rate", "rating": 1, "topics": ["networking"]}
        )
        assert engine.get_topic_affinity("networking") < 0

    def test_neutral_rating_no_change(
        self, engine: PreferenceEngine
    ) -> None:
        engine.process_feedback(
            {"action": "rate", "rating": 3, "topics": ["devops"]}
        )
        assert engine.get_topic_affinity("devops") == pytest.approx(0.0)


class TestRecalculateWeights:
    def test_returns_initial_under_5_feedback(
        self, engine: PreferenceEngine
    ) -> None:
        for _ in range(4):
            engine.process_feedback({"action": "accept", "topics": ["AI"]})
        result = engine.recalculate_weights()
        assert result == INITIAL_WEIGHTS

    def test_returns_weights_summing_to_100(
        self, engine: PreferenceEngine
    ) -> None:
        for i in range(10):
            engine.process_feedback(
                {"action": "accept" if i % 2 == 0 else "reject", "topics": ["AI"]}
            )
        history = [
            {"action": "accept", "topic_score": 25, "people_score": 20}
        ] * 5 + [
            {"action": "reject", "topic_score": 5, "people_score": 10}
        ] * 5
        result = engine.recalculate_weights(history)
        assert sum(result.values()) == 100

    def test_all_weights_at_least_5(
        self, engine: PreferenceEngine
    ) -> None:
        for i in range(10):
            engine.process_feedback({"action": "accept", "topics": []})
        result = engine.recalculate_weights([])
        for w in result.values():
            assert w >= 5

    def test_dimensions_match_initial(
        self, engine: PreferenceEngine
    ) -> None:
        for i in range(10):
            engine.process_feedback({"action": "accept", "topics": []})
        result = engine.recalculate_weights()
        assert set(result.keys()) == set(INITIAL_WEIGHTS.keys())


class TestFeedbackIntegration:
    def test_reject_then_accept_recovers(
        self, engine: PreferenceEngine
    ) -> None:
        # Reject Web3 twice
        engine.process_feedback(
            {"action": "reject", "topics": ["Web3"]}
        )
        engine.process_feedback(
            {"action": "reject", "topics": ["Web3"]}
        )
        val_after_reject = engine.get_topic_affinity("Web3")
        assert val_after_reject < 0

        # Accept Web3 events several times
        for _ in range(5):
            engine.process_feedback(
                {"action": "accept", "topics": ["Web3"]}
            )
        val_after_accept = engine.get_topic_affinity("Web3")
        assert val_after_accept > val_after_reject

    def test_feedback_count_tracks(self, engine: PreferenceEngine) -> None:
        assert engine.feedback_count == 0
        engine.process_feedback({"action": "accept", "topics": []})
        engine.process_feedback({"action": "reject", "topics": []})
        assert engine.feedback_count == 2


class TestGetStats:
    def test_stats_structure(self, engine: PreferenceEngine) -> None:
        engine.process_feedback(
            {"action": "accept", "topics": ["AI"]}
        )
        stats = engine.get_stats()
        assert "total_feedback" in stats
        assert "weights" in stats
        assert "top_topics" in stats
        assert "avoided_topics" in stats
        assert stats["total_feedback"] == 1

    def test_stats_top_topics(self, engine: PreferenceEngine) -> None:
        engine.process_feedback(
            {"action": "accept", "topics": ["AI"]}
        )
        engine.process_feedback(
            {"action": "reject", "topics": ["crypto"]}
        )
        stats = engine.get_stats()
        topics = [t["topic"] for t in stats["top_topics"]]
        assert "AI" in topics
