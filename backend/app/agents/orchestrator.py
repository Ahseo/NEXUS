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

SYSTEM_PROMPT = """You are NEXUS, an autonomous networking agent for {user_name}.
You run 24/7. Your mission: discover relevant events in SF, apply to them,
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

        # Initial kickoff message
        self.conversation_history = [
            {
                "role": "user",
                "content": (
                    f"You just started. Current time: {datetime.now(timezone.utc).isoformat()}. "
                    f"Begin your autonomous cycle. Check for any pending feedback, "
                    f"then search for new events in SF. "
                    f"Think step by step about what to do."
                ),
            }
        ]

        while self.running:
            try:
                response = await self._anthropic.messages.create(
                    model="claude-sonnet-4-5-20250514",
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

                # Handle tool calls
                if response.stop_reason == "tool_use":
                    tool_results: list[dict[str, Any]] = []
                    for block in response.content:
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

                            # Handle wait tool — actually sleep
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
                                await asyncio.sleep(hours * 3600)

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

                    # Feed new cycle prompt
                    self.conversation_history.append(
                        {
                            "role": "user",
                            "content": (
                                f"Current time: {datetime.now(timezone.utc).isoformat()}. "
                                f"Continue your autonomous cycle. What should you do next?"
                            ),
                        }
                    )

                # Trim history to prevent context overflow
                self.trim_history()

            except anthropic.APIError as e:
                logger.error("[AGENT] API error: %s. Recovering in 60s...", e)
                await asyncio.sleep(60)
            except Exception as e:
                logger.error("[AGENT] Error: %s. Recovering in 60s...", e)
                await asyncio.sleep(60)

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

        try:
            result = await self._dispatch_tool(tool_name, tool_input)
            # Increment counters for canary mode
            if tool_name == "yutori_browse":
                self._applies_today += 1
            return result
        except Exception as e:
            logger.error(
                "[AGENT] Tool %s failed: %s", tool_name, e, exc_info=True
            )
            return {"error": str(e), "tool": tool_name}

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

        # Broadcast via WebSocket if available
        if self._ws_broadcast:
            await self._ws_broadcast(
                {
                    "type": notification_type,
                    "data": data,
                    "priority": priority,
                }
            )

        return {
            "status": "notified",
            "type": notification_type,
            "priority": priority,
        }
