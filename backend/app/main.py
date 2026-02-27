from contextlib import asynccontextmanager
from collections.abc import AsyncGenerator

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.core.database import Base, engine
from app.core.websocket import manager
from app.routers import (
    agent_control,
    auth,
    events,
    feedback,
    graph,
    messages,
    people,
    profile,
    targets,
    webhooks,
)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    # Startup: create tables (hackathon convenience, use Alembic in prod)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    print(f"[NEXUS] Starting in {settings.nexus_mode.value} mode")
    yield
    # Shutdown
    print("[NEXUS] Shutting down")


app = FastAPI(
    title="NEXUS API",
    description="Autonomous Networking Agent for SF",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.frontend_url],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Register routers
app.include_router(auth.router)  # Public: no auth required
app.include_router(events.router)
app.include_router(people.router)
app.include_router(messages.router)
app.include_router(profile.router)
app.include_router(feedback.router)
app.include_router(graph.router)
app.include_router(targets.router)
app.include_router(agent_control.router)
app.include_router(webhooks.router)


@app.get("/health")
async def health_check() -> dict[str, str]:
    return {"status": "ok", "mode": settings.nexus_mode.value}


@app.websocket("/ws/{user_id}")
async def websocket_endpoint(websocket: WebSocket, user_id: str) -> None:
    await manager.connect(user_id, websocket)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(user_id)
