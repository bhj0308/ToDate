import uuid
from typing import Any

from pydantic import BaseModel, ConfigDict, EmailStr, Field

from app.common.enums import (
    AccountState,
    CriminalCheckStatus,
    Eligibility,
    IncomePercentileTier,
    UserStatus,
)


class RegisterRequest(BaseModel):
    email: EmailStr
    phone: str | None = None


class OtpStartRequest(BaseModel):
    destination: str  # phone number or email
    channel: str = Field(pattern="^(phone|email)$")


class OtpStartResponse(BaseModel):
    challenge_id: uuid.UUID
    # dev_code is only populated outside production so the flow is testable
    # without a real SMS/email provider. Never returned in production.
    dev_code: str | None = None


class OtpVerifyRequest(BaseModel):
    challenge_id: uuid.UUID
    code: str


class TokenPair(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class RefreshRequest(BaseModel):
    refresh_token: str


class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    email: str
    phone: str | None
    status: UserStatus
    account_state: AccountState


class ProfileUpdate(BaseModel):
    display_name: str | None = None
    bio: str | None = None
    prompts: list[Any] | None = None
    photos: list[Any] | None = None
    interests: list[Any] | None = None
    dining_preferences: dict[str, Any] | None = None
    latitude: float | None = None
    longitude: float | None = None
    city_market: str | None = None


class ProfileOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    user_id: uuid.UUID
    display_name: str | None
    bio: str | None
    prompts: list[Any] | None
    photos: list[Any] | None
    interests: list[Any] | None
    dining_preferences: dict[str, Any] | None
    latitude: float | None
    longitude: float | None
    city_market: str | None


class VerifiedAttributesOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    user_id: uuid.UUID
    identity_verified: bool
    criminal_check_status: CriminalCheckStatus
    income_percentile_tier: IncomePercentileTier | None
    education_level: str | None
    eligibility: Eligibility
