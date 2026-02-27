from __future__ import annotations

import asyncio
from dataclasses import dataclass
from urllib.parse import urlparse

from app.integrations.tavily_client import TavilyClient
from app.integrations.yutori_client import YutoriClient, YutoriTask
from app.models.event import EventSource
from app.services.deduplication import deduplicate_events

_EVENT_DOMAINS = [
    "eventbrite.com",
    "lu.ma",
    "meetup.com",
    "partiful.com",
    "luma-cal.com",
]

_DOMAIN_SOURCE_MAP: dict[str, EventSource] = {
    "eventbrite.com": EventSource.EVENTBRITE,
    "lu.ma": EventSource.LUMA,
    "luma-cal.com": EventSource.LUMA,
    "meetup.com": EventSource.MEETUP,
    "partiful.com": EventSource.PARTIFUL,
}


def _source_from_url(url: str) -> EventSource:
    hostname = urlparse(url).hostname or ""
    for domain, source in _DOMAIN_SOURCE_MAP.items():
        if hostname == domain or hostname.endswith(f".{domain}"):
            return source
    return EventSource.OTHER


def _build_queries(user_profile: dict) -> list[str]:
    interests = user_profile.get("interests", [])
    industries = user_profile.get("target_industries", [])
    terms = interests + industries
    seen: set[str] = set()
    queries: list[str] = []
    for term in terms:
        key = term.lower()
        if key not in seen:
            seen.add(key)
            queries.append(f"SF {term} events this week")
        if len(queries) >= 3:
            break
    if not queries:
        queries.append("SF tech events this week")
    return queries


@dataclass
class DiscoveryAgent:
    tavily: TavilyClient
    yutori: YutoriClient | None = None

    async def discover_events_tavily(self, user_profile: dict) -> list[dict]:
        """Build search queries from user interests and search event platforms."""
        queries = _build_queries(user_profile)
        all_events: list[dict] = []

        search_tasks = [
            self.tavily.search(
                query,
                include_domains=_EVENT_DOMAINS,
                max_results=10,
            )
            for query in queries
        ]
        results = await asyncio.gather(*search_tasks, return_exceptions=True)

        for result in results:
            if isinstance(result, BaseException):
                continue
            for item in result.results:
                title = item.get("title", "").strip()
                url = item.get("url", "").strip()
                if not title or not url:
                    continue
                all_events.append(
                    {
                        "title": title,
                        "url": url,
                        "source": _source_from_url(url).value,
                        "description": item.get("content", ""),
                    }
                )

        return all_events

    async def setup_event_scouts(self, user_profile: dict) -> list[YutoriTask]:
        """Create Yutori Scouting tasks for continuous monitoring."""
        if self.yutori is None:
            return []

        interests = user_profile.get("interests", [])
        tasks: list[YutoriTask] = []
        platforms = [
            ("https://lu.ma", "Luma"),
            ("https://www.eventbrite.com", "Eventbrite"),
        ]
        for start_url, platform_name in platforms:
            topic = ", ".join(interests[:3]) if interests else "tech"
            task = await self.yutori.scouting_create(
                task=f"Monitor {platform_name} for SF events about {topic}",
                start_url=start_url,
                schedule="daily",
            )
            tasks.append(task)
        return tasks

    async def run_discovery_cycle(self, user_profile: dict) -> list[dict]:
        """Run full discovery: Tavily search + dedup."""
        events = await self.discover_events_tavily(user_profile)
        return deduplicate_events(events)
