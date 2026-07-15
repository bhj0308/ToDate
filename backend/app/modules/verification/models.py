import uuid
from datetime import datetime

from sqlalchemy import DateTime
from sqlalchemy import Enum as SAEnum
from sqlalchemy import ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.common.base import GUID, Base, TimestampMixin, UUIDPrimaryKeyMixin
from app.common.enums import VerificationCaseType, VerificationState


class VerificationCase(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """docs/architecture/data-model.md `verification_cases`.

    The schema exists so migrations and other domains can reference it, but the
    lifecycle transitions are NOT implemented — see stub.py for why.
    """

    __tablename__ = "verification_cases"

    user_id: Mapped[uuid.UUID] = mapped_column(
        GUID(), ForeignKey("users.id"), nullable=False
    )
    case_type: Mapped[VerificationCaseType] = mapped_column(
        SAEnum(VerificationCaseType, name="verification_case_type"),
        nullable=False,
    )
    state: Mapped[VerificationState] = mapped_column(
        SAEnum(VerificationState, name="verification_state"),
        default=VerificationState.VERIFICATION_PENDING,
        nullable=False,
    )
    vendor: Mapped[str | None] = mapped_column(String(80))
    vendor_reference_id: Mapped[str | None] = mapped_column(String(128))
    disclosure_presented_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True)
    )
    authorization_captured_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True)
    )
    resolved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class VerificationDecision(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """The durable, consumable output. Other domains read this, never artifacts."""

    __tablename__ = "verification_decisions"

    verification_case_id: Mapped[uuid.UUID] = mapped_column(
        GUID(), ForeignKey("verification_cases.id"), nullable=False
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        GUID(), ForeignKey("users.id"), nullable=False
    )
    decision: Mapped[str] = mapped_column(String(32), nullable=False)
    decided_by: Mapped[str] = mapped_column(String(16), nullable=False)
    reason_code: Mapped[str | None] = mapped_column(String(80))


class VerificationArtifact(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """Raw vendor output — object-storage pointer only, never inline content.

    Restricted-tier data (docs/architecture/security.md): must never be queried
    outside the Vetted domain.
    """

    __tablename__ = "verification_artifacts"

    verification_case_id: Mapped[uuid.UUID] = mapped_column(
        GUID(), ForeignKey("verification_cases.id"), nullable=False
    )
    artifact_type: Mapped[str] = mapped_column(String(32), nullable=False)
    storage_ref: Mapped[str] = mapped_column(Text, nullable=False)
    retention_expires_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True)
    )
