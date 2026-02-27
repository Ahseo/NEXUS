from __future__ import annotations

import enum
from datetime import datetime

from pydantic import BaseModel, Field
from sqlalchemy import DateTime, Enum, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


# ── Enums ──────────────────────────────────────────────────────────────────────


class MessageChannel(str, enum.Enum):
    TWITTER_DM = "twitter_dm"
    LINKEDIN = "linkedin"
    EMAIL = "email"


class MessageStatus(str, enum.Enum):
    DRAFT = "draft"
    APPROVED = "approved"
    EDITED = "edited"
    SENT = "sent"
    REJECTED = "rejected"


# ── Pydantic Schemas ──────────────────────────────────────────────────────────


class ColdMessage(BaseModel):
    """A generated outreach message."""

    id: str
    recipient_id: str
    event_id: str
    channel: MessageChannel
    content: str

    status: MessageStatus = MessageStatus.DRAFT
    user_edits: str | None = None
    sent_at: datetime | None = None
    response_received: bool = False

    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class MessageCreate(BaseModel):
    """Payload to create a cold message."""

    recipient_id: str
    event_id: str
    channel: MessageChannel
    content: str


class MessageResponse(BaseModel):
    """API response for a cold message."""

    id: str
    recipient_id: str
    event_id: str
    channel: MessageChannel
    content: str
    status: MessageStatus
    user_edits: str | None = None
    sent_at: datetime | None = None
    response_received: bool
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


# ── SQLAlchemy ─────────────────────────────────────────────────────────────────


class MessageDB(Base):
    __tablename__ = "messages"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    recipient_id: Mapped[str] = mapped_column(String(36), nullable=False)
    event_id: Mapped[str] = mapped_column(String(36), nullable=False)
    channel: Mapped[str] = mapped_column(Enum(MessageChannel), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)

    status: Mapped[str] = mapped_column(
        Enum(MessageStatus), nullable=False, default=MessageStatus.DRAFT.value
    )
    user_edits: Mapped[str | None] = mapped_column(Text, nullable=True)
    sent_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    response_received: Mapped[bool] = mapped_column(default=False)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
