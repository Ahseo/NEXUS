"""Unit tests for Pydantic models, enums, and validation rules."""

from __future__ import annotations

from datetime import datetime

import pytest

from app.models.event import (
    EnrichedEvent,
    EventCreate,
    EventSource,
    EventStatus,
    EventType,
    RawEvent,
)
from app.models.feedback import Feedback, FeedbackAction, RejectionReason
from app.models.message import ColdMessage, MessageChannel, MessageCreate, MessageStatus
from app.models.person import PersonProfile, RawAttendee, SocialLinks
from app.models.profile import (
    MessageTone,
    ScoringWeights,
    TargetPerson,
    TargetPriority,
    TargetStatus,
    UserProfile,
)


# ── Enum tests ─────────────────────────────────────────────────────────────────


class TestEnums:
    def test_event_source_values(self) -> None:
        assert EventSource.LUMA == "luma"
        assert EventSource.EVENTBRITE == "eventbrite"
        assert EventSource.MEETUP == "meetup"
        assert EventSource.PARTIFUL == "partiful"
        assert EventSource.TWITTER == "twitter"
        assert EventSource.OTHER == "other"

    def test_event_type_values(self) -> None:
        assert EventType.CONFERENCE == "conference"
        assert EventType.DINNER == "dinner"
        assert EventType.HAPPY_HOUR == "happy_hour"
        assert EventType.DEMO_DAY == "demo_day"

    def test_event_status_lifecycle(self) -> None:
        statuses = [s.value for s in EventStatus]
        assert "discovered" in statuses
        assert "analyzed" in statuses
        assert "suggested" in statuses
        assert "accepted" in statuses
        assert "rejected" in statuses
        assert "applied" in statuses
        assert "confirmed" in statuses
        assert "waitlisted" in statuses
        assert "attended" in statuses
        assert "skipped" in statuses

    def test_message_channel_values(self) -> None:
        assert MessageChannel.TWITTER_DM == "twitter_dm"
        assert MessageChannel.LINKEDIN == "linkedin"
        assert MessageChannel.EMAIL == "email"

    def test_message_status_values(self) -> None:
        assert MessageStatus.DRAFT == "draft"
        assert MessageStatus.APPROVED == "approved"
        assert MessageStatus.SENT == "sent"

    def test_feedback_action_values(self) -> None:
        assert FeedbackAction.ACCEPT == "accept"
        assert FeedbackAction.REJECT == "reject"
        assert FeedbackAction.EDIT == "edit"
        assert FeedbackAction.RATE == "rate"
        assert FeedbackAction.SKIP == "skip"

    def test_rejection_reason_values(self) -> None:
        assert RejectionReason.NOT_RELEVANT == "not_relevant"
        assert RejectionReason.TOO_EXPENSIVE == "too_expensive"
        assert RejectionReason.SCHEDULE_CONFLICT == "schedule_conflict"

    def test_message_tone_values(self) -> None:
        assert MessageTone.CASUAL == "casual"
        assert MessageTone.PROFESSIONAL == "professional"
        assert MessageTone.FRIENDLY == "friendly"

    def test_target_priority_values(self) -> None:
        assert TargetPriority.HIGH == "high"
        assert TargetPriority.MEDIUM == "medium"
        assert TargetPriority.LOW == "low"

    def test_target_status_values(self) -> None:
        assert TargetStatus.SEARCHING == "searching"
        assert TargetStatus.FOUND_EVENT == "found_event"
        assert TargetStatus.MESSAGED == "messaged"
        assert TargetStatus.CONNECTED == "connected"


# ── Event models ───────────────────────────────────────────────────────────────


class TestRawEvent:
    def test_valid_raw_event(self, sample_raw_event: dict) -> None:
        event = RawEvent(**sample_raw_event)
        assert event.title == "AI Founders Dinner — SF"
        assert event.source == EventSource.LUMA

    def test_raw_event_invalid_source(self) -> None:
        with pytest.raises(ValueError):
            RawEvent(
                title="Test",
                url="https://example.com",
                source="invalid_source",
                description="test",
            )


class TestEnrichedEvent:
    def test_valid_enriched_event(self) -> None:
        event = EnrichedEvent(
            id="evt-1",
            url="https://lu.ma/test",
            title="AI Dinner",
            description="A dinner for AI founders",
            source=EventSource.LUMA,
            event_type=EventType.DINNER,
            date=datetime(2026, 3, 15, 18, 0),
            location="San Francisco, CA",
            relevance_score=85,
        )
        assert event.relevance_score == 85
        assert event.status == EventStatus.DISCOVERED

    def test_relevance_score_lower_bound(self) -> None:
        with pytest.raises(ValueError):
            EnrichedEvent(
                id="evt-1",
                url="https://lu.ma/test",
                title="Test",
                description="Test",
                source=EventSource.LUMA,
                event_type=EventType.DINNER,
                date=datetime(2026, 3, 15),
                location="SF",
                relevance_score=-1,
            )

    def test_relevance_score_upper_bound(self) -> None:
        with pytest.raises(ValueError):
            EnrichedEvent(
                id="evt-1",
                url="https://lu.ma/test",
                title="Test",
                description="Test",
                source=EventSource.LUMA,
                event_type=EventType.DINNER,
                date=datetime(2026, 3, 15),
                location="SF",
                relevance_score=101,
            )

    def test_user_rating_bounds(self) -> None:
        event = EnrichedEvent(
            id="evt-1",
            url="https://lu.ma/test",
            title="Test",
            description="Test",
            source=EventSource.LUMA,
            event_type=EventType.DINNER,
            date=datetime(2026, 3, 15),
            location="SF",
            relevance_score=50,
            user_rating=5,
        )
        assert event.user_rating == 5

        with pytest.raises(ValueError):
            EnrichedEvent(
                id="evt-1",
                url="https://lu.ma/test",
                title="Test",
                description="Test",
                source=EventSource.LUMA,
                event_type=EventType.DINNER,
                date=datetime(2026, 3, 15),
                location="SF",
                relevance_score=50,
                user_rating=6,
            )

        with pytest.raises(ValueError):
            EnrichedEvent(
                id="evt-1",
                url="https://lu.ma/test",
                title="Test",
                description="Test",
                source=EventSource.LUMA,
                event_type=EventType.DINNER,
                date=datetime(2026, 3, 15),
                location="SF",
                relevance_score=50,
                user_rating=0,
            )


class TestEventCreate:
    def test_valid_event_create(self) -> None:
        ec = EventCreate(
            url="https://lu.ma/test",
            title="Test Event",
            description="Description",
            source=EventSource.LUMA,
            event_type=EventType.MEETUP,
            date=datetime(2026, 3, 20),
            location="NYC",
            relevance_score=72,
        )
        assert ec.relevance_score == 72

    def test_score_validation(self) -> None:
        with pytest.raises(ValueError):
            EventCreate(
                url="u",
                title="t",
                description="d",
                source=EventSource.LUMA,
                event_type=EventType.MEETUP,
                date=datetime(2026, 3, 20),
                location="NYC",
                relevance_score=150,
            )


# ── Person models ──────────────────────────────────────────────────────────────


class TestPersonModels:
    def test_raw_attendee(self) -> None:
        a = RawAttendee(name="Jane Doe", title="CTO", company="Acme")
        assert a.name == "Jane Doe"
        assert a.linkedin is None

    def test_social_links(self) -> None:
        sl = SocialLinks(linkedin="linkedin.com/in/test")
        assert sl.twitter is None

    def test_person_profile_score_bounds(self) -> None:
        pp = PersonProfile(id="p-1", name="Jane", connection_score=100)
        assert pp.connection_score == 100

        with pytest.raises(ValueError):
            PersonProfile(id="p-1", name="Jane", connection_score=-5)

        with pytest.raises(ValueError):
            PersonProfile(id="p-1", name="Jane", connection_score=101)


# ── Message models ─────────────────────────────────────────────────────────────


class TestMessageModels:
    def test_cold_message(self) -> None:
        msg = ColdMessage(
            id="msg-1",
            recipient_id="p-1",
            event_id="evt-1",
            channel=MessageChannel.TWITTER_DM,
            content="Hey, saw you at the AI dinner!",
        )
        assert msg.status == MessageStatus.DRAFT
        assert msg.response_received is False

    def test_message_create(self) -> None:
        mc = MessageCreate(
            recipient_id="p-1",
            event_id="evt-1",
            channel=MessageChannel.EMAIL,
            content="Hello!",
        )
        assert mc.channel == MessageChannel.EMAIL

    def test_invalid_channel(self) -> None:
        with pytest.raises(ValueError):
            MessageCreate(
                recipient_id="p-1",
                event_id="evt-1",
                channel="pigeon",
                content="Hello!",
            )


# ── Profile models ─────────────────────────────────────────────────────────────


class TestUserProfile:
    def test_valid_profile(self, test_user_profile: dict) -> None:
        profile = UserProfile(**test_user_profile)
        assert profile.name == "John Park"
        assert profile.auto_apply_threshold == 80
        assert profile.message_tone == MessageTone.CASUAL

    def test_threshold_bounds(self) -> None:
        with pytest.raises(ValueError):
            ScoringWeights(auto_apply_threshold=101)

        with pytest.raises(ValueError):
            ScoringWeights(suggest_threshold=-1)

        sw = ScoringWeights(
            auto_apply_threshold=0,
            suggest_threshold=100,
            auto_schedule_threshold=50,
        )
        assert sw.auto_apply_threshold == 0
        assert sw.suggest_threshold == 100

    def test_profile_threshold_bounds(self, test_user_profile: dict) -> None:
        data = {**test_user_profile, "auto_apply_threshold": 150}
        with pytest.raises(ValueError):
            UserProfile(**data)

        data2 = {**test_user_profile, "suggest_threshold": -10}
        with pytest.raises(ValueError):
            UserProfile(**data2)


class TestTargetPerson:
    def test_valid_target_person(self) -> None:
        tp = TargetPerson(
            id="tp-1",
            name="Sam Altman",
            company="OpenAI",
            role="CEO",
            reason="Discuss AI safety partnership",
            priority=TargetPriority.HIGH,
        )
        assert tp.status == TargetStatus.SEARCHING
        assert tp.matched_events == []

    def test_defaults(self) -> None:
        tp = TargetPerson(id="tp-2", name="Test Person", reason="Testing")
        assert tp.priority == TargetPriority.MEDIUM
        assert tp.status == TargetStatus.SEARCHING
        assert tp.company is None


# ── Feedback models ────────────────────────────────────────────────────────────


class TestFeedback:
    def test_valid_feedback(self) -> None:
        fb = Feedback(
            id="fb-1",
            user_id="u-1",
            event_id="evt-1",
            action=FeedbackAction.ACCEPT,
        )
        assert fb.rating is None
        assert fb.reason is None

    def test_rating_bounds(self) -> None:
        fb = Feedback(
            id="fb-2",
            user_id="u-1",
            action=FeedbackAction.RATE,
            rating=5,
        )
        assert fb.rating == 5

        with pytest.raises(ValueError):
            Feedback(id="fb-3", user_id="u-1", action=FeedbackAction.RATE, rating=0)

        with pytest.raises(ValueError):
            Feedback(id="fb-4", user_id="u-1", action=FeedbackAction.RATE, rating=6)

    def test_reject_with_reason(self) -> None:
        fb = Feedback(
            id="fb-5",
            user_id="u-1",
            event_id="evt-1",
            action=FeedbackAction.REJECT,
            reason="not_relevant",
            free_text="Topics don't match my interests",
        )
        assert fb.reason == "not_relevant"
        assert fb.free_text is not None


# ── Serialization round-trip ───────────────────────────────────────────────────


class TestSerialization:
    def test_enriched_event_roundtrip(self) -> None:
        data = {
            "id": "evt-1",
            "url": "https://lu.ma/test",
            "title": "AI Dinner",
            "description": "Test",
            "source": "luma",
            "event_type": "dinner",
            "date": "2026-03-15T18:00:00",
            "location": "SF",
            "relevance_score": 75,
        }
        event = EnrichedEvent(**data)
        dumped = event.model_dump(mode="json")
        restored = EnrichedEvent(**dumped)
        assert restored.id == event.id
        assert restored.relevance_score == event.relevance_score
        assert restored.source == EventSource.LUMA

    def test_user_profile_roundtrip(self, test_user_profile: dict) -> None:
        profile = UserProfile(**test_user_profile)
        dumped = profile.model_dump(mode="json")
        restored = UserProfile(**dumped)
        assert restored.name == profile.name
        assert restored.auto_apply_threshold == profile.auto_apply_threshold

    def test_cold_message_roundtrip(self) -> None:
        msg = ColdMessage(
            id="msg-1",
            recipient_id="p-1",
            event_id="evt-1",
            channel=MessageChannel.LINKEDIN,
            content="Hello!",
        )
        dumped = msg.model_dump(mode="json")
        restored = ColdMessage(**dumped)
        assert restored.channel == MessageChannel.LINKEDIN

    def test_feedback_roundtrip(self) -> None:
        fb = Feedback(
            id="fb-1",
            user_id="u-1",
            event_id="evt-1",
            action=FeedbackAction.RATE,
            rating=4,
        )
        dumped = fb.model_dump(mode="json")
        restored = Feedback(**dumped)
        assert restored.rating == 4
        assert restored.action == FeedbackAction.RATE
