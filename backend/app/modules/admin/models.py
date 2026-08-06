import uuid
from datetime import datetime

from sqlalchemy import JSON, DateTime, ForeignKey, String, Text, func
from sqlalchemy import Enum as SAEnum
from sqlalchemy.orm import Mapped, mapped_column

from app.common.base import GUID, Base, TimestampMixin, UUIDPrimaryKeyMixin
from app.common.enums import AuditActorType, ModerationStatus, ModerationSubjectType


class ModerationCase(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """A report against a user/message/profile, per data-model.md."""

    __tablename__ = "moderation_cases"

    reporter_id: Mapped[uuid.UUID] = mapped_column(
        GUID(), ForeignKey("users.id"), nullable=False
    )
    subject_type: Mapped[ModerationSubjectType] = mapped_column(
        SAEnum(ModerationSubjectType, name="moderation_subject_type"), nullable=False
    )
    subject_id: Mapped[uuid.UUID] = mapped_column(GUID(), nullable=False)
    reason: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[ModerationStatus] = mapped_column(
        SAEnum(ModerationStatus, name="moderation_status"),
        default=ModerationStatus.OPEN,
        nullable=False,
    )
    assigned_admin_id: Mapped[uuid.UUID | None] = mapped_column(
        GUID(), ForeignKey("users.id")
    )
    resolved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class AuditEvent(UUIDPrimaryKeyMixin, Base):
    """Append-only admin/compliance audit trail, per data-model.md.

    No TimestampMixin: this table has no update path, so an `updated_at`
    column would be misleading.
    """

    __tablename__ = "audit_events"

    actor_type: Mapped[AuditActorType] = mapped_column(
        SAEnum(AuditActorType, name="audit_actor_type"), nullable=False
    )
    actor_id: Mapped[uuid.UUID | None] = mapped_column(GUID())
    event_type: Mapped[str] = mapped_column(String(120), nullable=False)
    subject_type: Mapped[str] = mapped_column(String(40), nullable=False)
    subject_id: Mapped[uuid.UUID] = mapped_column(GUID(), nullable=False)
    # Named event_metadata, not metadata: `metadata` is reserved on
    # DeclarativeBase for the schema registry (Base.metadata).
    event_metadata: Mapped[dict | None] = mapped_column(JSON)
    occurred_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )


class BetaInvite(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """Invite-only beta gate (Phase 1 GTM) — not yet in data-model.md."""

    __tablename__ = "beta_invites"

    email: Mapped[str] = mapped_column(String(320), nullable=False, unique=True)
    invited_by: Mapped[uuid.UUID | None] = mapped_column(
        GUID(), ForeignKey("users.id")
    )
    redeemed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
