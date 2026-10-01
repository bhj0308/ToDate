import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, model_validator

from app.common.enums import (
    AccountState,
    CriminalCheckStatus,
    Eligibility,
    IncomePercentileTier,
    ModerationStatus,
    ModerationSubjectType,
)
from app.common.phone import normalize_phone


class ModerationCaseCreate(BaseModel):
    subject_type: ModerationSubjectType
    subject_id: uuid.UUID
    reason: str


class ModerationCaseOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    reporter_id: uuid.UUID
    subject_type: ModerationSubjectType
    subject_id: uuid.UUID
    reason: str
    status: ModerationStatus
    assigned_admin_id: uuid.UUID | None
    created_at: datetime
    resolved_at: datetime | None


class ModerationCaseAction(BaseModel):
    decision: ModerationStatus  # actioned | dismissed


class AuditEventOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    actor_type: str
    actor_id: uuid.UUID | None
    event_type: str
    subject_type: str
    subject_id: uuid.UUID
    event_metadata: dict[str, Any] | None
    occurred_at: datetime


class BetaInviteCreate(BaseModel):
    """Invite by email or by phone — whichever the person will sign up with."""

    email: str | None = None
    phone: str | None = None

    @model_validator(mode="after")
    def _one_contact(self):
        if bool(self.email) == bool(self.phone):
            raise ValueError("provide exactly one of email or phone")
        if self.phone:
            self.phone = normalize_phone(self.phone)
        return self


class BetaInviteOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    email: str | None
    phone: str | None
    invited_by: uuid.UUID | None
    redeemed_at: datetime | None
    created_at: datetime


class AdminUserOut(BaseModel):
    """Curation-queue row: enough to decide, not a full profile dump."""

    id: uuid.UUID
    email: str
    account_state: AccountState
    display_name: str | None


class VerifiedAttributesUpdate(BaseModel):
    """Manual override standing in for blocked Verification (see service.py).

    All fields optional — only what's provided is changed.
    """

    identity_verified: bool | None = None
    criminal_check_status: CriminalCheckStatus | None = None
    income_percentile_tier: IncomePercentileTier | None = None
    education_level: str | None = None
    eligibility: Eligibility | None = None
