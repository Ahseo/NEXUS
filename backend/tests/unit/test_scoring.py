from __future__ import annotations

import pytest

from app.services.scoring import (
    ScoringEngine,
    validate_analyze_output,
    validate_discovery_output,
)


@pytest.fixture
def engine() -> ScoringEngine:
    return ScoringEngine()


# ── calculate_relevance ──────────────────────────────────────────────────────


def test_score_always_between_0_and_100(
    engine: ScoringEngine, test_user_profile: dict
) -> None:
    enriched = {
        "topics": ["AI agents", "developer tools", "fundraising"],
        "speakers": [
            {"name": "A", "role": "VC Partner", "company": "Sequoia"},
        ],
        "event_type": "dinner",
        "date": "2026-03-10T18:00:00",  # Tuesday evening
    }
    score = engine.calculate_relevance(enriched, test_user_profile)
    assert 0 <= score <= 100


def test_score_with_empty_enriched(
    engine: ScoringEngine, test_user_profile: dict
) -> None:
    score = engine.calculate_relevance({}, test_user_profile)
    assert 0 <= score <= 100


def test_empty_profile_returns_baseline(engine: ScoringEngine) -> None:
    enriched = {
        "topics": ["AI"],
        "speakers": [],
        "event_type": "meetup",
        "date": None,
    }
    empty_profile: dict = {
        "interests": [],
        "target_companies": [],
        "target_roles": [],
        "preferred_event_types": [],
        "preferred_days": [],
        "preferred_times": [],
    }
    score = engine.calculate_relevance(enriched, empty_profile)
    # Should be at least the historical baseline (7.5) + neutral time (7.5)
    assert score >= 7.5


# ── _score_topics ────────────────────────────────────────────────────────────


def test_topic_full_overlap(engine: ScoringEngine) -> None:
    score = engine._score_topics(
        ["AI agents", "developer tools", "fundraising"],
        ["AI agents", "developer tools", "fundraising"],
    )
    assert score == 30.0


def test_topic_no_overlap(engine: ScoringEngine) -> None:
    score = engine._score_topics(
        ["blockchain", "crypto"],
        ["AI agents", "developer tools", "fundraising"],
    )
    assert score == 0.0


def test_topic_partial_overlap(engine: ScoringEngine) -> None:
    score = engine._score_topics(
        ["AI agents"],
        ["AI agents", "developer tools", "fundraising"],
    )
    assert 0 < score < 30.0


def test_topic_empty_interests(engine: ScoringEngine) -> None:
    score = engine._score_topics(["AI agents"], [])
    assert score == 0.0


# ── _score_people ────────────────────────────────────────────────────────────


def test_people_from_target_companies(engine: ScoringEngine) -> None:
    speakers = [
        {"name": "A", "role": "Partner", "company": "Sequoia"},
    ]
    profile = {
        "target_companies": ["Sequoia", "a16z"],
        "target_roles": [],
    }
    score = engine._score_people(speakers, profile)
    assert score > 0


def test_people_matching_target_roles(engine: ScoringEngine) -> None:
    speakers = [
        {"name": "A", "role": "Senior Engineer", "company": "Startup"},
    ]
    profile = {
        "target_companies": [],
        "target_roles": ["Senior Engineer"],
    }
    score = engine._score_people(speakers, profile)
    assert score > 0


def test_people_no_speakers(engine: ScoringEngine) -> None:
    profile = {
        "target_companies": ["Sequoia"],
        "target_roles": ["VC Partner"],
    }
    score = engine._score_people([], profile)
    assert score == 0.0


def test_people_no_targets(engine: ScoringEngine) -> None:
    speakers = [{"name": "A", "role": "CEO", "company": "BigCo"}]
    profile: dict = {"target_companies": [], "target_roles": []}
    score = engine._score_people(speakers, profile)
    assert score == 0.0


# ── _score_event_type ────────────────────────────────────────────────────────


def test_event_type_exact_match(engine: ScoringEngine) -> None:
    score = engine._score_event_type("dinner", ["dinner", "meetup"])
    assert score == 15.0


def test_event_type_no_match(engine: ScoringEngine) -> None:
    score = engine._score_event_type("conference", ["dinner"])
    assert score == 0.0


def test_event_type_related_match(engine: ScoringEngine) -> None:
    # happy_hour is related to dinner
    score = engine._score_event_type("happy_hour", ["dinner"])
    assert score == 7.5


def test_event_type_empty_prefs(engine: ScoringEngine) -> None:
    score = engine._score_event_type("dinner", [])
    assert score == 0.0


# ── _score_time ──────────────────────────────────────────────────────────────


def test_time_preferred_day_and_time(engine: ScoringEngine) -> None:
    # 2026-03-10 is a Tuesday, 18:00 is evening
    score = engine._score_time("2026-03-10T18:00:00", ["tuesday"], ["evening"])
    assert score == 15.0


def test_time_wrong_day(engine: ScoringEngine) -> None:
    # 2026-03-11 is a Wednesday
    score = engine._score_time("2026-03-11T18:00:00", ["tuesday"], ["evening"])
    assert score < 15.0
    assert score >= 0.0


def test_time_no_date(engine: ScoringEngine) -> None:
    score = engine._score_time(None, ["tuesday"], ["evening"])
    assert score == 7.5


def test_time_no_preferences(engine: ScoringEngine) -> None:
    score = engine._score_time("2026-03-10T18:00:00", [], [])
    assert score == 15.0


# ── _score_historical ────────────────────────────────────────────────────────


def test_historical_returns_neutral(engine: ScoringEngine) -> None:
    assert engine._score_historical({}, {}) == 7.5


# ── validate_analyze_output ──────────────────────────────────────────────────


def test_validate_analyze_output_valid() -> None:
    enriched = {
        "relevance_score": 75.0,
        "event_type": "dinner",
        "entities": {
            "event_type": "dinner",
            "date": "2026-03-15T18:00:00",
            "location": "SF",
            "speakers": [],
            "topics": [],
            "companies": [],
            "target_audience": "",
            "capacity": None,
            "price": None,
            "application_required": False,
        },
    }
    errors = validate_analyze_output(enriched)
    assert errors == []


def test_validate_analyze_output_missing_score() -> None:
    errors = validate_analyze_output({"entities": {}})
    assert any("missing relevance_score" in e for e in errors)


def test_validate_analyze_output_invalid_score() -> None:
    enriched = {
        "relevance_score": 150.0,
        "entities": {
            "event_type": "dinner",
            "date": None,
            "location": "",
            "speakers": [],
            "topics": [],
            "companies": [],
            "target_audience": "",
            "capacity": None,
            "price": None,
            "application_required": False,
        },
    }
    errors = validate_analyze_output(enriched)
    assert any("out of range" in e for e in errors)


def test_validate_analyze_output_missing_entities() -> None:
    errors = validate_analyze_output({"relevance_score": 50.0})
    assert any("missing entities" in e for e in errors)


def test_validate_analyze_output_invalid_event_type() -> None:
    enriched = {
        "relevance_score": 50.0,
        "event_type": "invalid_type",
        "entities": {
            "event_type": "invalid_type",
            "date": None,
            "location": "",
            "speakers": [],
            "topics": [],
            "companies": [],
            "target_audience": "",
            "capacity": None,
            "price": None,
            "application_required": False,
        },
    }
    errors = validate_analyze_output(enriched)
    assert any("invalid event_type" in e for e in errors)


# ── validate_discovery_output ────────────────────────────────────────────────


def test_validate_discovery_output_valid() -> None:
    events = [
        {"title": "Event 1", "url": "https://example.com", "source": "luma"},
        {"title": "Event 2", "url": "https://example.com/2", "source": "meetup"},
    ]
    errors = validate_discovery_output(events)
    assert errors == []


def test_validate_discovery_output_missing_title() -> None:
    events = [{"url": "https://example.com", "source": "luma"}]
    errors = validate_discovery_output(events)
    assert any("missing title" in e for e in errors)


def test_validate_discovery_output_missing_url() -> None:
    events = [{"title": "Event", "source": "luma"}]
    errors = validate_discovery_output(events)
    assert any("missing url" in e for e in errors)


def test_validate_discovery_output_missing_source() -> None:
    events = [{"title": "Event", "url": "https://example.com"}]
    errors = validate_discovery_output(events)
    assert any("missing source" in e for e in errors)


def test_validate_discovery_output_empty_list() -> None:
    errors = validate_discovery_output([])
    assert errors == []
