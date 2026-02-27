from __future__ import annotations

import enum
from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field
from sqlalchemy import DateTime, Enum, Float, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import ARRAY, JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


# ── Enums ──────────────────────────────────────────────────────────────────────


class EventSource(str, enum.Enum):
    EVENTBRITE = "eventbrite"
    LUMA = "luma"
    MEETUP = "meetup"
    PARTIFUL = "partiful"
    TWITTER = "twitter"
    OTHER = "other"


class EventType(str, enum.Enum):
    CONFERENCE = "conference"
    MEETUP = "meetup"
    DINNER = "dinner"
    WORKSHOP = "workshop"
    HAPPY_HOUR = "happy_hour"
    DEMO_DAY = "demo_day"


class EventStatus(str, enum.Enum):
    DISCOVERED = "discovered"
    ANALYZED = "analyzed"
    SUGGESTED = "suggested"
    ACCEPTED = "accepted"
    REJECTED = "rejected"
    APPLIED = "applied"
    CONFIRMED = "confirmed"
    WAITLISTED = "waitlisted"
    ATTENDED = "attended"
    SKIPPED = "skipped"


# ── Pydantic Schemas ──────────────────────────────────────────────────────────


class RawEvent(BaseModel):
    """Event as scraped from source, before NER enrichment."""

    title: str
    url: str
    source: EventSource
    description: str


class ApplicationResult(BaseModel):
    status: str  # applied | waitlisted | failed | payment_required
    confirmation_id: str | None = None
    yutori_task_id: str


class EnrichedEvent(BaseModel):
    """Event after Claude NER and scoring."""

    id: str
    url: str
    title: str
    description: str
    source: EventSource

    event_type: EventType
    date: datetime
    end_date: datetime | None = None
    location: str
    capacity: int | None = None
    price: float | None = None
    speakers: list[dict[str, Any]] = Field(default_factory=list)
    topics: list[str] = Field(default_factory=list)
    target_audience: str = ""
    application_required: bool = False

    relevance_score: float = Field(ge=0, le=100)

    status: EventStatus = EventStatus.DISCOVERED
    rejection_reason: str | None = None
    application_result: ApplicationResult | None = None
    calendar_event_id: str | None = None
    user_rating: int | None = Field(default=None, ge=1, le=5)

    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class EventCreate(BaseModel):
    """Payload for creating an event via API."""

    url: str
    title: str
    description: str
    source: EventSource
    event_type: EventType
    date: datetime
    end_date: datetime | None = None
    location: str
    capacity: int | None = None
    price: float | None = None
    speakers: list[dict[str, Any]] = Field(default_factory=list)
    topics: list[str] = Field(default_factory=list)
    target_audience: str = ""
    application_required: bool = False
    relevance_score: float = Field(ge=0, le=100)


class EventResponse(BaseModel):
    """API response for a single event."""

    id: str
    url: str
    title: str
    description: str
    source: EventSource
    event_type: EventType
    date: datetime
    end_date: datetime | None = None
    location: str
    capacity: int | None = None
    price: float | None = None
    speakers: list[dict[str, Any]] = Field(default_factory=list)
    topics: list[str] = Field(default_factory=list)
    target_audience: str = ""
    application_required: bool = False
    relevance_score: float
    status: EventStatus
    rejection_reason: str | None = None
    application_result: ApplicationResult | None = None
    calendar_event_id: str | None = None
    user_rating: int | None = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


# ── SQLAlchemy ─────────────────────────────────────────────────────────────────


class EventDB(Base):
    __tablename__ = "events"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    url: Mapped[str] = mapped_column(Text, nullable=False)
    title: Mapped[str] = mapped_column(Text, nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    source: Mapped[str] = mapped_column(Enum(EventSource), nullable=False)

    event_type: Mapped[str] = mapped_column(Enum(EventType), nullable=False)
    date: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    end_date: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    location: Mapped[str] = mapped_column(Text, nullable=False)
    capacity: Mapped[int | None] = mapped_column(Integer, nullable=True)
    price: Mapped[float | None] = mapped_column(Float, nullable=True)
    speakers: Mapped[list[Any]] = mapped_column(JSONB, default=list)
    topics: Mapped[list[str]] = mapped_column(ARRAY(String), default=list)
    target_audience: Mapped[str] = mapped_column(Text, default="")
    application_required: Mapped[bool] = mapped_column(default=False)

    relevance_score: Mapped[float] = mapped_column(Float, nullable=False, default=0)

    status: Mapped[str] = mapped_column(
        Enum(EventStatus), nullable=False, default=EventStatus.DISCOVERED.value
    )
    rejection_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    application_result: Mapped[dict[str, Any] | None] = mapped_column(JSONB, nullable=True)
    calendar_event_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    user_rating: Mapped[int | None] = mapped_column(Integer, nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
