from __future__ import annotations

import enum
from datetime import datetime

from pydantic import BaseModel, Field
from sqlalchemy import DateTime, Enum, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


# ── Enums ──────────────────────────────────────────────────────────────────────


class FeedbackAction(str, enum.Enum):
    ACCEPT = "accept"
    REJECT = "reject"
    EDIT = "edit"
    RATE = "rate"
    SKIP = "skip"


class RejectionReason(str, enum.Enum):
    NOT_RELEVANT = "not_relevant"
    TOO_EXPENSIVE = "too_expensive"
    SCHEDULE_CONFLICT = "schedule_conflict"
    WRONG_LOCATION = "wrong_location"
    NOT_INTERESTED = "not_interested"
    OTHER = "other"


# ── Pydantic Schemas ──────────────────────────────────────────────────────────


class Feedback(BaseModel):
    """User feedback on events, persons, or messages."""

    id: str
    user_id: str
    event_id: str | None = None
    person_id: str | None = None
    message_id: str | None = None

    action: FeedbackAction
    reason: str | None = None
    free_text: str | None = None
    rating: int | None = Field(default=None, ge=1, le=5)

    created_at: datetime = Field(default_factory=datetime.utcnow)


class FeedbackResponse(BaseModel):
    """API response for feedback."""

    id: str
    user_id: str
    event_id: str | None = None
    person_id: str | None = None
    message_id: str | None = None
    action: FeedbackAction
    reason: str | None = None
    free_text: str | None = None
    rating: int | None = None
    created_at: datetime

    model_config = {"from_attributes": True}


# ── SQLAlchemy ─────────────────────────────────────────────────────────────────


class FeedbackDB(Base):
    __tablename__ = "feedback"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    user_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True)
    event_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    person_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    message_id: Mapped[str | None] = mapped_column(String(36), nullable=True)

    action: Mapped[str] = mapped_column(Enum(FeedbackAction), nullable=False)
    reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    free_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    rating: Mapped[int | None] = mapped_column(Integer, nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
