from fastapi import APIRouter

router = APIRouter(prefix="/api/graph", tags=["graph"])


@router.get("/network")
async def get_network_graph() -> dict:
    return {"nodes": [], "edges": [], "stats": {"total_people": 0, "total_events": 0}}


@router.get("/suggestions")
async def get_graph_suggestions() -> list[dict]:
    return []
