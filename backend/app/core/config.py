from enum import Enum

from pydantic_settings import BaseSettings, SettingsConfigDict


class NexusMode(str, Enum):
    DRY_RUN = "dry_run"
    REPLAY = "replay"
    CANARY = "canary"
    LIVE = "live"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    # Sponsor Tool API Keys
    tavily_api_key: str = ""
    yutori_api_key: str = ""
    neo4j_uri: str = ""
    neo4j_user: str = "neo4j"
    neo4j_password: str = ""
    reka_api_key: str = ""
    anthropic_api_key: str = ""

    # Google OAuth
    google_client_id: str = ""
    google_client_secret: str = ""

    # Database
    database_url: str = "postgresql+asyncpg://localhost:5432/nexus"

    # App Config
    secret_key: str = "change-me-in-production"
    nexus_mode: NexusMode = NexusMode.DRY_RUN
    backend_url: str = "http://localhost:8000"
    frontend_url: str = "http://localhost:3000"

    # Safety Limits
    max_auto_applies_per_day: int = 10
    max_auto_send_messages_per_day: int = 5

    # Scoring Thresholds (defaults from README)
    auto_apply_threshold: int = 80
    suggest_threshold: int = 50
    auto_schedule_threshold: int = 85

    @property
    def allow_side_effects(self) -> bool:
        return self.nexus_mode in (NexusMode.CANARY, NexusMode.LIVE)


settings = Settings()
