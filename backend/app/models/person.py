from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field
from sqlalchemy import DateTime, Float, String, Text, func
from sqlalchemy.dialects.postgresql import ARRAY, JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


# ── Pydantic Schemas ──────────────────────────────────────────────────────────


class SocialLinks(BaseModel):
    linkedin: str | None = None
    twitter: str | None = None


class RawAttendee(BaseModel):
    """Minimal attendee info scraped from event pages."""

    name: str
    title: str | None = None
    company: str | None = None
    linkedin: str | None = None
    twitter: str | None = None


class PersonProfile(BaseModel):
    """Fully enriched person profile."""

    id: str
    name: str
    title: str | None = None
    company: str | None = None
    linkedin: str | None = None
    twitter: str | None = None

    connection_score: float = Field(ge=0, le=100)
    mutual_connections: list[dict[str, str]] = Field(default_factory=list)
    shared_topics: list[str] = Field(default_factory=list)
    research_summary: str | None = None

    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class PersonResponse(BaseModel):
    """API response for a person."""

    id: str
    name: str
    title: str | None = None
    company: str | None = None
    linkedin: str | None = None
    twitter: str | None = None
    connection_score: float
    mutual_connections: list[dict[str, str]] = Field(default_factory=list)
    shared_topics: list[str] = Field(default_factory=list)
    research_summary: str | None = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


# ── SQLAlchemy ─────────────────────────────────────────────────────────────────


class PersonDB(Base):
    __tablename__ = "persons"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    name: Mapped[str] = mapped_column(Text, nullable=False)
    title: Mapped[str | None] = mapped_column(Text, nullable=True)
    company: Mapped[str | None] = mapped_column(Text, nullable=True)
    linkedin: Mapped[str | None] = mapped_column(Text, nullable=True)
    twitter: Mapped[str | None] = mapped_column(Text, nullable=True)

    connection_score: Mapped[float] = mapped_column(Float, nullable=False, default=0)
    mutual_connections: Mapped[list[dict[str, str]]] = mapped_column(JSONB, default=list)
    shared_topics: Mapped[list[str]] = mapped_column(ARRAY(String), default=list)
    research_summary: Mapped[str | None] = mapped_column(Text, nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
