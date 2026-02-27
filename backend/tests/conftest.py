import pytest


@pytest.fixture
def test_user_profile() -> dict:
    return {
        "id": "test-user-1",
        "name": "John Park",
        "email": "john@buildai.com",
        "role": "Founder & CEO",
        "company": "BuildAI",
        "product_description": "AI-powered CRM for SMBs",
        "linkedin": "linkedin.com/in/johnpark",
        "twitter": "x.com/johnpark",
        "networking_goals": ["find investors", "hire engineers"],
        "target_roles": ["VC Partner", "Senior Engineer", "CTO"],
        "target_companies": ["Sequoia", "a16z", "Google"],
        "target_industries": ["AI/ML", "SaaS", "Developer Tools"],
        "target_people": [],
        "interests": ["AI agents", "developer tools", "fundraising"],
        "preferred_event_types": ["dinner", "meetup", "conference"],
        "max_events_per_week": 4,
        "max_event_spend": 50,
        "preferred_days": ["tuesday", "thursday"],
        "preferred_times": ["evening"],
        "message_tone": "casual",
        "auto_apply_threshold": 80,
        "suggest_threshold": 50,
        "auto_schedule_threshold": 85,
    }


@pytest.fixture
def sample_raw_event() -> dict:
    return {
        "title": "AI Founders Dinner — SF",
        "url": "https://lu.ma/ai-dinner-sf",
        "source": "luma",
        "description": (
            "Intimate gathering of 30 founders and investors. "
            "Speakers: Sarah Chen (Sequoia), James Liu (a16z). "
            "Topics: AI agents, fundraising."
        ),
    }
