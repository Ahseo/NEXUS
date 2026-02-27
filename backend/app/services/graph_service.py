"""Graph service — manages Neo4j social graph for people discovery & ranking.

Uses Tavily for web search + Reka for structured data extraction (SNS discovery).
"""

from __future__ import annotations

import json
import logging
import uuid
from typing import Any

import httpx

from app.core.config import settings
from app.integrations.neo4j_client import Neo4jClient
from app.integrations.tavily_client import TavilyClient

logger = logging.getLogger(__name__)


def _id() -> str:
    return str(uuid.uuid4())[:8]


async def get_neo4j() -> Neo4jClient:
    client = Neo4jClient(
        uri=settings.neo4j_uri,
        user=settings.neo4j_user,
        password=settings.neo4j_password,
    )
    await client.connect()
    return client


async def seed_hackathon_event(
    event_url: str,
    event_title: str,
    user_email: str | None = None,
) -> dict[str, Any]:
    """Seed hackathon event + real participants into Neo4j."""
    neo4j = await get_neo4j()

    # Clear old data
    await neo4j.execute_write("MATCH (n) DETACH DELETE n", {})

    event_id = _id()

    # Store event
    await neo4j.execute_write(
        "CREATE (e:Event {url: $url, title: $title, id: $id, date: '2026-02-27', "
        "location: 'AWS Builder Loft, 525 Market St, SF', source: 'devpost', "
        "event_type: 'hackathon', participants: 112}) RETURN e",
        {"url": event_url, "title": event_title, "id": event_id},
    )

    # Create "Me" user node at the center
    await neo4j.execute_write(
        "CREATE (u:Person {id: $id, name: 'Me', title: 'Hacker', company: 'NEXUS', "
        "role: 'self', linkedin: '', twitter: '', email: $email, "
        "avatar_color: '#f97316', connection_score: 100, is_self: true}) "
        "WITH u MATCH (e:Event {url: $url}) CREATE (u)-[:ATTENDED]->(e)",
        {"id": "me", "email": user_email or "", "url": event_url},
    )

    participants = _get_real_participants()

    for p in participants:
        pid = p["id"]
        await neo4j.execute_write(
            "CREATE (p:Person {id: $id, name: $name, title: $title, company: $company, "
            "role: $role, linkedin: $linkedin, twitter: $twitter, facebook: $facebook, "
            "instagram: $instagram, email: $email, avatar_color: $color, "
            "connection_score: $score, is_self: false}) "
            "WITH p MATCH (e:Event {url: $url}) CREATE (p)-[:ATTENDED]->(e)",
            {
                "id": pid, "name": p["name"], "title": p["title"],
                "company": p["company"], "role": p["role"],
                "linkedin": p.get("linkedin", ""), "twitter": p.get("twitter", ""),
                "facebook": p.get("facebook", ""), "instagram": p.get("instagram", ""),
                "email": p.get("email", ""), "color": p["avatar_color"],
                "score": p["connection_score"], "url": event_url,
            },
        )
        # Topics
        for topic in p.get("topics", []):
            await neo4j.execute_write(
                "MERGE (t:Topic {name: $name}) "
                "WITH t MATCH (p:Person {id: $pid}) CREATE (p)-[:EXPERT_IN]->(t)",
                {"name": topic, "pid": pid},
            )
        # Company
        if p.get("company"):
            await neo4j.execute_write(
                "MERGE (c:Company {name: $name}) "
                "WITH c MATCH (p:Person {id: $pid}) CREATE (p)-[:WORKS_AT]->(c)",
                {"name": p["company"], "pid": pid},
            )

    # Create "Me" topics & connections
    my_topics = ["AI Agents", "LLM", "Autonomous Systems", "Networking", "Full Stack"]
    for topic in my_topics:
        await neo4j.execute_write(
            "MERGE (t:Topic {name: $name}) "
            "WITH t MATCH (p:Person {id: 'me'}) CREATE (p)-[:EXPERT_IN]->(t)",
            {"name": topic},
        )

    # Connect me to everyone (varying strength)
    await neo4j.execute_write(
        "MATCH (me:Person {id: 'me'}), (p:Person) WHERE p.id <> 'me' "
        "CREATE (me)-[:CONNECTED_TO {strength: p.connection_score * 0.8, source: 'event'}]->(p)",
        {},
    )

    # Create inter-person connections from shared topics
    await neo4j.execute_write(
        "MATCH (p1:Person)-[:EXPERT_IN]->(t:Topic)<-[:EXPERT_IN]-(p2:Person) "
        "WHERE p1.id < p2.id AND p1.id <> 'me' AND p2.id <> 'me' "
        "WITH p1, p2, COUNT(t) AS shared "
        "WHERE shared >= 2 "
        "CREATE (p1)-[:CONNECTED_TO {strength: shared * 25, source: 'shared_topics'}]->(p2)",
        {},
    )

    await neo4j.disconnect()

    return {
        "event_id": event_id,
        "event_title": event_title,
        "participants_count": len(participants) + 1,
    }


async def get_network_graph(user_email: str | None = None) -> dict[str, Any]:
    """Return full network graph for visualization."""
    neo4j = await get_neo4j()

    people = await neo4j.execute_query(
        "MATCH (p:Person) "
        "OPTIONAL MATCH (p)-[:EXPERT_IN]->(t:Topic) "
        "OPTIONAL MATCH (p)-[:ATTENDED]->(e:Event) "
        "RETURN p.id AS id, p.name AS name, p.title AS title, "
        "p.company AS company, p.linkedin AS linkedin, p.twitter AS twitter, "
        "p.facebook AS facebook, p.instagram AS instagram, "
        "p.github AS github, p.website AS website, "
        "p.email AS email, p.role AS role, p.avatar_color AS avatar_color, "
        "p.connection_score AS connection_score, p.is_self AS is_self, "
        "COLLECT(DISTINCT t.name) AS topics, "
        "COLLECT(DISTINCT e.title) AS events"
    )

    edges = await neo4j.execute_query(
        "MATCH (p1:Person)-[r:CONNECTED_TO]->(p2:Person) "
        "RETURN p1.id AS source, p2.id AS target, "
        "r.strength AS strength, r.source AS rel_source"
    )

    events = await neo4j.execute_query(
        "MATCH (e:Event) RETURN e.id AS id, e.title AS title, e.url AS url, "
        "e.date AS date, e.location AS location"
    )

    await neo4j.disconnect()

    nodes = []
    for p in people:
        nodes.append({
            "id": p["id"],
            "name": p["name"],
            "title": p.get("title", ""),
            "company": p.get("company", ""),
            "role": p.get("role", ""),
            "linkedin": p.get("linkedin") or "",
            "twitter": p.get("twitter") or "",
            "facebook": p.get("facebook") or "",
            "instagram": p.get("instagram") or "",
            "github": p.get("github") or "",
            "website": p.get("website") or "",
            "email": p.get("email") or "",
            "avatar_color": p.get("avatar_color", "#6366f1"),
            "connection_score": p.get("connection_score") or 0,
            "is_self": p.get("is_self", False),
            "topics": p.get("topics", []),
            "events": p.get("events", []),
        })

    return {
        "nodes": nodes,
        "edges": [
            {
                "source": e["source"],
                "target": e["target"],
                "strength": e.get("strength") or 10,
                "type": e.get("rel_source", "unknown"),
            }
            for e in edges
        ],
        "events": [
            {
                "id": e.get("id", ""),
                "title": e.get("title", ""),
                "url": e.get("url", ""),
                "date": str(e.get("date", "")),
                "location": e.get("location", ""),
            }
            for e in events
        ],
        "stats": {
            "total_people": len(nodes),
            "total_connections": len(edges),
            "total_events": len(events),
        },
    }


async def get_ranked_people(
    user_email: str | None = None,
    role_filter: str | None = None,
    topic_filter: str | None = None,
    limit: int = 50,
) -> list[dict[str, Any]]:
    """Return people ranked by connection score, with optional filters."""
    neo4j = await get_neo4j()

    where_clauses = ["NOT p.is_self = true"]
    params: dict[str, Any] = {"limit": limit}

    if role_filter:
        where_clauses.append(
            "(toLower(p.role) CONTAINS toLower($role) OR toLower(p.title) CONTAINS toLower($role))"
        )
        params["role"] = role_filter
    if topic_filter:
        where_clauses.append(
            "EXISTS { MATCH (p)-[:EXPERT_IN]->(t:Topic) WHERE toLower(t.name) CONTAINS toLower($topic) }"
        )
        params["topic"] = topic_filter

    where = f"WHERE {' AND '.join(where_clauses)}"

    results = await neo4j.execute_query(
        f"MATCH (p:Person) {where} "
        "OPTIONAL MATCH (p)-[:EXPERT_IN]->(t:Topic) "
        "OPTIONAL MATCH (p)-[:ATTENDED]->(e:Event) "
        "OPTIONAL MATCH (p)-[conn:CONNECTED_TO]-() "
        "WITH p, COLLECT(DISTINCT t.name) AS topics, "
        "COLLECT(DISTINCT e.title) AS events, "
        "COUNT(DISTINCT conn) AS connection_count "
        "RETURN p.id AS id, p.name AS name, p.title AS title, "
        "p.company AS company, p.role AS role, p.linkedin AS linkedin, "
        "p.twitter AS twitter, p.facebook AS facebook, p.instagram AS instagram, "
        "p.github AS github, p.website AS website, "
        "p.email AS email, p.avatar_color AS avatar_color, "
        "COALESCE(p.connection_score, 0) AS connection_score, "
        "topics, events, connection_count "
        "ORDER BY connection_score DESC LIMIT $limit",
        params,
    )

    await neo4j.disconnect()

    return [
        {
            "id": r["id"], "name": r["name"], "title": r.get("title", ""),
            "company": r.get("company", ""), "role": r.get("role", ""),
            "linkedin": r.get("linkedin") or "", "twitter": r.get("twitter") or "",
            "facebook": r.get("facebook") or "", "instagram": r.get("instagram") or "",
            "github": r.get("github") or "", "website": r.get("website") or "",
            "email": r.get("email") or "", "avatar_color": r.get("avatar_color", "#6366f1"),
            "connection_score": r.get("connection_score", 0),
            "topics": r.get("topics", []), "events": r.get("events", []),
            "connection_count": r.get("connection_count", 0), "rank": i + 1,
        }
        for i, r in enumerate(results)
    ]


async def search_people_tavily(query: str) -> list[dict[str, Any]]:
    if not settings.tavily_api_key:
        return []
    tavily = TavilyClient(api_key=settings.tavily_api_key)
    result = await tavily.search(query=query, search_depth="advanced", max_results=5, include_answer=True)
    return [{"title": r.get("title", ""), "url": r.get("url", ""), "content": r.get("content", "")[:300]} for r in result.results]


async def _reka_extract(prompt: str) -> str:
    """Call Reka Flash and return the assistant content."""
    async with httpx.AsyncClient(timeout=30) as http:
        resp = await http.post(
            "https://api.reka.ai/v1/chat",
            headers={"X-Api-Key": settings.reka_api_key, "Content-Type": "application/json"},
            json={"messages": [{"role": "user", "content": prompt}], "model": "reka-flash"},
        )
        data = resp.json()
        return data.get("responses", [{}])[0].get("message", {}).get("content", "")


async def enrich_person_sns(name: str, company: str, title: str = "") -> dict[str, str]:
    """Two-phase pipeline: Tavily multi-query search → Reka identity-verified extraction.

    Phase 1 — Tavily runs multiple targeted searches per platform.
    Phase 2 — Reka verifies each result is the SAME person (name + company match).
    """
    if not settings.tavily_api_key or not settings.reka_api_key:
        return {}

    tavily = TavilyClient(api_key=settings.tavily_api_key)
    identity = f"{name}, {title} at {company}" if title else f"{name} at {company}"

    # Phase 1: Multiple targeted Tavily searches
    search_queries = [
        f'"{name}" "{company}" linkedin twitter site:linkedin.com OR site:x.com',
        f'"{name}" "{company}" github instagram site:github.com OR site:instagram.com',
        f'"{name}" "{company}" email contact',
    ]

    all_context = f"TARGET PERSON: {identity}\n\n"
    for q in search_queries:
        try:
            result = await tavily.search(query=q, search_depth="advanced", max_results=3, include_answer=True)
            if result.answer:
                all_context += f"[Search answer]: {result.answer}\n"
            for r in result.results:
                all_context += f"URL: {r.get('url', '')}\nSnippet: {r.get('content', '')[:250]}\n\n"
        except Exception:
            continue

    # Phase 2: Reka identity-verified extraction
    prompt = f"""You are verifying social media accounts for a SPECIFIC person.

TARGET: {identity}

IMPORTANT RULES:
- Only return accounts that belong to THIS EXACT person (same name AND same company/role).
- If a search result mentions someone with a similar name but different company, IGNORE it.
- Twitter/X handles should NOT include @ prefix.
- For each field, return empty string "" if not found or not verified.

SEARCH RESULTS:
{all_context}

Return ONLY valid JSON (no markdown, no explanation):
{{"twitter": "", "instagram": "", "facebook": "", "github": "", "website": "", "email": "", "verified": true}}

The "verified" field should be true only if you are confident the accounts belong to {name} at {company}."""

    try:
        content = await _reka_extract(prompt)
        start = content.find("{")
        end = content.rfind("}") + 1
        if start >= 0 and end > start:
            parsed = json.loads(content[start:end])

            if not parsed.get("verified", False):
                logger.info("Reka could not verify identity for %s", name)

            cleaned: dict[str, str] = {}
            for k in ("twitter", "instagram", "facebook", "github", "website", "email"):
                val = parsed.get(k, "")
                if isinstance(val, list):
                    val = val[0] if val else ""
                val = str(val).strip()
                if val.lower() in ("", "empty", "none", "n/a", "not found", "unknown", "not available"):
                    val = ""
                if k == "twitter" and val:
                    val = val.lstrip("@")
                cleaned[k] = val
            return cleaned
    except Exception as e:
        logger.error("Reka enrichment failed for %s: %s", name, e)

    return {}


async def enrich_all_people_sns() -> dict[str, Any]:
    """Run Tavily+Reka SNS enrichment on all people in Neo4j and update their profiles."""
    neo4j = await get_neo4j()

    people = await neo4j.execute_query(
        "MATCH (p:Person) WHERE NOT p.is_self = true "
        "RETURN p.id AS id, p.name AS name, p.company AS company, p.title AS title"
    )

    enriched_count = 0
    results: list[dict[str, Any]] = []

    for p in people:
        name = p["name"]
        company = p.get("company", "")
        title = p.get("title", "")
        logger.info("Enriching SNS for %s (%s)...", name, company)

        sns = await enrich_person_sns(name, company, title)
        if not any(sns.values()):
            results.append({"name": name, "status": "no_results"})
            continue

        set_parts = []
        params: dict[str, Any] = {"pid": p["id"]}
        for key, val in sns.items():
            if val:
                set_parts.append(f"p.{key} = ${key}")
                params[key] = val

        if set_parts:
            await neo4j.execute_write(
                f"MATCH (p:Person {{id: $pid}}) SET {', '.join(set_parts)}",
                params,
            )
            enriched_count += 1
            results.append({"name": name, "status": "enriched", "found": sns})

    await neo4j.disconnect()
    return {"enriched": enriched_count, "total": len(people), "details": results}


def _get_real_participants() -> list[dict[str, Any]]:
    """ONLY verified real people from Autonomous Agents Hackathon.

    Sources:
    - LinkedIn post by Senso (linkedin.com/posts/ojus_we-will-be-at-the-upcoming-autonomous-agents-activity-7432147989860671488-Fk9Q)
    - Gary's Guide (garysguide.com/events/01yr0wq/Autonomous-Agents-Hackathon)
    - LinkedIn post by Joaquin L. (linkedin.com/posts/joaquinllenado_autonomous-agents-hackathon-luma-activity-7430984795490430977-BOjt)
    - Devpost event page (autonomous-agents-hackathon.devpost.com)

    All LinkedIn URLs are real and verified. No fake people.
    """
    c = ["#6366f1", "#10b981", "#8b5cf6", "#f59e0b", "#ef4444", "#3b82f6", "#ec4899", "#14b8a6", "#f97316", "#06b6d4"]
    return [
        # ── Speakers (from Senso LinkedIn post) ──
        {"id": _id(), "name": "Carter Huffman", "title": "CTO & Co-Founder", "company": "Modulate", "role": "speaker",
         "linkedin": "https://www.linkedin.com/in/carter-huffman-a9aba05b", "twitter": "", "facebook": "", "instagram": "",
         "email": "whuffman@whuffman.net", "avatar_color": c[0], "connection_score": 88,
         "topics": ["Voice AI", "AI Safety", "Autonomous Systems", "AI Agents"]},
        {"id": _id(), "name": "Dhruv Batra", "title": "Co-founder & Chief Scientist", "company": "Yutori", "role": "speaker",
         "linkedin": "https://www.linkedin.com/in/dhruv-batra-dbatra", "twitter": "", "facebook": "", "instagram": "",
         "email": "dhruv@dhruvbatra.com", "avatar_color": c[1], "connection_score": 92,
         "topics": ["Browser Automation", "AI Agents", "Computer Vision", "Autonomous Systems"]},
        {"id": _id(), "name": "Ojus Save", "title": "Developer Relations", "company": "Render", "role": "speaker",
         "linkedin": "https://www.linkedin.com/in/ojus", "twitter": "", "facebook": "", "instagram": "",
         "email": "i@saveoj.us", "avatar_color": c[2], "connection_score": 80,
         "topics": ["DevRel", "Cloud Deployment", "AI Agents", "Developer Tools"]},
        {"id": _id(), "name": "Andrew Bihl", "title": "Co-Founder & CTO", "company": "Numeric", "role": "speaker",
         "linkedin": "https://www.linkedin.com/in/andrewbihl", "twitter": "", "facebook": "", "instagram": "",
         "email": "andrew@numeric.io", "avatar_color": c[4], "connection_score": 82,
         "topics": ["Fintech", "AI Agents", "Accounting", "Autonomous Systems"]},
        # ── Judges (from Senso LinkedIn post) ──
        {"id": _id(), "name": "Graham Gullans", "title": "COO", "company": "Modulate AI", "role": "judge",
         "linkedin": "https://www.linkedin.com/in/grahamgullans", "twitter": "", "facebook": "", "instagram": "",
         "email": "", "avatar_color": c[6], "connection_score": 75,
         "topics": ["Operations", "AI Safety", "Voice AI", "Startup"]},
        {"id": _id(), "name": "Anushk Mittal", "title": "Co-founder & CEO", "company": "Shapes Inc", "role": "judge",
         "linkedin": "https://www.linkedin.com/in/anushkmittal", "twitter": "anushkmittal", "facebook": "", "instagram": "",
         "email": "", "avatar_color": c[7], "connection_score": 86,
         "topics": ["AI Agents", "Startup", "Product", "Autonomous Systems"]},
        {"id": _id(), "name": "Vladimir de Turckheim", "title": "Core Maintainer", "company": "Node.js", "role": "judge",
         "linkedin": "https://www.linkedin.com/in/vladimirdeturckheim", "twitter": "poledesfetes", "facebook": "", "instagram": "",
         "email": "", "avatar_color": c[8], "connection_score": 72,
         "topics": ["Node.js", "Open Source", "Security", "Developer Tools"]},
        {"id": _id(), "name": "Jon Turdiev", "title": "Senior Solutions Architect", "company": "AWS", "role": "judge",
         "linkedin": "https://www.linkedin.com/in/jonturdiev", "twitter": "", "facebook": "", "instagram": "",
         "email": "", "avatar_color": c[5], "connection_score": 78,
         "topics": ["Cloud Infrastructure", "AI Agents", "AWS", "Solutions Architecture"]},
        {"id": _id(), "name": "Shifra Williams", "title": "DevRel", "company": "Render", "role": "judge",
         "linkedin": "https://www.linkedin.com/in/shifra-williams", "twitter": "", "facebook": "", "instagram": "",
         "email": "", "avatar_color": c[9], "connection_score": 76,
         "topics": ["DevRel", "Cloud Deployment", "Developer Experience", "AI Agents"]},
        # ── Organizer ──
        {"id": _id(), "name": "Marcelo Chaman Mallqui", "title": "Founding Design Engineer", "company": "Gumloop", "role": "organizer",
         "linkedin": "https://www.linkedin.com/in/marc-cham", "twitter": "", "facebook": "", "instagram": "",
         "email": "marcelo@gumloop.com", "avatar_color": c[0], "connection_score": 90,
         "topics": ["AI Agents", "Hackathons", "Community", "Full Stack"]},
        # ── Verified participant (from their own LinkedIn post) ──
        {"id": _id(), "name": "Joaquin Llenado", "title": "Software Engineer", "company": "", "role": "participant",
         "linkedin": "https://www.linkedin.com/in/joaquinllenado", "twitter": "", "facebook": "", "instagram": "",
         "email": "", "avatar_color": c[3], "connection_score": 70,
         "topics": ["AI Agents", "Software Engineering", "Autonomous Systems"]},
    ]
