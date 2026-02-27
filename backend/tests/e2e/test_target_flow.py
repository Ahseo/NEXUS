"""E2E test: target people matching flow.

Creates a ConnectAgent, adds target people to user profile,
checks for matches in an attendee list, and verifies score boost.
"""

from __future__ import annotations

from typing import Any

import pytest

from app.agents.connect import ConnectAgent, TARGET_SCORE_BOOST


class TestTargetFlow:
    """Test the target people matching and score boost flow."""

    def test_target_match_found(self, test_user_profile: dict[str, Any]) -> None:
        """When a target person is in the attendee list, match is found."""
        connect = ConnectAgent()

        # Add target people to user profile
        user_profile = {
            **test_user_profile,
            "target_people": [
                {"name": "Sam Altman", "reason": "OpenAI CEO", "priority": "high"},
            ],
        }

        attendees = [
            {"name": "Sam Altman", "role": "CEO", "company": "OpenAI"},
            {"name": "Alice Smith", "role": "Engineer", "company": "Google"},
            {"name": "Bob Jones", "role": "VC Partner", "company": "Sequoia"},
        ]

        event = {
            "title": "AI Founders Dinner",
            "url": "https://lu.ma/ai-dinner",
            "relevance_score": 60,
        }

        matches = connect.check_target_matches(attendees, event, user_profile)

        assert len(matches) == 1
        assert matches[0]["target_person"]["name"] == "Sam Altman"
        assert matches[0]["matched_attendee"]["name"] == "Sam Altman"
        assert matches[0]["match_score"] >= 85

    def test_target_match_boosts_event_score(self, test_user_profile: dict[str, Any]) -> None:
        """A target match boosts event relevance_score by TARGET_SCORE_BOOST (30)."""
        connect = ConnectAgent()

        user_profile = {
            **test_user_profile,
            "target_people": [
                {"name": "Sam Altman", "reason": "OpenAI CEO", "priority": "high"},
            ],
        }

        attendees = [
            {"name": "Sam Altman", "role": "CEO", "company": "OpenAI"},
        ]

        initial_score = 60
        event = {
            "title": "AI Founders Dinner",
            "url": "https://lu.ma/ai-dinner",
            "relevance_score": initial_score,
        }

        connect.check_target_matches(attendees, event, user_profile)

        assert event["relevance_score"] == initial_score + TARGET_SCORE_BOOST

    def test_score_boost_capped_at_100(self, test_user_profile: dict[str, Any]) -> None:
        """Score boost is capped at 100 even if base + boost exceeds it."""
        connect = ConnectAgent()

        user_profile = {
            **test_user_profile,
            "target_people": [
                {"name": "Sam Altman", "reason": "OpenAI CEO", "priority": "high"},
            ],
        }

        attendees = [
            {"name": "Sam Altman", "role": "CEO", "company": "OpenAI"},
        ]

        event = {
            "title": "AI Dinner",
            "url": "https://lu.ma/ai-dinner",
            "relevance_score": 85,
        }

        connect.check_target_matches(attendees, event, user_profile)

        assert event["relevance_score"] == 100

    def test_no_match_when_no_targets(self, test_user_profile: dict[str, Any]) -> None:
        """No matches when user has no target people."""
        connect = ConnectAgent()

        # Default test_user_profile has empty target_people
        attendees = [
            {"name": "Sam Altman", "role": "CEO", "company": "OpenAI"},
        ]
        event = {"relevance_score": 60}

        matches = connect.check_target_matches(attendees, event, test_user_profile)
        assert matches == []
        assert event["relevance_score"] == 60  # unchanged

    def test_no_match_when_names_differ(self, test_user_profile: dict[str, Any]) -> None:
        """No match when attendee names don't fuzzy-match targets."""
        connect = ConnectAgent()

        user_profile = {
            **test_user_profile,
            "target_people": [
                {"name": "Sam Altman", "reason": "OpenAI CEO", "priority": "high"},
            ],
        }

        attendees = [
            {"name": "John Smith", "role": "Engineer", "company": "Acme"},
            {"name": "Jane Doe", "role": "Designer", "company": "DesignCo"},
        ]
        event = {"relevance_score": 60}

        matches = connect.check_target_matches(attendees, event, user_profile)
        assert matches == []
        assert event["relevance_score"] == 60

    def test_fuzzy_match_handles_slight_name_variation(
        self, test_user_profile: dict[str, Any]
    ) -> None:
        """Fuzzy matching catches minor name variations (e.g., extra space, case)."""
        connect = ConnectAgent()

        user_profile = {
            **test_user_profile,
            "target_people": [
                {"name": "Sam Altman", "reason": "OpenAI CEO", "priority": "high"},
            ],
        }

        attendees = [
            {"name": "sam altman", "role": "CEO", "company": "OpenAI"},
        ]
        event = {"relevance_score": 60}

        matches = connect.check_target_matches(attendees, event, user_profile)
        # fuzz.ratio("sam altman", "sam altman") == 100
        assert len(matches) == 1

    def test_multiple_target_matches(self, test_user_profile: dict[str, Any]) -> None:
        """Multiple targets can match in a single attendee list."""
        connect = ConnectAgent()

        user_profile = {
            **test_user_profile,
            "target_people": [
                {"name": "Sam Altman", "reason": "OpenAI CEO"},
                {"name": "Dario Amodei", "reason": "Anthropic CEO"},
            ],
        }

        attendees = [
            {"name": "Sam Altman", "role": "CEO", "company": "OpenAI"},
            {"name": "Dario Amodei", "role": "CEO", "company": "Anthropic"},
            {"name": "Random Person", "role": "Engineer", "company": "Acme"},
        ]
        event = {"relevance_score": 40}

        matches = connect.check_target_matches(attendees, event, user_profile)

        assert len(matches) == 2
        # Two matches: score boosted by 30 twice, capped at 100
        assert event["relevance_score"] == min(40 + TARGET_SCORE_BOOST * 2, 100)

    async def test_target_match_integrates_with_find_best_connections(
        self, test_user_profile: dict[str, Any]
    ) -> None:
        """Target matches integrate with connection scoring."""
        connect = ConnectAgent()

        user_profile = {
            **test_user_profile,
            "target_people": [
                {"name": "Sam Altman", "reason": "OpenAI CEO"},
            ],
        }

        attendees = [
            {"name": "Sam Altman", "role": "CEO", "company": "OpenAI"},
            {"name": "Random Person", "role": "Engineer", "company": "Unknown"},
        ]

        ranked = await connect.find_best_connections(attendees, user_profile)
        assert len(ranked) == 2
        # All should have connection_score
        for r in ranked:
            assert "connection_score" in r
