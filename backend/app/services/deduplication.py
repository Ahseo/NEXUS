from __future__ import annotations

from thefuzz import fuzz


def deduplicate_events(events: list[dict]) -> list[dict]:
    """Remove duplicate events using fuzzy title matching.

    Two events are duplicates if:
    - fuzz.ratio(title1, title2) > 80 AND
    - same date (if dates exist) or no dates to compare

    When merging, keep the event with the longer description.
    """
    if not events:
        return []

    unique: list[dict] = []

    for event in events:
        merged = False
        for i, existing in enumerate(unique):
            if _is_duplicate_event(event, existing):
                if len(event.get("description", "")) > len(
                    existing.get("description", "")
                ):
                    unique[i] = event
                merged = True
                break
        if not merged:
            unique.append(event)

    return unique


def deduplicate_attendees(attendees: list[dict]) -> list[dict]:
    """Remove duplicate attendees using name similarity (fuzz.ratio > 85)."""
    if not attendees:
        return []

    unique: list[dict] = []

    for attendee in attendees:
        merged = False
        name = attendee.get("name", "")
        for existing in unique:
            existing_name = existing.get("name", "")
            if name and existing_name and fuzz.ratio(name, existing_name) > 85:
                merged = True
                break
        if not merged:
            unique.append(attendee)

    return unique


def _is_duplicate_event(a: dict, b: dict) -> bool:
    title_a = a.get("title", "")
    title_b = b.get("title", "")
    if not title_a or not title_b:
        return False
    if fuzz.ratio(title_a, title_b) <= 80:
        return False
    date_a = a.get("date")
    date_b = b.get("date")
    if date_a and date_b:
        return date_a == date_b
    return True
