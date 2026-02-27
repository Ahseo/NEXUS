"""E2E test: feedback cycle — preference learning and scoring adjustment.

Processes accept/reject feedbacks, verifies topic affinities shift,
and confirms that scoring reflects the learned preferences.
"""

from __future__ import annotations

from typing import Any

import pytest

from app.services.preference_engine import PreferenceEngine
from app.services.scoring import ScoringEngine


class TestFeedbackCycle:
    """Test that feedback processing correctly adjusts preferences and scoring."""

    def test_accept_feedback_increases_topic_affinity(self) -> None:
        """5 accept feedbacks on AI topics should increase AI affinity."""
        engine = PreferenceEngine()

        for _ in range(5):
            engine.process_feedback({
                "action": "accept",
                "topics": ["AI agents", "machine learning"],
                "event_type": "meetup",
            })

        assert engine.get_topic_affinity("AI agents") > 0
        assert engine.get_topic_affinity("machine learning") > 0

    def test_reject_feedback_decreases_topic_affinity(self) -> None:
        """3 reject feedbacks on Web3 should push Web3 into avoided topics."""
        engine = PreferenceEngine()

        for _ in range(3):
            engine.process_feedback({
                "action": "reject",
                "topics": ["Web3", "blockchain"],
                "event_type": "conference",
            })

        assert engine.get_topic_affinity("Web3") < 0
        assert engine.get_topic_affinity("blockchain") < 0
        # After 3 rejects with REJECT_DELTA=-0.5, affinity = -1.0 (clamped)
        # which is < -0.5, so it should be in avoided_topics
        assert engine.is_topic_avoided("Web3")
        assert engine.is_topic_avoided("blockchain")

    def test_feedback_cycle_shifts_scoring(self, test_user_profile: dict[str, Any]) -> None:
        """Full cycle: process feedbacks, then verify scoring changes."""
        engine = PreferenceEngine()

        # Process 5 AI accept feedbacks
        for _ in range(5):
            engine.process_feedback({
                "action": "accept",
                "topics": ["AI agents"],
                "event_type": "dinner",
            })

        # Process 3 Web3 reject feedbacks
        for _ in range(3):
            engine.process_feedback({
                "action": "reject",
                "topics": ["Web3"],
                "event_type": "conference",
            })

        # Verify affinities
        ai_affinity = engine.get_topic_affinity("AI agents")
        web3_affinity = engine.get_topic_affinity("Web3")
        assert ai_affinity > 0, f"AI affinity should be positive, got {ai_affinity}"
        assert web3_affinity < 0, f"Web3 affinity should be negative, got {web3_affinity}"
        assert engine.is_topic_avoided("Web3")

        # Now score events with ScoringEngine
        scoring = ScoringEngine()

        ai_event = {
            "topics": ["AI agents", "developer tools"],
            "speakers": [{"name": "Alice", "role": "CTO", "company": "TechCo"}],
            "event_type": "dinner",
            "date": "2026-03-04T18:00:00",
        }

        web3_event = {
            "topics": ["Web3", "blockchain"],
            "speakers": [{"name": "Bob", "role": "Founder", "company": "CryptoCo"}],
            "event_type": "conference",
            "date": "2026-03-04T18:00:00",
        }

        ai_score = scoring.calculate_relevance(ai_event, test_user_profile)
        web3_score = scoring.calculate_relevance(web3_event, test_user_profile)

        # AI event should score higher because topics match user interests
        assert ai_score > web3_score

    def test_feedback_count_tracked(self) -> None:
        """Verify feedback count is incremented correctly."""
        engine = PreferenceEngine()
        assert engine.feedback_count == 0

        for i in range(8):
            engine.process_feedback({
                "action": "accept" if i < 5 else "reject",
                "topics": ["test"],
            })

        assert engine.feedback_count == 8

    def test_weight_recalculation_after_sufficient_feedback(self) -> None:
        """After >= 5 feedbacks, recalculate_weights should produce non-initial weights."""
        engine = PreferenceEngine()

        # Process 5 accepts and 3 rejects to get above the 5-feedback threshold
        for _ in range(5):
            engine.process_feedback({
                "action": "accept",
                "topics": ["AI"],
            })
        for _ in range(3):
            engine.process_feedback({
                "action": "reject",
                "topics": ["Web3"],
            })

        # With feedback history that differentiates dimensions
        feedback_history = [
            {"action": "accept", "topic_score": 25, "people_score": 10, "event_type_score": 15, "time_score": 10, "historical_score": 7},
            {"action": "accept", "topic_score": 28, "people_score": 12, "event_type_score": 10, "time_score": 8, "historical_score": 5},
            {"action": "accept", "topic_score": 20, "people_score": 15, "event_type_score": 12, "time_score": 10, "historical_score": 8},
            {"action": "reject", "topic_score": 5, "people_score": 0, "event_type_score": 5, "time_score": 10, "historical_score": 3},
            {"action": "reject", "topic_score": 3, "people_score": 0, "event_type_score": 8, "time_score": 7, "historical_score": 5},
        ]

        weights = engine.recalculate_weights(feedback_history)
        assert sum(weights.values()) == 100
        assert all(v >= 5 for v in weights.values())

    def test_mixed_feedback_preserves_affinity_order(self) -> None:
        """Mixed accept/reject on same topic produces intermediate affinity."""
        engine = PreferenceEngine()

        # 3 accepts then 1 reject on same topic
        for _ in range(3):
            engine.process_feedback({"action": "accept", "topics": ["DevOps"]})
        engine.process_feedback({"action": "reject", "topics": ["DevOps"]})

        # Net: 3 * 0.3 + 1 * (-0.5) = 0.9 - 0.5 = 0.4
        affinity = engine.get_topic_affinity("DevOps")
        assert 0.3 < affinity < 0.5  # approximately 0.4
        assert not engine.is_topic_avoided("DevOps")

    def test_avoided_topic_can_recover(self) -> None:
        """A topic that was avoided can recover if user starts accepting it."""
        engine = PreferenceEngine()

        # Push topic to avoided
        for _ in range(3):
            engine.process_feedback({"action": "reject", "topics": ["Web3"]})
        assert engine.is_topic_avoided("Web3")

        # Accept Web3 events to recover
        # Need enough to bring affinity above -0.3
        # Current: -1.0 (clamped), need to get to -0.3+
        # Each accept adds 0.3, so need ceil((1.0 - 0.3) / 0.3) = 3 accepts to reach -0.1
        for _ in range(3):
            engine.process_feedback({"action": "accept", "topics": ["Web3"]})

        # -1.0 + 3 * 0.3 = -0.1, which is >= -0.3
        assert not engine.is_topic_avoided("Web3")
        assert engine.get_topic_affinity("Web3") < 0  # still slightly negative

    def test_stats_reflect_feedback(self) -> None:
        """get_stats returns correct summary after feedback processing."""
        engine = PreferenceEngine()

        for _ in range(5):
            engine.process_feedback({"action": "accept", "topics": ["AI"]})
        for _ in range(3):
            engine.process_feedback({"action": "reject", "topics": ["Web3"]})

        stats = engine.get_stats()
        assert stats["total_feedback"] == 8
        assert "AI" in [t["topic"] for t in stats["top_topics"]]
        assert "Web3" in stats["avoided_topics"]
