from __future__ import annotations

from datetime import datetime
from typing import Any

from app.models.event import EventType


class ScoringEngine:
    """Calculate event relevance using 5 weighted dimensions."""

    def calculate_relevance(
        self, enriched: dict[str, Any], user_profile: dict[str, Any]
    ) -> float:
        """Score 0-100. Sum of 5 dimensions."""
        topic_score = self._score_topics(
            enriched.get("topics", []),
            user_profile.get("interests", []),
        )
        people_score = self._score_people(
            enriched.get("speakers", []),
            user_profile,
        )
        event_type_score = self._score_event_type(
            enriched.get("event_type", ""),
            user_profile.get("preferred_event_types", []),
        )
        time_score = self._score_time(
            enriched.get("date"),
            user_profile.get("preferred_days", []),
            user_profile.get("preferred_times", []),
        )
        historical_score = self._score_historical(enriched, user_profile)

        raw = topic_score + people_score + event_type_score + time_score + historical_score
        return max(0.0, min(100.0, raw))

    def _score_topics(
        self, event_topics: list[str], user_interests: list[str]
    ) -> float:
        """0-30 based on overlap between event topics and user interests."""
        if not user_interests:
            return 0.0
        normalised_interests = [i.lower() for i in user_interests]
        normalised_topics = [t.lower() for t in event_topics]
        matches = sum(1 for t in normalised_topics if t in normalised_interests)
        ratio = matches / max(len(normalised_interests), 1)
        return min(30.0, ratio * 30.0)

    def _score_people(
        self, speakers: list[dict[str, Any]], user_profile: dict[str, Any]
    ) -> float:
        """0-25 based on speakers from target companies or matching target roles."""
        if not speakers:
            return 0.0
        target_companies = [c.lower() for c in user_profile.get("target_companies", [])]
        target_roles = [r.lower() for r in user_profile.get("target_roles", [])]
        if not target_companies and not target_roles:
            return 0.0

        points = 0.0
        for speaker in speakers:
            company = (speaker.get("company") or "").lower()
            role = (speaker.get("role") or "").lower()
            if company and company in target_companies:
                points += 12.5
            if role and any(tr in role for tr in target_roles):
                points += 12.5

        return min(25.0, points)

    def _score_event_type(
        self, event_type: str, preferred_types: list[str]
    ) -> float:
        """0-15. Full score if exact match, partial for related types."""
        if not preferred_types:
            return 0.0
        normalised_pref = [p.lower() for p in preferred_types]
        normalised_type = event_type.lower()
        if normalised_type in normalised_pref:
            return 15.0

        # Partial credit for related types
        related: dict[str, list[str]] = {
            "conference": ["meetup", "workshop", "demo_day"],
            "meetup": ["conference", "happy_hour"],
            "dinner": ["happy_hour"],
            "workshop": ["conference", "meetup"],
            "happy_hour": ["dinner", "meetup"],
            "demo_day": ["conference", "meetup"],
        }
        related_types = related.get(normalised_type, [])
        if any(r in normalised_pref for r in related_types):
            return 7.5
        return 0.0

    def _score_time(
        self,
        date_str: str | None,
        preferred_days: list[str],
        preferred_times: list[str],
    ) -> float:
        """0-15. Check day of week and time of day against preferences."""
        if not date_str:
            return 7.5  # neutral when no date info

        try:
            dt = datetime.fromisoformat(str(date_str))
        except (ValueError, TypeError):
            return 7.5

        score = 0.0
        day_name = dt.strftime("%A").lower()
        normalised_days = [d.lower() for d in preferred_days]
        if not preferred_days or day_name in normalised_days:
            score += 7.5

        hour = dt.hour
        normalised_times = [t.lower() for t in preferred_times]
        if not preferred_times:
            score += 7.5
        elif "morning" in normalised_times and 6 <= hour < 12:
            score += 7.5
        elif "afternoon" in normalised_times and 12 <= hour < 17:
            score += 7.5
        elif "evening" in normalised_times and 17 <= hour < 23:
            score += 7.5

        return min(15.0, score)

    def _score_historical(
        self, enriched: dict[str, Any], user_profile: dict[str, Any]
    ) -> float:
        """0-15. Placeholder returning 7.5 (neutral) until feedback loop is implemented."""
        return 7.5


def validate_analyze_output(enriched: dict[str, Any]) -> list[str]:
    """Validate enriched event output. Return list of error strings."""
    errors: list[str] = []

    score = enriched.get("relevance_score")
    if score is None:
        errors.append("missing relevance_score")
    elif not (0 <= score <= 100):
        errors.append(f"relevance_score {score} out of range 0-100")

    entities = enriched.get("entities")
    if entities is None:
        errors.append("missing entities dict")
    else:
        expected_keys = {
            "event_type", "date", "location", "speakers",
            "topics", "companies", "target_audience",
            "capacity", "price", "application_required",
        }
        missing = expected_keys - set(entities.keys())
        if missing:
            errors.append(f"entities missing keys: {sorted(missing)}")

    event_type = enriched.get("event_type") or (entities or {}).get("event_type")
    valid_types = {t.value for t in EventType}
    if event_type and event_type not in valid_types:
        errors.append(f"invalid event_type: {event_type}")

    return errors


def validate_discovery_output(events: list[dict[str, Any]]) -> list[str]:
    """Validate discovery output. Return list of error strings."""
    errors: list[str] = []
    for i, event in enumerate(events):
        if not event.get("title"):
            errors.append(f"event[{i}] missing title")
        if not event.get("url"):
            errors.append(f"event[{i}] missing url")
        if not event.get("source"):
            errors.append(f"event[{i}] missing source")
    return errors
