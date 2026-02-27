from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from neo4j import AsyncDriver, AsyncGraphDatabase


@dataclass
class Neo4jClient:
    uri: str
    user: str
    password: str
    _driver: AsyncDriver | None = field(init=False, default=None, repr=False)

    async def connect(self) -> None:
        if self._driver is not None:
            return
        self._driver = AsyncGraphDatabase.driver(
            self.uri, auth=(self.user, self.password)
        )

    async def disconnect(self) -> None:
        if self._driver is not None:
            await self._driver.close()
            self._driver = None

    def _ensure_connected(self) -> AsyncDriver:
        if self._driver is None:
            raise RuntimeError("Not connected. Call connect() first.")
        return self._driver

    # -- Generic query helpers -------------------------------------------------

    async def execute_query(
        self, cypher: str, parameters: dict[str, Any] | None = None
    ) -> list[dict[str, Any]]:
        driver = self._ensure_connected()
        async with driver.session() as session:
            result = await session.run(cypher, parameters or {})  # type: ignore[arg-type]
            records = await result.data()
            return records

    async def execute_write(
        self, cypher: str, parameters: dict[str, Any] | None = None
    ) -> list[dict[str, Any]]:
        driver = self._ensure_connected()
        async with driver.session() as session:
            result = await session.run(cypher, parameters or {})  # type: ignore[arg-type]
            records = await result.data()
            await result.consume()
            return records

    # -- Domain-specific merge helpers -----------------------------------------

    async def merge_event(self, data: dict[str, Any]) -> list[dict[str, Any]]:
        cypher = (
            "MERGE (e:Event {url: $url}) "
            "SET e += $props "
            "RETURN e"
        )
        return await self.execute_write(
            cypher, {"url": data["url"], "props": data}
        )

    async def merge_person(self, data: dict[str, Any]) -> list[dict[str, Any]]:
        cypher = (
            "MERGE (p:Person {name: $name}) "
            "SET p += $props "
            "RETURN p"
        )
        return await self.execute_write(
            cypher, {"name": data["name"], "props": data}
        )

    async def merge_company(self, data: dict[str, Any]) -> list[dict[str, Any]]:
        cypher = (
            "MERGE (c:Company {name: $name}) "
            "SET c += $props "
            "RETURN c"
        )
        return await self.execute_write(
            cypher, {"name": data["name"], "props": data}
        )

    async def merge_topic(self, data: dict[str, Any]) -> list[dict[str, Any]]:
        cypher = (
            "MERGE (t:Topic {name: $name}) "
            "SET t += $props "
            "RETURN t"
        )
        return await self.execute_write(
            cypher, {"name": data["name"], "props": data}
        )

    async def create_relationship(
        self,
        from_label: str,
        from_key: str,
        from_value: str,
        rel_type: str,
        to_label: str,
        to_key: str,
        to_value: str,
        properties: dict[str, Any] | None = None,
    ) -> list[dict[str, Any]]:
        props_clause = " SET r += $props" if properties else ""
        cypher = (
            f"MATCH (a:{from_label} {{{from_key}: $from_val}}) "
            f"MATCH (b:{to_label} {{{to_key}: $to_val}}) "
            f"MERGE (a)-[r:{rel_type}]->(b)"
            f"{props_clause} "
            "RETURN type(r) as rel_type"
        )
        params: dict[str, Any] = {"from_val": from_value, "to_val": to_value}
        if properties:
            params["props"] = properties
        return await self.execute_write(cypher, params)
