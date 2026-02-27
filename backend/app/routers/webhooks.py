from fastapi import APIRouter

router = APIRouter(prefix="/webhooks", tags=["webhooks"])


@router.post("/yutori/new-event", status_code=200)
async def yutori_new_event(body: dict) -> dict:
    # TODO: Parse scout webhook, trigger analysis pipeline
    return {"status": "received", "event_data": body}


@router.post("/yutori/apply-result", status_code=200)
async def yutori_apply_result(body: dict) -> dict:
    # TODO: Update event status based on Yutori browsing result
    task_id = body.get("task_id", "")
    status = body.get("status", "unknown")
    return {"status": "processed", "task_id": task_id, "result": status}


@router.post("/google/calendar", status_code=200)
async def google_calendar_webhook(body: dict) -> dict:
    # TODO: Sync calendar changes
    return {"status": "received"}
