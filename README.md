# NEXUS - Autonomous Networking Agent for SF

> **"ManyChat for events — turn it on, it never stops. Discovers events, applies for you, stalks every attendee, finds their socials, and makes the first move."**

An autonomous, always-on agent that continuously scans San Francisco events, auto-applies based on your profile & preferences, schedules everything on your calendar, **deep-researches every attendee (iteratively, until it knows enough)**, resolves their social media accounts from just a name, drafts personalized cold outreach **before the event**, and sends follow-up messages **after** — all with a human-in-the-loop feedback system that learns and improves over time.

**The full loop:** Discover → Apply → Schedule → Research Attendees → Find Socials → Cold Message → Attend → Follow Up → Save to CRM → Repeat Forever

**Hackathon:** [Autonomous Agents Hackathon](https://autonomous-agents-hackathon.devpost.com/) — Feb 27, 2026, AWS Builder Loft SF
**Required:** 3+ sponsor tools | **Using:** Tavily Search + Neo4j + Yutori API + Fastino GLiNER + Render + Reka Vision (6 tools)

---

## Table of Contents

1. [Problem Statement](#problem-statement)
2. [Solution Overview](#solution-overview)
3. [Architecture](#architecture)
4. [Agent System Design](#agent-system-design)
5. [Sponsor Tool Integration](#sponsor-tool-integration)
6. [Feedback Loop & Personalization Engine](#feedback-loop--personalization-engine)
7. [Data Models](#data-models)
8. [UI/UX Design](#uiux-design)
9. [API Specifications](#api-specifications)
10. [Implementation Plan](#implementation-plan)
11. [Tech Stack](#tech-stack)
12. [Deployment](#deployment)
13. [Judging Criteria Alignment](#judging-criteria-alignment)

---

## Problem Statement

SF professionals drown in event noise. Hundreds of meetups, conferences, happy hours, and dinners happen weekly. The current experience:

1. **Discovery is fragmented** — Eventbrite, Luma, Meetup, Lu.ma, Partiful, X/Twitter, newsletters, Slack communities... no single source of truth
2. **Applying is manual** — each event has its own RSVP flow, application form, waitlist
3. **No intelligent filtering** — you waste time scrolling through irrelevant events
4. **Networking is blind** — you show up not knowing who's attending or who you *should* meet
5. **Follow-up dies** — you meet people but never send that first message
6. **Zero learning** — platforms don't learn your preferences over time

**The cost:** Missed connections that could have been your next co-founder, investor, hire, or customer.

---

## Solution Overview

NEXUS is a **continuously-running multi-agent system** that operates as your autonomous networking chief-of-staff:

```
┌─────────────────────────────────────────────────────────────┐
│                     NEXUS AGENT SYSTEM                       │
│                                                              │
│  ┌──────────┐   ┌──────────┐   ┌──────────┐   ┌──────────┐ │
│  │ DISCOVER │──▶│ ANALYZE  │──▶│   ACT    │──▶│ CONNECT  │ │
│  │  Agent   │   │  Agent   │   │  Agent   │   │  Agent   │ │
│  └──────────┘   └──────────┘   └──────────┘   └──────────┘ │
│       │              │              │              │         │
│       └──────────────┴──────────┴──────────────┘         │
│                          │                                   │
│                 ┌────────▼────────┐                          │
│                 │  FEEDBACK LOOP  │                          │
│                 │  (User Prefs)   │                          │
│                 └─────────────────┘                          │
└─────────────────────────────────────────────────────────────┘
```

### Core Loop (runs autonomously, 24/7)

| Phase | What happens | Sponsor Tool |
|-------|-------------|--------------|
| **DISCOVER** | Scans 10+ event sources across SF for upcoming events | **Tavily Search** + **Yutori Scouting** |
| **ANALYZE** | Extracts entities (people, companies, topics), scores relevance, builds relationship graph | **Fastino GLiNER** + **Neo4j** |
| **ACT** | Auto-applies/RSVPs, adds to calendar, handles waitlists | **Yutori Navigator** |
| **CONNECT** | Researches attendees, drafts personalized cold messages, queues for user approval | **Tavily Search** + **Neo4j** |

### What makes it autonomous

- **Yutori Scouting API** monitors event sources on a schedule — no polling needed
- Agent wakes up on new events, processes them through the pipeline
- User only intervenes via the feedback UI (approve/reject/adjust)
- System learns from every interaction

---

## Architecture

### System Architecture (Claude = Central Brain)

```
┌────────────────────────────────────────────────────────────────────┐
│                          FRONTEND (Next.js)                        │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌───────────┐            │
│  │ Dashboard │ │ Event    │ │ People   │ │ Settings/ │            │
│  │ (Feed)   │ │ Detail   │ │ Graph    │ │ Profile   │            │
│  └──────────┘ └──────────┘ └──────────┘ └───────────┘            │
└─────────────────────────┬──────────────────────────────────────────┘
                          │ REST + WebSocket
┌─────────────────────────▼──────────────────────────────────────────┐
│                        BACKEND (FastAPI)                            │
│                                                                     │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │              CLAUDE ReAct AGENT (The Brain)                  │   │
│  │                                                              │   │
│  │  System Prompt: user profile, goals, preferences, rules      │   │
│  │  Loop: Think → Pick Tool → Act → Observe → Think again       │   │
│  │                                                              │   │
│  │  ┌────────────────── TOOL BELT ────────────────────────┐    │   │
│  │  │                                                      │    │   │
│  │  │  tavily_search    yutori_browse    yutori_scout      │    │   │
│  │  │  fastino_extract  neo4j_query      neo4j_write       │    │   │
│  │  │  google_calendar  resolve_social   reka_vision       │    │   │
│  │  │  draft_message    notify_user      get_feedback      │    │   │
│  │  │                                                      │    │   │
│  │  └──────────────────────────────────────────────────────┘    │   │
│  └─────────────────────────────────────────────────────────────┘   │
│                                                                     │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────────────┐  │
│  │ PostgreSQL   │  │   Neo4j      │  │  Google Calendar API     │  │
│  │ (app state)  │  │ (graph =     │  │  (scheduling)            │  │
│  │              │  │  long-term   │  │                          │  │
│  │              │  │  memory)     │  │                          │  │
│  └──────────────┘  └──────────────┘  └──────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────┘

Render Background Worker: runs the Claude ReAct loop 24/7
Neo4j = Agent's long-term memory (survives context window resets)
```
```

### Agent Communication Flow

```
Discovery Agent                 Analyze Agent
     │                               │
     │  event_raw{title,url,source}  │
     │──────────────────────────────▶│
     │                               │
     │                          extracts entities
     │                          scores relevance
     │                          builds graph edges
     │                               │
     │                               │  event_enriched{score,entities,people}
     │                               │──────────────────────────────▶ Action Agent
     │                               │                                    │
     │                               │                              if score > threshold:
     │                               │                                apply/RSVP
     │                               │                                add to calendar
     │                               │                                    │
     │                               │                                    ▼
     │                               │                              Connect Agent
     │                               │                                    │
     │                               │                              research attendees
     │                               │                              draft messages
     │                               │                              queue for approval
     │                               │                                    │
     │                               │                                    ▼
     │                               │                              USER FEEDBACK
     │                               │                              (approve/reject/edit)
     │                               │                                    │
     │◀──────────────────────────────│◀───────────────────────────────────┘
     │          preference signal fed back to scoring model
```

---

## Agent System Design

### Agent 1: Discovery Agent

**Purpose:** Continuously find relevant events in SF across all platforms.

**Trigger:** Scheduled (every 6 hours) + Yutori Scouting webhooks (real-time)

**Data Sources Monitored:**

| Source | Method | Frequency |
|--------|--------|-----------|
| Eventbrite SF | Tavily Search (`site:eventbrite.com`) | 6h |
| Lu.ma SF events | Yutori Scouting API | Real-time |
| Meetup.com SF | Tavily Search (`site:meetup.com`) | 6h |
| Partiful | Yutori Scouting API | Real-time |
| SF tech Twitter/X | Tavily Search (topic: news) | 3h |
| Luma calendar pages | Yutori Scouting API | Real-time |
| Startup newsletters | Tavily Search | 12h |

**Implementation:**

```python
# Discovery Agent - Tavily Search
async def discover_events_tavily(user_profile: UserProfile) -> list[RawEvent]:
    """Search for events matching user's interests across platforms."""

    queries = build_search_queries(user_profile)
    # e.g., "SF AI startup events this week"
    #        "San Francisco tech networking events February 2026"
    #        "SF founder dinner meetup"

    all_events = []
    for query in queries:
        results = await tavily.search(
            query=query,
            search_depth="advanced",      # highest relevance
            topic="general",
            max_results=20,
            include_answer=True,
            include_raw_content="markdown",
            include_domains=[
                "eventbrite.com", "lu.ma", "meetup.com",
                "partiful.com", "luma-cal.com"
            ],
            time_range="week",
            country="us"
        )

        for result in results["results"]:
            raw_event = parse_event_from_search_result(result)
            all_events.append(raw_event)

    return deduplicate(all_events)


# Discovery Agent - Yutori Scouting (continuous monitoring)
async def setup_event_scouts():
    """Set up Yutori Scouts to monitor event platforms for changes."""

    scouts = [
        {
            "task": "Monitor for new AI/tech events in San Francisco",
            "start_url": "https://lu.ma/sf",
            "schedule": "every_6_hours",
            "webhook_url": f"{BACKEND_URL}/webhooks/yutori/new-event",
            "webhook_format": "scout"
        },
        {
            "task": "Monitor for new startup/founder events in SF Bay Area",
            "start_url": "https://www.eventbrite.com/d/ca--san-francisco/startup/",
            "schedule": "every_6_hours",
            "webhook_url": f"{BACKEND_URL}/webhooks/yutori/new-event",
            "webhook_format": "scout"
        }
    ]

    for scout_config in scouts:
        await yutori.scouting.create(**scout_config)
```

### Agent 2: Analyze Agent

**Purpose:** Extract entities, score relevance, and build the knowledge graph.

**Trigger:** New raw event from Discovery Agent

**Pipeline:**

```
Raw Event
    │
    ▼
[Fastino GLiNER] ──▶ Extract: people, companies, topics, roles
    │
    ▼
[Scoring Engine] ──▶ Calculate relevance score (0-100) based on:
    │                  - Topic match with user interests
    │                  - Speaker/attendee quality
    │                  - Company relevance
    │                  - Historical accept/reject patterns
    │                  - Time/location convenience
    ▼
[Neo4j] ──▶ Create/update graph nodes and relationships:
              (:Event)-[:HAS_SPEAKER]->(:Person)
              (:Person)-[:WORKS_AT]->(:Company)
              (:Event)-[:TAGGED]->(:Topic)
              (:User)-[:INTERESTED_IN]->(:Topic)
              (:User)-[:ATTENDED]->(:Event)
              (:User)-[:REJECTED]->(:Event {reason: "..."})
              (:Person)-[:CONNECTED_TO]->(:Person)
```

**Implementation:**

```python
# Analyze Agent - Entity Extraction with Fastino GLiNER 2
async def extract_entities(event: RawEvent) -> EnrichedEvent:
    """Extract structured entities from event description using GLiNER 2."""

    from gliner2 import GLiNER2

    extractor = GLiNER2.from_api()  # Uses PIONEER_API_KEY env var

    text = f"{event.title} {event.description} {event.raw_content}"

    # Combined multi-task extraction in ONE pass (efficient)
    schema = (extractor.create_schema()
        # NER: Extract people, companies, topics
        .entities({
            "person": "Names of speakers, organizers, or notable attendees",
            "company": "Company or organization names",
            "job_title": "Professional titles like CEO, Engineer, Partner",
            "technology": "Technologies, frameworks, or tools mentioned",
            "topic": "Event topics, themes, or subject areas"
        })
        # Classification: Event type
        .classification("event_type", [
            "conference", "meetup", "dinner", "workshop",
            "happy_hour", "demo_day", "hackathon", "panel"
        ])
        # Structured: Event metadata
        .structure("event_info")
            .field("event_name", dtype="str", description="Full event name")
            .field("date", dtype="str", description="Event date")
            .field("time", dtype="str", description="Event start time")
            .field("location", dtype="str", description="Venue or address")
            .field("price", dtype="str", description="Ticket price or 'Free'")
            .field("capacity", dtype="str", description="Number of spots")
            .field("target_audience", dtype="str", description="Who this event is for")
        # Relations: Who speaks where, works where
        .relations({
            "speaks_at": "Person presenting or speaking at event",
            "works_at": "Person employed at company",
            "organizes": "Person or company organizing the event"
        })
    )

    results = extractor.extract(text, schema, include_confidence=True)

    return EnrichedEvent(
        raw=event,
        entities=results.get("entities", {}),
        event_type=results.get("event_type", "meetup"),
        structured=results.get("event_info", [{}])[0],
        relations=results.get("relation_extraction", {}),
        relevance_score=await calculate_relevance(results)
    )


# Analyze Agent - Neo4j Knowledge Graph
async def update_knowledge_graph(event: EnrichedEvent):
    """Insert event and its entities into Neo4j knowledge graph."""

    async with neo4j_driver.session() as session:
        # Create event node
        await session.run("""
            MERGE (e:Event {url: $url})
            SET e.title = $title,
                e.date = datetime($date),
                e.location = $location,
                e.type = $type,
                e.relevance_score = $score,
                e.status = 'discovered',
                e.source = $source
        """, event.to_neo4j_params())

        # Create person nodes and relationships
        for speaker in event.structured.speakers:
            await session.run("""
                MERGE (p:Person {name: $name})
                SET p.title = $title, p.company = $company
                MERGE (e:Event {url: $event_url})
                MERGE (p)-[:SPEAKS_AT]->(e)

                MERGE (c:Company {name: $company})
                MERGE (p)-[:WORKS_AT]->(c)
            """, {**speaker, "event_url": event.raw.url})

        # Create topic nodes
        for topic in event.structured.topics:
            await session.run("""
                MERGE (t:Topic {name: $topic})
                MERGE (e:Event {url: $url})
                MERGE (e)-[:TAGGED]->(t)
            """, {"topic": topic, "url": event.raw.url})


# Relevance Scoring
async def calculate_relevance(structured, entities, user_profile) -> float:
    """Score event relevance 0-100 based on user profile and history."""

    score = 0.0
    weights = user_profile.learned_weights  # adapts over time

    # Topic match (0-30 points)
    topic_overlap = set(structured.topics) & set(user_profile.interests)
    score += (len(topic_overlap) / max(len(structured.topics), 1)) * weights.topic_weight

    # People quality (0-25 points) — query Neo4j for connection value
    people_score = await neo4j_query("""
        MATCH (p:Person)-[:SPEAKS_AT]->(e:Event {url: $url})
        OPTIONAL MATCH (p)-[:WORKS_AT]->(c:Company)
        OPTIONAL MATCH (u:User {id: $user_id})-[:WANTS_TO_MEET]->(target_role:Role)
        WHERE p.title CONTAINS target_role.name
        RETURN count(p) as relevant_people,
               collect(DISTINCT c.name) as companies
    """)
    score += min(people_score.relevant_people * 5, weights.people_weight)

    # Event type preference (0-15 points)
    if structured.event_type in user_profile.preferred_event_types:
        score += weights.type_weight

    # Time convenience (0-15 points)
    if is_convenient_time(structured.date, structured.time, user_profile.calendar):
        score += weights.time_weight

    # Historical pattern (0-15 points) — learned from accept/reject
    similar_events_accepted = await get_similar_event_acceptance_rate(structured)
    score += similar_events_accepted * weights.history_weight

    return min(score, 100.0)
```

### Agent 3: Action Agent

**Purpose:** Auto-apply to events, RSVP, handle waitlists, schedule on calendar.

**Trigger:** Event passes relevance threshold (configurable, default: 60/100)

**Decision Matrix:**

| Score | Action | User Involvement |
|-------|--------|-----------------|
| 80-100 | Auto-apply + Auto-schedule | Notification only |
| 60-79 | Auto-apply, ask to schedule | Approve/reject prompt |
| 40-59 | Suggest event, don't apply | User decides |
| 0-39 | Skip silently | None (logged for learning) |

**Implementation:**

```python
# Action Agent - Yutori Navigator for auto-apply
async def apply_to_event(event: EnrichedEvent, user_profile: UserProfile):
    """Use Yutori Navigator to autonomously apply/RSVP to an event."""

    # Build task description with user's info for form-filling
    task_description = f"""
    Apply/RSVP to this event. Fill out any required forms with the following info:
    - Name: {user_profile.name}
    - Email: {user_profile.email}
    - Company: {user_profile.company}
    - Role: {user_profile.role}
    - LinkedIn: {user_profile.linkedin}
    - What brings you: {generate_application_reason(event, user_profile)}

    If there's a waitlist, join the waitlist.
    If payment is required and amount is under ${user_profile.max_event_spend}, proceed.
    If payment exceeds limit, stop and report back.

    Return the confirmation status and any confirmation number/email.
    """

    response = await yutori.browsing.create(
        task=task_description,
        start_url=event.raw.url,
        max_steps=50,
        agent="navigator-n1-latest",
        require_auth=False,
        output_schema={
            "type": "object",
            "properties": {
                "status": {"type": "string", "enum": ["applied", "waitlisted", "failed", "payment_required"]},
                "confirmation_id": {"type": "string"},
                "notes": {"type": "string"}
            }
        },
        webhook_url=f"{BACKEND_URL}/webhooks/yutori/application-result"
    )

    return response


# Google Calendar Integration
async def schedule_event(event: EnrichedEvent, user_profile: UserProfile):
    """Add confirmed event to user's Google Calendar."""

    calendar_event = {
        "summary": f"{event.structured.event_name}",
        "description": (
            f"Source: {event.raw.url}\n"
            f"Relevance Score: {event.relevance_score}/100\n"
            f"Key People: {', '.join(p['name'] for p in event.structured.speakers[:5])}\n"
            f"Topics: {', '.join(event.structured.topics)}\n\n"
            f"--- NEXUS Auto-scheduled ---"
        ),
        "start": {
            "dateTime": event.structured.start_datetime.isoformat(),
            "timeZone": "America/Los_Angeles"
        },
        "end": {
            "dateTime": event.structured.end_datetime.isoformat(),
            "timeZone": "America/Los_Angeles"
        },
        "location": event.structured.location,
        "reminders": {
            "useDefault": False,
            "overrides": [
                {"method": "popup", "minutes": 60},
                {"method": "popup", "minutes": 15}
            ]
        }
    }

    result = await google_calendar.events().insert(
        calendarId="primary",
        body=calendar_event
    ).execute()

    return result
```

### Agent 4: Connect Agent (Deep Attendee Intelligence)

**Purpose:** Scrape attendee lists, deep-research each person iteratively until profile is "rich enough", find high-value connections, draft outreach.

**Trigger:** Event application confirmed OR event page has visible attendee list

**This is the killer feature.** Most networking tools show you a name. NEXUS builds a full dossier.

#### Step 1: Scrape Attendees from Event Platforms

```python
# Connect Agent - Attendee Scraping via Yutori Navigator
async def scrape_attendees(event: EnrichedEvent) -> list[RawAttendee]:
    """Use Yutori Navigator to scrape attendee/RSVP lists from event pages."""

    # Different strategies per platform
    scrape_strategies = {
        "lu.ma": {
            "task": (
                "Go to this Luma event page. Click on the attendee/guest list. "
                "Scroll through ALL attendees. For each person, extract their: "
                "full name, profile photo URL, tagline/bio, company, title, "
                "and any social links visible. If there's a 'Show more' or "
                "pagination, keep clicking until all attendees are loaded. "
                "Return ALL attendees as a structured list."
            ),
            "max_steps": 80,  # attendee lists can be long
        },
        "eventbrite.com": {
            "task": (
                "Navigate to this Eventbrite event. Check if there's a visible "
                "attendee list, speaker list, or host information. Extract all "
                "person names, titles, companies, and bios visible on the page."
            ),
            "max_steps": 50,
        },
        "meetup.com": {
            "task": (
                "Go to this Meetup event page. Click on 'Attendees' or the RSVP "
                "list. Scroll through and extract each attendee's name, Meetup "
                "profile tagline, and any visible info. Load all pages."
            ),
            "max_steps": 60,
        }
    }

    platform = detect_platform(event.raw.url)
    strategy = scrape_strategies.get(platform, scrape_strategies["eventbrite.com"])

    response = await yutori.browsing.create(
        task=strategy["task"],
        start_url=event.raw.url,
        max_steps=strategy["max_steps"],
        agent="navigator-n1-latest",
        output_schema={
            "type": "object",
            "properties": {
                "attendees": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "name": {"type": "string"},
                            "title": {"type": "string"},
                            "company": {"type": "string"},
                            "bio": {"type": "string"},
                            "profile_url": {"type": "string"},
                            "social_links": {
                                "type": "object",
                                "properties": {
                                    "linkedin": {"type": "string"},
                                    "twitter": {"type": "string"}
                                }
                            }
                        }
                    }
                },
                "total_attendees": {"type": "integer"},
                "attendees_scraped": {"type": "integer"}
            }
        }
    )

    return [RawAttendee(**a) for a in response["structured_result"]["attendees"]]
```

#### Step 2: Deep Research Loop (Iterative Enrichment)

This is where it gets powerful. For each attendee, we run an **iterative research loop** that keeps digging until the profile is "rich enough" to be actionable.

```python
# Connect Agent - Iterative Deep Research
RICHNESS_THRESHOLD = 0.7  # 0-1, how "complete" a profile needs to be

async def deep_research_person(
    attendee: RawAttendee,
    user_profile: UserProfile,
    max_iterations: int = 3
) -> PersonProfile:
    """
    Iteratively research a person until their profile is rich enough.
    Each iteration digs deeper based on what's still missing.
    """

    profile = PersonProfile(name=attendee.name, sources=[])
    iteration = 0

    while iteration < max_iterations:
        iteration += 1
        richness = calculate_profile_richness(profile)

        if richness >= RICHNESS_THRESHOLD:
            break  # Profile is rich enough

        # Determine what's still missing
        gaps = identify_gaps(profile)
        # e.g., ["current_role", "recent_projects", "investment_history", "social_presence"]

        # Build targeted search query based on gaps
        query = build_research_query(attendee, profile, gaps, iteration)

        # ── Iteration 1: Basic identity ──
        # "Sarah Chen Sequoia Capital Partner"
        #
        # ── Iteration 2: Deep dive on gaps ──
        # "Sarah Chen recent investments 2025 2026 AI portfolio"
        #
        # ── Iteration 3: Niche details ──
        # "Sarah Chen conference talks podcast interviews opinions AI agents"

        search_result = await tavily.search(
            query=query,
            search_depth="advanced",
            max_results=10 + (iteration * 5),  # cast wider net each iteration
            include_answer=True,
            include_raw_content="markdown",
            time_range="year" if iteration == 1 else None,  # recent first
        )

        # Extract structured data from search results using Fastino
        raw_text = (
            search_result.get("answer", "") + "\n" +
            "\n".join(r["content"] for r in search_result["results"])
        )

        extractor = GLiNER2.from_api()
        schema = (extractor.create_schema()
            .entities({
                "person": "Names of people connected to this individual",
                "company": "Companies this person is associated with",
                "technology": "Technologies or domains they work in",
                "investment": "Companies or funds they've invested in",
                "achievement": "Notable achievements, awards, or milestones"
            })
            .structure("person_profile")
                .field("current_role", dtype="str")
                .field("company", dtype="str")
                .field("previous_roles", dtype="list")
                .field("expertise_areas", dtype="list")
                .field("recent_projects", dtype="list")
                .field("education", dtype="str")
                .field("notable_opinions", dtype="list",
                       description="Public opinions, hot takes, or stated beliefs")
                .field("content_created", dtype="list",
                       description="Blog posts, podcasts, talks they've given")
            .relations({
                "invested_in": "Investment relationship",
                "works_with": "Professional collaboration",
                "previously_at": "Past employment"
            })
        )

        extracted = extractor.extract(raw_text, schema, include_confidence=True)

        # Merge new data into existing profile (don't overwrite, enrich)
        profile = merge_profile_data(profile, extracted, search_result["results"])

        # Update Neo4j graph with new connections discovered
        await update_person_graph(profile, extracted)

        print(f"  Iteration {iteration}: richness {richness:.2f} → "
              f"{calculate_profile_richness(profile):.2f}")

    # Final: resolve social media accounts
    profile.social_links = await resolve_social_accounts(profile)
    profile.connection_score = await calculate_connection_value(profile, user_profile)
    return profile


# ── CRITICAL FEATURE: Social Media Account Resolution ──
async def resolve_social_accounts(profile: PersonProfile) -> SocialLinks:
    """
    Given a name + basic info, find ALL social media accounts.
    Handles disambiguation of same-name people.
    This is the KILLER FEATURE — turns a name into actionable outreach channels.
    """

    name = profile.name
    company = profile.company or ""
    title = profile.current_role or ""

    social = SocialLinks()

    # Strategy 1: Direct Tavily search for social profiles
    for platform, query_template in {
        "linkedin": f"{name} {company} site:linkedin.com/in/",
        "twitter": f"{name} {company} site:twitter.com OR site:x.com",
        "instagram": f"{name} {company} site:instagram.com",
        "github": f"{name} {company} site:github.com",
    }.items():
        result = await tavily.search(
            query=query_template,
            search_depth="basic",
            max_results=5,
        )

        # Disambiguation: verify the profile matches our target person
        for r in result["results"]:
            if await verify_social_match(r, profile):
                setattr(social, platform, r["url"])
                break

    # Strategy 2: If LinkedIn found, use Yutori to scrape linked socials
    if social.linkedin:
        linked_socials = await yutori.browsing.create(
            task=(
                f"Go to this LinkedIn profile. Find any linked websites, "
                f"Twitter/X handle, or other social media links on the profile. "
                f"Also note their headline and current position for verification."
            ),
            start_url=social.linkedin,
            max_steps=20,
            output_schema={
                "type": "object",
                "properties": {
                    "twitter": {"type": "string"},
                    "website": {"type": "string"},
                    "other_links": {"type": "array", "items": {"type": "string"}},
                    "headline": {"type": "string"}
                }
            }
        )
        if linked_socials.get("structured_result"):
            sr = linked_socials["structured_result"]
            social.twitter = social.twitter or sr.get("twitter")
            social.website = sr.get("website")

    # Strategy 3: Reka Vision — analyze Instagram/X profile pics & content
    # to verify identity across platforms (same face = same person)
    if social.instagram and social.linkedin:
        # Use Reka Vision to cross-verify profile photos match
        social.verified = await cross_verify_profiles_reka(
            social.instagram, social.linkedin
        )

    return social


async def verify_social_match(
    search_result: dict,
    target: PersonProfile
) -> bool:
    """
    Disambiguate: is this social profile actually our target person?
    Uses Fastino GLiNER to extract identity signals and compare.
    """
    extractor = GLiNER2.from_api()

    extracted = extractor.extract_entities(
        search_result.get("content", ""),
        {
            "person": "Full names of people",
            "company": "Companies or organizations",
            "job_title": "Professional roles or titles"
        },
        include_confidence=True
    )

    entities = extracted.get("entities", {})
    found_names = [e["text"] if isinstance(e, dict) else e
                   for e in entities.get("person", [])]
    found_companies = [e["text"] if isinstance(e, dict) else e
                       for e in entities.get("company", [])]

    # Match: name fuzzy match + company or title match
    name_match = any(fuzz.ratio(target.name.lower(), n.lower()) > 80
                     for n in found_names)
    company_match = any(fuzz.ratio((target.company or "").lower(), c.lower()) > 70
                        for c in found_companies)

    return name_match and (company_match or not target.company)


async def cross_verify_profiles_reka(
    instagram_url: str,
    linkedin_url: str
) -> bool:
    """Use Reka Vision API to verify same person across platforms."""
    # Reka Vision can compare profile images and bio content
    # Returns True if high confidence it's the same person
    result = await reka.vision.compare(
        urls=[instagram_url, linkedin_url],
        prompt="Are these two social media profiles the same person? "
               "Compare profile photos, names, and bio information."
    )
    return result.get("same_person_confidence", 0) > 0.8


def calculate_profile_richness(profile: PersonProfile) -> float:
    """Score how 'complete' a person's profile is. 0 = empty, 1 = full."""

    fields = {
        "current_role": 0.15,       # must know what they do
        "company": 0.10,            # must know where
        "expertise_areas": 0.15,    # must know their domain
        "recent_projects": 0.10,    # what they're working on NOW
        "previous_roles": 0.05,     # career trajectory
        "notable_opinions": 0.15,   # conversation hooks!
        "content_created": 0.10,    # shows thought leadership
        "social_links": 0.10,       # needed for cold outreach
        "mutual_connections": 0.10, # graph-based signal
    }

    score = 0.0
    for field, weight in fields.items():
        value = getattr(profile, field, None)
        if value and (isinstance(value, str) and len(value) > 2
                      or isinstance(value, list) and len(value) > 0):
            score += weight
    return score


def identify_gaps(profile: PersonProfile) -> list[str]:
    """Return which fields are still empty or thin."""
    gaps = []
    if not profile.current_role: gaps.append("current_role")
    if not profile.expertise_areas: gaps.append("expertise")
    if not profile.recent_projects: gaps.append("recent_activity")
    if not profile.notable_opinions: gaps.append("opinions_and_views")
    if not profile.social_links: gaps.append("social_presence")
    if not profile.content_created: gaps.append("content_and_talks")
    return gaps


def build_research_query(
    attendee: RawAttendee,
    profile: PersonProfile,
    gaps: list[str],
    iteration: int
) -> str:
    """Build progressively deeper search queries based on gaps."""

    base = f"{attendee.name}"
    if attendee.company:
        base += f" {attendee.company}"

    if iteration == 1:
        # Broad identity search
        return f"{base} {attendee.title or ''}"

    elif iteration == 2:
        # Fill specific gaps
        gap_terms = {
            "recent_activity": "recent projects 2025 2026",
            "opinions_and_views": "interview podcast opinion",
            "expertise": "expertise specialization domain",
            "social_presence": "twitter linkedin blog",
            "content_and_talks": "conference talk blog post podcast"
        }
        terms = " ".join(gap_terms.get(g, g) for g in gaps[:2])
        return f"{base} {terms}"

    else:
        # Niche: find conversation hooks
        user_interests = " ".join(profile.expertise_areas[:2]) if profile.expertise_areas else ""
        return f"{base} {user_interests} thoughts perspective"
```

#### Step 3: Neo4j Graph-Powered Connection Scoring

```python
# Connect Agent - Neo4j Connection Analysis
async def find_best_connections(event_url: str, user_id: str) -> list[PersonProfile]:
    """Use Neo4j graph to find highest-value connections at an event."""

    results = await neo4j_driver.session().run("""
        // Find people at this event
        MATCH (e:Event {url: $event_url})<-[:SPEAKS_AT|ATTENDS]-(p:Person)

        // Check for mutual connections (2nd degree)
        OPTIONAL MATCH (u:User {id: $user_id})-[:KNOWS]->(mutual:Person)-[:KNOWS]->(p)

        // Check for shared interests
        OPTIONAL MATCH (p)-[:EXPERT_IN]->(t:Topic)<-[:INTERESTED_IN]-(u:User {id: $user_id})

        // Check for company relevance
        OPTIONAL MATCH (p)-[:WORKS_AT]->(c:Company)<-[:TARGETS]-(u:User {id: $user_id})

        // Check if user wants to meet this type of role
        OPTIONAL MATCH (u:User {id: $user_id})-[:WANTS_TO_MEET]->(r:Role)
        WHERE p.title CONTAINS r.name

        RETURN p,
               count(DISTINCT mutual) as mutual_connections,
               collect(DISTINCT t.name) as shared_topics,
               c.name as company,
               count(DISTINCT r) as role_match,
               // Connection value score
               count(DISTINCT mutual) * 10 +
               count(DISTINCT t) * 5 +
               CASE WHEN c IS NOT NULL THEN 20 ELSE 0 END +
               count(DISTINCT r) * 15 as graph_score
        ORDER BY graph_score DESC
        LIMIT 10
    """, {"event_url": event_url, "user_id": user_id})

    return [build_person_profile(r) for r in results]
```

#### Step 4: Cold Message Drafting (Context-Rich)

```python
# Connect Agent - Cold Message Drafting
async def draft_cold_message(
    person: PersonProfile,
    event: EnrichedEvent,
    user_profile: UserProfile
) -> ColdMessage:
    """Draft hyper-personalized cold outreach using deep research data."""

    # The magic: we have SO much context from the research loop
    context = {
        "sender": {
            "name": user_profile.name,
            "role": user_profile.role,
            "company": user_profile.company,
            "product": user_profile.product_description,
            "looking_for": user_profile.networking_goals
        },
        "recipient": {
            "name": person.name,
            "role": person.current_role,
            "company": person.company,
            "expertise": person.expertise_areas,
            # These are the GOLD — conversation hooks from deep research
            "notable_opinions": person.notable_opinions,
            "recent_projects": person.recent_projects,
            "content_created": person.content_created,
        },
        "event": {
            "name": event.structured.get("event_name", event.raw.title),
            "shared_topics": list(
                set(person.expertise_areas or []) & set(event.structured.get("topics", []))
            )
        },
        "graph_context": {
            "mutual_connections": person.mutual_connections,
            "shared_topics": person.shared_topics,
            "connection_path": person.connection_path  # how they're linked in the graph
        }
    }

    # LLM generates message with STRICT constraints
    message = await generate_message(
        context=context,
        constraints={
            "max_length": 100,  # words — short is better
            "tone": user_profile.message_tone,
            "must_include": [
                "reference to their recent work or opinion",  # proves you did research
                "specific event reference",                    # shared context
                "clear reason to connect"                      # not generic
            ],
            "must_not_include": [
                "generic flattery ('big fan of your work')",
                "sales pitch or product plug",
                "asking for a favor in first message"
            ],
            "channel": person.best_channel
        }
    )

    return ColdMessage(
        recipient=person,
        channel=person.best_channel,
        content=message,
        status="draft",
        context=context
    )
```

#### Step 5: Post-Event Follow-Up Messages

Pre-event cold messages get you the intro. **Post-event follow-ups** close the loop.

```python
# Connect Agent - Post-Event Follow-Up
async def generate_followup_messages(event: EnrichedEvent, user: UserProfile):
    """
    After an event ends, automatically draft follow-up messages
    for people the user actually interacted with (or wanted to meet).
    """

    # Get people the user marked as "met" or "want to follow up"
    met_people = await get_people_met_at_event(event.id, user.id)

    # Also get the pre-event top connections (even if user didn't mark them)
    top_connections = await find_best_connections(event.url, user.id)

    all_followups = set(met_people + top_connections[:3])

    for person in all_followups:
        # Different message for met vs. didn't meet
        if person in met_people:
            message_type = "met_followup"
            constraints = {
                "must_include": [
                    "reference to specific conversation or topic discussed",
                    "concrete next step (coffee, call, intro)"
                ],
                "tone": "warm",
                "max_length": 80,
            }
        else:
            message_type = "missed_followup"
            constraints = {
                "must_include": [
                    "mention you were both at the same event",
                    "reference to their work that's relevant"
                ],
                "tone": "casual",
                "max_length": 60,
            }

        # Choose best channel considering platform limits
        channel = await select_best_channel(person, user)

        message = await generate_message(
            context={**build_context(person, event, user), "type": message_type},
            constraints=constraints
        )

        await save_message_draft(ColdMessage(
            recipient=person,
            channel=channel,
            content=message,
            status="draft",
            message_type=message_type
        ))


async def select_best_channel(person: PersonProfile, user: UserProfile) -> str:
    """
    Select outreach channel considering platform limits.
    LinkedIn free = ~5 connection requests/week → use sparingly.
    """

    # Check remaining LinkedIn budget this week
    linkedin_sent = await count_linkedin_messages_this_week(user.id)
    linkedin_remaining = user.linkedin_weekly_limit - linkedin_sent  # default 5

    if person.social_links.twitter:
        return "twitter_dm"  # no hard limits, best for cold
    elif person.social_links.linkedin and linkedin_remaining > 0:
        return "linkedin"
    elif person.social_links.email:
        return "email"
    elif person.social_links.instagram:
        return "instagram_dm"  # last resort
    else:
        return "twitter_dm"  # search for their handle
```

#### Handling Private Attendee Lists

Many events don't show attendees until you register, or keep them completely private.

```python
# Indirect attendee discovery strategies
async def discover_attendees_indirect(event: EnrichedEvent) -> list[RawAttendee]:
    """
    When attendee list is private, use indirect methods to discover who's going.
    """

    attendees = []

    # Strategy 1: Scrape event page after registration (we already applied)
    if event.application_result and event.application_result["status"] == "applied":
        # Now we're registered — attendee list might be visible
        scrape_result = await yutori.browsing.create(
            task=(
                "I'm already registered for this event. Navigate to the event "
                "page and look for any attendee list, guest list, or RSVP list "
                "that's now visible to registered attendees. Extract all names, "
                "titles, companies, and profile links."
            ),
            start_url=event.raw.url,
            max_steps=40,
            output_schema=ATTENDEE_SCHEMA
        )
        attendees.extend(parse_attendees(scrape_result))

    # Strategy 2: Search social media for people mentioning the event
    social_mentions = await tavily.search(
        query=f'"{event.raw.title}" attending OR "see you" OR "excited for"',
        search_depth="advanced",
        max_results=20,
        topic="news",
        time_range="week",
        include_domains=["twitter.com", "x.com", "linkedin.com"]
    )
    for mention in social_mentions["results"]:
        person = extract_person_from_social_post(mention)
        if person:
            attendees.append(person)

    # Strategy 3: Check event organizer's followers/connections
    if event.structured.get("organizer"):
        org_connections = await tavily.search(
            query=f"{event.structured['organizer']} {event.raw.title} speaker guest",
            search_depth="advanced",
            max_results=10
        )
        for result in org_connections["results"]:
            extractor = GLiNER2.from_api()
            entities = extractor.extract_entities(
                result["content"],
                ["person", "company", "job_title"],
                include_confidence=True
            )
            for person_name in entities.get("entities", {}).get("person", []):
                name = person_name["text"] if isinstance(person_name, dict) else person_name
                attendees.append(RawAttendee(name=name, source="indirect"))

    # Strategy 4: Check if other attendees shared the event link
    link_sharers = await tavily.search(
        query=f"{event.raw.url}",
        search_depth="basic",
        max_results=10
    )
    for sharer in link_sharers["results"]:
        person = extract_person_from_social_post(sharer)
        if person:
            attendees.append(person)

    return deduplicate_attendees(attendees)
```

### The Always-On Agent (Replaces Fixed Daemon)

The NexusDaemon from the old design is **gone**. Instead, Claude IS the daemon.
It runs as a Render Background Worker, thinking and acting in a continuous loop.

The key difference: **the old daemon had 5 fixed loops running on timers.**
The new agent has **1 thinking loop that decides what to do based on context.**

```
OLD (fixed pipeline):                 NEW (thinking agent):
┌─────────────────────┐               ┌─────────────────────┐
│ discovery_loop (6h) │               │                     │
│ research_loop (12h) │               │   Claude thinks:    │
│ message_loop  (24h) │    ──▶        │   "What should I    │
│ followup_loop (6h)  │               │    do right now?"   │
│ webhook_loop        │               │   → picks tool      │
└─────────────────────┘               │   → acts            │
 5 timers, no intelligence            │   → observes result │
                                      │   → thinks again    │
                                      └─────────────────────┘
                                       1 brain, full autonomy
```

The old NexusDaemon code is kept below for reference on the async tool
implementations, but the orchestration logic is now entirely in Claude's
system prompt + ReAct loop above.

```python
# agents/daemon.py — DEPRECATED: replaced by Claude ReAct agent
# Kept for reference on tool implementations only
import asyncio
from datetime import datetime, timedelta

class NexusDaemon:
    """
    The autonomous daemon that runs the NEXUS pipeline continuously.
    Start it once. It discovers, analyzes, applies, and connects — forever.
    """

    def __init__(self, user_profile: UserProfile):
        self.user = user_profile
        self.pipeline = nexus_pipeline  # LangGraph compiled graph
        self.running = True

        # Cycle configuration (adapts over time)
        self.discovery_interval = timedelta(hours=6)   # search for new events
        self.research_interval = timedelta(hours=12)    # deep-research attendees
        self.message_interval = timedelta(hours=24)     # draft new outreach

        self.last_discovery = None
        self.last_research = None
        self.last_message_draft = None

    async def start(self):
        """Main daemon loop — runs indefinitely."""
        print(f"[NEXUS] Daemon started for {self.user.name}")
        print(f"[NEXUS] Discovery every {self.discovery_interval}")
        print(f"[NEXUS] Running autonomously. Ctrl+C or UI pause to stop.")

        # Run ALL loops concurrently — this is what makes it truly autonomous
        await asyncio.gather(
            self.discovery_loop(),      # find events (every 6h)
            self.research_loop(),       # deep-research attendees (every 12h)
            self.message_loop(),        # draft pre-event messages (every 24h)
            self.followup_loop(),       # post-event follow-ups (every 6h)
            self.webhook_listener(),    # real-time Yutori Scout alerts
        )

    # ── Loop 1: Discovery (every 6 hours) ──
    async def discovery_loop(self):
        """Continuously discover new events."""
        while self.running:
            try:
                print(f"\n[DISCOVER] {datetime.now()} Starting discovery cycle...")

                # 1. Tavily Search across all event platforms
                raw_events = await discover_events_tavily(self.user)
                print(f"[DISCOVER] Found {len(raw_events)} raw events")

                # 2. Deduplicate against known events in Neo4j
                new_events = await filter_known_events(raw_events)
                print(f"[DISCOVER] {len(new_events)} are new")

                # 3. Analyze + Score each new event
                for event in new_events:
                    enriched = await extract_entities(event)
                    await update_knowledge_graph(enriched)

                    # 4. Auto-action based on score
                    if enriched.relevance_score >= self.user.auto_apply_threshold:
                        print(f"[ACTION] Auto-applying to: {event.title} "
                              f"(score: {enriched.relevance_score})")
                        result = await apply_to_event(enriched, self.user)
                        if result["status"] == "applied":
                            await schedule_event(enriched, self.user)
                            # Trigger attendee research
                            await self.queue_attendee_research(enriched)

                    elif enriched.relevance_score >= self.user.suggest_threshold:
                        # Push to UI for user review
                        await notify_user("event:suggested", enriched)

                    # else: skip silently, but still stored in Neo4j for learning

                self.last_discovery = datetime.now()
                print(f"[DISCOVER] Cycle complete. Next in {self.discovery_interval}")

            except Exception as e:
                print(f"[DISCOVER] Error: {e}. Retrying next cycle.")

            await asyncio.sleep(self.discovery_interval.total_seconds())

    # ── Loop 2: Attendee Research (triggered by confirmed events) ──
    async def research_loop(self):
        """Deep-research attendees for upcoming confirmed events."""
        while self.running:
            try:
                # Get events where we're confirmed but haven't researched attendees
                events = await get_events_needing_research()

                for event in events:
                    print(f"\n[RESEARCH] Scraping attendees for: {event.title}")

                    # Step 1: Scrape attendee list via Yutori
                    attendees = await scrape_attendees(event)
                    print(f"[RESEARCH] Found {len(attendees)} attendees")

                    # Step 2: Deep research each person (iterative loop!)
                    for attendee in attendees:
                        # Skip if we already have a rich profile
                        existing = await get_person_from_neo4j(attendee.name)
                        if existing and calculate_profile_richness(existing) >= RICHNESS_THRESHOLD:
                            continue

                        print(f"[RESEARCH] Deep-researching: {attendee.name}")
                        profile = await deep_research_person(attendee, self.user)
                        print(f"[RESEARCH] {attendee.name}: richness "
                              f"{calculate_profile_richness(profile):.2f}, "
                              f"connection score {profile.connection_score}")

                    # Step 3: Find best connections using graph
                    best = await find_best_connections(event.url, self.user.id)
                    print(f"[RESEARCH] Top connections: "
                          f"{[p.name for p in best[:3]]}")

                    # Mark event as "researched"
                    await mark_event_researched(event)

            except Exception as e:
                print(f"[RESEARCH] Error: {e}")

            await asyncio.sleep(self.research_interval.total_seconds())

    # ── Loop 3: Message Drafting (for researched events) ──
    async def message_loop(self):
        """Draft cold messages for top connections at upcoming events."""
        while self.running:
            try:
                events = await get_researched_events_without_messages()

                for event in events:
                    best_connections = await find_best_connections(event.url, self.user.id)

                    for person in best_connections[:3]:  # top 3 per event
                        # Only draft if we have a rich enough profile
                        if calculate_profile_richness(person) < 0.5:
                            continue

                        message = await draft_cold_message(person, event, self.user)
                        await save_message_draft(message)
                        await notify_user("message:drafted", message)
                        print(f"[CONNECT] Draft ready: → {person.name} "
                              f"via {message.channel}")

            except Exception as e:
                print(f"[CONNECT] Error: {e}")

            await asyncio.sleep(self.message_interval.total_seconds())

    # ── Loop 4: Post-Event Follow-Up (checks daily) ──
    async def followup_loop(self):
        """After events end, auto-generate follow-up messages."""
        while self.running:
            try:
                # Find events that ended in the last 24h without follow-ups
                ended_events = await get_recently_ended_events(hours=24)

                for event in ended_events:
                    print(f"\n[FOLLOWUP] Generating follow-ups for: {event.title}")
                    await generate_followup_messages(event, self.user)
                    await mark_event_followed_up(event)

                    # Save all contacts to CRM / Neo4j
                    attendees = await get_event_attendees(event.id)
                    for person in attendees:
                        await save_to_contact_db(person, event, self.user)
                    print(f"[CRM] Saved {len(attendees)} contacts from {event.title}")

            except Exception as e:
                print(f"[FOLLOWUP] Error: {e}")

            await asyncio.sleep(timedelta(hours=6).total_seconds())

    # ── Loop 5: Webhook Listener (real-time from Yutori Scouts) ──
    async def webhook_listener(self):
        """Handle incoming webhooks from Yutori Scouts (new event alerts)."""
        # This is handled by the FastAPI webhook endpoint
        # When a Scout detects a new event, it triggers the analysis pipeline
        pass

    async def queue_attendee_research(self, event: EnrichedEvent):
        """Mark an event for attendee research in the next research cycle."""
        await mark_event_for_research(event)

    async def stop(self):
        """Gracefully stop the daemon."""
        self.running = False
        print("[NEXUS] Daemon stopping...")


# Entry point
async def main():
    user = await load_user_profile()
    daemon = NexusDaemon(user)
    await daemon.start()

if __name__ == "__main__":
    asyncio.run(main())
```

**What the daemon does while you sleep:**

```
┌──────────────────────────────────────────────────────────────────┐
│                    NEXUS DAEMON TIMELINE                         │
│                                                                  │
│  6:00 AM  [DISCOVER] Tavily scans 10+ event platforms           │
│           Found 8 new SF events for this week                    │
│           Scored: 2 auto-apply, 4 suggest, 2 skip               │
│                                                                  │
│  6:05 AM  [ACTION] Auto-applied to "AI Founders Dinner" (92/100)│
│           Auto-applied to "DevTools Meetup" (85/100)             │
│           Calendar synced for both                               │
│                                                                  │
│  6:10 AM  [RESEARCH] Scraping Lu.ma attendees for AI Dinner     │
│           Found 34 attendees                                     │
│           Deep-researching Sarah Chen (Sequoia)... 3 iterations  │
│             → Iter 1: identity ✓ (richness: 0.35)               │
│             → Iter 2: investments, opinions ✓ (richness: 0.68)  │
│             → Iter 3: recent talks, hot takes ✓ (richness: 0.82)│
│           Deep-researching Marcus Johnson (BuildAI)... 2 iter    │
│             → Iter 1: identity ✓ (richness: 0.40)               │
│             → Iter 2: product, expertise ✓ (richness: 0.71)     │
│           ... (researched 34 attendees in ~15 minutes)           │
│                                                                  │
│  6:30 AM  [CONNECT] Top 3 connections identified via Neo4j graph│
│           Draft message → Sarah Chen (LinkedIn) ✓               │
│           Draft message → Marcus Johnson (Twitter DM) ✓         │
│           Draft message → Alex Rivera (Email) ✓                 │
│                                                                  │
│  7:00 AM  You wake up. Open NEXUS dashboard.                    │
│           See: 2 events applied, 4 suggested, 3 messages ready  │
│           Approve 2 messages, edit 1, reject 1 event            │
│           NEXUS learns from every action.                        │
│                                                                  │
│  12:00 PM [DISCOVER] Next cycle. Finds 3 more events.           │
│           Scoring has IMPROVED because of morning feedback.      │
│           Auto-skips a Web3 event (learned: user rejects Web3)  │
│                                                                  │
│  6:00 PM  [DISCOVER] Evening cycle.                             │
│  6:05 PM  [RESEARCH] New attendees for tomorrow's meetup.       │
│  6:20 PM  [CONNECT] 2 more message drafts ready.               │
│                                                                  │
│  ... repeats forever ...                                         │
└──────────────────────────────────────────────────────────────────┘
```

---

## Core Architecture: Claude as Central Orchestrator (ReAct Agent)

**NEXUS is not a scripted pipeline. It's an AI agent that thinks, decides, and acts.**

Claude is the brain. It has tools. It decides what to do, in what order, based on context. When something fails, it reasons about alternatives. When the user gives feedback, it adjusts strategy in real-time.

```
┌─────────────────────────────────────────────────────────────────┐
│                                                                  │
│                    CLAUDE (ReAct Agent)                           │
│                    ════════════════════                           │
│                    "The Brain"                                    │
│                                                                  │
│    Observes state → Thinks → Picks a tool → Acts → Repeats      │
│                                                                  │
│    ┌─────────────────────────────────────────────────────────┐   │
│    │                    TOOL BELT                             │   │
│    │                                                         │   │
│    │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  │   │
│    │  │ tavily_search│  │yutori_browse │  │yutori_scout  │  │   │
│    │  │ (find events │  │(apply, scrape│  │(monitor new  │  │   │
│    │  │  & people)   │  │ attendees)   │  │  events)     │  │   │
│    │  └──────────────┘  └──────────────┘  └──────────────┘  │   │
│    │                                                         │   │
│    │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  │   │
│    │  │fastino_extract│ │ neo4j_query  │  │neo4j_write   │  │   │
│    │  │(NER, classify│  │(find connect-│  │(save people, │  │   │
│    │  │ structure)   │  │ ions, score) │  │ events)      │  │   │
│    │  └──────────────┘  └──────────────┘  └──────────────┘  │   │
│    │                                                         │   │
│    │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  │   │
│    │  │google_calendar│ │reka_vision   │  │resolve_social│  │   │
│    │  │(schedule,    │  │(verify faces,│  │(find X, IG,  │  │   │
│    │  │ check busy)  │  │ analyze posts│  │ LinkedIn)    │  │   │
│    │  └──────────────┘  └──────────────┘  └──────────────┘  │   │
│    │                                                         │   │
│    │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  │   │
│    │  │draft_message │  │send_message  │  │get_feedback  │  │   │
│    │  │(write cold/  │  │(queue for    │  │(read user    │  │   │
│    │  │ followup msg)│  │ user approve)│  │ decisions)   │  │   │
│    │  └──────────────┘  └──────────────┘  └──────────────┘  │   │
│    │                                                         │   │
│    │  ┌──────────────┐  ┌──────────────┐                     │   │
│    │  │get_user_prefs│  │update_scores │                     │   │
│    │  │(read profile,│  │(adjust weights│                    │   │
│    │  │ history)     │  │ from feedback)│                    │   │
│    │  └──────────────┘  └──────────────┘                     │   │
│    └─────────────────────────────────────────────────────────┘   │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### Why ReAct Agent, Not a Fixed Pipeline

| Fixed Pipeline (before) | ReAct Agent (now) |
|------------------------|-------------------|
| Always: search → extract → score → apply → research → message | Claude decides what to do next based on what it sees |
| Event page is blank? Pipeline crashes | "Page is blank. Let me try searching X for mentions of this event instead." |
| Attendee list private? Skip | "List is private. Let me check if I'm registered... yes. Let me re-scrape as a registered user." |
| Score = 65, threshold = 80? Hard skip | "Score is 65 but the speaker is from Sequoia and user wants to meet VCs. I'll suggest this one." |
| LinkedIn at 5/5 limit? Fail | "LinkedIn is maxed this week. Let me find their X handle and DM there instead." |
| 3 AM, nothing to do? Sleep 6 hours | "No new events, but tomorrow's dinner has 5 unresearched attendees. Let me research them now." |

### Implementation: Claude Agent with Tool Use

```python
# agents/orchestrator.py — Claude as the central brain
import anthropic
import json
from datetime import datetime

client = anthropic.Anthropic()

# ── Tool Definitions ──
TOOLS = [
    {
        "name": "tavily_search",
        "description": (
            "Search the web for events, people, companies, or any information. "
            "Use this to discover new events on Eventbrite, Luma, Meetup, etc. "
            "Also use this to research attendees — find their background, "
            "recent activity, social media presence."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "Search query"},
                "search_depth": {"type": "string", "enum": ["basic", "advanced"]},
                "max_results": {"type": "integer", "default": 10},
                "include_domains": {
                    "type": "array", "items": {"type": "string"},
                    "description": "Limit search to these domains"
                },
                "time_range": {
                    "type": "string", "enum": ["day", "week", "month"],
                    "description": "How recent the results should be"
                }
            },
            "required": ["query"]
        }
    },
    {
        "name": "yutori_browse",
        "description": (
            "Send an autonomous web agent to interact with a website. "
            "Use this to: apply/RSVP to events (fill forms, click buttons), "
            "scrape attendee lists from event pages, extract info from profiles. "
            "The agent navigates the site autonomously."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "task": {"type": "string", "description": "What the agent should do"},
                "start_url": {"type": "string", "description": "URL to start from"},
                "max_steps": {"type": "integer", "default": 50},
                "output_schema": {"type": "object", "description": "Expected output structure"}
            },
            "required": ["task", "start_url"]
        }
    },
    {
        "name": "yutori_scout",
        "description": (
            "Set up continuous monitoring on a URL. The scout watches for changes "
            "and alerts when new events appear. Use this for platforms like Luma "
            "where new events appear frequently."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "task": {"type": "string"},
                "start_url": {"type": "string"},
                "schedule": {"type": "string", "enum": ["hourly", "every_6_hours", "daily"]}
            },
            "required": ["task", "start_url"]
        }
    },
    {
        "name": "fastino_extract",
        "description": (
            "Extract structured entities from text using GLiNER 2. "
            "Can extract: people, companies, job titles, topics, dates, etc. "
            "Can also classify text (event type, sentiment) and extract "
            "structured JSON (event metadata, person profiles). "
            "Very fast (<150ms). Use this before storing data in Neo4j."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "text": {"type": "string", "description": "Text to extract from"},
                "entity_types": {
                    "type": "array", "items": {"type": "string"},
                    "description": "Entity types to extract, e.g. ['person', 'company', 'topic']"
                },
                "structured_schema": {
                    "type": "object",
                    "description": "Optional: JSON schema for structured extraction"
                },
                "classify": {
                    "type": "object",
                    "description": "Optional: classification task, e.g. {'event_type': ['conference','meetup','dinner']}"
                }
            },
            "required": ["text"]
        }
    },
    {
        "name": "neo4j_query",
        "description": (
            "Query the Neo4j knowledge graph. Use Cypher queries to: "
            "find connections between people, check event history, "
            "find mutual connections, score relationship value, "
            "check if a person/event already exists, get user preferences. "
            "The graph contains: User, Event, Person, Company, Topic nodes."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "cypher": {"type": "string", "description": "Cypher query to execute"},
                "params": {"type": "object", "description": "Query parameters"}
            },
            "required": ["cypher"]
        }
    },
    {
        "name": "neo4j_write",
        "description": (
            "Write to the Neo4j knowledge graph. Create or update nodes and "
            "relationships: new events, people, companies, attendance records, "
            "feedback signals, social links, etc."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "cypher": {"type": "string", "description": "Cypher write query"},
                "params": {"type": "object"}
            },
            "required": ["cypher"]
        }
    },
    {
        "name": "google_calendar",
        "description": (
            "Interact with user's Google Calendar. Actions: "
            "'check_busy' — see if user is free at a given time, "
            "'create_event' — add event to calendar, "
            "'list_upcoming' — see what's coming up this week."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "action": {"type": "string", "enum": ["check_busy", "create_event", "list_upcoming"]},
                "event_data": {"type": "object", "description": "For create_event: title, start, end, location"},
                "time_range": {"type": "object", "description": "For check_busy/list: start and end datetime"}
            },
            "required": ["action"]
        }
    },
    {
        "name": "resolve_social_accounts",
        "description": (
            "Given a person's name + company/title, find their social media accounts. "
            "Searches for LinkedIn, X/Twitter, Instagram, GitHub profiles. "
            "Uses disambiguation to handle same-name people. "
            "Returns verified social links."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "name": {"type": "string"},
                "company": {"type": "string"},
                "title": {"type": "string"},
                "known_links": {"type": "array", "items": {"type": "string"}}
            },
            "required": ["name"]
        }
    },
    {
        "name": "reka_vision",
        "description": (
            "Analyze images or visual web content. Use this to: "
            "compare profile photos across platforms (same person?), "
            "analyze Instagram posts for conversation hooks, "
            "extract info from event flyers/images."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "url": {"type": "string", "description": "URL of image or page to analyze"},
                "prompt": {"type": "string", "description": "What to analyze/extract"}
            },
            "required": ["url", "prompt"]
        }
    },
    {
        "name": "draft_message",
        "description": (
            "Draft a personalized cold or follow-up message to a person. "
            "Provide full context: who they are, what event, why connect. "
            "Returns a draft that goes to user for approval — never auto-sends."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "recipient": {"type": "object", "description": "Person profile data"},
                "event": {"type": "object", "description": "Event context"},
                "message_type": {"type": "string", "enum": ["cold_pre_event", "followup_post_event", "missed_connection"]},
                "channel": {"type": "string", "enum": ["twitter_dm", "linkedin", "email", "instagram_dm"]},
                "tone": {"type": "string", "enum": ["casual", "professional", "friendly"]}
            },
            "required": ["recipient", "message_type", "channel"]
        }
    },
    {
        "name": "get_user_feedback",
        "description": (
            "Check for new user feedback: event accepts/rejects, message approvals/edits, "
            "preference updates. Returns pending actions the user has taken in the UI."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "since": {"type": "string", "description": "ISO datetime to check from"}
            }
        }
    },
    {
        "name": "notify_user",
        "description": (
            "Send a notification to the user's dashboard. "
            "Use this to surface event suggestions, draft messages, or status updates."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "type": {"type": "string", "enum": ["event_suggested", "event_applied", "message_drafted", "person_found", "status_update"]},
                "data": {"type": "object"},
                "priority": {"type": "string", "enum": ["low", "medium", "high"]}
            },
            "required": ["type", "data"]
        }
    },
    {
        "name": "wait",
        "description": (
            "Wait for a specified duration before the next action. "
            "Use this between cycles. The agent remains alive and resumes after."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "hours": {"type": "number", "description": "Hours to wait"},
                "reason": {"type": "string", "description": "Why waiting"}
            },
            "required": ["hours"]
        }
    }
]

# ── The System Prompt: Claude's Mission ──
SYSTEM_PROMPT = """You are NEXUS, an autonomous networking agent for {user_name}.
You run 24/7. Your mission: discover relevant events in {city}, apply to them,
research attendees, find their social accounts, draft personalized messages,
and learn from every interaction.

## Your User
- Name: {user_name}
- Role: {user_role} at {user_company}
- Product: {user_product}
- Interests: {user_interests}
- Networking goals: {user_goals}
- Target roles: {user_target_roles}
- Target companies: {user_target_companies}
- Preferred event types: {user_preferred_types}
- Max events/week: {max_events_week}
- Auto-apply threshold: {auto_apply_threshold}/100
- Suggest threshold: {suggest_threshold}/100
- Message tone: {message_tone}

## Your Tools
You have 13 tools. Use them in whatever order makes sense for the situation.
You are NOT following a fixed script — think about what the user needs RIGHT NOW
and pick the right tools.

## Rules
1. NEVER auto-send a message. Always draft → notify user → wait for approval.
2. When an event looks relevant (score > suggest_threshold), notify the user.
3. When an event is very relevant (score > auto_apply_threshold), apply AND notify.
4. Always check Google Calendar for conflicts before scheduling.
5. When researching a person, keep digging until you have enough for a good message.
   Don't stop at just a name and title — find their opinions, recent work, socials.
6. Learn from feedback. If user rejects "Web3" events, stop suggesting them.
7. After an event ends, generate follow-up messages for people worth connecting with.
8. When you have nothing urgent, look for unresearched attendees at upcoming events.
9. Save EVERYTHING to Neo4j — events, people, connections, feedback. The graph is
   your long-term memory.
10. Use Reka Vision to verify social accounts (same profile photo = same person).

## Your Loop
You run forever. Each cycle:
1. Check for user feedback (accepts, rejects, message edits)
2. Process feedback → update preferences in Neo4j
3. Search for new events
4. Analyze & score each event
5. Take action (apply, suggest, skip) based on score
6. For confirmed events: research attendees, find socials, draft messages
7. For ended events: draft follow-ups, save contacts
8. Wait, then repeat

But you're smart — if step 3 finds nothing new, skip to step 6.
If there are unresearched attendees, prioritize that over searching for new events.
THINK about what's most valuable to do right now.
"""


# ── The Agent Loop ──
class NexusAgent:
    """
    Claude-powered autonomous agent. Not a pipeline — a thinking agent
    that decides what to do next based on the full context.
    """

    def __init__(self, user_profile: dict):
        self.user = user_profile
        self.conversation_history = []
        self.running = True

    def build_system_prompt(self) -> str:
        return SYSTEM_PROMPT.format(**self.user)

    async def run_forever(self):
        """The main agent loop. Runs until stopped."""

        print(f"[NEXUS] Agent started for {self.user['user_name']}")
        print(f"[NEXUS] Brain: Claude claude-sonnet-4-5-20250514 | Tools: 13 | Mode: Autonomous")
        print(f"[NEXUS] Running forever. The agent thinks for itself.\n")

        # Initial kickoff message
        self.conversation_history = [
            {
                "role": "user",
                "content": (
                    f"You just started. Current time: {datetime.now().isoformat()}. "
                    f"Begin your autonomous cycle. Check for any pending feedback, "
                    f"then search for new events in {self.user['city']}. "
                    f"Think step by step about what to do."
                )
            }
        ]

        while self.running:
            try:
                # Claude thinks and acts
                response = client.messages.create(
                    model="claude-sonnet-4-5-20250514",
                    max_tokens=4096,
                    system=self.build_system_prompt(),
                    tools=TOOLS,
                    messages=self.conversation_history
                )

                # Process Claude's response
                assistant_message = {"role": "assistant", "content": response.content}
                self.conversation_history.append(assistant_message)

                # Handle tool calls
                if response.stop_reason == "tool_use":
                    tool_results = []
                    for block in response.content:
                        if block.type == "tool_use":
                            print(f"[AGENT] Using tool: {block.name}")
                            print(f"         Input: {json.dumps(block.input, indent=2)[:200]}...")

                            # Execute the tool
                            result = await self.execute_tool(block.name, block.input)

                            tool_results.append({
                                "type": "tool_result",
                                "tool_use_id": block.id,
                                "content": json.dumps(result)
                            })

                            # Special: if agent chose to wait, actually sleep
                            if block.name == "wait":
                                hours = block.input.get("hours", 1)
                                reason = block.input.get("reason", "cycle complete")
                                print(f"[AGENT] Waiting {hours}h — {reason}")
                                await asyncio.sleep(hours * 3600)

                    # Feed tool results back to Claude
                    self.conversation_history.append({
                        "role": "user",
                        "content": tool_results
                    })

                elif response.stop_reason == "end_turn":
                    # Claude finished thinking, feed it a new cycle prompt
                    for block in response.content:
                        if hasattr(block, "text"):
                            print(f"[AGENT] Thinking: {block.text[:200]}...")

                    # Continue the loop with context
                    self.conversation_history.append({
                        "role": "user",
                        "content": (
                            f"Current time: {datetime.now().isoformat()}. "
                            f"Continue your autonomous cycle. What should you do next?"
                        )
                    })

                # Trim history to avoid context overflow (keep last 50 turns)
                if len(self.conversation_history) > 100:
                    # Keep system-critical context, trim old tool results
                    self.conversation_history = (
                        self.conversation_history[:2] +  # initial messages
                        self.conversation_history[-50:]    # recent context
                    )

            except Exception as e:
                print(f"[AGENT] Error: {e}. Recovering in 60s...")
                await asyncio.sleep(60)

    async def execute_tool(self, tool_name: str, tool_input: dict) -> dict:
        """Route tool calls to actual implementations."""

        if tool_name == "tavily_search":
            return await execute_tavily_search(tool_input)
        elif tool_name == "yutori_browse":
            return await execute_yutori_browse(tool_input)
        elif tool_name == "yutori_scout":
            return await execute_yutori_scout(tool_input)
        elif tool_name == "fastino_extract":
            return await execute_fastino_extract(tool_input)
        elif tool_name == "neo4j_query":
            return await execute_neo4j_query(tool_input)
        elif tool_name == "neo4j_write":
            return await execute_neo4j_write(tool_input)
        elif tool_name == "google_calendar":
            return await execute_google_calendar(tool_input)
        elif tool_name == "resolve_social_accounts":
            return await execute_resolve_social(tool_input)
        elif tool_name == "reka_vision":
            return await execute_reka_vision(tool_input)
        elif tool_name == "draft_message":
            return await execute_draft_message(tool_input)
        elif tool_name == "get_user_feedback":
            return await execute_get_feedback(tool_input)
        elif tool_name == "notify_user":
            return await execute_notify_user(tool_input)
        elif tool_name == "wait":
            return {"status": "waited", "hours": tool_input.get("hours", 1)}
        else:
            return {"error": f"Unknown tool: {tool_name}"}


# ── Entry Point ──
async def main():
    user = await load_user_profile_from_db()
    agent = NexusAgent(user)
    await agent.run_forever()

if __name__ == "__main__":
    asyncio.run(main())
```

### What a Real Agent Cycle Looks Like

This is not scripted. This is Claude actually thinking:

```
[AGENT] Thinking: "It's 6:00 AM. Let me start by checking if the user
         gave any feedback overnight..."

[AGENT] Using tool: get_user_feedback
         Input: {"since": "2026-02-26T18:00:00"}
         Result: User rejected "SF Web3 Mixer" — reason: "not my industry"
                 User approved message to Sarah Chen — sent via LinkedIn
                 User edited message to Marcus Johnson — changed tone

[AGENT] Thinking: "User rejected Web3 again. That's the 3rd Web3 rejection.
         I need to update their preferences to deprioritize Web3/crypto events.
         Also, the message edit tells me they prefer a more casual tone with CTOs."

[AGENT] Using tool: neo4j_write
         Input: {cypher: "MATCH (u:User {id: $id}) SET u.avoided_topics =
                 u.avoided_topics + ['web3', 'crypto']..."}

[AGENT] Thinking: "Now let me search for new events this week..."

[AGENT] Using tool: tavily_search
         Input: {"query": "SF AI startup events this week February 2026",
                 "search_depth": "advanced", "include_domains": ["lu.ma", "eventbrite.com"]}
         Result: Found 6 events

[AGENT] Thinking: "Found 6 events. Let me extract entities from each one
         and score them. The AI Founders Dinner looks very relevant —
         let me check the details..."

[AGENT] Using tool: fastino_extract
         Input: {"text": "AI Founders Dinner — intimate gathering of 30 founders
                  and investors...", "entity_types": ["person", "company", "topic"]}
         Result: speakers: ["Sarah Chen (Sequoia)", "James Liu (a16z)"],
                 topics: ["AI agents", "fundraising"]

[AGENT] Thinking: "Score: AI topics match (✓), Sequoia + a16z are target
         companies (✓), dinner format is preferred (✓), Thursday evening (✓).
         This is easily 90+. But wait — let me check the calendar first."

[AGENT] Using tool: google_calendar
         Input: {"action": "check_busy", "time_range": {"start": "2026-02-28T19:00",
                 "end": "2026-02-28T22:00"}}
         Result: Free

[AGENT] Thinking: "Calendar is clear. Score is high. Auto-applying."

[AGENT] Using tool: yutori_browse
         Input: {"task": "Apply to this event. Fill in: Name: John Park,
                  Role: CEO at BuildAI...", "start_url": "https://lu.ma/ai-dinner-sf"}
         Result: {"status": "applied", "confirmation_id": "EVT-2894"}

[AGENT] Using tool: google_calendar
         Input: {"action": "create_event", "event_data": {"title": "AI Founders Dinner",
                 "start": "2026-02-28T19:00", "location": "The Battery, SF"}}

[AGENT] Using tool: notify_user
         Input: {"type": "event_applied", "data": {"title": "AI Founders Dinner",
                 "score": 92, "confirmation": "EVT-2894"}, "priority": "high"}

[AGENT] Thinking: "Applied and scheduled. Now the attendee list should be
         visible since I'm registered. Let me scrape it."

[AGENT] Using tool: yutori_browse
         Input: {"task": "I'm registered for this event. Go to the guest list
                  and extract all attendee names, titles, and companies.",
                 "start_url": "https://lu.ma/ai-dinner-sf"}
         Result: 28 attendees found

[AGENT] Thinking: "28 attendees. Let me research the most interesting ones.
         Sarah Chen from Sequoia — the user wants to meet VCs. Let me dig
         deep on her. Starting with basic search..."

[AGENT] Using tool: tavily_search
         Input: {"query": "Sarah Chen Sequoia Capital Partner investments 2025 2026"}

[AGENT] Thinking: "Got her basic profile but I don't have her recent opinions
         or social accounts yet. Need to go deeper."

[AGENT] Using tool: tavily_search
         Input: {"query": "Sarah Chen Sequoia AI agents podcast interview opinion"}

[AGENT] Using tool: resolve_social_accounts
         Input: {"name": "Sarah Chen", "company": "Sequoia Capital", "title": "Partner"}
         Result: {"linkedin": "linkedin.com/in/sarahchen-seq",
                  "twitter": "x.com/sarahchen_vc",
                  "instagram": null}

[AGENT] Using tool: reka_vision
         Input: {"url": "x.com/sarahchen_vc",
                 "prompt": "What topics does this person tweet about? Recent interests?"}
         Result: "AI agents, developer tools, recently tweeted about agent UX..."

[AGENT] Thinking: "Now I have enough for a great message. She recently tweeted
         about agent UX — and the user is building an AI agent product. Perfect hook."

[AGENT] Using tool: draft_message
         Input: {"recipient": {"name": "Sarah Chen", "role": "Partner", ...},
                 "message_type": "cold_pre_event",
                 "channel": "twitter_dm", "tone": "casual"}
         Result: Draft saved

[AGENT] Using tool: notify_user
         Input: {"type": "message_drafted", "data": {"to": "Sarah Chen",
                 "channel": "twitter_dm", "event": "AI Founders Dinner"}}

[AGENT] Thinking: "Sarah Chen done. Let me research the next high-value
         attendee... James Liu from a16z. Same process."

... (continues researching attendees) ...

[AGENT] Thinking: "Researched top 5 attendees. 3 message drafts ready.
         Let me check — are there any events from yesterday that I need
         to send follow-ups for?"

[AGENT] Using tool: neo4j_query
         Input: {cypher: "MATCH (e:Event) WHERE e.date < datetime()
                  AND e.status = 'attended' AND NOT e.followed_up
                  RETURN e"}
         Result: "DevTools SF Meetup (yesterday)"

[AGENT] Thinking: "Yesterday's meetup — I should draft follow-ups.
         Who did the user meet?"

... (generates follow-up messages) ...

[AGENT] Thinking: "All done for this cycle. Nothing urgent left.
         Next discovery should happen in about 4 hours.
         Let me wait."

[AGENT] Using tool: wait
         Input: {"hours": 4, "reason": "cycle complete, next discovery in 4h"}
```

---

## Sponsor Tool Integration

### Tool 1: Tavily Search API

**Role:** Event discovery + People research

| Usage | Endpoint | Config |
|-------|----------|--------|
| Event discovery | `POST /search` | `search_depth: "advanced"`, `topic: "general"`, `include_domains: [event platforms]` |
| People research | `POST /search` | `search_depth: "advanced"`, `include_answer: true`, `include_raw_content: "markdown"` |
| Trend monitoring | `POST /search` | `topic: "news"`, `time_range: "day"` |

**Auth:** Bearer token `tvly-{API_KEY}`

**Why Tavily:** The `/search` endpoint with `advanced` depth + `include_answer` gives structured, AI-summarized results perfect for agent consumption. The `include_domains` filter lets us target specific event platforms. The `/research` endpoint could power deep-dive people analysis.

### Tool 2: Neo4j (AuraDB)

**Role:** Knowledge graph for events, people, companies, relationships

**Schema:**

```cypher
// Node types
(:User {id, name, role, company, product, interests[], goals[]})
(:Event {url, title, date, location, type, score, status})
(:Person {name, title, company, linkedin, twitter})
(:Company {name, industry, stage, size})
(:Topic {name, category})
(:Role {name})  // e.g., "investor", "founder", "engineer"

// Relationship types
(:User)-[:INTERESTED_IN {weight}]->(:Topic)
(:User)-[:WANTS_TO_MEET]->(:Role)
(:User)-[:TARGETS]->(:Company)
(:User)-[:ATTENDED {feedback, rating}]->(:Event)
(:User)-[:REJECTED {reason, timestamp}]->(:Event)
(:User)-[:KNOWS {strength}]->(:Person)
(:Event)-[:HAS_SPEAKER]->(:Person)
(:Event)-[:TAGGED]->(:Topic)
(:Person)-[:WORKS_AT]->(:Company)
(:Person)-[:EXPERT_IN]->(:Topic)
(:Person)-[:CONNECTED_TO {source}]->(:Person)
(:Company)-[:IN_INDUSTRY]->(:Topic)
```

**Why Neo4j:** Graph queries are perfect for "find people who share interests with me AND attend the same event AND work at companies I'm targeting" — impossible to do efficiently in SQL. The relationship traversal is the killer feature for networking intelligence.

### Tool 3: Yutori API

**Role:** Autonomous web browsing (apply to events) + continuous monitoring (discover events)

| API | Usage | Key Config |
|-----|-------|-----------|
| **Browsing API** | Auto-apply/RSVP to events | `POST /v1/browsing/tasks` — fills forms, clicks buttons, handles waitlists |
| **Scouting API** | Monitor event platforms for new events | Scheduled monitoring with webhook callbacks |
| **Research API** | Deep research on venues/events | One-time research tasks with 100+ MCP tools |

**Auth:** `X-API-Key` header

**Why Yutori:** Navigator can actually *do things* on websites — fill application forms, RSVP, join waitlists. No other tool in the sponsor list can autonomously interact with web UIs. The Scouting API makes discovery truly autonomous (push-based, not pull-based).

### Tool 4: Fastino GLiNER (Bonus)

**Role:** Entity extraction from event pages and people profiles

| Mode | Usage |
|------|-------|
| `ner` | Extract person names, companies, job titles, technologies, topics from raw event text |
| `structured` | Parse event pages into structured schema (date, time, speakers, capacity, etc.) |
| `classification` | Classify event type (networking, conference, workshop, dinner, etc.) |

**Why Fastino:** GLiNER runs in <150ms on CPU. We process hundreds of events — fast, structured extraction without LLM inference costs is critical. Also powers social media account disambiguation (is this LinkedIn "Sarah Chen" the same person?).

### Tool 5: Render (Deployment + Background Workers)

**Role:** Host the entire stack — frontend, backend API, and the **always-on daemon worker**

| Service | Render Type | Purpose |
|---------|-------------|---------|
| `nexus-web` | Web Service (Node) | Next.js frontend dashboard |
| `nexus-api` | Web Service (Python) | FastAPI backend |
| `nexus-daemon` | **Background Worker** | The autonomous agent loop that never stops |
| `nexus-db` | PostgreSQL | App state, user profiles, event history |

**Why Render:** The Background Worker is critical — it's what makes the agent truly autonomous. Not a cron job. Not a lambda. A persistent process that runs the discovery→analyze→act→connect loop 24/7. Render's worker type is perfect for this.

### Tool 6: Reka Vision (Social Verification + Content Analysis)

**Role:** Visual intelligence for profile verification and social media content analysis

| Use Case | How |
|----------|-----|
| **Profile photo cross-verification** | Same person across LinkedIn, X, Instagram? Compare profile pictures. |
| **Instagram content analysis** | Analyze stories, reels, carousel posts to understand a person's interests, lifestyle, recent activities |
| **Event page screenshot analysis** | Extract info from event flyers/images that text scraping misses |

**Why Reka Vision:** When you find 3 "Sarah Chen" profiles on X, Reka Vision can compare the profile photo against her LinkedIn photo and tell you which one is the real match. Also, analyzing someone's Instagram gives conversation hooks no text search can provide ("saw you were in Tokyo last week — how was it?").

```python
# Reka Vision - Instagram content analysis for conversation hooks
async def analyze_social_content(person: PersonProfile) -> list[str]:
    """Analyze a person's public Instagram/X posts for conversation hooks."""

    hooks = []

    if person.social_links.instagram:
        # Use Reka Vision to understand their recent visual content
        analysis = await reka.vision.analyze(
            url=person.social_links.instagram,
            prompt=(
                "Analyze this person's recent public posts. "
                "What are their interests? Recent trips? "
                "Hobbies? Events they attended? "
                "Extract 3-5 specific conversation starters."
            )
        )
        hooks.extend(analysis.get("conversation_hooks", []))

    if person.social_links.twitter:
        # Analyze pinned tweet / recent tweets visually
        analysis = await reka.vision.analyze(
            url=person.social_links.twitter,
            prompt=(
                "What is this person passionate about based on their "
                "recent tweets? What topics do they engage with most?"
            )
        )
        hooks.extend(analysis.get("conversation_hooks", []))

    return hooks
```

---

## Feedback Loop & Personalization Engine

This is the core differentiator. NEXUS learns from every user interaction.

### Feedback Signals

```
┌─────────────────────────────────────────────────────────┐
│                   FEEDBACK SIGNALS                       │
│                                                          │
│  EXPLICIT SIGNALS (user actively provides)               │
│  ├── Accept/Reject event recommendation                  │
│  ├── Rejection reason (dropdown + free text)             │
│  │   ├── "Not my industry"                               │
│  │   ├── "Bad timing"                                    │
│  │   ├── "Too expensive"                                 │
│  │   ├── "Don't like the format"                         │
│  │   ├── "Already going to something"                    │
│  │   └── Custom reason                                   │
│  ├── Edit suggested cold message before sending          │
│  ├── Rate attended event (1-5 stars)                     │
│  ├── Mark person as "want to meet" / "not interested"    │
│  ├── Update profile (interests, role, goals)             │
│  └── Set preferences (max events/week, budget, etc.)     │
│                                                          │
│  IMPLICIT SIGNALS (system observes)                      │
│  ├── Time spent viewing event detail                     │
│  ├── Events clicked but not accepted                     │
│  ├── Messages approved vs edited vs rejected             │
│  ├── Calendar conflicts (busy times)                     │
│  ├── Event attendance pattern (day of week, time)        │
│  └── Response rate to sent messages                      │
└─────────────────────────────────────────────────────────┘
```

### Preference Learning Model

```python
class PreferenceEngine:
    """Learns user preferences from feedback signals."""

    def __init__(self, user_id: str):
        self.user_id = user_id
        self.weights = ScoringWeights(
            topic_weight=30.0,     # adjusts based on topic accept/reject ratio
            people_weight=25.0,    # adjusts based on people-driven acceptances
            type_weight=15.0,      # adjusts based on event type preferences
            time_weight=15.0,      # adjusts based on time pattern
            history_weight=15.0    # adjusts based on similar event history
        )

    async def process_feedback(self, feedback: Feedback):
        """Update preference model based on user feedback."""

        event = await get_event(feedback.event_id)

        if feedback.action == "reject":
            # Decrease weight for matching attributes
            for topic in event.topics:
                await self.adjust_topic_affinity(topic, delta=-0.1)

            if feedback.reason == "bad_timing":
                await self.update_time_preferences(event.datetime, negative=True)
            elif feedback.reason == "not_my_industry":
                for topic in event.topics:
                    await self.adjust_topic_affinity(topic, delta=-0.5)
            elif feedback.reason == "too_expensive":
                await self.lower_budget_threshold(event.price)

            # Store in Neo4j for graph-based learning
            await neo4j_session.run("""
                MATCH (u:User {id: $user_id}), (e:Event {id: $event_id})
                CREATE (u)-[:REJECTED {
                    reason: $reason,
                    timestamp: datetime(),
                    feedback_text: $text
                }]->(e)
            """, {
                "user_id": self.user_id,
                "event_id": feedback.event_id,
                "reason": feedback.reason,
                "text": feedback.free_text
            })

        elif feedback.action == "accept":
            # Increase weight for matching attributes
            for topic in event.topics:
                await self.adjust_topic_affinity(topic, delta=+0.3)
            await self.update_time_preferences(event.datetime, negative=False)

            # Reinforce in Neo4j
            await neo4j_session.run("""
                MATCH (u:User {id: $user_id}), (e:Event {id: $event_id})
                CREATE (u)-[:ACCEPTED {timestamp: datetime()}]->(e)
            """, {"user_id": self.user_id, "event_id": feedback.event_id})

        # Recalculate weights using accept/reject history
        await self.recalculate_weights()

    async def recalculate_weights(self):
        """Recalibrate scoring weights based on full feedback history."""

        # Query Neo4j for patterns
        history = await neo4j_session.run("""
            MATCH (u:User {id: $user_id})-[r:ACCEPTED|REJECTED]->(e:Event)
            MATCH (e)-[:TAGGED]->(t:Topic)
            RETURN type(r) as action,
                   e.type as event_type,
                   collect(t.name) as topics,
                   e.date.hour as hour,
                   e.date.dayOfWeek as day
            ORDER BY r.timestamp DESC
            LIMIT 100
        """, {"user_id": self.user_id})

        # Compute acceptance rates per dimension
        topic_rates = compute_acceptance_rate_by(history, "topics")
        type_rates = compute_acceptance_rate_by(history, "event_type")
        time_rates = compute_acceptance_rate_by(history, "hour")

        # Adjust weights — dimensions with higher variance get more weight
        self.weights = rebalance_weights(topic_rates, type_rates, time_rates)
```

### User Profile Schema

```typescript
interface UserProfile {
  // Identity
  id: string;
  name: string;
  email: string;

  // Professional
  role: string;                    // "Founder & CEO"
  company: string;                 // "MyStartup"
  product_description: string;     // "AI-powered CRM for SMBs"
  linkedin: string;
  twitter: string;

  // Networking Goals
  networking_goals: string[];      // ["find investors", "hire engineers", "find customers"]
  target_roles: string[];          // ["VC Partner", "Senior Engineer", "CTO"]
  target_companies: string[];      // ["Sequoia", "a16z", "Google"]
  target_industries: string[];     // ["AI/ML", "SaaS", "Developer Tools"]

  // Preferences (learned + explicit)
  interests: string[];             // ["AI agents", "developer tools", "fundraising"]
  preferred_event_types: string[]; // ["dinner", "meetup", "conference"]
  max_events_per_week: number;     // 4
  max_event_spend: number;         // 50 (USD per event)
  preferred_days: string[];        // ["tuesday", "thursday"]
  preferred_times: string[];       // ["evening"]
  message_tone: string;            // "casual" | "professional" | "friendly"

  // Auto-action thresholds (adjusted by feedback loop)
  auto_apply_threshold: number;    // 80 (score 80+ = auto-apply)
  suggest_threshold: number;       // 50 (score 50+ = suggest)
  auto_schedule_threshold: number; // 85 (score 85+ = auto-add to calendar)
}
```

---

## Data Models

### Core Entities

```typescript
// Event lifecycle: discovered → analyzed → suggested → accepted/rejected → applied → confirmed → attended → rated
interface Event {
  id: string;
  url: string;
  title: string;
  description: string;
  source: "eventbrite" | "luma" | "meetup" | "partiful" | "twitter" | "other";

  // Extracted by Fastino GLiNER
  event_type: "conference" | "meetup" | "dinner" | "workshop" | "happy_hour" | "demo_day";
  date: DateTime;
  end_date?: DateTime;
  location: string;
  capacity?: number;
  price?: number;
  speakers: Person[];
  topics: string[];
  target_audience: string;
  application_required: boolean;

  // Computed by Analyze Agent
  relevance_score: number;         // 0-100

  // Status tracking
  status: "discovered" | "analyzed" | "suggested" | "accepted" | "rejected" | "applied" | "confirmed" | "waitlisted" | "attended" | "skipped";

  rejection_reason?: string;
  application_result?: {
    status: "applied" | "waitlisted" | "failed" | "payment_required";
    confirmation_id?: string;
    yutori_task_id: string;
  };
  calendar_event_id?: string;
  user_rating?: number;            // 1-5 post-attendance

  created_at: DateTime;
  updated_at: DateTime;
}

interface Person {
  id: string;
  name: string;
  title?: string;
  company?: string;
  linkedin?: string;
  twitter?: string;

  // Computed
  connection_score: number;        // how valuable is this connection
  mutual_connections: Person[];
  shared_topics: string[];
  research_summary?: string;       // from Tavily deep research
}

interface ColdMessage {
  id: string;
  recipient: Person;
  event: Event;                    // context: which event triggered this
  channel: "twitter_dm" | "linkedin" | "email";
  content: string;

  status: "draft" | "approved" | "edited" | "sent" | "rejected";
  user_edits?: string;            // if user edited before sending
  sent_at?: DateTime;
  response_received?: boolean;
}

interface Feedback {
  id: string;
  user_id: string;
  event_id?: string;
  person_id?: string;
  message_id?: string;

  action: "accept" | "reject" | "edit" | "rate" | "skip";
  reason?: string;
  free_text?: string;
  rating?: number;

  created_at: DateTime;
}
```

---

## UI/UX Design

### Screen 1: Dashboard (Main Feed)

```
┌──────────────────────────────────────────────────────────┐
│  NEXUS                          [Profile] [Settings] [?] │
├──────────────────────────────────────────────────────────┤
│                                                          │
│  📊 This Week: 3 events scheduled | 2 pending review    │
│  ─────────────────────────────────────────────────────── │
│                                                          │
│  ┌────────────────────────────────────────────────────┐  │
│  │ NEW  SF AI Founders Dinner           Score: 92/100 │  │
│  │      Thu Feb 28 · 7:00 PM · SOMA                   │  │
│  │      12 attendees · 3 people you should meet        │  │
│  │                                                      │  │
│  │      [✓ Accept & Apply]  [✗ Skip]  [Later]         │  │
│  │      Why recommended: Matches "AI", "founders"...   │  │
│  └────────────────────────────────────────────────────┘  │
│                                                          │
│  ┌────────────────────────────────────────────────────┐  │
│  │ AUTO-APPLIED  Startup Grind SF Monthly  Score: 85  │  │
│  │      ✓ Applied · Calendar synced                    │  │
│  │      Wed Mar 5 · 6:30 PM · Financial District      │  │
│  │      5 high-value connections identified            │  │
│  │                                                      │  │
│  │      [View People] [View Messages] [Remove]         │  │
│  └────────────────────────────────────────────────────┘  │
│                                                          │
│  ┌────────────────────────────────────────────────────┐  │
│  │ PENDING  DevTools SF Meetup             Score: 67  │  │
│  │      Mon Mar 3 · 6:00 PM · Mission                 │  │
│  │      8 attendees                                    │  │
│  │                                                      │  │
│  │      [✓ Apply]  [✗ Skip]  [Tell me more]           │  │
│  └────────────────────────────────────────────────────┘  │
│                                                          │
│  ── Rejected ──────────────────────────────────────────  │
│  │ Web3 Mixer (Score: 45) - Skipped: "not my industry" │ │
│  │ Yoga Retreat (Score: 22) - Auto-skipped              │ │
│                                                          │
└──────────────────────────────────────────────────────────┘
```

### Screen 2: Event Detail + People

```
┌──────────────────────────────────────────────────────────┐
│  ← Back    SF AI Founders Dinner           Score: 92    │
├──────────────────────────────────────────────────────────┤
│                                                          │
│  Thu Feb 28 · 7:00 PM - 10:00 PM                        │
│  The Battery, 717 Battery St, San Francisco              │
│  Capacity: 40 · Price: Free · Format: Dinner             │
│  Topics: AI Agents, Fundraising, B2B SaaS                │
│                                                          │
│  Status: ✓ Applied (confirmation #EVT-2894)              │
│  Calendar: ✓ Synced to Google Calendar                   │
│                                                          │
│  ─── People You Should Meet ────────────────────────     │
│                                                          │
│  ┌──────────────────────────────────────────────────┐    │
│  │ 1. Sarah Chen · Partner @ Sequoia                 │    │
│  │    Connection Score: 95                            │    │
│  │    Why: Invests in AI/SaaS · 2 mutual connections │    │
│  │    Shared interests: AI agents, developer tools   │    │
│  │                                                    │    │
│  │    Draft Message:                                  │    │
│  │    "Hi Sarah, I'll be at the AI Founders Dinner   │    │
│  │     Thursday — would love to chat about what       │    │
│  │     you're seeing in the AI agent space. I'm       │    │
│  │     building [product] and think there's an        │    │
│  │     interesting angle on..."                       │    │
│  │                                                    │    │
│  │    [✓ Send via LinkedIn] [✎ Edit] [✗ Skip]       │    │
│  └──────────────────────────────────────────────────┘    │
│                                                          │
│  ┌──────────────────────────────────────────────────┐    │
│  │ 2. Marcus Johnson · CTO @ BuildAI                 │    │
│  │    Connection Score: 78                            │    │
│  │    Why: Building similar product · shared investor │    │
│  │    ...                                             │    │
│  └──────────────────────────────────────────────────┘    │
│                                                          │
└──────────────────────────────────────────────────────────┘
```

### Screen 3: People Graph (Neo4j Visualization)

```
┌──────────────────────────────────────────────────────────┐
│  ← Back    Your Network Graph                            │
├──────────────────────────────────────────────────────────┤
│                                                          │
│  Filter: [All] [Want to Meet] [Met] [Connected]          │
│                                                          │
│           ┌─────┐                                        │
│           │ YOU │                                        │
│           └──┬──┘                                        │
│         ┌────┼────────┐                                  │
│         │    │        │                                  │
│      ┌──▼──┐│  ┌─────▼────┐                             │
│      │Sarah││  │ AI Agents│                              │
│      │Chen ││  │  (topic) │                              │
│      └──┬──┘│  └─────┬────┘                              │
│         │   │        │                                   │
│    ┌────▼───▼──┐  ┌──▼─────┐                             │
│    │ Sequoia   │  │Marcus  │                              │
│    │(company)  │  │Johnson │                              │
│    └───────────┘  └────────┘                              │
│                                                          │
│  Interactive: Click any node to see details              │
│  Powered by Neo4j graph visualization                    │
│                                                          │
└──────────────────────────────────────────────────────────┘
```

### Screen 4: Onboarding / Profile Setup

```
┌──────────────────────────────────────────────────────────┐
│  Welcome to NEXUS                                        │
│  Let's set up your autonomous networking agent           │
├──────────────────────────────────────────────────────────┤
│                                                          │
│  Step 1 of 4: About You                                  │
│                                                          │
│  Name: [________________________]                        │
│  Role: [________________________] (e.g., Founder & CEO)  │
│  Company: [_____________________]                        │
│  Your product (1-2 sentences):                           │
│  [___________________________________________________]   │
│  [___________________________________________________]   │
│                                                          │
│  LinkedIn: [________________________]                    │
│  Twitter:  [________________________]                    │
│  Email:    [________________________]                    │
│                                                          │
│                                          [Next →]        │
├──────────────────────────────────────────────────────────┤
│                                                          │
│  Step 2 of 4: Networking Goals                           │
│                                                          │
│  What are you looking for? (select all that apply)       │
│  [x] Find investors / fundraise                          │
│  [x] Hire talent                                         │
│  [ ] Find co-founder                                     │
│  [x] Meet potential customers                            │
│  [ ] Learn / upskill                                     │
│  [ ] Find mentors                                        │
│  [ ] General networking                                  │
│  [ ] Other: [_______________]                            │
│                                                          │
│  Who do you want to meet? (roles)                        │
│  [VC Partner] [x] [Engineer] [x] [Founder] [x]          │
│  [Product Manager] [ ] [Designer] [ ] [Other: ____]     │
│                                                          │
│  Target companies (optional):                            │
│  [Sequoia, a16z, Y Combinator, Google, ___________]     │
│                                                          │
├──────────────────────────────────────────────────────────┤
│                                                          │
│  Step 3 of 4: Event Preferences                          │
│                                                          │
│  Interests / Topics:                                     │
│  [AI/ML] [x] [SaaS] [x] [Web3] [ ] [DevTools] [x]     │
│  [Fintech] [ ] [Healthcare] [ ] [Add custom: _____]     │
│                                                          │
│  Event types I like:                                     │
│  [Dinner] [x] [Meetup] [x] [Conference] [ ]            │
│  [Happy Hour] [x] [Workshop] [ ] [Demo Day] [x]        │
│                                                          │
│  Max events per week: [  4  ]                            │
│  Max spend per event: [$ 50 ]                            │
│  Preferred days: [Tue] [x] [Thu] [x] [Fri] [x]         │
│  Preferred times: [Morning] [ ] [Evening] [x]           │
│                                                          │
├──────────────────────────────────────────────────────────┤
│                                                          │
│  Step 4 of 4: Automation Level                           │
│                                                          │
│  How autonomous should NEXUS be?                         │
│                                                          │
│  Event Applications:                                     │
│  ( ) Full auto — apply to everything above threshold     │
│  (x) Semi-auto — apply to high-score, ask for medium     │
│  ( ) Manual — always ask me first                        │
│                                                          │
│  Calendar:                                               │
│  (x) Auto-sync confirmed events                          │
│  ( ) Ask before adding to calendar                       │
│                                                          │
│  Cold Messages:                                          │
│  ( ) Auto-send approved messages                         │
│  (x) Always show me drafts first                         │
│  ( ) Don't send messages for me                          │
│                                                          │
│  [Connect Google Calendar]  [Connect LinkedIn]           │
│                                                          │
│                               [Launch NEXUS →]           │
└──────────────────────────────────────────────────────────┘
```

### Screen 5: Settings / Feedback Dashboard

```
┌──────────────────────────────────────────────────────────┐
│  Settings & Insights                                     │
├──────────────────────────────────────────────────────────┤
│                                                          │
│  ── Agent Performance ──────────────────────────────     │
│  Events discovered this month:  47                       │
│  Events recommended:            18                       │
│  Events you accepted:           12 (67% accept rate)     │
│  Applications submitted:        12                       │
│  Applications confirmed:        10 (83% success)         │
│  Messages sent:                 8                        │
│  Messages with responses:       5  (63% response rate)   │
│                                                          │
│  ── Learned Preferences ────────────────────────────     │
│  Top topics: AI Agents (0.92), DevTools (0.85),          │
│              Fundraising (0.78)                           │
│  Avoided topics: Web3 (0.12), Crypto (0.08)              │
│  Best days: Thursday (0.90), Tuesday (0.85)              │
│  Best times: 6-8 PM (0.95)                               │
│  Preferred format: Dinner (0.88), Meetup (0.72)          │
│                                                          │
│  [Reset Preferences] [Export Data] [Pause Agent]         │
│                                                          │
│  ── Automation Thresholds ──────────────────────────     │
│  Auto-apply above:    [====|====80=====] 80/100          │
│  Suggest above:       [==|=====50======] 50/100          │
│  Auto-schedule above: [=====|===85=====] 85/100          │
│                                                          │
│  ── Integrations ───────────────────────────────────     │
│  Google Calendar: ✓ Connected                            │
│  LinkedIn:        ✓ Connected (for messages)             │
│  Twitter/X:       ○ Not connected [Connect]              │
│                                                          │
└──────────────────────────────────────────────────────────┘
```

---

## API Specifications

### Backend REST API

```yaml
# Event Endpoints
GET    /api/events                    # List events (with filters)
GET    /api/events/:id                # Event detail
POST   /api/events/:id/accept         # Accept event recommendation
POST   /api/events/:id/reject         # Reject with reason
POST   /api/events/:id/apply          # Manually trigger apply
GET    /api/events/:id/people         # People at this event
POST   /api/events/:id/rate           # Post-event rating

# People Endpoints
GET    /api/people                    # List discovered people
GET    /api/people/:id                # Person detail + research
GET    /api/people/:id/graph          # Person's graph connections
POST   /api/people/:id/mark           # Mark as "want to meet" / "not interested"

# Message Endpoints
GET    /api/messages                  # List draft/sent messages
GET    /api/messages/:id              # Message detail
POST   /api/messages/:id/approve      # Approve and send
POST   /api/messages/:id/edit         # Edit then send
POST   /api/messages/:id/reject       # Reject message

# Profile Endpoints
GET    /api/profile                   # Get user profile
PUT    /api/profile                   # Update profile
GET    /api/profile/preferences       # Get learned preferences
PUT    /api/profile/preferences       # Override preferences

# Feedback Endpoints
POST   /api/feedback                  # Submit any feedback signal
GET    /api/feedback/stats            # Feedback analytics

# Graph Endpoints
GET    /api/graph/network             # Full network graph data
GET    /api/graph/suggestions         # Graph-based suggestions

# Webhook Endpoints (internal)
POST   /webhooks/yutori/new-event     # Yutori Scout webhook
POST   /webhooks/yutori/apply-result  # Yutori Browsing result
POST   /webhooks/google/calendar      # Calendar sync webhook

# Agent Control
GET    /api/agent/status              # Agent health/status
POST   /api/agent/pause               # Pause all agents
POST   /api/agent/resume              # Resume agents
POST   /api/agent/run-now             # Force discovery cycle
```

### WebSocket Events (Real-time UI updates)

```typescript
// Server → Client events
interface WSEvents {
  "event:discovered": { event: Event };                    // new event found
  "event:analyzed": { event: Event; score: number };       // event scored
  "event:applied": { event: Event; result: string };       // application result
  "event:scheduled": { event: Event; calendar_id: string };// calendar synced
  "person:discovered": { person: Person; event: Event };   // new person found
  "message:drafted": { message: ColdMessage };             // new draft ready
  "message:sent": { message: ColdMessage };                // message sent
  "agent:status": { agent: string; status: string };       // agent health
}
```

---

## Implementation Plan

### Phase 0: Setup (30 min)

```
- [ ] Initialize Next.js project with TypeScript
- [ ] Set up FastAPI backend
- [ ] Provision Neo4j AuraDB (free tier: 200k nodes)
- [ ] Obtain API keys: Tavily, Yutori, Fastino
- [ ] Set up Google Calendar OAuth
- [ ] Deploy skeleton to Render (sponsor tool for hosting)
```

### Phase 1: Core Pipeline — Discovery + Analysis (1.5 hours)

```
- [ ] Implement Discovery Agent
  - [ ] Tavily Search integration (event queries)
  - [ ] Yutori Scouting setup (continuous monitoring)
  - [ ] Event deduplication logic
- [ ] Implement Analyze Agent
  - [ ] Fastino GLiNER entity extraction
  - [ ] Neo4j schema creation + graph population
  - [ ] Relevance scoring engine
- [ ] Wire up Discovery → Analysis pipeline
- [ ] Test: discover 10+ real SF events, extract entities, score
```

### Phase 2: Action Agent (1 hour)

```
- [ ] Implement Yutori Navigator auto-apply flow
  - [ ] Build task descriptions from user profile
  - [ ] Handle application results (success/waitlist/fail)
  - [ ] Webhook handler for async results
- [ ] Google Calendar integration
  - [ ] OAuth flow
  - [ ] Auto-create events
  - [ ] Conflict detection
- [ ] Test: auto-apply to a real event, verify calendar sync
```

### Phase 3: Connect Agent (1 hour)

```
- [ ] People research pipeline
  - [ ] Tavily deep search on attendees
  - [ ] Fastino entity extraction on profiles
  - [ ] Neo4j graph-based connection scoring
- [ ] Cold message generation
  - [ ] Context-aware message templates
  - [ ] LLM-powered personalization
  - [ ] Draft queue with approval flow
- [ ] Test: research 5 people, generate messages, verify quality
```

### Phase 4: Feedback Loop + UI (1.5 hours)

```
- [ ] Frontend dashboard
  - [ ] Event feed with accept/reject/skip
  - [ ] Rejection reason modal
  - [ ] Event detail + people view
  - [ ] Message approval flow
  - [ ] Settings page
- [ ] Preference engine
  - [ ] Process feedback signals
  - [ ] Weight recalculation
  - [ ] Neo4j preference storage
- [ ] Onboarding flow
  - [ ] Profile setup wizard
  - [ ] Interest selection
  - [ ] Automation level config
- [ ] WebSocket real-time updates
```

### Phase 5: Polish + Demo (30 min)

```
- [ ] Graph visualization (Neo4j → D3.js or neovis.js)
- [ ] Agent status dashboard
- [ ] Record 3-minute demo video
- [ ] Push to GitHub
- [ ] Submit to Devpost
```

### Phase 6: Test Hardening + Validation Gates (45 min)

```
- [ ] Add unit tests for scoring, deduplication, preference updates
- [ ] Add contract tests for Tavily/Yutori/Fastino/Neo4j clients (mocked)
- [ ] Add orchestrator tests for routing rules (auto-apply vs suggest)
- [ ] Add 1 golden end-to-end test using recorded fixtures
- [ ] Define release gate thresholds (pipeline success, duplicate rate, message quality)
- [ ] Add "dry-run mode" (no external side effects) for safe autonomous testing
```

---

## Tech Stack

| Layer | Technology | Reason |
|-------|-----------|--------|
| **Frontend** | Next.js 15 + TypeScript | Fast SSR, App Router, React Server Components |
| **UI Components** | shadcn/ui + Tailwind CSS | Rapid prototyping, beautiful defaults |
| **Graph Viz** | neovis.js or react-force-graph | Neo4j native visualization |
| **Backend** | FastAPI (Python) | Async-native, serves UI + executes tool calls |
| **Agent Brain** | Claude API (ReAct loop) | Central orchestrator — thinks, decides, acts. NOT a fixed pipeline |
| **Database** | PostgreSQL (app state) | Reliable, structured data |
| **Graph Database** | Neo4j AuraDB (free tier) | Knowledge graph, relationship queries |
| **Search** | Tavily Search API | AI-optimized search for agents |
| **Web Agent** | Yutori Navigator + Scouting | Autonomous web browsing + monitoring |
| **NER/Extraction** | Fastino GLiNER 2 | Fast entity extraction, <150ms |
| **Calendar** | Google Calendar API | Most widely used calendar |
| **Auth** | NextAuth.js + Google OAuth | Calendar integration requires OAuth |
| **Real-time** | WebSocket (FastAPI) | Live UI updates |
| **Hosting** | Render | Sponsor tool + easy deploy |
| **LLM** | Claude API (agent brain + messages) | Powers the ReAct loop AND generates personalized messages |

---

## Deployment

### Render (Sponsor Tool) Deployment

```yaml
# render.yaml
services:
  # FastAPI Backend
  - type: web
    name: nexus-api
    runtime: python
    buildCommand: pip install -r requirements.txt
    startCommand: uvicorn main:app --host 0.0.0.0 --port $PORT
    envVars:
      - key: TAVILY_API_KEY
        sync: false
      - key: YUTORI_API_KEY
        sync: false
      - key: FASTINO_API_KEY
        sync: false
      - key: NEO4J_URI
        sync: false
      - key: NEO4J_PASSWORD
        sync: false
      - key: GOOGLE_CLIENT_ID
        sync: false
      - key: GOOGLE_CLIENT_SECRET
        sync: false

  # Next.js Frontend
  - type: web
    name: nexus-web
    runtime: node
    buildCommand: npm run build
    startCommand: npm start

  # Background Worker (Agent Loop)
  - type: worker
    name: nexus-agents
    runtime: python
    buildCommand: pip install -r requirements.txt
    startCommand: python -m agents.orchestrator

databases:
  - name: nexus-db
    plan: free
    databaseName: nexus
```

---

## Judging Criteria Alignment

| Criteria (20% each) | How NEXUS wins |
|---------------------|----------------|
| **Autonomy** | Agents run 24/7 — Yutori Scouting monitors event sources, Discovery triggers on webhooks, Action auto-applies, Connect auto-drafts. User only reviews and provides feedback. The system learns and becomes MORE autonomous over time. |
| **Idea** | Solves a real, painful problem for every SF professional. The "networking chief-of-staff" concept is immediately understandable. Feedback loop makes it genuinely useful, not just a demo. |
| **Technical Implementation** | Multi-agent architecture with LangGraph orchestration, Neo4j knowledge graph for relationship intelligence, real-time WebSocket UI, preference learning engine. Clean separation of concerns. |
| **Tool Use** | Deep integration of 5 sponsor tools: Tavily (discovery + research), Neo4j (knowledge graph), Yutori (web automation + monitoring), Fastino (entity extraction), Render (deployment). Each tool used for its core strength. |
| **Presentation** | Live demo: onboard → watch agent discover real events → see auto-apply happen → explore people graph → approve cold message. 3-min story arc: problem → solution → live demo → impact. |

---

## Demo Script (3 minutes)

```
0:00 - 0:30  PROBLEM
  "Imagine you just moved to SF. Hundreds of events every week.
   You're drowning in Eventbrite, Luma, Meetup tabs.
   You miss the dinner where your future investor was sitting."

0:30 - 1:00  SOLUTION
  "Meet NEXUS — your autonomous networking chief-of-staff."
  Show onboarding: enter role, company, goals, preferences.
  "It learns what you care about and acts on your behalf."

1:00 - 2:00  LIVE DEMO
  Show dashboard: "While we were talking, NEXUS found 12 events."
  Click into top-scored event: show entity extraction, people analysis.
  "It already applied to this dinner — here's the confirmation."
  Show calendar: event auto-synced.
  Show people tab: "These 3 people are who you should meet. Here's why."
  Show draft message: personalized cold outreach.
  Click "Send" — message goes out.

  Reject an event: select reason "not my industry" →
  "Watch the score update — NEXUS learns in real-time."

2:00 - 2:30  TECH
  Flash architecture diagram.
  "5 sponsor tools: Tavily searches, Fastino extracts,
   Neo4j maps relationships, Yutori applies and monitors,
   Render hosts it all. LangGraph orchestrates. Feedback loop learns."

2:30 - 3:00  IMPACT
  "NEXUS has been running for 6 hours. It discovered 47 events,
   recommended 18, I accepted 12, it applied to all 12,
   10 confirmed, and I have 8 personalized intros ready to send.
   That would have taken me 4 hours manually. NEXUS did it in the
   background while I was coding."
```

---

## MVP Scope (Hackathon Day Reality Check)

**Available time:** 11:00 AM - 4:30 PM = **5.5 hours of coding**

### What MUST work for demo (MVP)

| Feature | Priority | Time |
|---------|----------|------|
| User onboarding (profile + preferences) | P0 | 30 min |
| Tavily event discovery (10+ real SF events) | P0 | 45 min |
| Fastino GLiNER entity extraction | P0 | 30 min |
| Neo4j graph creation + query | P0 | 45 min |
| Relevance scoring engine | P0 | 30 min |
| Yutori Navigator auto-apply (1 real event) | P0 | 45 min |
| Dashboard UI (event feed + accept/reject) | P0 | 60 min |
| Feedback loop (reject with reason → score update) | P0 | 30 min |
| Google Calendar sync | P1 | 20 min |
| Cold message drafting | P1 | 20 min |
| Deploy to Render | P0 | 15 min |
| **Total** | | **5h 30min** |

### What we SKIP for MVP (nice-to-have)

- Yutori Scouting (continuous monitoring) — use scheduled Tavily instead
- WebSocket real-time updates — use polling
- Graph visualization with neovis.js — show Neo4j browser screenshot instead
- LinkedIn/Twitter message sending — show drafts only
- Post-event rating flow
- Full settings page

### Fallback Plan

If any sponsor API is down or has issues:

| Risk | Fallback |
|------|----------|
| Yutori Navigator fails on a site | Pre-record a successful apply, show Yutori task ID + view_url as proof |
| Tavily rate limit hit | Pre-cache 20 event results in DB, show live search alongside |
| Fastino API unreachable | Use `GLiNER2.from_pretrained()` locally (model is only 205MB) |
| Neo4j AuraDB connection issues | Use local Neo4j Docker as backup |
| Render deploy fails | Demo from localhost, show render.yaml as deployment proof |

---

## Cost Analysis (Hackathon Day)

| Service | Free Tier | Expected Usage | Cost |
|---------|-----------|----------------|------|
| **Tavily** | 1,000 searches/mo | ~100 searches | $0 |
| **Neo4j AuraDB** | 200k nodes free | ~500 nodes | $0 |
| **Yutori** | Hackathon credits (check with sponsor) | ~20 browsing tasks | $0 (with credits) |
| **Fastino GLiNER** | API key from gliner.pioneer.ai | ~200 extractions | $0 (free tier) |
| **Render** | Free tier (750 hours/mo) | 1 day | $0 |
| **Google Calendar API** | Free (with OAuth) | ~20 event creates | $0 |
| **Claude API** | Existing credits | ~50 message generations | ~$2 |
| **Total** | | | **~$2** |

---

## Error Handling & Edge Cases

### Event Deduplication

Same event appears on Eventbrite AND Lu.ma — how do we handle?

```python
async def deduplicate_events(events: list[RawEvent]) -> list[RawEvent]:
    """Deduplicate events using title similarity + date + location."""

    seen = {}
    unique = []

    for event in events:
        # Normalize: lowercase, strip whitespace, remove special chars
        key_title = normalize(event.title)
        key_date = event.date.strftime("%Y-%m-%d") if event.date else ""

        # Fuzzy match: if title similarity > 80% AND same date → duplicate
        is_dup = False
        for seen_key, seen_event in seen.items():
            if (fuzz.ratio(key_title, seen_key) > 80
                and key_date == seen_event.date_str):
                # Keep the one with more info (longer description)
                if len(event.description) > len(seen_event.description):
                    seen[seen_key] = event
                is_dup = True
                break

        if not is_dup:
            seen[key_title] = event
            unique.append(event)

    return unique
```

### Calendar Conflict Detection

```python
async def check_calendar_conflicts(
    event_datetime: datetime,
    duration_hours: float = 3.0
) -> list[dict]:
    """Check Google Calendar for conflicts before scheduling."""

    time_min = event_datetime.isoformat() + "Z"
    time_max = (event_datetime + timedelta(hours=duration_hours)).isoformat() + "Z"

    events = await calendar_service.events().list(
        calendarId="primary",
        timeMin=time_min,
        timeMax=time_max,
        singleEvents=True
    ).execute()

    return events.get("items", [])
```

### Yutori Navigator Failure Recovery

```python
async def apply_with_retry(event: EnrichedEvent, user: UserProfile) -> dict:
    """Apply to event with retry logic and graceful degradation."""

    try:
        result = await yutori.browsing.create(
            task=build_apply_task(event, user),
            start_url=event.raw.url,
            max_steps=50,
            agent="navigator-n1-latest",
            output_schema=APPLICATION_RESULT_SCHEMA
        )

        # Poll for completion (Yutori tasks are async)
        for _ in range(30):  # max 5 min wait
            status = await yutori.browsing.get(result["task_id"])
            if status["status"] in ("succeeded", "failed"):
                break
            await asyncio.sleep(10)

        if status["status"] == "succeeded":
            return {"status": "applied", **status.get("structured_result", {})}
        else:
            # Log failure, mark event as "apply_failed"
            return {"status": "failed", "reason": status.get("result", "Unknown")}

    except Exception as e:
        # Graceful degradation: save event URL for manual apply
        return {
            "status": "manual_required",
            "url": event.raw.url,
            "error": str(e)
        }
```

---

## Testing & Validation Strategy

NEXUS is autonomous, so correctness cannot depend on ad-hoc manual checks.
Validation is a first-class system: every layer must prove its behavior before side effects (apply/send/schedule) are allowed.

### 1) Test Pyramid (What to test where)

| Layer | Goal | Example Assertions | Frequency |
|-------|------|--------------------|-----------|
| **Unit tests** | Verify deterministic logic | score range is 0-100, dedup merges near-identical events, preference weights update correctly | Every commit |
| **Contract tests** | Verify external API adapters | Tavily result parsing survives missing fields, Yutori status mapping is stable, Neo4j query responses map to models | Every commit |
| **Agent-node tests** | Verify each agent in isolation | Discovery returns normalized `RawEvent[]`; Analyze enriches with entities + score; Connect returns ranked people + draft objects | Every commit |
| **Orchestrator tests** | Verify routing and state transitions | `score >= auto_apply_threshold` routes to Action; otherwise Suggest path; failed action does not trigger unsafe downstream actions | Every commit |
| **Integration/E2E tests** | Verify full cycle behavior | discover -> analyze -> apply(dry-run) -> research -> draft pipeline produces expected artifacts | PR + pre-release |
| **Live smoke tests** | Verify production health with guardrails | one canary cycle with strict limits, no irreversible action unless checks pass | Post-deploy |

### 2) Agent Self-Verification (Built-in Runtime Assertions)

Each agent stage runs explicit validation checks before passing state to next stage.
If checks fail, stage retries with fallback; if still failing, task is quarantined for human review.

```python
def validate_discovery_output(events: list[RawEvent]) -> ValidationResult:
    errors = []
    if not events:
        errors.append("no_events")
    required = ["title", "url", "source"]
    completeness = compute_required_field_completeness(events, required)
    if completeness < 0.95:
        errors.append(f"low_completeness:{completeness:.2f}")
    return ValidationResult(ok=len(errors) == 0, errors=errors)

def validate_analyze_output(event: EnrichedEvent) -> ValidationResult:
    errors = []
    if not (0 <= event.relevance_score <= 100):
        errors.append("invalid_score_range")
    if not event.entities:
        errors.append("empty_entities")
    return ValidationResult(ok=len(errors) == 0, errors=errors)
```

Runtime policy:

| Check | Fail Action |
|------|-------------|
| Discovery output invalid | Retry with narrower query set; fallback to cached seeds |
| Analyze invalid score/entities | Re-run extraction once; fallback to low-confidence queue |
| Action apply fails | Mark `manual_required`; never silently drop |
| Connect low profile richness | Skip send; keep draft in review queue |

### 3) Safety Modes for Autonomous Testing

- **Dry-run mode:** executes full reasoning/tool selection but blocks side effects:
  - No real RSVP submission
  - No real message sending
  - No real calendar writes
- **Replay mode:** runs pipeline on recorded fixture events/attendees for deterministic regression testing.
- **Canary mode:** enables side effects only for a tiny sample (e.g., 1 event/day, top-1 draft only).

Recommended runtime flags:

```bash
NEXUS_MODE=dry_run|replay|canary|live
ALLOW_SIDE_EFFECTS=false|true
MAX_AUTO_APPLIES_PER_DAY=1
MAX_AUTO_SEND_MESSAGES_PER_DAY=0
```

### 4) Quality Evaluation for "Who to Meet" + Message Drafts

#### Connection recommendation quality

Define offline labeled set (`tests/fixtures/recommendation_eval.jsonl`) with expected top candidates.

Metrics:

- Precision@3 for suggested people
- Coverage of required constraints (shared topics, target companies, event relevance)
- Explanation quality (must include at least 1 concrete graph reason)

Target release thresholds:

- `precision_at_3 >= 0.67`
- `constraint_coverage >= 0.90`
- `explanation_presence >= 0.95`

#### Message quality

Use rubric-based checks before allowing `approved -> sent` automation:

- personalization score (0-1)
- banned-pattern violations (must be 0):
  - generic flattery
  - first-message product pitch
  - asking for favors immediately
- factual grounding (claims must link to extracted profile/event facts)

Target thresholds:

- `personalization_score >= 0.75`
- `banned_pattern_violations == 0`
- `grounded_claim_ratio >= 0.90`

### 5) CI/CD Gates (Block bad releases)

Minimum pipeline:

```yaml
jobs:
  unit_contract:
    - pytest tests/unit tests/contract -q
  agent_orchestrator:
    - pytest tests/agents tests/orchestrator -q
  e2e_replay:
    - pytest tests/e2e/test_full_cycle_replay.py -q
  quality_eval:
    - python scripts/eval_recommendations.py --min-p-at-3 0.67
    - python scripts/eval_messages.py --min-personalization 0.75 --max-banned 0
```

Release is blocked if any gate fails.
No "warning-only" mode for autonomous side-effect paths.

### 6) Observability + Auditability

Every cycle should produce structured logs and metrics:

- correlation id per cycle (`cycle_id`)
- per-tool latency/success/failure
- assertion failures by stage
- side-effect attempts and outcomes (`apply`, `calendar`, `send`)
- fallback activations (`cached_results_used`, `manual_required_count`)

Persist an immutable audit trail:

- input snapshot (sanitized)
- agent decision trace (why action chosen)
- tool outputs (redacted)
- final state transition

This makes incidents debuggable and prevents "black-box" autonomous behavior.

### 7) Production Rollout Playbook

1. **Week 1: Shadow mode**
   - Run full agent loop with `ALLOW_SIDE_EFFECTS=false`
   - Compare outputs with human decisions
2. **Week 2: Canary mode**
   - Enable auto-apply for top-1 event/day only
   - Keep message sending manual approval only
3. **Week 3+: Gradual autonomy increase**
   - Raise limits only if KPIs stay healthy for 7 consecutive days

Rollback triggers (immediate downgrade to dry-run):

- duplicate apply rate > 2%
- incorrect recipient/message mismatch > 0
- user reject rate spikes > 40% day-over-day
- external API contract breakage above threshold

### 8) Suggested Test Directory Structure

```text
tests/
  unit/
    test_scoring.py
    test_deduplication.py
    test_preference_engine.py
  contract/
    test_tavily_client.py
    test_yutori_client.py
    test_fastino_client.py
    test_neo4j_client.py
  agents/
    test_discovery_agent.py
    test_analyze_agent.py
    test_action_agent.py
    test_connect_agent.py
  orchestrator/
    test_routing_rules.py
    test_state_transitions.py
  e2e/
    test_full_cycle_replay.py
  fixtures/
    events_sf_sample.json
    attendees_sample.json
    recommendation_eval.jsonl
```

---

## Project Structure

```
nexus/
├── README.md
├── render.yaml
│
├── backend/                          # FastAPI + Agents
│   ├── main.py                       # FastAPI app entry
│   ├── requirements.txt
│   ├── config.py                     # Environment config
│   │
│   ├── agents/                       # Agent system
│   │   ├── orchestrator.py           # LangGraph orchestrator
│   │   ├── discovery.py              # Discovery Agent
│   │   ├── analyze.py                # Analyze Agent
│   │   ├── action.py                 # Action Agent
│   │   └── connect.py                # Connect Agent
│   │
│   ├── integrations/                 # External API clients
│   │   ├── tavily_client.py
│   │   ├── yutori_client.py
│   │   ├── fastino_client.py
│   │   ├── neo4j_client.py
│   │   └── google_calendar.py
│   │
│   ├── engine/                       # Core logic
│   │   ├── preference.py             # Preference learning engine
│   │   ├── scoring.py                # Event relevance scoring
│   │   ├── message_generator.py      # Cold message drafting
│   │   └── deduplication.py          # Event dedup logic
│   │
│   ├── api/                          # REST endpoints
│   │   ├── events.py
│   │   ├── people.py
│   │   ├── messages.py
│   │   ├── profile.py
│   │   ├── feedback.py
│   │   ├── graph.py
│   │   └── webhooks.py
│   │
│   ├── models/                       # Pydantic models
│   │   ├── event.py
│   │   ├── person.py
│   │   ├── message.py
│   │   ├── profile.py
│   │   └── feedback.py
│   │
│   └── db/                           # Database
│       ├── postgres.py
│       └── neo4j_schema.cypher
│
├── frontend/                         # Next.js App
│   ├── package.json
│   ├── next.config.js
│   ├── tailwind.config.js
│   │
│   ├── app/
│   │   ├── layout.tsx
│   │   ├── page.tsx                  # Dashboard
│   │   ├── events/
│   │   │   └── [id]/page.tsx         # Event detail
│   │   ├── people/
│   │   │   └── page.tsx              # People graph
│   │   ├── messages/
│   │   │   └── page.tsx              # Message queue
│   │   ├── settings/
│   │   │   └── page.tsx              # Settings
│   │   └── onboarding/
│   │       └── page.tsx              # Onboarding wizard
│   │
│   ├── components/
│   │   ├── EventCard.tsx
│   │   ├── EventDetail.tsx
│   │   ├── PersonCard.tsx
│   │   ├── MessageDraft.tsx
│   │   ├── RejectModal.tsx
│   │   ├── NetworkGraph.tsx
│   │   ├── PreferenceSliders.tsx
│   │   └── OnboardingSteps.tsx
│   │
│   ├── hooks/
│   │   ├── useWebSocket.ts
│   │   ├── useEvents.ts
│   │   └── useFeedback.ts
│   │
│   └── lib/
│       ├── api.ts                    # API client
│       └── types.ts                  # TypeScript types
│
└── scripts/
    ├── seed_neo4j.py                 # Initialize graph schema
    └── demo_data.py                  # Demo data for presentation
```

---

## Key Differentiators vs. Other Hackathon Projects

1. **Actually autonomous** — not just a chatbot. Agents run continuously, discover events, and take action without prompting.
2. **Feedback loop that learns** — rejection reasons, acceptance patterns, and message edits all feed back into the scoring model. Gets better with every interaction.
3. **Graph intelligence** — Neo4j knowledge graph enables "who should I meet" queries that are impossible with traditional databases. 2nd-degree connections, shared interest overlap, company targeting.
4. **Real web actions** — Yutori Navigator actually fills forms and clicks buttons. Not a mock or simulation.
5. **Production-ready UI** — Not just a terminal script. Full dashboard with real-time updates, graph visualization, and approval workflows.

---

*Built for the [Autonomous Agents Hackathon](https://autonomous-agents-hackathon.devpost.com/) — Feb 27, 2026*
