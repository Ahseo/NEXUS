from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

import httpx

_DEFAULT_BASE_URL = "https://api.reka.ai"
_TIMEOUT = 60.0


@dataclass
class RekaVisionResult:
    analysis: str
    conversation_hooks: list[str]
    raw: dict[str, Any]

    @classmethod
    def from_response(cls, data: dict[str, Any]) -> RekaVisionResult:
        return cls(
            analysis=data.get("analysis", ""),
            conversation_hooks=data.get("conversation_hooks", []),
            raw=data,
        )


@dataclass
class RekaClient:
    api_key: str
    base_url: str = _DEFAULT_BASE_URL
    _client: httpx.AsyncClient = field(init=False, repr=False)

    def __post_init__(self) -> None:
        if not self.api_key:
            raise ValueError("reka_api_key is required")
        self._client = httpx.AsyncClient(
            base_url=self.base_url,
            headers={"X-API-Key": self.api_key},
            timeout=_TIMEOUT,
        )

    async def close(self) -> None:
        await self._client.aclose()

    async def analyze(self, url: str, prompt: str) -> RekaVisionResult:
        body = {"url": url, "prompt": prompt}
        resp = await self._client.post("/v1/vision/analyze", json=body)
        resp.raise_for_status()
        return RekaVisionResult.from_response(resp.json())

    async def compare(
        self, urls: list[str], prompt: str
    ) -> RekaVisionResult:
        body = {"urls": urls, "prompt": prompt}
        resp = await self._client.post("/v1/vision/compare", json=body)
        resp.raise_for_status()
        return RekaVisionResult.from_response(resp.json())
