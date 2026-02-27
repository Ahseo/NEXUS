from __future__ import annotations

import enum
from datetime import datetime

from pydantic import BaseModel, Field
from sqlalchemy import DateTime, Enum, Float, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import ARRAY, JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


# ── Enums ──────────────────────────────────────────────────────────────────────


class MessageTone(str, enum.Enum):
    CASUAL = "casual"
    PROFESSIONAL = "professional"
    FRIENDLY = "friendly"


class TargetPriority(str, enum.Enum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class TargetStatus(str, enum.Enum):
    SEARCHING = "searching"
    FOUND_EVENT = "found_event"
    MESSAGED = "messaged"
    CONNECTED = "connected"


# ── Pydantic Schemas ──────────────────────────────────────────────────────────


class ScoringWeights(BaseModel):
    """User-configurable weights for event scoring."""

    auto_apply_threshold: int = Field(default=80, ge=0, le=100)
    suggest_threshold: int = Field(default=50, ge=0, le=100)
    auto_schedule_threshold: int = Field(default=85, ge=0, le=100)


class TargetPerson(BaseModel):
    """A specific individual the user wants to connect with."""

    id: str
    name: str
    company: str | None = None
    role: str | None = None
    reason: str
    priority: TargetPriority = TargetPriority.MEDIUM
    status: TargetStatus = TargetStatus.SEARCHING
    added_at: datetime = Field(default_factory=datetime.utcnow)
    matched_events: list[str] = Field(default_factory=list)  # event IDs


class UserProfile(BaseModel):
    """Full user profile including networking preferences."""

    id: str
    name: str
    email: str

    # Professional
    role: str
    company: str
    product_description: str
    linkedin: str = ""
    twitter: str = ""

    # Networking Goals
    networking_goals: list[str] = Field(default_factory=list)
    target_roles: list[str] = Field(default_factory=list)
    target_companies: list[str] = Field(default_factory=list)
    target_industries: list[str] = Field(default_factory=list)

    # Target People
    target_people: list[TargetPerson] = Field(default_factory=list)

    # Preferences
    interests: list[str] = Field(default_factory=list)
    preferred_event_types: list[str] = Field(default_factory=list)
    max_events_per_week: int = Field(default=4, ge=0)
    max_event_spend: float = Field(default=50, ge=0)
    preferred_days: list[str] = Field(default_factory=list)
    preferred_times: list[str] = Field(default_factory=list)
    message_tone: MessageTone = MessageTone.CASUAL

    # Auto-action thresholds
    auto_apply_threshold: int = Field(default=80, ge=0, le=100)
    suggest_threshold: int = Field(default=50, ge=0, le=100)
    auto_schedule_threshold: int = Field(default=85, ge=0, le=100)

    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


# ── SQLAlchemy ─────────────────────────────────────────────────────────────────


class UserProfileDB(Base):
    __tablename__ = "user_profiles"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    name: Mapped[str] = mapped_column(Text, nullable=False)
    email: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)

    role: Mapped[str] = mapped_column(Text, nullable=False)
    company: Mapped[str] = mapped_column(Text, nullable=False)
    product_description: Mapped[str] = mapped_column(Text, nullable=False)
    linkedin: Mapped[str] = mapped_column(Text, default="")
    twitter: Mapped[str] = mapped_column(Text, default="")

    networking_goals: Mapped[list[str]] = mapped_column(ARRAY(String), default=list)
    target_roles: Mapped[list[str]] = mapped_column(ARRAY(String), default=list)
    target_companies: Mapped[list[str]] = mapped_column(ARRAY(String), default=list)
    target_industries: Mapped[list[str]] = mapped_column(ARRAY(String), default=list)

    target_people: Mapped[list[dict[str, str]]] = mapped_column(JSONB, default=list)

    interests: Mapped[list[str]] = mapped_column(ARRAY(String), default=list)
    preferred_event_types: Mapped[list[str]] = mapped_column(ARRAY(String), default=list)
    max_events_per_week: Mapped[int] = mapped_column(Integer, default=4)
    max_event_spend: Mapped[float] = mapped_column(Float, default=50)
    preferred_days: Mapped[list[str]] = mapped_column(ARRAY(String), default=list)
    preferred_times: Mapped[list[str]] = mapped_column(ARRAY(String), default=list)
    message_tone: Mapped[str] = mapped_column(
        Enum(MessageTone), default=MessageTone.CASUAL.value
    )

    auto_apply_threshold: Mapped[int] = mapped_column(Integer, default=80)
    suggest_threshold: Mapped[int] = mapped_column(Integer, default=50)
    auto_schedule_threshold: Mapped[int] = mapped_column(Integer, default=85)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )


class TargetPersonDB(Base):
    __tablename__ = "target_persons"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    user_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True)
    name: Mapped[str] = mapped_column(Text, nullable=False)
    company: Mapped[str | None] = mapped_column(Text, nullable=True)
    role: Mapped[str | None] = mapped_column(Text, nullable=True)
    reason: Mapped[str] = mapped_column(Text, nullable=False)
    priority: Mapped[str] = mapped_column(
        Enum(TargetPriority), default=TargetPriority.MEDIUM.value
    )
    status: Mapped[str] = mapped_column(
        Enum(TargetStatus), default=TargetStatus.SEARCHING.value
    )
    matched_events: Mapped[list[str]] = mapped_column(ARRAY(String), default=list)

    added_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
