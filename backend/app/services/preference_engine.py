"""Preference engine — learns from user feedback to improve scoring.

Processes explicit feedback (accept/reject/edit/rate) and adjusts
topic affinities, time preferences, and scoring weights over time.
"""

from __future__ import annotations

import logging
from typing import Any

logger = logging.getLogger(__name__)

# Initial scoring dimension weights (sum to 100)
INITIAL_WEIGHTS = {
    "topic": 30,
    "people": 25,
    "event_type": 15,
    "time": 15,
    "historical": 15,
}

# Affinity adjustment deltas
ACCEPT_DELTA = 0.3
REJECT_DELTA = -0.5
EDIT_DELTA = -0.1  # light negative signal — message was off
RATE_DELTA_MAP = {5: 0.5, 4: 0.3, 3: 0.0, 2: -0.3, 1: -0.5}

# Budget / time preference adjustments
BUDGET_LOWER_RATIO = 0.8  # multiply max_event_spend by this on "too_expensive"


class PreferenceEngine:
    """Learns user preferences from feedback and adjusts scoring parameters."""

    def __init__(self) -> None:
        self.topic_affinities: dict[str, float] = {}
        self.avoided_topics: set[str] = set()
        self.preferred_times: dict[str, float] = {}
        self.weights: dict[str, int] = dict(INITIAL_WEIGHTS)
        self._feedback_count = 0

    def process_feedback(self, feedback: dict[str, Any]) -> None:
        """Process a single feedback signal and update preferences."""
        action = feedback.get("action", "")
        topics: list[str] = feedback.get("topics", [])
        event_type: str = feedback.get("event_type", "")
        rejection_reason: str = feedback.get("reason", "")
        rating: int | None = feedback.get("rating")
        event_time: str = feedback.get("event_time", "")
        price: float | None = feedback.get("price")

        self._feedback_count += 1

        if action == "accept":
            for topic in topics:
                self.adjust_topic_affinity(topic, ACCEPT_DELTA)

        elif action == "reject":
            for topic in topics:
                self.adjust_topic_affinity(topic, REJECT_DELTA)
            if rejection_reason == "not_my_industry":
                for topic in topics:
                    self.adjust_topic_affinity(topic, REJECT_DELTA)
            elif rejection_reason == "bad_timing" and event_time:
                self.update_time_preferences(event_time, negative=True)
            elif rejection_reason == "too_expensive" and price is not None:
                self.lower_budget_threshold(price)

        elif action == "edit":
            for topic in topics:
                self.adjust_topic_affinity(topic, EDIT_DELTA)

        elif action == "rate" and rating is not None:
            delta = RATE_DELTA_MAP.get(rating, 0.0)
            for topic in topics:
                self.adjust_topic_affinity(topic, delta)

    def adjust_topic_affinity(self, topic: str, delta: float) -> None:
        """Adjust affinity for a topic. Clamp to [-1.0, 1.0].

        When affinity drops below -0.5, add to avoided_topics.
        """
        current = self.topic_affinities.get(topic, 0.0)
        new_val = max(-1.0, min(1.0, current + delta))
        self.topic_affinities[topic] = new_val

        if new_val < -0.5:
            self.avoided_topics.add(topic)
        elif topic in self.avoided_topics and new_val >= -0.3:
            self.avoided_topics.discard(topic)

    def update_time_preferences(
        self, event_time: str, *, negative: bool = False
    ) -> None:
        """Update time preference scores.

        Parses day-of-week from event_time and adjusts preference.
        """
        day = _extract_day(event_time)
        if not day:
            return
        current = self.preferred_times.get(day, 0.0)
        delta = -0.3 if negative else 0.2
        self.preferred_times[day] = max(-1.0, min(1.0, current + delta))

    def lower_budget_threshold(self, price: float) -> None:
        """Record that a price was too expensive — for external use."""
        logger.info("User found $%.2f too expensive", price)

    def get_topic_affinity(self, topic: str) -> float:
        """Get current affinity for a topic. Default 0.0."""
        return self.topic_affinities.get(topic, 0.0)

    def is_topic_avoided(self, topic: str) -> bool:
        """Check if a topic is on the avoided list."""
        return topic in self.avoided_topics

    def recalculate_weights(
        self, feedback_history: list[dict[str, Any]] | None = None
    ) -> dict[str, int]:
        """Recalculate scoring dimension weights from feedback history.

        If not enough data (< 5 feedback signals), return initial weights.
        Otherwise, compute acceptance rates per dimension and rebalance.

        Weights always sum to 100 and are all positive (min 5).
        """
        if self._feedback_count < 5:
            return dict(INITIAL_WEIGHTS)

        # Compute variance contribution per dimension
        # Topics that strongly differentiate accept/reject get more weight
        topic_variance = self._compute_dimension_variance(
            "topic", feedback_history or []
        )
        people_variance = self._compute_dimension_variance(
            "people", feedback_history or []
        )
        type_variance = self._compute_dimension_variance(
            "event_type", feedback_history or []
        )
        time_variance = self._compute_dimension_variance(
            "time", feedback_history or []
        )
        hist_variance = self._compute_dimension_variance(
            "historical", feedback_history or []
        )

        raw = {
            "topic": INITIAL_WEIGHTS["topic"] + topic_variance,
            "people": INITIAL_WEIGHTS["people"] + people_variance,
            "event_type": INITIAL_WEIGHTS["event_type"] + type_variance,
            "time": INITIAL_WEIGHTS["time"] + time_variance,
            "historical": INITIAL_WEIGHTS["historical"] + hist_variance,
        }

        # Ensure minimum weight of 5 per dimension
        for k in raw:
            raw[k] = max(5.0, raw[k])

        # Normalize to sum to 100
        total = sum(raw.values())
        self.weights = {
            k: max(5, round(v / total * 100)) for k, v in raw.items()
        }

        # Adjust rounding to ensure exact sum of 100
        diff = 100 - sum(self.weights.values())
        if diff != 0:
            # Add/subtract from the largest weight
            largest = max(self.weights, key=lambda k: self.weights[k])
            self.weights[largest] += diff

        return dict(self.weights)

    @staticmethod
    def _compute_dimension_variance(
        dimension: str, history: list[dict[str, Any]]
    ) -> float:
        """Compute how much a dimension differentiates accepted vs rejected events.

        Returns a delta to add to the base weight (-10 to +10).
        """
        if not history:
            return 0.0

        accepted_scores: list[float] = []
        rejected_scores: list[float] = []
        for fb in history:
            score = fb.get(f"{dimension}_score", 0)
            if fb.get("action") == "accept":
                accepted_scores.append(score)
            elif fb.get("action") == "reject":
                rejected_scores.append(score)

        if not accepted_scores or not rejected_scores:
            return 0.0

        avg_accept = sum(accepted_scores) / len(accepted_scores)
        avg_reject = sum(rejected_scores) / len(rejected_scores)
        diff = avg_accept - avg_reject

        # Scale: large difference => increase weight, small => decrease
        return max(-10.0, min(10.0, diff))

    @property
    def feedback_count(self) -> int:
        return self._feedback_count

    def get_stats(self) -> dict[str, Any]:
        """Return summary statistics for the settings page."""
        top_topics = sorted(
            self.topic_affinities.items(), key=lambda x: x[1], reverse=True
        )[:5]
        bottom_topics = sorted(
            self.topic_affinities.items(), key=lambda x: x[1]
        )[:5]

        return {
            "total_feedback": self._feedback_count,
            "weights": dict(self.weights),
            "top_topics": [
                {"topic": t, "affinity": a} for t, a in top_topics
            ],
            "avoided_topics": list(self.avoided_topics),
            "bottom_topics": [
                {"topic": t, "affinity": a} for t, a in bottom_topics
            ],
            "time_preferences": dict(self.preferred_times),
        }


def _extract_day(event_time: str) -> str:
    """Extract day of week from ISO datetime string."""
    try:
        from datetime import datetime

        dt = datetime.fromisoformat(event_time.replace("Z", "+00:00"))
        return dt.strftime("%A").lower()
    except (ValueError, AttributeError):
        return ""
