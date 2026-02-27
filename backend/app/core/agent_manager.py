"""Manages the background NexusAgent lifecycle.

Starts the agent as a background asyncio task, wires it to integration
clients and WebSocket broadcasting, and exposes pause/resume/run-now controls.

Agent state (paused/running) is persisted to DB so it survives restarts.
"""

from __future__ import annotations

import asyncio
import logging
from typing import Any

from sqlalchemy import select

from app.core.config import settings
from app.core.database import async_session_factory
from app.core.websocket import manager
from app.models.agent_state import AgentStateDB
from app.models.profile import UserProfileDB

logger = logging.getLogger(__name__)

_STATE_KEY = "agent_status"


class AgentManager:
    """Singleton that owns the background NexusAgent task."""

    def __init__(self) -> None:
        self._agent: Any = None  # NexusAgent (lazy import to avoid circular)
        self._task: asyncio.Task[None] | None = None
        self._status = "idle"

    # ── DB state helpers ───────────────────────────────────────────

    async def _load_persisted_status(self) -> str | None:
        """Read agent status from DB. Returns None if no row exists."""
        try:
            async with async_session_factory() as session:
                result = await session.execute(
                    select(AgentStateDB).where(AgentStateDB.key == _STATE_KEY)
                )
                row = result.scalar_one_or_none()
                return row.value if row else None
        except Exception:
            logger.debug("Failed to read persisted agent state", exc_info=True)
            return None

    async def _persist_status(self, value: str) -> None:
        """Upsert agent status to DB."""
        try:
            async with async_session_factory() as session:
                result = await session.execute(
                    select(AgentStateDB).where(AgentStateDB.key == _STATE_KEY)
                )
                row = result.scalar_one_or_none()
                if row:
                    row.value = value
                else:
                    session.add(AgentStateDB(key=_STATE_KEY, value=value))
                await session.commit()
        except Exception:
            logger.debug("Failed to persist agent state", exc_info=True)

    # ── Properties ────────────────────────────────────────────────────

    @property
    def status(self) -> str:
        if self._agent and self._agent.running:
            return "running"
        if self._task and not self._task.done():
            return "running"
        return self._status

    @property
    def agent(self) -> Any:
        return self._agent

    # ── Lifecycle ─────────────────────────────────────────────────────

    async def start(self) -> None:
        """Start the background agent for the first onboarded user."""
        if self._task and not self._task.done():
            logger.warning("Agent already running")
            return

        # Check if agent was paused before restart
        persisted = await self._load_persisted_status()
        if persisted == "paused":
            logger.info("[WINGMAN] Agent was paused — staying paused")
            self._status = "paused"
            # Still load the agent so resume works without full restart
            await self._init_agent()
            return

        user_profile = await self._load_user_profile()
        if not user_profile:
            logger.info("No onboarded user found — agent waiting")
            self._status = "waiting_for_user"
            return

        await self._init_agent()
        if not self._agent:
            return

        self._task = asyncio.create_task(self._run_agent())
        self._status = "running"
        await self._persist_status("running")

        await manager.broadcast(
            {
                "type": "agent:status",
                "data": {"status": "running", "agent": "wingman"},
            }
        )
        logger.info(
            "[WINGMAN] Background agent started for %s in %s mode",
            self._agent.user.get("name", "?"),
            settings.nexus_mode.value,
        )

    async def _init_agent(self) -> None:
        """Initialize the agent instance (without starting the loop)."""
        if self._agent:
            return

        user_profile = await self._load_user_profile()
        if not user_profile:
            return

        from app.agents.orchestrator import NexusAgent
        from app.integrations.neo4j_client import Neo4jClient
        from app.integrations.reka_client import RekaClient
        from app.integrations.tavily_client import TavilyClient
        from app.integrations.yutori_client import YutoriClient

        tavily = None
        if settings.tavily_api_key:
            try:
                tavily = TavilyClient(api_key=settings.tavily_api_key)
            except ValueError:
                logger.warning("Tavily API key invalid, agent won't have search")

        yutori = None
        if settings.yutori_api_key:
            try:
                yutori = YutoriClient(api_key=settings.yutori_api_key)
            except Exception:
                logger.warning("Yutori client init failed")

        neo4j = None
        if settings.neo4j_uri and settings.neo4j_password:
            try:
                neo4j = Neo4jClient(
                    uri=settings.neo4j_uri,
                    user=settings.neo4j_user,
                    password=settings.neo4j_password,
                )
                await neo4j.connect()
                logger.info("[WINGMAN] Neo4j connected")
            except Exception:
                logger.warning("Neo4j client init/connect failed", exc_info=True)
                neo4j = None

        reka = None
        if settings.reka_api_key:
            try:
                reka = RekaClient(api_key=settings.reka_api_key)
            except Exception:
                logger.warning("Reka client init failed")

        self._agent = NexusAgent(
            user_profile=user_profile,
            tavily=tavily,
            yutori=yutori,
            neo4j=neo4j,
            reka=reka,
            ws_broadcast=manager.broadcast,
            mode=settings.nexus_mode,
        )

    async def _run_agent(self) -> None:
        try:
            await self._agent.run_forever()
        except asyncio.CancelledError:
            logger.info("[WINGMAN] Agent task cancelled")
        except Exception:
            logger.exception("[WINGMAN] Agent crashed — will need manual restart")
            self._status = "crashed"
            await self._persist_status("crashed")
            await manager.broadcast(
                {
                    "type": "agent:status",
                    "data": {"status": "crashed", "agent": "wingman"},
                }
            )

    async def stop(self) -> None:
        """Gracefully stop the agent."""
        if self._agent:
            self._agent.pause()
            if self._agent._neo4j:
                try:
                    await self._agent._neo4j.disconnect()
                except Exception:
                    pass
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        self._status = "stopped"
        await self._persist_status("stopped")
        await manager.broadcast(
            {
                "type": "agent:status",
                "data": {"status": "stopped", "agent": "wingman"},
            }
        )

    async def pause(self) -> None:
        if self._agent:
            self._agent.pause()
            self._status = "paused"
            await self._persist_status("paused")
            await manager.broadcast(
                {
                    "type": "agent:status",
                    "data": {"status": "paused", "agent": "wingman"},
                }
            )

    async def resume(self) -> None:
        if self._agent and self._task and self._task.done():
            self._agent.running = True
            self._task = asyncio.create_task(self._run_agent())
            self._status = "running"
        elif self._agent:
            self._agent.running = True
            self._status = "running"
            # Agent was paused but task not done yet — start the loop
            if not self._task or self._task.done():
                self._task = asyncio.create_task(self._run_agent())
        else:
            await self.start()
            return  # start() handles persist + broadcast

        await self._persist_status("running")
        await manager.broadcast(
            {
                "type": "agent:status",
                "data": {"status": "running", "agent": "wingman"},
            }
        )

    async def run_now(self) -> None:
        """Trigger an immediate cycle (start if not running)."""
        if not self._agent:
            await self.start()
        elif self._task and self._task.done():
            await self.resume()

    def get_status(self) -> dict[str, Any]:
        tools_available: list[str] = []
        if self._agent:
            if self._agent._tavily:
                tools_available.append("tavily_search")
            if self._agent._yutori:
                tools_available.extend(["yutori_browse", "yutori_scout"])
            if self._agent._neo4j:
                tools_available.extend(["neo4j_query", "neo4j_write"])
            if self._agent._reka:
                tools_available.append("reka_vision")
        return {
            "status": self.status,
            "mode": settings.nexus_mode.value,
            "has_agent": self._agent is not None,
            "tools_available": tools_available,
        }

    # ── Helpers ───────────────────────────────────────────────────────

    async def _load_user_profile(self) -> dict[str, Any] | None:
        """Load the first onboarded user profile from DB."""
        async with async_session_factory() as session:
            result = await session.execute(
                select(UserProfileDB)
                .where(UserProfileDB.onboarding_completed.is_(True))
                .limit(1)
            )
            user = result.scalar_one_or_none()
            if not user:
                return None
            return {
                "name": user.name,
                "email": user.email,
                "role": user.role,
                "company": user.company,
                "product_description": user.product_description,
                "interests": user.interests or [],
                "networking_goals": user.networking_goals or [],
                "target_roles": user.target_roles or [],
                "target_companies": user.target_companies or [],
                "preferred_event_types": user.preferred_event_types or [],
                "max_events_per_week": user.max_events_per_week,
                "auto_apply_threshold": user.auto_apply_threshold,
                "suggest_threshold": user.suggest_threshold,
                "message_tone": user.message_tone,
            }


# Global singleton
agent_manager = AgentManager()
