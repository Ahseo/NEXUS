from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

import httpx

_DEFAULT_BASE_URL = "https://api.yutori.com"
_TIMEOUT = 30.0


@dataclass
class YutoriTask:
    task_id: str
    status: str
    result: dict[str, Any] | None

    @classmethod
    def from_response(cls, data: dict[str, Any]) -> YutoriTask:
        return cls(
            task_id=data.get("task_id", ""),
            status=data.get("status", "unknown"),
            result=data.get("result"),
        )


@dataclass
class YutoriClient:
    api_key: str
    base_url: str = _DEFAULT_BASE_URL
    _client: httpx.AsyncClient = field(init=False, repr=False)

    def __post_init__(self) -> None:
        if not self.api_key:
            raise ValueError("yutori_api_key is required")
        self._client = httpx.AsyncClient(
            base_url=self.base_url,
            headers={"X-API-Key": self.api_key},
            timeout=_TIMEOUT,
        )

    async def close(self) -> None:
        await self._client.aclose()

    # -- Browsing API ----------------------------------------------------------

    async def browsing_create(
        self,
        task: str,
        *,
        start_url: str | None = None,
        max_steps: int = 50,
        output_schema: dict[str, Any] | None = None,
        webhook_url: str | None = None,
    ) -> YutoriTask:
        body: dict[str, Any] = {"task": task, "max_steps": max_steps}
        if start_url:
            body["start_url"] = start_url
        if output_schema:
            body["output_schema"] = output_schema
        if webhook_url:
            body["webhook_url"] = webhook_url

        resp = await self._client.post("/v1/browsing/tasks", json=body)
        resp.raise_for_status()
        return YutoriTask.from_response(resp.json())

    async def browsing_get(self, task_id: str) -> YutoriTask:
        resp = await self._client.get(f"/v1/browsing/tasks/{task_id}")
        resp.raise_for_status()
        return YutoriTask.from_response(resp.json())

    # -- Scouting API ----------------------------------------------------------

    async def scouting_create(
        self,
        task: str,
        *,
        start_url: str | None = None,
        schedule: str | None = None,
        webhook_url: str | None = None,
    ) -> YutoriTask:
        body: dict[str, Any] = {"task": task}
        if start_url:
            body["start_url"] = start_url
        if schedule:
            body["schedule"] = schedule
        if webhook_url:
            body["webhook_url"] = webhook_url

        resp = await self._client.post("/v1/scouting/tasks", json=body)
        resp.raise_for_status()
        return YutoriTask.from_response(resp.json())
