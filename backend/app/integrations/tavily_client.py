from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from tavily import AsyncTavilyClient


@dataclass
class TavilySearchResult:
    query: str
    answer: str | None
    results: list[dict[str, Any]]
    raw_content: list[str]

    @classmethod
    def from_response(cls, data: dict[str, Any]) -> TavilySearchResult:
        return cls(
            query=data.get("query", ""),
            answer=data.get("answer"),
            results=data.get("results", []),
            raw_content=[
                r.get("raw_content", "")
                for r in data.get("results", [])
                if r.get("raw_content")
            ],
        )


@dataclass
class TavilyClient:
    api_key: str
    _client: AsyncTavilyClient = field(init=False, repr=False)

    def __post_init__(self) -> None:
        if not self.api_key:
            raise ValueError("tavily_api_key is required")
        self._client = AsyncTavilyClient(api_key=self.api_key)

    async def search(
        self,
        query: str,
        *,
        search_depth: str = "advanced",
        max_results: int = 10,
        include_domains: list[str] | None = None,
        time_range: str | None = None,
        include_answer: bool = False,
        include_raw_content: bool = False,
    ) -> TavilySearchResult:
        kwargs: dict[str, Any] = {
            "query": query,
            "search_depth": search_depth,
            "max_results": max_results,
            "include_answer": include_answer,
            "include_raw_content": include_raw_content,
        }
        if include_domains:
            kwargs["include_domains"] = include_domains
        if time_range:
            kwargs["days"] = _time_range_to_days(time_range)

        response = await self._client.search(**kwargs)
        return TavilySearchResult.from_response(response)


def _time_range_to_days(time_range: str) -> int:
    mapping = {"day": 1, "week": 7, "month": 30, "year": 365}
    return mapping.get(time_range, 7)
