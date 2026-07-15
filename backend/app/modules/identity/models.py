import uuid

from sqlalchemy import Enum as SAEnum
from sqlalchemy import ForeignKey, Numeric, String, Text
from sqlalchemy import JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.common.base import GUID, Base, TimestampMixin, UUIDPrimaryKeyMixin
from app.common.enums import (
    AccountState,
    CriminalCheckStatus,
    Eligibility,
    IncomePercentileTier,
    UserStatus,
)


class User(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """Canonical account record (docs/architecture/data-model.md `users`).

    No password column, by design — auth is passwordless OTP per ADR-0001.
    """

    __tablename__ = "users"

    email: Mapped[str] = mapped_column(String(320), unique=True, nullable=False)
    phone: Mapped[str | None] = mapped_column(String(32), unique=True)
    status: Mapped[UserStatus] = mapped_column(
        SAEnum(UserStatus, name="user_status"),
        default=UserStatus.ACTIVE,
        nullable=False,
    )
    account_state: Mapped[AccountState] = mapped_column(
        SAEnum(AccountState, name="account_state"),
        default=AccountState.REGISTERED,
        nullable=False,
    )

    profile: Mapped["Profile"] = relationship(
        back_populates="user", uselist=False
    )
    verified_attributes: Mapped["VerifiedAttributes"] = relationship(
        back_populates="user", uselist=False
    )


class Profile(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """User-authored, dating-facing content. Holds NO verified facts."""

    __tablename__ = "profiles"

    user_id: Mapped[uuid.UUID] = mapped_column(
        GUID(), ForeignKey("users.id"), unique=True, nullable=False
    )
    display_name: Mapped[str | None] = mapped_column(String(120))
    bio: Mapped[str | None] = mapped_column(Text)
    prompts: Mapped[list | None] = mapped_column(JSON)
    photos: Mapped[list | None] = mapped_column(JSON)
    interests: Mapped[list | None] = mapped_column(JSON)
    dining_preferences: Mapped[dict | None] = mapped_column(JSON)
    # Location stored as lat/lng for v1 bootability. PostGIS geography(point)
    # is a later migration once the DB has PostGIS enabled — see data-model doc.
    latitude: Mapped[float | None] = mapped_column(Numeric(9, 6))
    longitude: Mapped[float | None] = mapped_column(Numeric(9, 6))
    city_market: Mapped[str | None] = mapped_column(String(80))

    user: Mapped["User"] = relationship(back_populates="profile")


class VerifiedAttributes(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """System-controlled verified facts. Nothing here is user-editable.

    Populated by the Vetted domain; consumed read-only by Matchmaking etc.
    (never the raw artifacts — see docs/architecture/security.md).
    """

    __tablename__ = "verified_attributes"

    user_id: Mapped[uuid.UUID] = mapped_column(
        GUID(), ForeignKey("users.id"), unique=True, nullable=False
    )
    identity_verified: Mapped[bool] = mapped_column(default=False, nullable=False)
    criminal_check_status: Mapped[CriminalCheckStatus] = mapped_column(
        SAEnum(CriminalCheckStatus, name="criminal_check_status"),
        default=CriminalCheckStatus.PENDING,
        nullable=False,
    )
    income_percentile_tier: Mapped[IncomePercentileTier | None] = mapped_column(
        SAEnum(IncomePercentileTier, name="income_percentile_tier")
    )
    education_level: Mapped[str | None] = mapped_column(String(80))
    eligibility: Mapped[Eligibility] = mapped_column(
        SAEnum(Eligibility, name="eligibility"),
        default=Eligibility.INELIGIBLE,
        nullable=False,
    )

    user: Mapped["User"] = relationship(back_populates="verified_attributes")


class OtpChallenge(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """Short-lived OTP code for passwordless login (ADR-0001).

    In dev the code is logged rather than sent via SMS — a real SMS provider
    is a vendor-selection item (docs/vendors/vendor-selection.md).
    """

    __tablename__ = "otp_challenges"

    destination: Mapped[str] = mapped_column(String(320), nullable=False)
    channel: Mapped[str] = mapped_column(String(16), nullable=False)  # phone|email
    code_hash: Mapped[str] = mapped_column(String(128), nullable=False)
    consumed: Mapped[bool] = mapped_column(default=False, nullable=False)
