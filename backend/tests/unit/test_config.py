import os

import pytest

from app.core.config import NexusMode, Settings


def test_default_settings():
    s = Settings(
        _env_file=None,  # type: ignore[call-arg]
    )
    assert s.nexus_mode == NexusMode.DRY_RUN
    assert s.auto_apply_threshold == 80
    assert s.suggest_threshold == 50
    assert s.auto_schedule_threshold == 85
    assert s.max_auto_applies_per_day == 10
    assert s.max_auto_send_messages_per_day == 5


def test_allow_side_effects_dry_run():
    s = Settings(nexus_mode=NexusMode.DRY_RUN, _env_file=None)  # type: ignore[call-arg]
    assert s.allow_side_effects is False


def test_allow_side_effects_live():
    s = Settings(nexus_mode=NexusMode.LIVE, _env_file=None)  # type: ignore[call-arg]
    assert s.allow_side_effects is True


def test_allow_side_effects_canary():
    s = Settings(nexus_mode=NexusMode.CANARY, _env_file=None)  # type: ignore[call-arg]
    assert s.allow_side_effects is True


def test_allow_side_effects_replay():
    s = Settings(nexus_mode=NexusMode.REPLAY, _env_file=None)  # type: ignore[call-arg]
    assert s.allow_side_effects is False


def test_settings_from_env(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("TAVILY_API_KEY", "tvly-test")
    monkeypatch.setenv("NEXUS_MODE", "live")
    s = Settings(_env_file=None)  # type: ignore[call-arg]
    assert s.tavily_api_key == "tvly-test"
    assert s.nexus_mode == NexusMode.LIVE
