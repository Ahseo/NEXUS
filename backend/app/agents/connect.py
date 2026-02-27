from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any

from thefuzz import fuzz

from app.integrations.reka_client import RekaClient
from app.integrations.tavily_client import TavilyClient
from app.integrations.yutori_client import YutoriClient

logger = logging.getLogger(__name__)

# Profile richness weights (sum to 1.0)
RICHNESS_WEIGHTS: dict[str, float] = {
    "current_role": 0.15,
    "company": 0.10,
    "bio": 0.10,
    "linkedin": 0.15,
    "twitter": 0.10,
    "recent_work": 0.15,
    "interests": 0.10,
    "mutual_connections": 0.05,
    "conversation_hooks": 0.10,
}

RICHNESS_THRESHOLD = 0.7
TARGET_MATCH_THRESHOLD = 85  # fuzz.ratio percentage
TARGET_SCORE_BOOST = 30

# Platform-specific scraping strategies
_PLATFORM_STRATEGIES: dict[str, str] = {
    "lu.ma": (
        "Go to the event page. Find the guest list or attendees section. "
        "Extract each attendee's name, title, and company if visible."
    ),
    "eventbrite.com": (
        "Go to the event page. Look for organizer info and any listed speakers "
        "or featured attendees. Extract names, titles, and companies."
    ),
    "meetup.com": (
        "Go to the event page. Find the attendees/RSVP list. "
        "Extract each attendee's name and any profile info shown."
    ),
}


def _detect_platform(url: str) -> str:
    for platform in _PLATFORM_STRATEGIES:
        if platform in url:
            return platform
    return ""


@dataclass
class ConnectAgent:
    _tavily: TavilyClient | None = None
    _yutori: YutoriClient | None = None
    _reka: RekaClient | None = None

    async def scrape_attendees(self, event: dict[str, Any]) -> list[dict[str, Any]]:
        """Use Yutori to scrape attendee list from event page.

        Platform-specific strategies for lu.ma, eventbrite, meetup.
        Returns list of dicts with name, role, company (whatever available).
        If yutori not available, return empty list.
        """
        if self._yutori is None:
            return []

        url = event.get("url", "")
        if not url:
            return []

        platform = _detect_platform(url)
        strategy = _PLATFORM_STRATEGIES.get(
            platform,
            "Go to the event page and extract attendee names, titles, and companies.",
        )

        task = await self._yutori.browsing_create(
            task=strategy,
            start_url=url,
            output_schema={
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "name": {"type": "string"},
                        "role": {"type": "string"},
                        "company": {"type": "string"},
                    },
                },
            },
        )

        if task.result and isinstance(task.result, list):
            return task.result
        if task.result and isinstance(task.result, dict):
            result: list[dict[str, Any]] = task.result.get("attendees", [])
            return result
        return []

    async def deep_research_person(
        self,
        attendee: dict[str, Any],
        user_profile: dict[str, Any],
        max_iterations: int = 3,
    ) -> dict[str, Any]:
        """Iterative enrichment loop:

        1. Calculate current profile richness
        2. If >= RICHNESS_THRESHOLD, return profile
        3. Identify gaps (missing fields)
        4. Build research query targeting gaps
        5. Search with Tavily
        6. Parse results and update profile
        7. Repeat up to max_iterations
        Returns enriched profile dict.
        """
        profile: dict[str, Any] = dict(attendee)

        for iteration in range(1, max_iterations + 1):
            richness = self.calculate_profile_richness(profile)
            if richness >= RICHNESS_THRESHOLD:
                break

            gaps = self.identify_gaps(profile)
            if not gaps:
                break

            query = self.build_research_query(attendee, profile, gaps, iteration)

            if self._tavily is None:
                break

            result = await self._tavily.search(query, max_results=5)
            profile = self._merge_search_results(profile, result.results, gaps)

        profile["richness_score"] = self.calculate_profile_richness(profile)
        return profile

    async def resolve_social_accounts(
        self, profile: dict[str, Any]
    ) -> dict[str, str | None]:
        """Find LinkedIn, Twitter, Instagram, GitHub for a person.

        Strategy 1: Direct Tavily search for "{name} {company} linkedin/twitter/etc"
        Strategy 2: Search for social profiles via known info
        Returns dict with keys: linkedin, twitter, instagram, github (url or None).
        """
        socials: dict[str, str | None] = {
            "linkedin": profile.get("linkedin"),
            "twitter": profile.get("twitter"),
            "instagram": profile.get("instagram"),
            "github": profile.get("github"),
        }

        if self._tavily is None:
            return socials

        name = profile.get("name", "")
        company = profile.get("company", "")

        platform_domains: dict[str, list[str]] = {
            "linkedin": ["linkedin.com"],
            "twitter": ["twitter.com", "x.com"],
            "instagram": ["instagram.com"],
            "github": ["github.com"],
        }

        for platform, domains in platform_domains.items():
            if socials.get(platform):
                continue
            query = f"{name} {company} {platform}".strip()
            result = await self._tavily.search(
                query, include_domains=domains, max_results=3
            )
            for item in result.results:
                url = item.get("url", "")
                if any(d in url for d in domains):
                    socials[platform] = url
                    break

        return socials

    async def cross_verify_profiles_reka(self, url1: str, url2: str) -> bool:
        """Use Reka Vision to compare profile photos from 2 platforms.

        Returns True if likely same person, False otherwise.
        If reka not available, return True (optimistic).
        """
        if self._reka is None:
            return True

        result = await self._reka.compare(
            urls=[url1, url2],
            prompt=(
                "Compare the profile photos in these two pages. "
                "Are they likely the same person? Answer YES or NO."
            ),
        )
        analysis_lower = result.analysis.lower()
        return "no" not in analysis_lower

    def calculate_profile_richness(self, profile: dict[str, Any]) -> float:
        """Weighted completeness score 0-1.0.

        Uses RICHNESS_WEIGHTS dict. A field is "present" if it's a non-empty string
        or non-empty list.
        """
        score = 0.0
        for field_name, weight in RICHNESS_WEIGHTS.items():
            value = profile.get(field_name)
            if isinstance(value, str) and value.strip():
                score += weight
            elif isinstance(value, list) and len(value) > 0:
                score += weight
        return round(score, 4)

    def identify_gaps(self, profile: dict[str, Any]) -> list[str]:
        """Return list of missing/empty field names from RICHNESS_WEIGHTS keys."""
        gaps: list[str] = []
        for field_name in RICHNESS_WEIGHTS:
            value = profile.get(field_name)
            if isinstance(value, str) and value.strip():
                continue
            if isinstance(value, list) and len(value) > 0:
                continue
            gaps.append(field_name)
        return gaps

    def build_research_query(
        self,
        attendee: dict[str, Any],
        profile: dict[str, Any],
        gaps: list[str],
        iteration: int,
    ) -> str:
        """Build progressive search query:

        iteration 1: broad "{name} {company}"
        iteration 2: fill gaps "{name} {company} {gap_fields}"
        iteration 3: niche sources "{name} linkedin OR twitter OR github"
        """
        name = attendee.get("name", "")
        company = profile.get("company", "") or attendee.get("company", "")

        if iteration == 1:
            return f"{name} {company}".strip()

        if iteration == 2:
            gap_terms = " ".join(gaps[:3])
            return f"{name} {company} {gap_terms}".strip()

        # iteration >= 3: niche sources
        return f"{name} linkedin OR twitter OR github"

    def check_target_matches(
        self,
        attendees: list[dict[str, Any]],
        event: dict[str, Any],
        user_profile: dict[str, Any],
    ) -> list[dict[str, Any]]:
        """Check if any attendees match target people (fuzz.ratio > 85).

        Returns list of matches with target_person info and matched_attendee.
        Boost event relevance_score by 30 (cap at 100).
        """
        targets: list[dict[str, Any]] = user_profile.get("target_people", [])
        if not targets:
            return []

        matches: list[dict[str, Any]] = []
        for attendee in attendees:
            attendee_name = attendee.get("name", "")
            if not attendee_name:
                continue
            for target in targets:
                target_name = target.get("name", "")
                if not target_name:
                    continue
                ratio = fuzz.ratio(attendee_name.lower(), target_name.lower())
                if ratio >= TARGET_MATCH_THRESHOLD:
                    current_score = event.get("relevance_score", 0)
                    event["relevance_score"] = min(
                        current_score + TARGET_SCORE_BOOST, 100
                    )
                    matches.append(
                        {
                            "target_person": target,
                            "matched_attendee": attendee,
                            "match_score": ratio,
                        }
                    )
        return matches

    async def find_best_connections(
        self,
        attendees: list[dict[str, Any]],
        user_profile: dict[str, Any],
    ) -> list[dict[str, Any]]:
        """Score and rank attendees by connection value.

        Consider: role match, company match, mutual interests, profile richness.
        Return sorted list (best first).
        """
        target_roles = [r.lower() for r in user_profile.get("target_roles", [])]
        target_companies = [c.lower() for c in user_profile.get("target_companies", [])]
        user_interests = [i.lower() for i in user_profile.get("interests", [])]

        scored: list[dict[str, Any]] = []
        for attendee in attendees:
            score = 0.0

            # Role match (0-30)
            role = (attendee.get("role") or attendee.get("current_role") or "").lower()
            for target_role in target_roles:
                if fuzz.partial_ratio(target_role, role) > 70:
                    score += 30
                    break

            # Company match (0-25)
            company = (attendee.get("company") or "").lower()
            for target_company in target_companies:
                if fuzz.partial_ratio(target_company, company) > 70:
                    score += 25
                    break

            # Mutual interests (0-25)
            person_interests = [
                i.lower() for i in attendee.get("interests", [])
            ]
            if person_interests and user_interests:
                overlap = sum(
                    1
                    for pi in person_interests
                    if any(fuzz.partial_ratio(pi, ui) > 70 for ui in user_interests)
                )
                score += min(overlap * 5, 25)

            # Profile richness (0-20)
            richness = attendee.get(
                "richness_score", self.calculate_profile_richness(attendee)
            )
            score += richness * 20

            attendee_with_score = dict(attendee)
            attendee_with_score["connection_score"] = round(score, 2)
            scored.append(attendee_with_score)

        scored.sort(key=lambda x: x["connection_score"], reverse=True)
        return scored

    def _merge_search_results(
        self,
        profile: dict[str, Any],
        results: list[dict[str, Any]],
        gaps: list[str],
    ) -> dict[str, Any]:
        """Parse search results and fill in gaps."""
        for result in results:
            content = result.get("content", "") or ""
            url = result.get("url", "") or ""
            content_lower = content.lower()

            if "current_role" in gaps and not profile.get("current_role"):
                title = result.get("title", "")
                if title:
                    profile["current_role"] = title
                    if "current_role" in gaps:
                        gaps.remove("current_role")

            if "linkedin" in gaps and "linkedin.com" in url:
                profile["linkedin"] = url
                if "linkedin" in gaps:
                    gaps.remove("linkedin")

            if "twitter" in gaps and ("twitter.com" in url or "x.com" in url):
                profile["twitter"] = url
                if "twitter" in gaps:
                    gaps.remove("twitter")

            if "bio" in gaps and len(content) > 50:
                profile["bio"] = content[:500]
                if "bio" in gaps:
                    gaps.remove("bio")

            if "recent_work" in gaps and any(
                kw in content_lower for kw in ["published", "wrote", "built", "launched"]
            ):
                profile["recent_work"] = content[:500]
                if "recent_work" in gaps:
                    gaps.remove("recent_work")

            if "company" in gaps and not profile.get("company"):
                # Try to extract company from content
                for keyword in ["at ", "@ ", "founder of ", "ceo of "]:
                    if keyword in content_lower:
                        idx = content_lower.index(keyword) + len(keyword)
                        company_text = content[idx : idx + 50].split(",")[0].split(".")[0].strip()
                        if company_text:
                            profile["company"] = company_text
                            if "company" in gaps:
                                gaps.remove("company")
                            break

        return profile
