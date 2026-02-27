from fastapi import APIRouter, Depends, HTTPException

from app.core.deps import CurrentUser, DbSession, get_current_user
from app.models.profile import UserProfileDB

router = APIRouter(
    prefix="/api/profile",
    tags=["profile"],
    dependencies=[Depends(get_current_user)],
)


@router.get("")
async def get_profile(user: CurrentUser, db: DbSession) -> dict:
    profile = await db.get(UserProfileDB, user["user_id"])
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")
    return {
        "id": profile.id,
        "name": profile.name,
        "email": profile.email,
        "role": profile.role,
        "company": profile.company,
        "product_description": profile.product_description,
        "linkedin": profile.linkedin,
        "twitter": profile.twitter,
        "networking_goals": profile.networking_goals or [],
        "target_roles": profile.target_roles or [],
        "target_companies": profile.target_companies or [],
        "target_industries": profile.target_industries or [],
        "interests": profile.interests or [],
        "preferred_event_types": profile.preferred_event_types or [],
        "max_events_per_week": profile.max_events_per_week,
        "max_event_spend": profile.max_event_spend,
        "preferred_days": profile.preferred_days or [],
        "preferred_times": profile.preferred_times or [],
        "message_tone": profile.message_tone,
        "auto_apply_threshold": profile.auto_apply_threshold,
        "suggest_threshold": profile.suggest_threshold,
        "auto_schedule_threshold": profile.auto_schedule_threshold,
        "onboarding_completed": profile.onboarding_completed,
    }


@router.put("")
async def update_profile(body: dict, user: CurrentUser, db: DbSession) -> dict:
    profile = await db.get(UserProfileDB, user["user_id"])
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")

    updatable_fields = [
        "name", "email", "role", "company", "product_description",
        "linkedin", "twitter", "networking_goals", "target_roles",
        "target_companies", "target_industries", "interests",
        "preferred_event_types", "max_events_per_week", "max_event_spend",
        "preferred_days", "preferred_times", "message_tone",
        "auto_apply_threshold", "suggest_threshold", "auto_schedule_threshold",
    ]
    for field in updatable_fields:
        if field in body:
            setattr(profile, field, body[field])

    # Mark onboarding as completed on first profile save
    if not profile.onboarding_completed:
        profile.onboarding_completed = True

    await db.commit()
    await db.refresh(profile)
    return {"status": "updated", "id": profile.id}


@router.get("/preferences")
async def get_preferences(user: CurrentUser, db: DbSession) -> dict:
    profile = await db.get(UserProfileDB, user["user_id"])
    if not profile:
        return {
            "topic_weight": 30,
            "people_weight": 25,
            "type_weight": 15,
            "time_weight": 15,
            "history_weight": 15,
        }
    return {
        "auto_apply_threshold": profile.auto_apply_threshold,
        "suggest_threshold": profile.suggest_threshold,
        "auto_schedule_threshold": profile.auto_schedule_threshold,
        "topic_weight": 30,
        "people_weight": 25,
        "type_weight": 15,
        "time_weight": 15,
        "history_weight": 15,
    }


@router.put("/preferences")
async def update_preferences(body: dict, user: CurrentUser, db: DbSession) -> dict:
    profile = await db.get(UserProfileDB, user["user_id"])
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")

    pref_fields = ["auto_apply_threshold", "suggest_threshold", "auto_schedule_threshold"]
    for field in pref_fields:
        if field in body:
            setattr(profile, field, body[field])

    await db.commit()
    await db.refresh(profile)
    return {"status": "updated"}
