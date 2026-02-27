## Inspiration

A venture partner who could write your first check is standing ten feet away from you. You don't know. You're talking to someone who has nothing to do with what you're building, because you walked into this room blind — just like everyone else.

Now imagine you didn't. Imagine you walked in already knowing every person in the room — what they're building, what they're looking for, and exactly why the two of you should talk. Imagine the first message was already sent before you left the house. That's not networking. That's an unfair advantage.

## What it does

Wingman is an autonomous agent that turns a list of names into real connections.

Give it an event and it will:

- **Identify every attendee** — from just a name and event context, it finds who they actually are (role, company, background, social profiles)
- **Tell you who matters** — scores each person against your goals so you know exactly who to find in the room
- **Send the first message for you** — drafts personalized intros based on deep research and queues them for your approval
- **Handle the full lifecycle** — discovers events, auto-applies, syncs your calendar, and sends follow-ups after

The core insight: a Luma attendee list with 80 blank profiles is useless to you, but it's a goldmine for an AI agent with web search and a knowledge graph. Wingman turns that list into a briefing document before you even leave the house.

## How we built it

Wingman is a **Claude-powered ReAct agent** — not a scripted pipeline. Claude is the brain: it observes, thinks, picks a tool, acts, and repeats.

The agent has a belt of 11 tools built on top of 4 sponsor integrations:

- **Tavily Search** — discovers events across the web and deep-researches attendees
- **Neo4j AuraDB** — stores the entire relationship graph (people, companies, events, topics) as long-term memory that survives context resets
- **Yutori Navigator + Scouting** — autonomously browses websites to RSVP/apply and monitors event platforms for real-time alerts via webhooks
- **Reka Vision** — verifies attendee identities by analyzing profile photos and social media content

The backend is **FastAPI** running a continuous agent loop as a Render background worker. The frontend is **Next.js 15** with real-time WebSocket updates — you see events, scores, and draft messages appear live as the agent works.

The feedback loop is the secret weapon: every time you accept, reject, or edit something, preference signals flow back into Neo4j and the scoring weights update. The agent literally gets better at being you.

## Challenges we ran into

**Making the agent truly autonomous without being reckless.** An agent that auto-applies to events and sends messages on your behalf needs guardrails. We built a tiered autonomy system — high-confidence actions (score > 90) happen automatically, medium-confidence actions get suggested, and anything involving outreach goes through human approval first.

**Attendee research depth vs. speed.** A single Tavily search gives you a name and title. That's not enough to write a meaningful cold message. We built an iterative research loop with a "richness score" — the agent keeps searching until it hits a threshold (0.7+), pulling from multiple angles (work history, recent talks, social presence, mutual connections).

**Identity resolution across platforms.** Someone named "Sarah Chen" on a Luma attendee list could be any of 10,000 Sarah Chens. Combining Tavily search, Reka Vision for profile photo cross-referencing, and Neo4j graph context (company, role, location) to disambiguate was one of the hardest problems we solved.

## Accomplishments that we're proud of

- The agent **actually works end-to-end**: it discovers real SF events, extracts real attendees, builds a real knowledge graph, and generates outreach messages that don't sound like a robot wrote them
- The **iterative research loop** is genuinely impressive — watching it go from "Sarah Chen" to a 3-paragraph dossier with investment thesis, recent podcast quotes, and mutual connections in under 60 seconds
- The **feedback loop closes the circle** — reject a Web3 event with "not my industry" and watch the agent immediately deprioritize every Web3 event in the queue
- Neo4j as **long-term memory** means the agent gets smarter across sessions, not just within one context window
- Built it in a single hackathon day with 4 sponsor tools deeply integrated, not bolted on

## What we learned

- **ReAct agents beat pipelines for messy, real-world tasks.** A fixed pipeline crashes when a page is blank or an attendee list is private. A thinking agent tries a different approach.
- **The knowledge graph is the killer feature.** Once you have people, companies, events, and topics in Neo4j with relationship edges, the queries you can run are magical: "Find me attendees who work at companies in my target list that I haven't met yet."
- **Human-in-the-loop isn't a compromise — it's the product.** Users don't want full autopilot for networking. They want a draft they can approve in 2 seconds. The approval moment is where trust is built.
- **Sponsor tools compose beautifully.** Tavily finds the signal, Yutori acts on it, Neo4j remembers it, Reka verifies it. Each tool does one thing extremely well and the agent orchestrates the rest.

## What's next for Wingman

- **Multi-city expansion** — SF is the prototype, but this pipeline works for NYC, London, Berlin, anywhere with a dense event scene
- **Post-event intelligence** — auto-detect who you actually talked to (calendar + location + photo analysis) and prioritize follow-ups accordingly
- **Warm intro routing** — "You know Alice, Alice knows Bob, Bob is attending Thursday's dinner. Want me to ask Alice for an intro?"
- **Team mode** — share a Wingman instance across a startup team so your CEO, CTO, and head of sales aren't all showing up to the same events
- **CRM sync** — push every contact, interaction, and follow-up into HubSpot/Salesforce automatically
- **Voice prep briefings** — morning audio summary: "You have 2 events today. Here are the 5 people you should find and what to talk about."
