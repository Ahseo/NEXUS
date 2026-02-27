from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any

from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build


@dataclass
class GoogleCalendarClient:
    credentials: Credentials
    calendar_id: str = "primary"

    def _service(self) -> Any:
        return build("calendar", "v3", credentials=self.credentials)

    def check_busy(
        self,
        time_min: datetime,
        time_max: datetime,
    ) -> list[dict[str, str]]:
        service = self._service()
        body = {
            "timeMin": time_min.isoformat() + "Z",
            "timeMax": time_max.isoformat() + "Z",
            "items": [{"id": self.calendar_id}],
        }
        result = service.freebusy().query(body=body).execute()
        busy: list[dict[str, str]] = result.get("calendars", {}).get(self.calendar_id, {}).get("busy", [])
        return busy

    def create_event(self, event_data: dict[str, Any]) -> dict[str, Any]:
        service = self._service()
        event: dict[str, Any] = (
            service.events()
            .insert(calendarId=self.calendar_id, body=event_data)
            .execute()
        )
        return event

    def list_upcoming(
        self,
        time_min: datetime,
        time_max: datetime,
        max_results: int = 20,
    ) -> list[dict[str, Any]]:
        service = self._service()
        result = (
            service.events()
            .list(
                calendarId=self.calendar_id,
                timeMin=time_min.isoformat() + "Z",
                timeMax=time_max.isoformat() + "Z",
                maxResults=max_results,
                singleEvents=True,
                orderBy="startTime",
            )
            .execute()
        )
        items: list[dict[str, Any]] = result.get("items", [])
        return items
