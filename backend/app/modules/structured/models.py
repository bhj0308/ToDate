import uuid
from datetime import datetime

from sqlalchemy import DateTime
from sqlalchemy import Enum as SAEnum
from sqlalchemy import ForeignKey, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import JSON

from app.common.base import GUID, Base, TimestampMixin, UUIDPrimaryKeyMixin
from app.common.enums import DateOutcome, DatePromptChoice


class Message(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "messages"

    match_id: Mapped[uuid.UUID] = mapped_column(
        GUID(), ForeignKey("matches.id"), nullable=False
    )
    sender_id: Mapped[uuid.UUID] = mapped_column(
        GUID(), ForeignKey("users.id"), nullable=False
    )
    body: Mapped[str] = mapped_column(Text, nullable=False)


class DatePromptResponse(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """One row per (match, user) — private until both sides have responded."""

    __tablename__ = "date_prompt_responses"
    __table_args__ = (UniqueConstraint("match_id", "user_id"),)

    match_id: Mapped[uuid.UUID] = mapped_column(
        GUID(), ForeignKey("matches.id"), nullable=False
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        GUID(), ForeignKey("users.id"), nullable=False
    )
    choice: Mapped[DatePromptChoice] = mapped_column(
        SAEnum(DatePromptChoice, name="date_prompt_choice"), nullable=False
    )


class AvailabilityWindow(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """2-week slot list submitted by each user once SCHEDULE_READY."""

    __tablename__ = "availability_windows"
    __table_args__ = (UniqueConstraint("match_id", "user_id"),)

    match_id: Mapped[uuid.UUID] = mapped_column(
        GUID(), ForeignKey("matches.id"), nullable=False
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        GUID(), ForeignKey("users.id"), nullable=False
    )
    # List of ISO-8601 datetime strings representing proposed slots.
    slots: Mapped[list] = mapped_column(JSON, nullable=False)


class DatePlan(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """Confirmed date — one per match, created once both sides are SCHEDULE_READY."""

    __tablename__ = "date_plans"

    match_id: Mapped[uuid.UUID] = mapped_column(
        GUID(), ForeignKey("matches.id"), unique=True, nullable=False
    )
    venue_name: Mapped[str] = mapped_column(Text, nullable=False)
    venue_address: Mapped[str | None] = mapped_column(Text)
    scheduled_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
    outcome: Mapped[DateOutcome | None] = mapped_column(
        SAEnum(DateOutcome, name="date_outcome")
    )
    outcome_recorded_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True)
    )
