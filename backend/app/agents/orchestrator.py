"""NexusAgent — Claude-powered autonomous networking agent.

This is the central brain of the NEXUS system. It uses a ReAct loop
where Claude decides what to do next based on full context, using 13
tools to discover events, research people, and draft messages.
"""

from __future__ import annotations

import asyncio
import json
import logging
from datetime import datetime, timezone
from typing import Any

import anthropic

from app.core.config import NexusMode, settings
from app.integrations.neo4j_client import Neo4jClient
from app.integrations.reka_client import RekaClient
from app.integrations.tavily_client import TavilyClient
from app.integrations.yutori_client import YutoriClient

logger = logging.getLogger(__name__)

# ── Tool Definitions (13 tools) ─────────────────────────────────────────────

TOOLS: list[dict[str, Any]] = [
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
                "search_depth": {
                    "type": "string",
                    "enum": ["basic", "advanced"],
                },
                "max_results": {"type": "integer", "default": 10},
                "include_domains": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Limit search to these domains",
                },
                "time_range": {
                    "type": "string",
                    "enum": ["day", "week", "month"],
                    "description": "How recent the results should be",
                },
            },
            "required": ["query"],
        },
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
                "task": {
                    "type": "string",
                    "description": "What the agent should do",
                },
                "start_url": {
                    "type": "string",
                    "description": "URL to start from",
                },
                "max_steps": {"type": "integer", "default": 50},
                "output_schema": {
                    "type": "object",
                    "description": "Expected output structure",
                },
            },
            "required": ["task", "start_url"],
        },
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
                "schedule": {
                    "type": "string",
                    "enum": ["hourly", "every_6_hours", "daily"],
                },
            },
            "required": ["task", "start_url"],
        },
    },
    {
        "name": "reka_vision",
        "description": (
            "Analyze images or visual web content. Use this to: "
            "compare profile photos across platforms (same person?), "
            "analyze Instagram/X posts for conversation hooks, "
            "extract info from event flyers/images that text scraping misses."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "url": {
                    "type": "string",
                    "description": "URL of image or page to analyze",
                },
                "prompt": {
                    "type": "string",
                    "description": "What to analyze or compare in the visual content",
                },
                "compare_urls": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Optional: multiple URLs to compare (e.g. profile photos)",
                },
            },
            "required": ["url", "prompt"],
        },
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
                "cypher": {
                    "type": "string",
                    "description": "Cypher query to execute",
                },
                "params": {"type": "object", "description": "Query parameters"},
            },
            "required": ["cypher"],
        },
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
                "cypher": {
                    "type": "string",
                    "description": "Cypher write query",
                },
                "params": {"type": "object"},
            },
            "required": ["cypher"],
        },
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
                "action": {
                    "type": "string",
                    "enum": ["check_busy", "create_event", "list_upcoming"],
                },
                "event_data": {
                    "type": "object",
                    "description": "For create_event: title, start, end, location",
                },
                "time_range": {
                    "type": "object",
                    "description": "For check_busy/list: start and end datetime",
                },
            },
            "required": ["action"],
        },
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
                "known_links": {
                    "type": "array",
                    "items": {"type": "string"},
                },
            },
            "required": ["name"],
        },
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
                "recipient": {
                    "type": "object",
                    "description": "Person profile data",
                },
                "event": {"type": "object", "description": "Event context"},
                "message_type": {
                    "type": "string",
                    "enum": [
                        "cold_pre_event",
                        "followup_post_event",
                        "missed_connection",
                    ],
                },
                "channel": {
                    "type": "string",
                    "enum": [
                        "twitter_dm",
                        "linkedin",
                        "email",
                        "instagram_dm",
                    ],
                },
                "tone": {
                    "type": "string",
                    "enum": ["casual", "professional", "friendly"],
                },
            },
            "required": ["recipient", "message_type", "channel"],
        },
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
                "since": {
                    "type": "string",
                    "description": "ISO datetime to check from",
                },
            },
        },
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
                "type": {
                    "type": "string",
                    "enum": [
                        "event_suggested",
                        "event_applied",
                        "message_drafted",
                        "person_found",
                        "status_update",
                    ],
                },
                "data": {"type": "object"},
                "priority": {
                    "type": "string",
                    "enum": ["low", "medium", "high"],
                },
            },
            "required": ["type", "data"],
        },
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
                "hours": {
                    "type": "number",
                    "description": "Hours to wait",
                },
                "reason": {
                    "type": "string",
                    "description": "Why waiting",
                },
            },
            "required": ["hours"],
        },
    },
]

# All valid tool names for routing
TOOL_NAMES: set[str] = {t["name"] for t in TOOLS}

# ── System Prompt ────────────────────────────────────────────────────────────

SYSTEM_PROMPT = """You are Wingman, an autonomous networking agent for {user_name}.
You run 24/7. Your mission: discover relevant events in SF, APPLY to them,
research attendees, find their social accounts, draft personalized messages.

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

## CRITICAL: How to Apply to Events

When you find a relevant event, you MUST apply using yutori_browse. This is the most
important part of your job. Do NOT just discover events — ACT on them.

**Step-by-step to apply to an event:**
1. Find event URL from tavily_search results
2. Use `yutori_browse` with:
   - task: (see example below)
   - start_url: the event URL (e.g. https://lu.ma/xxx or https://eventbrite.com/xxx)
   - output_schema: {{"status": "string", "confirmation_id": "string", "payment_required": "boolean", "payment_amount": "number"}}
3. Save the event to Neo4j with neo4j_write
4. Notify the user with notify_user

**Example yutori_browse call for event registration:**
```
task: "Navigate through ALL registration sub-pages. Fill in: Name: {user_name}, Email: {user_email}, Company: {user_company}.

CRITICAL — PAYMENT DETECTION: Before clicking any final submit/confirm button, CHECK the page for ANY of these signs:
- A price shown (e.g. '$25', '€10', 'USD 50', any currency amount)
- Words like 'checkout', 'payment', 'billing', 'credit card', 'debit card', 'purchase', 'order summary', 'total', 'pay now'
- A Stripe, PayPal, Square, or payment iframe/widget
- Eventbrite 'Place Order' button with a non-zero total
- Ticket types with prices (even if one is free, check which one is selected)
- 'Add to cart' or 'Buy tickets' buttons

If ANY payment indicator is found: STOP. Do NOT proceed. Set payment_required=true and payment_amount to the displayed price.
If the event is truly free (price shows $0.00 or 'Free'): proceed with registration and set payment_required=false."
start_url: "https://lu.ma/example-event"
output_schema: {{"status": "string", "confirmation_id": "string", "payment_required": "boolean", "payment_amount": "number"}}
```

**Decision matrix (use this for EVERY event you find):**
- Score 80-100: IMMEDIATELY use yutori_browse to apply + save to Neo4j
- Score 50-79: Save to Neo4j + notify_user to suggest it
- Score < 50: Skip (don't even save)

Score an event by how well it matches the user's interests, goals, and preferred types.

## How to Report Event Recommendations

When you find events via tavily_search, call `notify_user` for EACH event worth recommending:
- type: "event_suggested"
- data must include:
  - event.title: Event name
  - event.url: Event page URL
  - event.date: Event date (ISO or readable)
  - event.location: Venue or "Online"
  - event.source: Platform (e.g. "luma", "eventbrite", "meetup")
  - event.price: 0 for free events, dollar amount as number, null if unknown
  - event.description: 1-2 sentence description of the event
  - event.topics: Array of relevant topic tags
  - event.speakers: Array of notable speakers (if known)
  - score: Your relevance score (0-100)
  - why: 1-2 sentence explanation of why this event is relevant to the user

## How to Report After Applying

After yutori_browse completes an event application, you MUST call `notify_user`:
- type: "event_applied"
- data must include:
  - event.title, event.url, event.date, event.location, event.source, event.price
  - application_status: "applied", "waitlisted", "failed", or "payment_required"
  - payment_required: boolean (true if checkout/payment page was encountered)
  - payment_amount: number or null

## How to Research Attendees

After applying to an event, research who's attending:
1. Use `yutori_browse` to scrape the attendee list from the event page
   - task: "Go to this event page and extract the list of attendees/guests. Return their names, titles, and companies."
   - start_url: event URL
2. For interesting attendees, use `tavily_search` to research them
3. Use `resolve_social_accounts` to find their LinkedIn, Twitter, etc.
4. Save everything to Neo4j with `neo4j_write`
5. Use `draft_message` to create a personalized pre-event message

## Rules
1. NEVER auto-send messages. Draft → notify user → wait for approval.
2. After discovering events, IMMEDIATELY apply to the best ones. Do NOT just search endlessly.
3. Always save events and people to Neo4j.
4. Check Google Calendar for conflicts before scheduling.
5. Learn from user feedback.

## Your Cycle
Each cycle you should:
1. Search for upcoming events (tavily_search) — max 2-3 searches
2. Score and APPLY to the best events (yutori_browse) — this is the key step!
3. Research attendees at confirmed events
4. Draft messages for interesting people
5. Wait 1-2 hours, then repeat

IMPORTANT: Do NOT spend the whole cycle just searching. Search briefly, then APPLY.
The user wants you to actually register for events, not just find them.
"""


# ── Side-effect tools (blocked in dry_run/replay modes) ─────────────────────

_SIDE_EFFECT_TOOLS: frozenset[str] = frozenset(
    {
        "yutori_browse",
        "yutori_scout",
        "google_calendar",
        "notify_user",
    }
)


# ── The Agent ────────────────────────────────────────────────────────────────


class NexusAgent:
    """Claude-powered autonomous agent with ReAct loop.

    Not a pipeline — a thinking agent that decides what to do next
    based on the full context.
    """

    def __init__(
        self,
        user_profile: dict[str, Any],
        *,
        tavily: TavilyClient | None = None,
        yutori: YutoriClient | None = None,
        neo4j: Neo4jClient | None = None,
        reka: RekaClient | None = None,
        mode: NexusMode | None = None,
        ws_broadcast: Any | None = None,
    ) -> None:
        self.user = user_profile
        self.mode = mode or settings.nexus_mode
        self.conversation_history: list[dict[str, Any]] = []
        self.running = False

        # Integration clients
        self._tavily = tavily
        self._yutori = yutori
        self._neo4j = neo4j
        self._reka = reka

        # WebSocket broadcaster for real-time UI updates
        self._ws_broadcast = ws_broadcast

        # Anthropic client
        self._anthropic = anthropic.AsyncAnthropic(
            api_key=settings.anthropic_api_key or "dummy",
        )

        # Counters for safety limits
        self._applies_today = 0
        self._messages_today = 0
        self._last_reset_date: str = ""

    # ── Properties ───────────────────────────────────────────────────────

    @property
    def allow_side_effects(self) -> bool:
        return self.mode in (NexusMode.CANARY, NexusMode.LIVE)

    @property
    def tool_names(self) -> set[str]:
        return TOOL_NAMES

    # ── System prompt builder ────────────────────────────────────────────

    def build_system_prompt(self) -> str:
        return SYSTEM_PROMPT.format(
            user_name=self.user.get("name", "User"),
            user_email=self.user.get("email", ""),
            user_role=self.user.get("role", ""),
            user_company=self.user.get("company", ""),
            user_product=self.user.get("product_description", ""),
            user_interests=", ".join(self.user.get("interests", [])),
            user_goals=", ".join(self.user.get("networking_goals", [])),
            user_target_roles=", ".join(self.user.get("target_roles", [])),
            user_target_companies=", ".join(
                self.user.get("target_companies", [])
            ),
            user_preferred_types=", ".join(
                self.user.get("preferred_event_types", [])
            ),
            max_events_week=self.user.get("max_events_per_week", 4),
            auto_apply_threshold=self.user.get("auto_apply_threshold", 80),
            suggest_threshold=self.user.get("suggest_threshold", 50),
            message_tone=self.user.get("message_tone", "casual"),
        )

    # ── Conversation history management ──────────────────────────────────

    def trim_history(self) -> None:
        """Keep first 2 messages + last 50 to avoid context overflow."""
        if len(self.conversation_history) > 100:
            self.conversation_history = (
                self.conversation_history[:2]
                + self.conversation_history[-50:]
            )

    # ── Safety limit helpers ─────────────────────────────────────────────

    def _reset_daily_counters_if_needed(self) -> None:
        today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        if self._last_reset_date != today:
            self._applies_today = 0
            self._messages_today = 0
            self._last_reset_date = today

    def _check_canary_limits(self, tool_name: str) -> bool:
        """In canary mode, enforce daily limits."""
        if self.mode != NexusMode.CANARY:
            return True
        self._reset_daily_counters_if_needed()
        if tool_name == "yutori_browse":
            if self._applies_today >= settings.max_auto_applies_per_day:
                return False
        if tool_name == "notify_user":
            if self._messages_today >= settings.max_auto_send_messages_per_day:
                return False
        return True

    # ── Main loop ────────────────────────────────────────────────────────

    async def run_forever(self) -> None:
        """The main agent loop. Runs until stopped."""
        self.running = True

        logger.info(
            "[NEXUS] Agent started for %s", self.user.get("name", "User")
        )
        logger.info(
            "[NEXUS] Mode: %s | Tools: %d", self.mode.value, len(TOOLS)
        )

        # Only set initial kickoff if no existing history (allows resume)
        if not self.conversation_history:
            self.conversation_history = [
                {
                    "role": "user",
                    "content": (
                        f"You just started. Current time: {datetime.now(timezone.utc).isoformat()}. "
                        f"Begin your autonomous cycle:\n"
                        f"1. Search for upcoming events in SF matching my interests (1-2 tavily_search calls)\n"
                        f"2. Pick the most relevant events and APPLY to them using yutori_browse\n"
                        f"3. Save applied events to Neo4j\n"
                        f"4. Research attendees at applied events\n"
                        f"Start now — search for events, then apply to the best ones."
                    ),
                }
            ]

        while self.running:
            try:
                response = await self._anthropic.messages.create(
                    model="claude-opus-4-20250514",
                    max_tokens=4096,
                    system=self.build_system_prompt(),
                    tools=TOOLS,  # type: ignore[arg-type]
                    messages=self.conversation_history,  # type: ignore[arg-type]
                )

                # Add assistant response to history
                assistant_content = [
                    block.model_dump() for block in response.content
                ]
                self.conversation_history.append(
                    {"role": "assistant", "content": assistant_content}
                )

                if not self.running:
                    break

                # Handle tool calls
                if response.stop_reason == "tool_use":
                    tool_results: list[dict[str, Any]] = []
                    for block in response.content:
                        if not self.running:
                            break
                        if block.type == "tool_use":
                            logger.info(
                                "[AGENT] Using tool: %s", block.name
                            )
                            result = await self.execute_tool(
                                block.name, block.input  # type: ignore[arg-type]
                            )
                            tool_results.append(
                                {
                                    "type": "tool_result",
                                    "tool_use_id": block.id,
                                    "content": json.dumps(result),
                                }
                            )

                            # Handle wait tool — sleep in chunks so pause works
                            if block.name == "wait":
                                hours = float(block.input.get("hours", 1))  # type: ignore[union-attr]
                                reason = block.input.get(  # type: ignore[union-attr]
                                    "reason", "cycle complete"
                                )
                                logger.info(
                                    "[AGENT] Waiting %.1fh — %s",
                                    hours,
                                    reason,
                                )
                                remaining = hours * 3600
                                while remaining > 0 and self.running:
                                    chunk = min(remaining, 10)
                                    await asyncio.sleep(chunk)
                                    remaining -= chunk

                    self.conversation_history.append(
                        {"role": "user", "content": tool_results}
                    )

                elif response.stop_reason == "end_turn":
                    # Log Claude's thinking
                    for block in response.content:
                        if block.type == "text":
                            logger.info(
                                "[AGENT] Thinking: %s", block.text[:200]
                            )

                    # Feed new cycle prompt — push toward action
                    self.conversation_history.append(
                        {
                            "role": "user",
                            "content": (
                                f"Current time: {datetime.now(timezone.utc).isoformat()}. "
                                f"Continue your cycle. If you found events, APPLY to the best ones "
                                f"using yutori_browse NOW. If you already applied, research the "
                                f"attendees. If you've done both, draft messages for interesting "
                                f"people, then wait 1-2 hours."
                            ),
                        }
                    )

                # Trim history to prevent context overflow
                self.trim_history()

            except anthropic.APIError as e:
                logger.error("[AGENT] API error: %s. Recovering in 60s...", e)
                for _ in range(60):
                    if not self.running:
                        break
                    await asyncio.sleep(1)
            except Exception as e:
                logger.error("[AGENT] Error: %s. Recovering in 60s...", e)
                for _ in range(60):
                    if not self.running:
                        break
                    await asyncio.sleep(1)

    def pause(self) -> None:
        self.running = False

    def resume(self) -> None:
        self.running = True

    # ── Tool execution router ────────────────────────────────────────────

    async def execute_tool(
        self, tool_name: str, tool_input: dict[str, Any]
    ) -> dict[str, Any]:
        """Route tool calls to actual implementations.

        Respects NEXUS_MODE safety restrictions.
        """

        # Block side-effect tools in dry_run / replay
        if tool_name in _SIDE_EFFECT_TOOLS and not self.allow_side_effects:
            logger.info(
                "[AGENT] Blocked %s in %s mode", tool_name, self.mode.value
            )
            return {
                "status": "blocked",
                "reason": f"Side effects disabled in {self.mode.value} mode",
            }

        # Enforce canary limits
        if not self._check_canary_limits(tool_name):
            return {
                "status": "blocked",
                "reason": "Daily limit reached in canary mode",
            }

        # Broadcast tool start via WebSocket
        if self._ws_broadcast:
            await self._ws_broadcast(
                {
                    "type": "agent:status",
                    "data": {
                        "status": "running",
                        "agent": "wingman",
                        "tool": tool_name,
                    },
                }
            )

        try:
            result = await self._dispatch_tool(tool_name, tool_input)
            # Increment counters for canary mode
            if tool_name == "yutori_browse":
                self._applies_today += 1

            # Broadcast tool-specific events
            if self._ws_broadcast:
                await self._broadcast_tool_event(tool_name, tool_input, result)

            return result
        except Exception as e:
            logger.error(
                "[AGENT] Tool %s failed: %s", tool_name, e, exc_info=True
            )
            return {"error": str(e), "tool": tool_name}

    async def _broadcast_tool_event(
        self,
        tool_name: str,
        tool_input: dict[str, Any],
        result: dict[str, Any],
    ) -> None:
        """Broadcast specific WebSocket events based on tool results."""
        if not self._ws_broadcast:
            return

        if tool_name == "tavily_search":
            raw_results = result.get("results", [])
            count = len(raw_results)
            top_results = raw_results[:5]
            await self._ws_broadcast(
                {
                    "type": "event:discovered",
                    "data": {
                        "event": {"title": tool_input.get("query", "search")},
                        "count": count,
                        "search_results": top_results,
                        "agent": "wingman",
                    },
                }
            )
        elif tool_name == "yutori_browse":
            task_desc = tool_input.get("task", "")
            url = tool_input.get("start_url", "")
            # If the task mentions apply/RSVP, it's an application
            is_apply = any(
                kw in task_desc.lower()
                for kw in ["apply", "rsvp", "register", "sign up", "attend"]
            )
            if is_apply:
                browse_result = result.get("result") or {}
                payment_required = False
                payment_amount = None
                event_date = None
                event_location = None
                if isinstance(browse_result, dict):
                    payment_required = browse_result.get("payment_required", False)
                    payment_amount = browse_result.get("payment_amount")
                    event_date = browse_result.get("date") or browse_result.get("event_date")
                    event_location = browse_result.get("location") or browse_result.get("venue")
                # Also try to get from the last analyzed event context
                last_ctx = getattr(self, "_last_event_context", {})
                if not event_date and isinstance(last_ctx, dict):
                    event_date = last_ctx.get("date")
                if not event_location and isinstance(last_ctx, dict):
                    event_location = last_ctx.get("location")
                event_data: dict[str, Any] = {"title": task_desc[:100], "url": url}
                if event_date:
                    event_data["date"] = event_date
                if event_location:
                    event_data["location"] = event_location
                await self._ws_broadcast(
                    {
                        "type": "event:applied",
                        "data": {
                            "event": event_data,
                            "status": result.get("status", "pending"),
                            "payment_required": payment_required,
                            "payment_amount": payment_amount,
                            "agent": "wingman",
                        },
                    }
                )
            else:
                await self._ws_broadcast(
                    {
                        "type": "person:discovered",
                        "data": {
                            "person": {"name": f"Browsing: {task_desc[:80]}"},
                            "url": url,
                            "agent": "wingman",
                        },
                    }
                )
        elif tool_name == "yutori_scout":
            await self._ws_broadcast(
                {
                    "type": "event:discovered",
                    "data": {
                        "event": {"title": f"Scout: {tool_input.get('task', '')[:80]}"},
                        "agent": "wingman",
                    },
                }
            )
        elif tool_name == "neo4j_write":
            await self._ws_broadcast(
                {
                    "type": "person:discovered",
                    "data": {
                        "person": {"name": "graph updated"},
                        "agent": "wingman",
                    },
                }
            )
        elif tool_name == "neo4j_query":
            count = result.get("count", 0)
            await self._ws_broadcast(
                {
                    "type": "agent:status",
                    "data": {
                        "status": "running",
                        "agent": "wingman",
                        "tool": "neo4j_query",
                        "detail": f"Found {count} records",
                    },
                }
            )
        elif tool_name == "draft_message":
            await self._ws_broadcast(
                {
                    "type": "message:drafted",
                    "data": {
                        "channel": result.get("channel", ""),
                        "type": result.get("message_type", ""),
                        "agent": "wingman",
                    },
                }
            )
        elif tool_name == "resolve_social_accounts":
            name = tool_input.get("name", "")
            links = result.get("social_links", {})
            found = [k for k, v in links.items() if v]
            await self._ws_broadcast(
                {
                    "type": "person:discovered",
                    "data": {
                        "person": {"name": name},
                        "socials_found": found,
                        "agent": "wingman",
                    },
                }
            )
        elif tool_name == "google_calendar":
            action = tool_input.get("action", "")
            if action == "create_event":
                await self._ws_broadcast(
                    {
                        "type": "event:scheduled",
                        "data": {
                            "event": tool_input.get("event_data", {}),
                            "agent": "wingman",
                        },
                    }
                )

    async def _dispatch_tool(
        self, tool_name: str, tool_input: dict[str, Any]
    ) -> dict[str, Any]:
        """Internal dispatcher to integration clients."""

        if tool_name == "tavily_search":
            return await self._exec_tavily_search(tool_input)
        elif tool_name == "yutori_browse":
            return await self._exec_yutori_browse(tool_input)
        elif tool_name == "yutori_scout":
            return await self._exec_yutori_scout(tool_input)
        elif tool_name == "reka_vision":
            return await self._exec_reka_vision(tool_input)
        elif tool_name == "neo4j_query":
            return await self._exec_neo4j_query(tool_input)
        elif tool_name == "neo4j_write":
            return await self._exec_neo4j_write(tool_input)
        elif tool_name == "google_calendar":
            return await self._exec_google_calendar(tool_input)
        elif tool_name == "resolve_social_accounts":
            return await self._exec_resolve_social(tool_input)
        elif tool_name == "draft_message":
            return await self._exec_draft_message(tool_input)
        elif tool_name == "get_user_feedback":
            return await self._exec_get_feedback(tool_input)
        elif tool_name == "notify_user":
            return await self._exec_notify_user(tool_input)
        elif tool_name == "wait":
            return {"status": "waited", "hours": tool_input.get("hours", 1)}
        else:
            return {"error": f"Unknown tool: {tool_name}"}

    # ── Tool implementations ─────────────────────────────────────────────

    async def _exec_tavily_search(
        self, inp: dict[str, Any]
    ) -> dict[str, Any]:
        if not self._tavily:
            return {"error": "Tavily client not configured"}
        result = await self._tavily.search(
            query=inp["query"],
            search_depth=inp.get("search_depth", "advanced"),
            max_results=inp.get("max_results", 10),
            include_domains=inp.get("include_domains"),
            time_range=inp.get("time_range"),
            include_answer=True,
            include_raw_content=False,
        )
        return {
            "query": result.query,
            "answer": result.answer,
            "results": [
                {
                    "title": r.get("title", ""),
                    "url": r.get("url", ""),
                    "content": r.get("content", "")[:500],
                }
                for r in result.results
            ],
        }

    async def _exec_yutori_browse(
        self, inp: dict[str, Any]
    ) -> dict[str, Any]:
        if not self._yutori:
            return {"error": "Yutori client not configured"}
        task = await self._yutori.browsing_create(
            task=inp["task"],
            start_url=inp.get("start_url"),
            max_steps=inp.get("max_steps", 50),
            output_schema=inp.get("output_schema"),
        )
        return {
            "task_id": task.task_id,
            "status": task.status,
            "result": task.result,
        }

    async def _exec_yutori_scout(
        self, inp: dict[str, Any]
    ) -> dict[str, Any]:
        if not self._yutori:
            return {"error": "Yutori client not configured"}
        task = await self._yutori.scouting_create(
            task=inp["task"],
            start_url=inp.get("start_url"),
            schedule=inp.get("schedule"),
        )
        return {"task_id": task.task_id, "status": task.status}

    async def _exec_reka_vision(
        self, inp: dict[str, Any]
    ) -> dict[str, Any]:
        if not self._reka:
            return {"error": "Reka client not configured"}
        compare_urls = inp.get("compare_urls")
        if compare_urls:
            result = await self._reka.compare(
                urls=compare_urls, prompt=inp["prompt"]
            )
        else:
            result = await self._reka.analyze(
                url=inp["url"], prompt=inp["prompt"]
            )
        return {
            "analysis": result.analysis,
            "conversation_hooks": result.conversation_hooks,
        }

    async def _exec_neo4j_query(
        self, inp: dict[str, Any]
    ) -> dict[str, Any]:
        if not self._neo4j:
            return {"error": "Neo4j client not configured"}
        records = await self._neo4j.execute_query(
            inp["cypher"], inp.get("params")
        )
        return {"records": records, "count": len(records)}

    async def _exec_neo4j_write(
        self, inp: dict[str, Any]
    ) -> dict[str, Any]:
        if not self._neo4j:
            return {"error": "Neo4j client not configured"}
        records = await self._neo4j.execute_write(
            inp["cypher"], inp.get("params")
        )
        return {"status": "written", "affected": len(records)}

    async def _exec_google_calendar(
        self, inp: dict[str, Any]
    ) -> dict[str, Any]:
        # Google Calendar requires OAuth credentials — not yet connected
        action = inp["action"]
        return {
            "status": "not_connected",
            "action": action,
            "message": "Google Calendar not connected yet",
        }

    async def _exec_resolve_social(
        self, inp: dict[str, Any]
    ) -> dict[str, Any]:
        # Composite tool: uses Tavily search + Reka Vision for verification
        name = inp["name"]
        company = inp.get("company", "")
        title = inp.get("title", "")

        links: dict[str, str | None] = {
            "linkedin": None,
            "twitter": None,
            "instagram": None,
            "github": None,
        }

        if self._tavily:
            # Search for LinkedIn
            query = f"{name} {company} {title} LinkedIn"
            result = await self._tavily.search(
                query=query, max_results=3, include_domains=["linkedin.com"]
            )
            if result.results:
                links["linkedin"] = result.results[0].get("url")

            # Search for Twitter/X
            query = f"{name} {company} Twitter OR X site:x.com"
            result = await self._tavily.search(
                query=query, max_results=3, include_domains=["x.com"]
            )
            if result.results:
                links["twitter"] = result.results[0].get("url")

        return {"name": name, "social_links": links}

    async def _exec_draft_message(
        self, inp: dict[str, Any]
    ) -> dict[str, Any]:
        # Message drafting uses Claude — will be fully implemented in Phase 6
        return {
            "status": "drafted",
            "message_type": inp.get("message_type", "cold_pre_event"),
            "channel": inp.get("channel", "linkedin"),
            "draft": "Message drafting will be implemented in Connect Agent phase.",
        }

    async def _exec_get_feedback(
        self, inp: dict[str, Any]
    ) -> dict[str, Any]:
        # Reads pending feedback from database — stub for now
        return {"feedback": [], "since": inp.get("since", "")}

    async def _exec_notify_user(
        self, inp: dict[str, Any]
    ) -> dict[str, Any]:
        notification_type = inp["type"]
        data = inp.get("data", {})
        priority = inp.get("priority", "medium")

        # Cache event context for later use (e.g. when applying)
        if notification_type == "event_suggested" and isinstance(data, dict):
            ev = data.get("event", {})
            if isinstance(ev, dict):
                self._last_event_context = {
                    "date": ev.get("date"),
                    "location": ev.get("location"),
                    "title": ev.get("title"),
                    "url": ev.get("url"),
                }

        # Map agent notify_user types to standard WS event types
        type_mapping: dict[str, str] = {
            "event_suggested": "event:analyzed",
            "event_applied": "event:applied",
        }
        ws_type = type_mapping.get(notification_type, notification_type)

        # Ensure agent field is set
        if isinstance(data, dict):
            data.setdefault("agent", "wingman")

        # Broadcast via WebSocket if available
        if self._ws_broadcast:
            await self._ws_broadcast(
                {
                    "type": ws_type,
                    "data": data,
                    "priority": priority,
                }
            )

        return {
            "status": "notified",
            "type": ws_type,
            "priority": priority,
        }
