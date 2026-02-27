from fastapi import APIRouter, Depends

from app.core.deps import get_current_user

router = APIRouter(
    prefix="/api/agent",
    tags=["agent"],
    dependencies=[Depends(get_current_user)],
)

_agent_state = {"status": "idle", "last_cycle": None, "events_discovered": 0, "events_applied": 0}


@router.get("/status")
async def get_agent_status() -> dict:
    return _agent_state


@router.post("/pause", status_code=200)
async def pause_agent() -> dict:
    _agent_state["status"] = "paused"
    return {"status": "paused"}


@router.post("/resume", status_code=200)
async def resume_agent() -> dict:
    _agent_state["status"] = "running"
    return {"status": "running"}


@router.post("/run-now", status_code=200)
async def run_now() -> dict:
    _agent_state["status"] = "running"
    return {"status": "triggered", "message": "Discovery cycle started"}
