from __future__ import annotations

import logging
from typing import Any

logger = logging.getLogger(__name__)

MAX_MESSAGE_LENGTH = 100  # words

# Channel preference order (most preferred first)
_CHANNEL_PREFERENCE = ["twitter_dm", "linkedin", "email", "instagram_dm"]


class MessageGenerator:
    def __init__(self) -> None:
        self._linkedin_sends_this_week = 0
        self._max_linkedin_per_week = 20

    def draft_cold_message(
        self, person: dict[str, Any], event: dict[str, Any], user_profile: dict[str, Any]
    ) -> dict[str, Any]:
        """Draft personalized cold message.

        Must include: reference to their recent work, specific event mention, clear reason
        to connect.
        Must NOT include: generic flattery, sales pitch, asking for favors.
        Returns dict with: recipient, channel, message_type, body, word_count.
        Max MAX_MESSAGE_LENGTH words.
        """
        name = person.get("name", "")
        first_name = name.split()[0] if name else "there"
        event_title = event.get("title", "the event")
        user_name = user_profile.get("name", "")
        user_role = user_profile.get("role", "")
        user_company = user_profile.get("company", "")
        recent_work = person.get("recent_work", "")
        person_role = person.get("current_role") or person.get("role") or ""
        person_company = person.get("company", "")
        tone = user_profile.get("message_tone", "casual")

        # Build the work reference
        work_ref = ""
        if recent_work:
            work_snippet = recent_work[:80].rstrip()
            if not work_snippet.endswith("."):
                work_snippet = work_snippet.rsplit(" ", 1)[0]
            work_ref = f"I came across your work on {work_snippet}. "

        # Build the connection reason
        reason = self._build_connection_reason(person, user_profile)

        # Build the message body based on tone
        if tone == "professional":
            body = (
                f"Hi {first_name}, I noticed you're attending {event_title}. "
                f"{work_ref}"
                f"I'm {user_name}, {user_role} at {user_company}. "
                f"{reason}"
                f"Would be great to connect at the event."
            )
        else:
            body = (
                f"Hey {first_name}! Saw you're going to {event_title}. "
                f"{work_ref}"
                f"I'm {user_name} — {user_role} at {user_company}. "
                f"{reason}"
                f"Would love to chat!"
            )

        body = self._trim_to_word_limit(body, MAX_MESSAGE_LENGTH)
        channel = self.select_best_channel(person)

        return {
            "recipient": name,
            "channel": channel,
            "message_type": "cold_outreach",
            "body": body,
            "word_count": len(body.split()),
        }

    def generate_followup_message(
        self,
        person: dict[str, Any],
        event: dict[str, Any],
        user_profile: dict[str, Any],
        met: bool = True,
    ) -> dict[str, Any]:
        """Generate follow-up message.

        met=True: "Great meeting you at {event}..."
        met=False: "Sorry I missed you at {event}..."
        Returns dict with message fields.
        """
        name = person.get("name", "")
        first_name = name.split()[0] if name else "there"
        event_title = event.get("title", "the event")
        user_name = user_profile.get("name", "")
        recent_work = person.get("recent_work", "")

        work_ref = ""
        if recent_work:
            work_snippet = recent_work[:60].rstrip()
            if not work_snippet.endswith("."):
                work_snippet = work_snippet.rsplit(" ", 1)[0]
            work_ref = f" Your work on {work_snippet} is really interesting."

        if met:
            body = (
                f"Hey {first_name}! Great meeting you at {event_title}. "
                f"Really enjoyed our conversation.{work_ref} "
                f"Let's keep in touch — {user_name}"
            )
        else:
            body = (
                f"Hey {first_name}, sorry I missed you at {event_title}. "
                f"I saw you were attending and wanted to reach out.{work_ref} "
                f"Would love to connect — {user_name}"
            )

        body = self._trim_to_word_limit(body, MAX_MESSAGE_LENGTH)
        channel = self.select_best_channel(person)

        return {
            "recipient": name,
            "channel": channel,
            "message_type": "followup_met" if met else "followup_missed",
            "body": body,
            "word_count": len(body.split()),
        }

    def select_best_channel(self, person: dict[str, Any]) -> str:
        """Select best outreach channel.

        Prefer: twitter_dm > linkedin > email > instagram_dm.
        If LinkedIn weekly limit reached, fall back to next option.
        Returns channel string.
        """
        linkedin_available = (
            self._linkedin_sends_this_week < self._max_linkedin_per_week
        )

        for channel in _CHANNEL_PREFERENCE:
            if channel == "linkedin" and not linkedin_available:
                continue
            # Check if person has this channel
            channel_key = channel.replace("_dm", "")
            if person.get(channel_key):
                return channel

        # Default to email if nothing else available
        return "email"

    def _build_connection_reason(
        self, person: dict[str, Any], user_profile: dict[str, Any]
    ) -> str:
        """Build a specific reason to connect based on overlapping interests."""
        person_interests = [i.lower() for i in person.get("interests", [])]
        user_interests = [i.lower() for i in user_profile.get("interests", [])]

        shared = []
        for pi in person_interests:
            for ui in user_interests:
                if pi == ui or (pi in ui or ui in pi):
                    shared.append(pi)
                    break

        if shared:
            topic = shared[0]
            return f"We're both into {topic} — "

        person_role = (person.get("current_role") or person.get("role") or "").lower()
        target_roles = [r.lower() for r in user_profile.get("target_roles", [])]
        for target in target_roles:
            if target in person_role or person_role in target:
                return f"Your experience as {person.get('current_role') or person.get('role', '')} is really relevant to what we're building. "

        return ""

    def _trim_to_word_limit(self, text: str, max_words: int) -> str:
        """Trim text to max_words, ending at a sentence or natural break."""
        words = text.split()
        if len(words) <= max_words:
            return text

        trimmed = " ".join(words[:max_words])
        # Try to end at a sentence
        last_period = trimmed.rfind(".")
        last_excl = trimmed.rfind("!")
        last_break = max(last_period, last_excl)
        if last_break > len(trimmed) // 2:
            return trimmed[: last_break + 1]
        return trimmed
