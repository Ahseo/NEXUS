from __future__ import annotations

import json
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.agents.analyze import AnalyzeAgent


_MOCK_ENTITIES = {
    "event_type": "dinner",
    "date": "2026-03-15T18:00:00",
    "location": "San Francisco, CA",
    "speakers": [
        {"name": "Sarah Chen", "role": "VC Partner", "company": "Sequoia"},
        {"name": "James Liu", "role": "Partner", "company": "a16z"},
    ],
    "topics": ["AI agents", "fundraising"],
    "companies": ["Sequoia", "a16z"],
    "target_audience": "founders and investors",
    "capacity": 30,
    "price": None,
    "application_required": False,
}


def _make_claude_response(entities: dict) -> MagicMock:
    """Create a mock Claude API response."""
    content_block = MagicMock()
    content_block.type = "text"
    content_block.text = json.dumps(entities)
    response = MagicMock()
    response.content = [content_block]
    return response


@pytest.fixture
def mock_neo4j() -> AsyncMock:
    neo4j = AsyncMock()
    neo4j.merge_event = AsyncMock(return_value=[])
    neo4j.merge_person = AsyncMock(return_value=[])
    neo4j.merge_company = AsyncMock(return_value=[])
    neo4j.merge_topic = AsyncMock(return_value=[])
    neo4j.create_relationship = AsyncMock(return_value=[])
    return neo4j


@pytest.fixture
def agent(mock_neo4j: AsyncMock) -> AnalyzeAgent:
    return AnalyzeAgent(neo4j=mock_neo4j)


# ── extract_entities ─────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_extract_entities_returns_correct_structure(
    agent: AnalyzeAgent, sample_raw_event: dict
) -> None:
    with patch.object(
        agent._anthropic.messages, "create", new_callable=AsyncMock
    ) as mock_create:
        mock_create.return_value = _make_claude_response(_MOCK_ENTITIES)

        result = await agent.extract_entities(sample_raw_event)

    assert result["event_type"] == "dinner"
    assert result["date"] == "2026-03-15T18:00:00"
    assert result["location"] == "San Francisco, CA"
    assert len(result["speakers"]) == 2
    assert result["speakers"][0]["name"] == "Sarah Chen"
    assert result["topics"] == ["AI agents", "fundraising"]
    assert result["companies"] == ["Sequoia", "a16z"]
    assert result["capacity"] == 30
    assert result["price"] is None
    assert result["application_required"] is False


@pytest.mark.asyncio
async def test_extract_entities_no_speakers(
    agent: AnalyzeAgent, sample_raw_event: dict
) -> None:
    entities_no_speakers = {**_MOCK_ENTITIES, "speakers": [], "companies": []}
    with patch.object(
        agent._anthropic.messages, "create", new_callable=AsyncMock
    ) as mock_create:
        mock_create.return_value = _make_claude_response(entities_no_speakers)

        result = await agent.extract_entities(sample_raw_event)

    assert result["speakers"] == []
    assert result["companies"] == []


@pytest.mark.asyncio
async def test_extract_entities_invalid_event_type_defaults_to_meetup(
    agent: AnalyzeAgent, sample_raw_event: dict
) -> None:
    entities_bad_type = {**_MOCK_ENTITIES, "event_type": "unknown_type"}
    with patch.object(
        agent._anthropic.messages, "create", new_callable=AsyncMock
    ) as mock_create:
        mock_create.return_value = _make_claude_response(entities_bad_type)

        result = await agent.extract_entities(sample_raw_event)

    assert result["event_type"] == "meetup"


# ── update_knowledge_graph ───────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_update_knowledge_graph_calls_merge_methods(
    agent: AnalyzeAgent, mock_neo4j: AsyncMock
) -> None:
    enriched = {
        "url": "https://lu.ma/ai-dinner-sf",
        "title": "AI Founders Dinner",
        "entities": _MOCK_ENTITIES,
    }

    await agent.update_knowledge_graph(enriched)

    mock_neo4j.merge_event.assert_called_once()
    assert mock_neo4j.merge_person.call_count == 2
    # 2 speaker companies + 2 companies list entries (Sequoia, a16z appear in both)
    assert mock_neo4j.merge_company.call_count >= 2
    assert mock_neo4j.merge_topic.call_count == 2
    # SPEAKS_AT for each speaker + WORKS_AT for each speaker with company + TAGGED for each topic
    assert mock_neo4j.create_relationship.call_count >= 4


@pytest.mark.asyncio
async def test_update_knowledge_graph_skips_when_no_neo4j(
    sample_raw_event: dict,
) -> None:
    agent = AnalyzeAgent(neo4j=None)
    enriched = {
        "url": "https://lu.ma/ai-dinner-sf",
        "title": "AI Founders Dinner",
        "entities": _MOCK_ENTITIES,
    }
    # Should not raise
    await agent.update_knowledge_graph(enriched)


# ── analyze_event (full pipeline) ───────────────────────────────────────────


@pytest.mark.asyncio
async def test_analyze_event_full_pipeline(
    agent: AnalyzeAgent,
    mock_neo4j: AsyncMock,
    sample_raw_event: dict,
    test_user_profile: dict,
) -> None:
    with patch.object(
        agent._anthropic.messages, "create", new_callable=AsyncMock
    ) as mock_create:
        mock_create.return_value = _make_claude_response(_MOCK_ENTITIES)

        result = await agent.analyze_event(sample_raw_event, test_user_profile)

    # Should have enriched fields
    assert "id" in result
    assert result["url"] == sample_raw_event["url"]
    assert result["title"] == sample_raw_event["title"]
    assert "entities" in result
    assert "relevance_score" in result
    assert 0 <= result["relevance_score"] <= 100

    # Neo4j should have been updated
    mock_neo4j.merge_event.assert_called_once()
