# NEXUS Architecture

## Overview

NEXUS is an autonomous networking agent for SF professionals. It continuously discovers events, auto-applies, researches attendees, and drafts personalized outreach messages. The system runs as a multi-agent pipeline with human-in-the-loop feedback.

**Full loop:** Discover → Apply → Schedule → Research Attendees → Find Socials → Cold Message → Attend → Follow Up → Save to CRM → Repeat Forever

## Tech Stack

| Layer | Technology | Purpose |
|-------|-----------|---------|
| Frontend | Next.js 15 + TypeScript | SSR, App Router, React Server Components |
| UI Components | shadcn/ui + Tailwind CSS | Rapid prototyping |
| Graph Viz | neovis.js or react-force-graph | Neo4j native visualization |
| Backend | FastAPI (Python) | Async API + agent execution |
| Agent Brain | Claude API (ReAct loop) | Central orchestrator |
| Database | PostgreSQL | Application state |
| Graph DB | Neo4j AuraDB (free tier) | Knowledge graph, relationship queries |
| Search | Tavily Search API | AI-optimized search |
| Web Agent | Yutori Navigator + Scouting | Autonomous browsing + monitoring |
| Vision | Reka Vision | Profile verification + social content analysis |
| Calendar | Google Calendar API | Calendar sync |
| Auth | NextAuth.js + Google OAuth | Authentication |
| Real-time | WebSocket (FastAPI) | Live UI updates |
| LLM | Claude API | Agent brain + message generation |

## 4 Sponsor Tools

1. **Tavily Search API** - Event discovery + people research. Uses `search_depth: "advanced"` with domain filtering for event platforms.
2. **Neo4j (AuraDB)** - Knowledge graph storing events, people, companies, and relationships. Graph queries power networking intelligence (e.g., "find people who share interests AND attend the same event AND work at target companies").
3. **Yutori API** - Autonomous web browsing (auto-apply/RSVP via Browsing API), continuous event monitoring (Scouting API), and deep research (Research API with 100+ MCP tools).
4. **Reka Vision** - Profile photo cross-verification across platforms, Instagram/X content analysis for conversation hooks, event page screenshot analysis.

## Deployment Topology (Render)

```
┌─────────────────────────────────────────────┐
│                  Render                       │
│                                               │
│  ┌─────────────┐  ┌──────────────┐           │
│  │  nexus-web   │  │  nexus-api    │          │
│  │  (Next.js)   │→ │  (FastAPI)    │          │
│  │  Port: 3000  │  │  Port: 8000   │          │
│  └─────────────┘  └──────┬───────┘           │
│                          │                    │
│                   ┌──────┴───────┐            │
│                   │ nexus-agents  │            │
│                   │ (Worker)      │            │
│                   └──────┬───────┘            │
│                          │                    │
│  ┌──────────┐     ┌─────┴──────┐             │
│  │ nexus-db  │     │  Neo4j     │             │
│  │ (Postgres)│     │  AuraDB    │             │
│  └──────────┘     └────────────┘             │
└─────────────────────────────────────────────┘
```

Services:
- **nexus-web** - Next.js frontend (node runtime)
- **nexus-api** - FastAPI backend (python runtime, uvicorn)
- **nexus-agents** - Background worker running agent orchestrator loop
- **nexus-db** - PostgreSQL database (Render free tier)
- **Neo4j AuraDB** - External graph database (free tier: 200k nodes)

## Directory Structure

```
NEXUS/
├── README.md              # Full specification
├── render.yaml            # Render deployment config
├── scripts/               # Utility scripts
├── backend/
│   ├── pyproject.toml
│   ├── requirements.txt
│   ├── app/
│   │   ├── main.py        # FastAPI entrypoint
│   │   ├── core/          # Config, database setup
│   │   │   ├── config.py
│   │   │   └── database.py
│   │   ├── models/        # Pydantic + SQLAlchemy models
│   │   ├── routers/       # API route handlers
│   │   ├── services/      # Business logic
│   │   ├── integrations/  # Tavily, Neo4j, Yutori, Reka clients
│   │   ├── agents/        # Agent implementations
│   │   └── db/            # DB migrations, Neo4j schema
│   └── tests/
│       ├── conftest.py
│       ├── unit/
│       ├── contract/      # Integration contract tests
│       ├── e2e/
│       ├── fixtures/
│       ├── agents/
│       └── orchestrator/
├── frontend/
│   ├── package.json
│   ├── tsconfig.json
│   └── src/
│       └── app/           # Next.js App Router pages
│           ├── layout.tsx
│           ├── page.tsx   # Dashboard
│           ├── events/[id]/page.tsx
│           ├── people/page.tsx
│           ├── messages/page.tsx
│           ├── settings/page.tsx
│           ├── onboarding/page.tsx
│           └── targets/page.tsx
└── .claude/
    └── docs/              # Architecture documentation
```

## Frontend-Backend Communication

1. **REST API** - Standard HTTP requests from Next.js to FastAPI (`/api/*` endpoints)
2. **WebSocket** - Real-time updates pushed from FastAPI to frontend for live event notifications, agent status, and message drafts
3. **Webhooks** - External services (Yutori, Google Calendar) POST to FastAPI webhook endpoints, which then push updates via WebSocket to the frontend
