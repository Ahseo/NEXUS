from __future__ import annotations

import json
import uuid
from datetime import datetime
from typing import Any

import anthropic

from app.core.config import settings
from app.integrations.neo4j_client import Neo4jClient
from app.models.event import EventType
from app.services.scoring import ScoringEngine


_EXTRACTION_PROMPT = """\
You are a structured data extractor for networking events.

Given an event title, URL, source, and description, extract the following fields as JSON:

{
  "event_type": one of "conference", "meetup", "dinner", "workshop", "happy_hour", "demo_day",
  "date": ISO 8601 datetime string or null if not found,
  "location": string or "",
  "speakers": [{"name": "...", "role": "...", "company": "..."}],
  "topics": ["topic1", "topic2"],
  "companies": ["company1", "company2"],
  "target_audience": string or "",
  "capacity": integer or null,
  "price": float or null,
  "application_required": boolean
}

Rules:
- Only extract information explicitly stated in the description.
- If a speaker's role or company is not mentioned, use empty string.
- Companies should include any companies mentioned (sponsors, speaker affiliations, etc.).
- Return ONLY valid JSON, no markdown fences or extra text.
"""


class AnalyzeAgent:
    """Extract entities from events via Claude API and score them for relevance."""

    def __init__(self, neo4j: Neo4jClient | None = None) -> None:
        self._neo4j = neo4j
        self._anthropic = anthropic.AsyncAnthropic(
            api_key=settings.anthropic_api_key or "dummy"
        )
        self._scoring = ScoringEngine()

    async def extract_entities(self, event: dict[str, Any]) -> dict[str, Any]:
        """Use Claude API to extract structured entities from event description.

        Returns dict with event_type, date, location, speakers, topics,
        companies, target_audience, capacity, price, application_required.
        """
        user_content = (
            f"Title: {event.get('title', '')}\n"
            f"URL: {event.get('url', '')}\n"
            f"Source: {event.get('source', '')}\n"
            f"Description: {event.get('description', '')}"
        )

        response = await self._anthropic.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=1024,
            messages=[
                {"role": "user", "content": f"{_EXTRACTION_PROMPT}\n\n{user_content}"}
            ],
        )

        first_block = response.content[0]
        raw_text: str = first_block.text if first_block.type == "text" else ""  # type: ignore[union-attr]
        entities = json.loads(raw_text)

        # Validate event_type
        valid_types = {t.value for t in EventType}
        if entities.get("event_type") not in valid_types:
            entities["event_type"] = "meetup"

        # Ensure required keys have defaults
        entities.setdefault("date", None)
        entities.setdefault("location", "")
        entities.setdefault("speakers", [])
        entities.setdefault("topics", [])
        entities.setdefault("companies", [])
        entities.setdefault("target_audience", "")
        entities.setdefault("capacity", None)
        entities.setdefault("price", None)
        entities.setdefault("application_required", False)

        return entities

    async def update_knowledge_graph(self, enriched: dict[str, Any]) -> None:
        """Populate Neo4j with event data.

        Creates/merges Event, Person, Company, Topic nodes and relationships.
        """
        if self._neo4j is None:
            return

        entities = enriched.get("entities", {})

        # Merge event node
        await self._neo4j.merge_event(
            {
                "url": enriched["url"],
                "title": enriched["title"],
                "event_type": entities.get("event_type", ""),
                "date": entities.get("date", ""),
                "location": entities.get("location", ""),
            }
        )

        # Merge speakers and create relationships
        for speaker in entities.get("speakers", []):
            name = speaker.get("name", "")
            if not name:
                continue
            await self._neo4j.merge_person(
                {
                    "name": name,
                    "role": speaker.get("role", ""),
                    "company": speaker.get("company", ""),
                }
            )
            await self._neo4j.create_relationship(
                "Person", "name", name,
                "SPEAKS_AT",
                "Event", "url", enriched["url"],
            )
            company = speaker.get("company", "")
            if company:
                await self._neo4j.merge_company({"name": company})
                await self._neo4j.create_relationship(
                    "Person", "name", name,
                    "WORKS_AT",
                    "Company", "name", company,
                )

        # Merge companies mentioned in entities
        for company_name in entities.get("companies", []):
            await self._neo4j.merge_company({"name": company_name})

        # Merge topics and tag event
        for topic_name in entities.get("topics", []):
            await self._neo4j.merge_topic({"name": topic_name})
            await self._neo4j.create_relationship(
                "Event", "url", enriched["url"],
                "TAGGED",
                "Topic", "name", topic_name,
            )

    async def analyze_event(
        self, raw_event: dict[str, Any], user_profile: dict[str, Any]
    ) -> dict[str, Any]:
        """Full pipeline: extract entities, score, update graph.

        Returns enriched event dict with relevance_score.
        """
        entities = await self.extract_entities(raw_event)

        enriched: dict[str, Any] = {
            "id": str(uuid.uuid4()),
            "url": raw_event.get("url", ""),
            "title": raw_event.get("title", ""),
            "description": raw_event.get("description", ""),
            "source": raw_event.get("source", ""),
            "entities": entities,
            "event_type": entities.get("event_type", "meetup"),
            "date": entities.get("date"),
            "location": entities.get("location", ""),
            "speakers": entities.get("speakers", []),
            "topics": entities.get("topics", []),
            "companies": entities.get("companies", []),
            "target_audience": entities.get("target_audience", ""),
            "capacity": entities.get("capacity"),
            "price": entities.get("price"),
            "application_required": entities.get("application_required", False),
        }

        score = self._scoring.calculate_relevance(enriched, user_profile)
        enriched["relevance_score"] = score

        await self.update_knowledge_graph(enriched)

        return enriched
