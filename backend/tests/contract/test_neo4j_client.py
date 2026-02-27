from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.integrations.neo4j_client import Neo4jClient


# -- Helpers -------------------------------------------------------------------


def _make_mock_driver() -> MagicMock:
    """Create a mock AsyncDriver with session/run/data chain."""
    mock_result = AsyncMock()
    mock_result.data = AsyncMock(return_value=[{"n": {"name": "test"}}])
    mock_result.consume = AsyncMock()

    mock_session = AsyncMock()
    mock_session.run = AsyncMock(return_value=mock_result)
    mock_session.__aenter__ = AsyncMock(return_value=mock_session)
    mock_session.__aexit__ = AsyncMock(return_value=False)

    mock_driver = AsyncMock()
    mock_driver.session = MagicMock(return_value=mock_session)
    mock_driver.close = AsyncMock()

    return mock_driver


# -- Tests ---------------------------------------------------------------------


class TestNeo4jClientConnection:
    @pytest.mark.asyncio
    async def test_connect_creates_driver(self) -> None:
        with patch(
            "app.integrations.neo4j_client.AsyncGraphDatabase"
        ) as MockGDB:
            mock_driver = _make_mock_driver()
            MockGDB.driver.return_value = mock_driver

            client = Neo4jClient(
                uri="bolt://localhost:7687",
                user="neo4j",
                password="test-pass",
            )
            await client.connect()

            MockGDB.driver.assert_called_once_with(
                "bolt://localhost:7687", auth=("neo4j", "test-pass")
            )

    @pytest.mark.asyncio
    async def test_connect_is_idempotent(self) -> None:
        with patch(
            "app.integrations.neo4j_client.AsyncGraphDatabase"
        ) as MockGDB:
            mock_driver = _make_mock_driver()
            MockGDB.driver.return_value = mock_driver

            client = Neo4jClient(
                uri="bolt://localhost:7687", user="neo4j", password="test"
            )
            await client.connect()
            await client.connect()

            assert MockGDB.driver.call_count == 1

    @pytest.mark.asyncio
    async def test_disconnect_closes_driver(self) -> None:
        with patch(
            "app.integrations.neo4j_client.AsyncGraphDatabase"
        ) as MockGDB:
            mock_driver = _make_mock_driver()
            MockGDB.driver.return_value = mock_driver

            client = Neo4jClient(
                uri="bolt://localhost:7687", user="neo4j", password="test"
            )
            await client.connect()
            await client.disconnect()

            mock_driver.close.assert_called_once()
            assert client._driver is None

    @pytest.mark.asyncio
    async def test_disconnect_when_not_connected(self) -> None:
        client = Neo4jClient(
            uri="bolt://localhost:7687", user="neo4j", password="test"
        )
        await client.disconnect()  # Should not raise


class TestNeo4jClientQuery:
    @pytest.mark.asyncio
    async def test_execute_query_not_connected_raises(self) -> None:
        client = Neo4jClient(
            uri="bolt://localhost:7687", user="neo4j", password="test"
        )
        with pytest.raises(RuntimeError, match="Not connected"):
            await client.execute_query("MATCH (n) RETURN n")

    @pytest.mark.asyncio
    async def test_execute_query(self) -> None:
        with patch(
            "app.integrations.neo4j_client.AsyncGraphDatabase"
        ) as MockGDB:
            mock_driver = _make_mock_driver()
            MockGDB.driver.return_value = mock_driver

            client = Neo4jClient(
                uri="bolt://localhost:7687", user="neo4j", password="test"
            )
            await client.connect()
            results = await client.execute_query(
                "MATCH (n:Person) WHERE n.name = $name RETURN n",
                {"name": "Sarah Chen"},
            )

            session = mock_driver.session.return_value
            session.run.assert_called_once_with(
                "MATCH (n:Person) WHERE n.name = $name RETURN n",
                {"name": "Sarah Chen"},
            )
            assert results == [{"n": {"name": "test"}}]

    @pytest.mark.asyncio
    async def test_execute_write(self) -> None:
        with patch(
            "app.integrations.neo4j_client.AsyncGraphDatabase"
        ) as MockGDB:
            mock_driver = _make_mock_driver()
            MockGDB.driver.return_value = mock_driver

            client = Neo4jClient(
                uri="bolt://localhost:7687", user="neo4j", password="test"
            )
            await client.connect()
            results = await client.execute_write(
                "CREATE (n:Person {name: $name}) RETURN n",
                {"name": "Test Person"},
            )

            assert results == [{"n": {"name": "test"}}]


class TestNeo4jClientMerge:
    @pytest.mark.asyncio
    async def test_merge_event(self) -> None:
        with patch(
            "app.integrations.neo4j_client.AsyncGraphDatabase"
        ) as MockGDB:
            mock_driver = _make_mock_driver()
            MockGDB.driver.return_value = mock_driver

            client = Neo4jClient(
                uri="bolt://localhost:7687", user="neo4j", password="test"
            )
            await client.connect()
            await client.merge_event(
                {"url": "https://lu.ma/ai-dinner", "title": "AI Dinner"}
            )

            session = mock_driver.session.return_value
            call_args = session.run.call_args
            assert "MERGE (e:Event {url: $url})" in call_args[0][0]
            assert call_args[0][1]["url"] == "https://lu.ma/ai-dinner"

    @pytest.mark.asyncio
    async def test_merge_person(self) -> None:
        with patch(
            "app.integrations.neo4j_client.AsyncGraphDatabase"
        ) as MockGDB:
            mock_driver = _make_mock_driver()
            MockGDB.driver.return_value = mock_driver

            client = Neo4jClient(
                uri="bolt://localhost:7687", user="neo4j", password="test"
            )
            await client.connect()
            await client.merge_person(
                {"name": "Sarah Chen", "title": "Partner", "company": "Sequoia"}
            )

            session = mock_driver.session.return_value
            call_args = session.run.call_args
            assert "MERGE (p:Person {name: $name})" in call_args[0][0]
            assert call_args[0][1]["name"] == "Sarah Chen"

    @pytest.mark.asyncio
    async def test_merge_company(self) -> None:
        with patch(
            "app.integrations.neo4j_client.AsyncGraphDatabase"
        ) as MockGDB:
            mock_driver = _make_mock_driver()
            MockGDB.driver.return_value = mock_driver

            client = Neo4jClient(
                uri="bolt://localhost:7687", user="neo4j", password="test"
            )
            await client.connect()
            await client.merge_company({"name": "Sequoia", "industry": "VC"})

            session = mock_driver.session.return_value
            call_args = session.run.call_args
            assert "MERGE (c:Company {name: $name})" in call_args[0][0]

    @pytest.mark.asyncio
    async def test_merge_topic(self) -> None:
        with patch(
            "app.integrations.neo4j_client.AsyncGraphDatabase"
        ) as MockGDB:
            mock_driver = _make_mock_driver()
            MockGDB.driver.return_value = mock_driver

            client = Neo4jClient(
                uri="bolt://localhost:7687", user="neo4j", password="test"
            )
            await client.connect()
            await client.merge_topic({"name": "AI Agents", "category": "tech"})

            session = mock_driver.session.return_value
            call_args = session.run.call_args
            assert "MERGE (t:Topic {name: $name})" in call_args[0][0]


class TestNeo4jClientRelationship:
    @pytest.mark.asyncio
    async def test_create_relationship(self) -> None:
        with patch(
            "app.integrations.neo4j_client.AsyncGraphDatabase"
        ) as MockGDB:
            mock_driver = _make_mock_driver()
            MockGDB.driver.return_value = mock_driver

            client = Neo4jClient(
                uri="bolt://localhost:7687", user="neo4j", password="test"
            )
            await client.connect()
            await client.create_relationship(
                from_label="Person",
                from_key="name",
                from_value="Sarah Chen",
                rel_type="WORKS_AT",
                to_label="Company",
                to_key="name",
                to_value="Sequoia",
                properties={"since": "2020"},
            )

            session = mock_driver.session.return_value
            call_args = session.run.call_args
            cypher = call_args[0][0]
            assert "MATCH (a:Person {name: $from_val})" in cypher
            assert "MATCH (b:Company {name: $to_val})" in cypher
            assert "MERGE (a)-[r:WORKS_AT]->(b)" in cypher
            assert "SET r += $props" in cypher

    @pytest.mark.asyncio
    async def test_create_relationship_no_properties(self) -> None:
        with patch(
            "app.integrations.neo4j_client.AsyncGraphDatabase"
        ) as MockGDB:
            mock_driver = _make_mock_driver()
            MockGDB.driver.return_value = mock_driver

            client = Neo4jClient(
                uri="bolt://localhost:7687", user="neo4j", password="test"
            )
            await client.connect()
            await client.create_relationship(
                from_label="Event",
                from_key="url",
                from_value="https://lu.ma/test",
                rel_type="HAS_SPEAKER",
                to_label="Person",
                to_key="name",
                to_value="Sarah Chen",
            )

            session = mock_driver.session.return_value
            cypher = session.run.call_args[0][0]
            assert "SET r += $props" not in cypher
