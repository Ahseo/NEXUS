from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any

from app.core.config import settings
from app.integrations.yutori_client import YutoriClient

logger = logging.getLogger(__name__)


@dataclass
class ActionDecision:
    action: str  # "auto_apply", "suggest", "skip"
    should_schedule: bool
    reason: str


class ActionAgent:
    def __init__(self, yutori: YutoriClient | None = None):
        self._yutori = yutori
        self._applies_today = 0

    def decide(self, score: float, user_profile: dict) -> ActionDecision:
        """Decision matrix based on score thresholds.

        score >= auto_apply_threshold (80): auto_apply + schedule
        score >= suggest_threshold (50): suggest (apply but ask about schedule)
        score < suggest_threshold: skip
        """
        auto_threshold = user_profile.get(
            "auto_apply_threshold", settings.auto_apply_threshold
        )
        suggest_threshold = user_profile.get(
            "suggest_threshold", settings.suggest_threshold
        )

        if score >= auto_threshold:
            return ActionDecision(
                action="auto_apply",
                should_schedule=True,
                reason=f"Score {score} >= auto-apply threshold {auto_threshold}",
            )
        if score >= suggest_threshold:
            return ActionDecision(
                action="suggest",
                should_schedule=False,
                reason=f"Score {score} >= suggest threshold {suggest_threshold}",
            )
        return ActionDecision(
            action="skip",
            should_schedule=False,
            reason=f"Score {score} below suggest threshold {suggest_threshold}",
        )

    async def apply_to_event(
        self, event: dict, user_profile: dict
    ) -> dict[str, Any]:
        """Use Yutori Navigator to RSVP/apply to an event."""
        if self._yutori is None:
            return {"status": "error", "reason": "yutori_client_not_configured"}

        if not settings.allow_side_effects:
            logger.info("Side effects disabled (mode=%s), skipping apply", settings.nexus_mode)
            return {"status": "dry_run", "reason": "side_effects_disabled"}

        if self._applies_today >= settings.max_auto_applies_per_day:
            return {"status": "rate_limited", "reason": "max_auto_applies_per_day reached"}

        name = user_profile.get("name", "")
        email = user_profile.get("email", "")
        role = user_profile.get("role", "")
        company = user_profile.get("company", "")

        task_description = (
            f"RSVP or apply to the event at {event.get('url', '')}. "
            f"Fill in any forms with: Name: {name}, Email: {email}, "
            f"Role: {role}, Company: {company}."
        )

        webhook_url = f"{settings.backend_url}/webhooks/yutori"

        yutori_task = await self._yutori.browsing_create(
            task=task_description,
            start_url=event.get("url"),
            max_steps=50,
            output_schema={
                "status": "string",
                "confirmation_id": "string|null",
            },
            webhook_url=webhook_url,
        )

        self._applies_today += 1

        return {
            "status": "applied",
            "yutori_task_id": yutori_task.task_id,
            "confirmation_id": None,
        }

    async def schedule_event(self, event: dict) -> dict[str, Any]:
        """Add event to Google Calendar (stub - returns not_connected for now)."""
        return {
            "status": "not_connected",
            "reason": "Google Calendar not connected",
        }

    def check_calendar_conflicts(
        self, event_date: str, busy_periods: list[dict]
    ) -> bool:
        """Check if event time overlaps with any busy period."""
        for period in busy_periods:
            start = period.get("start", "")
            end = period.get("end", "")
            if start <= event_date <= end:
                return True
        return False

    async def apply_with_retry(
        self, event: dict, user_profile: dict, max_retries: int = 2
    ) -> dict[str, Any]:
        """Apply with retry logic. On final failure, return manual_required with event URL."""
        last_error: str = ""
        for attempt in range(max_retries + 1):
            try:
                result = await self.apply_to_event(event, user_profile)
                if result.get("status") != "error":
                    return result
                last_error = result.get("reason", "unknown")
            except Exception as exc:
                last_error = str(exc)
                logger.warning(
                    "Apply attempt %d/%d failed: %s",
                    attempt + 1,
                    max_retries + 1,
                    last_error,
                )
        return {
            "status": "manual_required",
            "reason": last_error,
            "url": event.get("url", ""),
        }

    async def process_event(
        self, enriched_event: dict, user_profile: dict
    ) -> dict[str, Any]:
        """Full action pipeline: decide -> apply/suggest/skip -> schedule if appropriate."""
        score = enriched_event.get("relevance_score", 0)
        decision = self.decide(score, user_profile)

        result: dict[str, Any] = {
            "action": decision.action,
            "reason": decision.reason,
            "should_schedule": decision.should_schedule,
        }

        if decision.action == "auto_apply":
            apply_result = await self.apply_with_retry(enriched_event, user_profile)
            result["application"] = apply_result

            if decision.should_schedule:
                schedule_result = await self.schedule_event(enriched_event)
                result["schedule"] = schedule_result

        elif decision.action == "suggest":
            apply_result = await self.apply_with_retry(enriched_event, user_profile)
            result["application"] = apply_result

        return result
