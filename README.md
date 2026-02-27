<p align="center">
  <img src="frontend/public/logo.svg" alt="Wingman" width="80" />
</p>

<h1 align="center">Wingman</h1>

<p align="center">
  <strong>Your autonomous networking agent.</strong><br/>
  Discovers events, auto-applies, deep-researches every attendee, and drafts personalized outreach — so you never show up blind.
</p>

<p align="center">
  <a href="#features">Features</a> •
  <a href="#how-it-works">How It Works</a> •
  <a href="#tech-stack">Tech Stack</a> •
  <a href="#getting-started">Getting Started</a> •
  <a href="#deployment">Deployment</a> •
  <a href="#architecture">Architecture</a> •
  <a href="#license">License</a>
</p>

---

## What is Wingman?

Wingman is a continuously-running AI agent that acts as your networking chief-of-staff. It autonomously:

1. **Scans 10+ event sources** (Eventbrite, Lu.ma, Meetup, Partiful, Twitter, newsletters)
2. **Scores & auto-applies** to events matching your profile
3. **Deep-researches every attendee** — from just a name, it finds their background, role, company, and socials
4. **Drafts personalized cold messages** with relevant hooks before the event
5. **Learns from your feedback** to get smarter over time

**The full loop:** Discover → Score → Apply → Schedule → Research Attendees → Find Socials → Draft Outreach → Attend → Follow Up → Repeat

> Built at the [Autonomous Agents Hackathon](https://autonomous-agents-hackathon.devpost.com/) (Feb 2026)

---

## Features

### Event Discovery & Scoring
- Real-time monitoring of event sources via webhooks + scheduled sweeps
- NER extraction of speakers, attendees, companies, and topics
- Relevance scoring (0–100) based on topic match, speaker quality, company relevance, and your history
- Auto-apply to events scoring 80+ (configurable threshold)

### Attendee Research
- **Iterative deep research** — Claude decides when it knows enough (richness score > 0.7)
- Cross-references names via web search, vision-based identity verification, and graph context
- Builds a knowledge graph of people, companies, and relationships

### Personalized Outreach
- Drafts cold messages using investment thesis context, recent activity hooks, and mutual connections
- Human-in-the-loop: all messages queued for your approval before sending
- Daily safety limits (max 10 auto-applies, max 5 auto-sends)

### Learning Feedback Loop
- Accept/reject/edit feedback flows into the knowledge graph
- Preference signals update scoring weights over time
- Reject Web3 events once → agent deprioritizes Web3 going forward

### Real-Time Dashboard
- WebSocket-powered live updates as the agent works
- Agent status controls (pause/resume/run now)
- Event feed, people profiles, message drafts, and activity log

---

## How It Works

```
┌──────────┐    ┌──────────┐    ┌──────────┐    ┌──────────┐
│ DISCOVER │───▶│ ANALYZE  │───▶│   ACT    │───▶│ CONNECT  │
│  Agent   │    │  Agent   │    │  Agent   │    │  Agent   │
└──────────┘    └──────────┘    └──────────┘    └──────────┘
      │               │               │               │
      └───────────────┴───────┬───────┴───────────────┘
                              │
                     ┌────────▼────────┐
                     │  FEEDBACK LOOP  │
                     │  (learns prefs) │
                     └─────────────────┘
```

| Phase | Description | Tools Used |
|-------|-------------|------------|
| **Discover** | Scans event sources, detects new events via webhooks | Tavily Search, Yutori Scouting |
| **Analyze** | Extracts entities, scores relevance, builds knowledge graph | Neo4j, Claude NER |
| **Act** | Auto-applies, adds to Google Calendar, manages waitlists | Yutori Navigator, Google Calendar |
| **Connect** | Researches attendees, verifies identities, drafts outreach | Tavily, Reka Vision, Neo4j |

The core brain is a **Claude ReAct agent** with 13 integrated tools running as a background worker.

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| **Frontend** | Next.js 16, React 19, TypeScript, Tailwind CSS v4 |
| **Backend** | FastAPI, Python 3.11+, SQLAlchemy (async) |
| **AI/Agent** | Claude (Anthropic SDK), ReAct loop architecture |
| **Databases** | PostgreSQL (Supabase) — app state, Neo4j AuraDB — knowledge graph |
| **Integrations** | Tavily Search, Yutori API, Reka Vision, Google Calendar |
| **Deployment** | Render (web + worker services) |

---

## Getting Started

### Prerequisites

- Python 3.11+
- Node.js 18+
- PostgreSQL database ([Supabase](https://supabase.com) recommended)
- Neo4j instance ([AuraDB](https://neo4j.com/cloud/aura/) free tier works)

### 1. Clone the repo

```bash
git clone https://github.com/Ahseo/NEXUS.git
cd NEXUS
```

### 2. Set up environment variables

```bash
cp .env.example .env
```

Fill in your API keys:

```env
# Sponsor Tool APIs
TAVILY_API_KEY=tvly-xxxxx
YUTORI_API_KEY=yutori-xxxxx
NEO4J_URI=neo4j+s://xxxxx.databases.neo4j.io
NEO4J_USER=neo4j
NEO4J_PASSWORD=xxxxx
REKA_API_KEY=reka-xxxxx
ANTHROPIC_API_KEY=sk-ant-xxxxx

# Google OAuth (Calendar)
GOOGLE_CLIENT_ID=xxxxx.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=xxxxx

# Database
DATABASE_URL=postgresql+asyncpg://...

# App Config
SECRET_KEY=change-me-in-production
NEXUS_MODE=dry_run  # dry_run | canary | live
```

### 3. Start the backend

```bash
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### 4. Start the frontend

```bash
cd frontend
npm install
npm run dev
```

The app will be running at `http://localhost:3000` with the API at `http://localhost:8000`.

### 5. (Optional) Seed demo data

```bash
cd backend
python scripts/demo_data.py
python scripts/seed_neo4j.py
```

---

## Deployment

Wingman is configured for one-click deployment on [Render](https://render.com) via `render.yaml`:

| Service | Type | Description |
|---------|------|-------------|
| `nexus-api` | Web | FastAPI backend |
| `nexus-web` | Web | Next.js frontend |
| `nexus-agents` | Worker | Background agent orchestrator |

Set your environment variables in the Render dashboard and deploy.

---

## Architecture

```
Frontend (Next.js)  ◄──── REST + WebSocket ────►  Backend (FastAPI)
                                                        │
                                                  Claude ReAct Agent
                                                  (13 integrated tools)
                                                        │
                            ┌───────────┬───────────┬───┴───────┐
                            ▼           ▼           ▼           ▼
                       PostgreSQL    Neo4j     Google Cal    Sponsor APIs
                       (app state)  (graph)   (scheduling)  (Tavily, Yutori, Reka)
```

### Project Structure

```
NEXUS/
├── frontend/
│   └── src/
│       ├── app/            # Next.js app router (pages)
│       ├── components/     # React components
│       ├── hooks/          # Custom hooks
│       └── lib/            # API client & types
├── backend/
│   └── app/
│       ├── agents/         # Agent orchestrator & sub-agents
│       ├── core/           # Config, auth, database, websocket
│       ├── models/         # SQLAlchemy & Pydantic models
│       ├── routers/        # API endpoints
│       ├── services/       # Scoring, messages, preferences
│       └── integrations/   # Tavily, Neo4j, Yutori, Reka clients
├── render.yaml             # Render deployment config
└── .env.example            # Environment variable template
```

### Execution Modes

| Mode | Behavior |
|------|----------|
| `dry_run` | No side effects — no RSVPs, no calendar, no messages sent |
| `canary` | Suggests events but doesn't auto-apply |
| `live` | Full autonomy — auto-apply & send enabled |

---

## API Overview

All endpoints require JWT authentication unless noted.

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/events` | `GET` | List discovered events |
| `/api/events/{id}/accept` | `PUT` | Accept an event suggestion |
| `/api/events/{id}/reject` | `PUT` | Reject an event |
| `/api/people` | `GET` | List researched attendees |
| `/api/messages` | `GET` | List draft messages |
| `/api/messages/{id}/approve` | `PUT` | Approve a draft for sending |
| `/api/profile` | `GET/PUT` | User profile & preferences |
| `/api/feedback` | `POST` | Submit feedback on suggestions |
| `/api/agent/pause` | `POST` | Pause the agent |
| `/api/agent/resume` | `POST` | Resume the agent |
| `/api/chat` | `POST` | Chat with the agent (streaming) |
| `/ws/{user_id}` | `WebSocket` | Real-time agent updates |

---

## License

MIT

---

<p align="center">
  Built with Claude, FastAPI, Next.js, Neo4j, Tavily, Yutori, and Reka
</p>
