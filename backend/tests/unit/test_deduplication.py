from __future__ import annotations

import pytest

from app.services.deduplication import deduplicate_attendees, deduplicate_events


class TestDeduplicateEvents:
    def test_similar_titles_same_date_are_merged(self) -> None:
        events = [
            {
                "title": "AI Founders Dinner — SF",
                "url": "https://lu.ma/ai-dinner",
                "source": "luma",
                "description": "A long and detailed description of the AI founders dinner event.",
                "date": "2026-03-05T18:30:00",
            },
            {
                "title": "AI Founders Dinner SF",
                "url": "https://www.eventbrite.com/e/ai-dinner",
                "source": "eventbrite",
                "description": "Short desc.",
                "date": "2026-03-05T18:30:00",
            },
        ]
        result = deduplicate_events(events)
        assert len(result) == 1
        assert "long and detailed" in result[0]["description"]

    def test_keeps_event_with_longer_description(self) -> None:
        events = [
            {
                "title": "Generative AI Demo Day SF",
                "url": "https://a.com",
                "description": "Short.",
                "date": "2026-03-10T13:00:00",
            },
            {
                "title": "Generative AI Demo Day SF 2026",
                "url": "https://b.com",
                "description": "Watch 15 startups demo their generative AI products. Judges from Google, Microsoft, and OpenAI.",
                "date": "2026-03-10T13:00:00",
            },
        ]
        result = deduplicate_events(events)
        assert len(result) == 1
        assert "15 startups" in result[0]["description"]

    def test_different_dates_not_merged(self) -> None:
        events = [
            {
                "title": "AI Founders Dinner — SF",
                "url": "https://lu.ma/dinner1",
                "description": "March 5 dinner.",
                "date": "2026-03-05T18:30:00",
            },
            {
                "title": "AI Founders Dinner — SF",
                "url": "https://lu.ma/dinner2",
                "description": "March 12 dinner.",
                "date": "2026-03-12T18:30:00",
            },
        ]
        result = deduplicate_events(events)
        assert len(result) == 2

    def test_no_dates_are_merged(self) -> None:
        events = [
            {
                "title": "AI Founders Dinner — SF",
                "url": "https://a.com",
                "description": "Long description of event one for testing.",
            },
            {
                "title": "AI Founders Dinner SF",
                "url": "https://b.com",
                "description": "Short.",
            },
        ]
        result = deduplicate_events(events)
        assert len(result) == 1

    def test_single_event_returns_unchanged(self) -> None:
        events = [
            {
                "title": "Solo Event",
                "url": "https://lu.ma/solo",
                "description": "Only event.",
            }
        ]
        result = deduplicate_events(events)
        assert len(result) == 1
        assert result[0]["title"] == "Solo Event"

    def test_empty_list_returns_empty(self) -> None:
        result = deduplicate_events([])
        assert result == []

    def test_dissimilar_titles_not_merged(self) -> None:
        events = [
            {
                "title": "AI Founders Dinner",
                "url": "https://a.com",
                "description": "Dinner.",
                "date": "2026-03-05T18:30:00",
            },
            {
                "title": "Kubernetes Meetup",
                "url": "https://b.com",
                "description": "K8s event.",
                "date": "2026-03-05T18:30:00",
            },
        ]
        result = deduplicate_events(events)
        assert len(result) == 2


class TestDeduplicateAttendees:
    def test_similar_names_merged(self) -> None:
        attendees = [
            {"name": "John Park", "email": "john@example.com"},
            {"name": "John S. Park", "email": "johnpark@other.com"},
        ]
        result = deduplicate_attendees(attendees)
        assert len(result) == 1

    def test_different_names_kept(self) -> None:
        attendees = [
            {"name": "John Park", "email": "john@example.com"},
            {"name": "Sarah Chen", "email": "sarah@example.com"},
        ]
        result = deduplicate_attendees(attendees)
        assert len(result) == 2

    def test_empty_list(self) -> None:
        result = deduplicate_attendees([])
        assert result == []

    def test_single_attendee(self) -> None:
        attendees = [{"name": "Alice", "email": "alice@example.com"}]
        result = deduplicate_attendees(attendees)
        assert len(result) == 1
