"""Seed Neo4j with schema constraints and indexes."""

import asyncio
import os
from pathlib import Path

from neo4j import AsyncGraphDatabase


async def seed_schema() -> None:
    uri = os.getenv("NEO4J_URI", "")
    user = os.getenv("NEO4J_USER", "neo4j")
    password = os.getenv("NEO4J_PASSWORD", "")

    if not uri:
        print("NEO4J_URI not set, skipping schema seed")
        return

    schema_path = Path(__file__).parent.parent / "backend" / "app" / "db" / "neo4j_schema.cypher"
    schema_text = schema_path.read_text()

    statements = [
        line.strip()
        for line in schema_text.split(";")
        if line.strip() and not line.strip().startswith("//")
    ]

    driver = AsyncGraphDatabase.driver(uri, auth=(user, password))
    async with driver:
        async with driver.session() as session:
            for stmt in statements:
                try:
                    await session.run(stmt)
                    print(f"  OK: {stmt[:60]}...")
                except Exception as e:
                    print(f"  SKIP: {stmt[:60]}... ({e})")

    print(f"\nSeeded {len(statements)} schema statements")


if __name__ == "__main__":
    asyncio.run(seed_schema())
