from fastapi import APIRouter, Depends

from app.core.deps import get_current_user

router = APIRouter(
    prefix="/api/graph",
    tags=["graph"],
    dependencies=[Depends(get_current_user)],
)


@router.get("/network")
async def get_network_graph() -> dict:
    return {"nodes": [], "edges": [], "stats": {"total_people": 0, "total_events": 0}}


@router.get("/suggestions")
async def get_graph_suggestions() -> list[dict]:
    return []
