"""Seed demo data for NEXUS presentation.

Creates realistic events, people, messages, and a user profile
for a 3-minute live demo.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

DEMO_PROFILE = {
    "id": "demo-user",
    "name": "John Park",
    "email": "john@buildai.com",
    "role": "Founder & CEO",
    "company": "BuildAI",
    "product_description": "AI-powered CRM for SMBs",
    "linkedin": "linkedin.com/in/johnpark",
    "twitter": "x.com/johnpark",
    "networking_goals": ["find investors", "hire engineers", "find design partners"],
    "target_roles": ["VC Partner", "Senior Engineer", "CTO"],
    "target_companies": ["Sequoia", "a16z", "Google", "OpenAI"],
    "target_industries": ["AI/ML", "SaaS", "Developer Tools"],
    "target_people": [
        {"id": "tp-1", "name": "Sam Altman", "company": "OpenAI", "reason": "Discuss AI agent ecosystem", "priority": "high", "status": "searching"},
        {"id": "tp-2", "name": "Sarah Chen", "company": "Sequoia", "reason": "Series A fundraising", "priority": "high", "status": "found_event"},
    ],
    "interests": ["AI agents", "developer tools", "fundraising", "product-led growth"],
    "preferred_event_types": ["dinner", "meetup", "demo_day"],
    "max_events_per_week": 4,
    "max_event_spend": 50,
    "preferred_days": ["tuesday", "thursday"],
    "preferred_times": ["evening"],
    "message_tone": "casual",
    "auto_apply_threshold": 80,
    "suggest_threshold": 50,
    "auto_schedule_threshold": 85,
}

DEMO_EVENTS = [
    {
        "id": "evt-1",
        "title": "AI Founders Dinner — SF",
        "url": "https://lu.ma/ai-dinner-sf",
        "source": "luma",
        "event_type": "dinner",
        "date": "2026-02-28T19:00:00",
        "location": "The Battery, SF",
        "description": "Intimate gathering of 30 founders and investors. Speakers: Sarah Chen (Sequoia), James Liu (a16z).",
        "speakers": [{"name": "Sarah Chen", "role": "VC Partner", "company": "Sequoia"}, {"name": "James Liu", "role": "Partner", "company": "a16z"}],
        "topics": ["AI agents", "fundraising"],
        "relevance_score": 95,
        "status": "applied",
        "capacity": 30,
    },
    {
        "id": "evt-2",
        "title": "SF Developer Tools Meetup",
        "url": "https://lu.ma/sf-devtools",
        "source": "luma",
        "event_type": "meetup",
        "date": "2026-03-01T18:00:00",
        "location": "GitHub HQ, SF",
        "description": "Monthly meetup for developer tools enthusiasts. Demo slots available.",
        "speakers": [{"name": "Alex Rivera", "role": "CTO", "company": "DevTool Co"}],
        "topics": ["developer tools", "open source"],
        "relevance_score": 78,
        "status": "suggested",
    },
    {
        "id": "evt-3",
        "title": "Crypto Winter Survival Tactics",
        "url": "https://eventbrite.com/crypto-winter",
        "source": "eventbrite",
        "event_type": "conference",
        "date": "2026-03-02T09:00:00",
        "location": "Moscone Center, SF",
        "description": "All-day conference about surviving the crypto winter.",
        "topics": ["crypto", "web3", "blockchain"],
        "relevance_score": 15,
        "status": "rejected",
        "rejection_reason": "not_my_industry",
    },
    {
        "id": "evt-4",
        "title": "Y Combinator Demo Day After-Party",
        "url": "https://lu.ma/yc-afterparty",
        "source": "luma",
        "event_type": "happy_hour",
        "date": "2026-03-05T20:00:00",
        "location": "Press Club, SF",
        "description": "Celebrate with the latest YC batch. Open bar, great conversations.",
        "topics": ["startups", "fundraising", "networking"],
        "relevance_score": 88,
        "status": "applied",
    },
]

DEMO_PEOPLE = [
    {"id": "p-1", "name": "Sarah Chen", "role": "VC Partner", "company": "Sequoia", "connection_score": 95, "social_links": {"linkedin": "linkedin.com/in/sarachen", "twitter": "x.com/sarachen"}, "conversation_hooks": ["Recently led $50M Series B in AI company", "Spoke at TechCrunch about agent future"]},
    {"id": "p-2", "name": "James Liu", "role": "Partner", "company": "a16z", "connection_score": 90, "social_links": {"linkedin": "linkedin.com/in/jamesliu", "twitter": "x.com/jamesliu"}, "conversation_hooks": ["Published article on AI agents last week"]},
    {"id": "p-3", "name": "Alex Rivera", "role": "CTO", "company": "DevTool Co", "connection_score": 72, "social_links": {"linkedin": "linkedin.com/in/alexrivera"}, "conversation_hooks": ["Building similar product, potential integration"]},
    {"id": "p-4", "name": "Maya Patel", "role": "Senior Engineer", "company": "Google", "connection_score": 68, "social_links": {"linkedin": "linkedin.com/in/mayapatel", "github": "github.com/mayapatel"}, "conversation_hooks": ["Works on LLM infrastructure team"]},
]

DEMO_MESSAGES = [
    {"id": "m-1", "recipient": "Sarah Chen", "channel": "linkedin", "type": "cold_pre_event", "body": "Hi Sarah — saw you're speaking at the AI Founders Dinner this Thursday. Your recent Series B in AI agents is exactly the space I'm building in (AI-powered CRM at BuildAI). Would love to chat about what you're seeing in the agent ecosystem. See you there!", "status": "pending"},
    {"id": "m-2", "recipient": "James Liu", "channel": "twitter_dm", "type": "cold_pre_event", "body": "Hey James — looking forward to the AI dinner Thursday! Read your piece on agents last week. Building something in that space at BuildAI — our CRM uses autonomous agents for lead qualification. Would be great to connect.", "status": "pending"},
    {"id": "m-3", "recipient": "Alex Rivera", "channel": "linkedin", "type": "cold_pre_event", "body": "Hi Alex — noticed we'll both be at the DevTools meetup. Your work at DevTool Co caught my eye — I'm building an AI CRM at BuildAI and see some integration possibilities. Coffee before the event?", "status": "approved"},
]


def main() -> None:
    print("NEXUS Demo Data Generator")
    print("=" * 40)
    print(f"Profile: {DEMO_PROFILE['name']} ({DEMO_PROFILE['company']})")
    print(f"Events: {len(DEMO_EVENTS)}")
    print(f"People: {len(DEMO_PEOPLE)}")
    print(f"Messages: {len(DEMO_MESSAGES)}")

    output = {
        "profile": DEMO_PROFILE,
        "events": DEMO_EVENTS,
        "people": DEMO_PEOPLE,
        "messages": DEMO_MESSAGES,
    }

    out_path = Path(__file__).parent / "demo_output.json"
    out_path.write_text(json.dumps(output, indent=2))
    print(f"\nWritten to {out_path}")


if __name__ == "__main__":
    main()
