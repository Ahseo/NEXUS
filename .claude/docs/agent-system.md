# NEXUS Agent System

## Overview

NEXUS uses a Claude-powered ReAct (Reason + Act) loop as its central brain. The `NexusAgent` orchestrator runs 24/7 as a Render background worker, calling Claude API in a continuous think-act-observe cycle. Four specialized agents handle domain logic: Discovery, Analyze, Action, and Connect.

## Orchestrator (NexusAgent)

The orchestrator in `backend/app/agents/orchestrator.py` drives the main loop:

1. Claude receives the system prompt (user profile, goals, rules) + conversation history
2. Claude picks a tool from the 12-tool belt
3. The orchestrator executes the tool via integration clients
4. The result is fed back as a tool_result message
5. Claude thinks again and picks the next action
6. On `end_turn`, a new cycle prompt is injected to keep the loop alive

Model: `claude-sonnet-4-5-20250514` with `max_tokens=4096`.

## System Prompt Template

The system prompt is built dynamically from the user profile. It injects: name, role, company, product, interests, goals, target roles/companies, preferred event types, max events/week, auto-apply threshold, suggest threshold, and message tone. The prompt defines 10 behavioral rules (e.g., never auto-send messages, always check calendar for conflicts, save everything to Neo4j).

## Tool Belt (12 Tools)

| Tool | Sponsor | Purpose |
|------|---------|---------|
| `tavily_search` | Tavily | Web search for events, people, companies |
| `yutori_browse` | Yutori | Autonomous web agent for RSVP/apply, scraping |
| `yutori_scout` | Yutori | Continuous URL monitoring (hourly/daily) |
| `neo4j_query` | Neo4j | Cypher read queries on the knowledge graph |
| `neo4j_write` | Neo4j | Create/update nodes and relationships |
| `reka_vision` | Reka | Image analysis, profile photo cross-verification |
| `google_calendar` | -- | Check availability, create events, list upcoming |
| `resolve_social_accounts` | -- | Composite: Tavily search + Reka verification |
| `draft_message` | -- | Generate personalized cold/follow-up messages |
| `get_user_feedback` | -- | Read pending user actions from the UI |
| `notify_user` | -- | Push notifications to dashboard via WebSocket |
| `wait` | -- | Sleep between cycles (triggers asyncio.sleep) |

## 4 Specialized Agents

**Discovery Agent** (`discovery.py`): Builds search queries from user interests, searches event platforms (Eventbrite, Luma, Meetup, Partiful) via Tavily, deduplicates results, and optionally sets up Yutori scouts for continuous monitoring.

**Analyze Agent** (`analyze.py`): Extracts structured entities (speakers, topics, companies) from event descriptions using Claude API, scores relevance via `ScoringEngine`, and populates the Neo4j knowledge graph with Event, Person, Company, and Topic nodes.

**Action Agent** (`action.py`): Decision matrix based on score thresholds: auto_apply (score >= 80), suggest (score >= 50), or skip. Uses Yutori Navigator for RSVP with retry logic. Enforces daily apply limits.

**Connect Agent** (`connect.py`): Scrapes attendee lists via Yutori (platform-specific strategies), runs iterative deep research until profile richness >= 0.7, resolves social accounts (LinkedIn, Twitter, Instagram, GitHub), cross-verifies profiles with Reka Vision, matches against target people using fuzzy matching (threshold: 85), and ranks connections by score.

## 4 Sponsor Tool Integrations

1. **Tavily Search API** -- Event discovery with domain filtering, people research with `search_depth: "advanced"`, AI-generated answers
2. **Neo4j (AuraDB)** -- Knowledge graph as long-term memory: User, Event, Person, Company, Topic nodes with relationship queries (SPEAKS_AT, WORKS_AT, TAGGED, etc.)
3. **Yutori API** -- Browsing API for autonomous form filling/RSVP, Scouting API for continuous event monitoring on schedule
4. **Reka Vision** -- Profile photo comparison across platforms, Instagram/X content analysis for conversation hooks, event flyer extraction

## Safety Modes

Controlled by `NEXUS_MODE` environment variable (enum in `app/core/config.py`):

| Mode | Side Effects | Description |
|------|-------------|-------------|
| `dry_run` | Blocked | Read-only. No applies, no notifications, no calendar writes |
| `replay` | Blocked | Replay recorded conversations for testing |
| `canary` | Limited | Live but rate-limited: max 10 applies/day, max 5 messages/day |
| `live` | Full | Production mode, all tools enabled |

Side-effect tools blocked in dry_run/replay: `yutori_browse`, `yutori_scout`, `google_calendar`, `notify_user`.

## Conversation History Management

The orchestrator maintains a `conversation_history` list of messages. When the list exceeds 100 entries, it is trimmed to: first 2 messages (initial context) + last 50 messages (recent context). This prevents context window overflow while preserving the kickoff prompt and recent state.
