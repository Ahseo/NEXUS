from fastapi import APIRouter

router = APIRouter(prefix="/api/profile", tags=["profile"])

_profile: dict = {}
_preferences: dict = {}


@router.get("")
async def get_profile() -> dict:
    return _profile or {"message": "No profile set up yet"}


@router.put("")
async def update_profile(body: dict) -> dict:
    _profile.update(body)
    return _profile


@router.get("/preferences")
async def get_preferences() -> dict:
    return _preferences or {
        "topic_weight": 30,
        "people_weight": 25,
        "type_weight": 15,
        "time_weight": 15,
        "history_weight": 15,
    }


@router.put("/preferences")
async def update_preferences(body: dict) -> dict:
    _preferences.update(body)
    return _preferences
