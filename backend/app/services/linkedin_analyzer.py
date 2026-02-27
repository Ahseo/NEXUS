"""Analyze LinkedIn profiles using REKA API to extract preferences and interests."""

from __future__ import annotations

import logging
from typing import Any

import httpx

from app.core.config import settings

logger = logging.getLogger(__name__)

REKA_API_URL = "https://api.reka.ai/v1/chat"


async def analyze_linkedin_profile(
    name: str,
    linkedin_url: str,
    notes: str = "",
) -> dict[str, Any]:
    """Use REKA API to analyze a person based on their LinkedIn URL and any notes.

    Returns a profile dict with: name, linkedin_url, preferences, interests,
    topics, suggested_message, connection_score.
    """
    if not settings.reka_api_key:
        logger.warning("REKA_API_KEY not set, returning basic profile")
        return _basic_profile(name, linkedin_url, notes)

    prompt = (
        f"Analyze this person for networking purposes.\n"
        f"Name: {name}\n"
        f"LinkedIn: {linkedin_url}\n"
        f"Notes from meeting them: {notes}\n\n"
        f"Based on the LinkedIn URL and context, infer:\n"
        f"1. Their likely professional interests (list of 3-5 topics)\n"
        f"2. Their likely industry/domain\n"
        f"3. Suggested conversation topics to build rapport\n"
        f"4. A short networking follow-up message (casual, under 50 words)\n\n"
        f"Return as JSON with keys: interests, industry, conversation_topics, "
        f"suggested_message, connection_score (1-100 based on networking potential)"
    )

    try:
        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.post(
                REKA_API_URL,
                headers={
                    "X-Api-Key": settings.reka_api_key,
                    "Content-Type": "application/json",
                },
                json={
                    "model": "reka-flash",
                    "messages": [{"role": "user", "content": prompt}],
                },
            )
            resp.raise_for_status()
            data = resp.json()

            content = data.get("responses", [{}])[0].get("message", {}).get("content", "")

            # Try to parse JSON from response
            import json
            try:
                # Find JSON block in response
                start = content.find("{")
                end = content.rfind("}") + 1
                if start >= 0 and end > start:
                    parsed = json.loads(content[start:end])
                    return {
                        "name": name,
                        "linkedin_url": linkedin_url,
                        "notes": notes,
                        "interests": parsed.get("interests", []),
                        "industry": parsed.get("industry", ""),
                        "conversation_topics": parsed.get("conversation_topics", []),
                        "suggested_message": parsed.get("suggested_message", ""),
                        "connection_score": parsed.get("connection_score", 50),
                    }
            except (json.JSONDecodeError, KeyError):
                pass

            # Fallback: return raw analysis
            return {
                "name": name,
                "linkedin_url": linkedin_url,
                "notes": notes,
                "interests": [],
                "industry": "",
                "conversation_topics": [],
                "suggested_message": "",
                "connection_score": 50,
                "raw_analysis": content,
            }

    except Exception as e:
        logger.error(f"REKA API error: {e}")
        return _basic_profile(name, linkedin_url, notes)


def _basic_profile(name: str, linkedin_url: str, notes: str) -> dict[str, Any]:
    """Fallback profile when REKA API is unavailable."""
    return {
        "name": name,
        "linkedin_url": linkedin_url,
        "notes": notes,
        "interests": [],
        "industry": "",
        "conversation_topics": [],
        "suggested_message": f"Hey {name.split()[0] if name else 'there'}! Great connecting at the event. Would love to stay in touch!",
        "connection_score": 50,
    }
