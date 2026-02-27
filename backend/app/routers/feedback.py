from fastapi import APIRouter

router = APIRouter(prefix="/api/feedback", tags=["feedback"])

_feedback_store: list[dict] = []


@router.post("", status_code=201)
async def submit_feedback(body: dict) -> dict:
    _feedback_store.append(body)
    return {"status": "received", "feedback_count": len(_feedback_store)}


@router.get("/stats")
async def get_feedback_stats() -> dict:
    total = len(_feedback_store)
    accepts = sum(1 for f in _feedback_store if f.get("action") == "accept")
    rejects = sum(1 for f in _feedback_store if f.get("action") == "reject")
    return {
        "total_feedback": total,
        "accept_count": accepts,
        "reject_count": rejects,
        "accept_rate": accepts / total if total > 0 else 0,
    }
