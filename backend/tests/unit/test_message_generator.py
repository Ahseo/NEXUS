from __future__ import annotations

import pytest

from app.services.message_generator import MAX_MESSAGE_LENGTH, MessageGenerator


@pytest.fixture
def generator() -> MessageGenerator:
    return MessageGenerator()


@pytest.fixture
def sample_person() -> dict:
    return {
        "name": "Sarah Chen",
        "current_role": "Partner",
        "company": "Sequoia",
        "twitter": "https://x.com/sarachen",
        "linkedin": "https://linkedin.com/in/sarachen",
        "recent_work": "Led Series A investment in AI infrastructure startups",
        "interests": ["AI agents", "developer tools"],
    }


@pytest.fixture
def sample_event() -> dict:
    return {
        "title": "AI Founders Dinner — SF",
        "url": "https://lu.ma/ai-dinner-sf",
    }


@pytest.fixture
def sample_user_profile() -> dict:
    return {
        "name": "John Park",
        "role": "Founder & CEO",
        "company": "BuildAI",
        "interests": ["AI agents", "developer tools", "fundraising"],
        "target_roles": ["VC Partner", "Senior Engineer"],
        "message_tone": "casual",
    }


class TestDraftColdMessage:
    def test_cold_message_under_100_words(
        self,
        generator: MessageGenerator,
        sample_person: dict,
        sample_event: dict,
        sample_user_profile: dict,
    ) -> None:
        msg = generator.draft_cold_message(sample_person, sample_event, sample_user_profile)
        assert msg["word_count"] <= MAX_MESSAGE_LENGTH

    def test_cold_message_includes_event_reference(
        self,
        generator: MessageGenerator,
        sample_person: dict,
        sample_event: dict,
        sample_user_profile: dict,
    ) -> None:
        msg = generator.draft_cold_message(sample_person, sample_event, sample_user_profile)
        assert "AI Founders Dinner" in msg["body"]

    def test_cold_message_includes_person_info(
        self,
        generator: MessageGenerator,
        sample_person: dict,
        sample_event: dict,
        sample_user_profile: dict,
    ) -> None:
        msg = generator.draft_cold_message(sample_person, sample_event, sample_user_profile)
        assert "Sarah" in msg["body"]


class TestFollowupMessage:
    def test_followup_met_message(
        self,
        generator: MessageGenerator,
        sample_person: dict,
        sample_event: dict,
        sample_user_profile: dict,
    ) -> None:
        msg = generator.generate_followup_message(
            sample_person, sample_event, sample_user_profile, met=True
        )
        assert "Great meeting" in msg["body"]
        assert msg["message_type"] == "followup_met"

    def test_followup_missed_message(
        self,
        generator: MessageGenerator,
        sample_person: dict,
        sample_event: dict,
        sample_user_profile: dict,
    ) -> None:
        msg = generator.generate_followup_message(
            sample_person, sample_event, sample_user_profile, met=False
        )
        assert "missed" in msg["body"].lower()
        assert msg["message_type"] == "followup_missed"


class TestSelectChannel:
    def test_select_channel_prefers_twitter(
        self,
        generator: MessageGenerator,
    ) -> None:
        person = {
            "twitter": "https://x.com/someone",
            "linkedin": "https://linkedin.com/in/someone",
        }
        assert generator.select_best_channel(person) == "twitter_dm"

    def test_select_channel_linkedin_limit(
        self,
        generator: MessageGenerator,
    ) -> None:
        generator._linkedin_sends_this_week = 20
        person = {
            "linkedin": "https://linkedin.com/in/someone",
            "email": "someone@example.com",
        }
        channel = generator.select_best_channel(person)
        assert channel != "linkedin"
        assert channel == "email"
