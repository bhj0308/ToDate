import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict

from app.common.enums import DateOutcome, DatePromptChoice, MatchState


class MessageCreate(BaseModel):
    body: str


class MessageOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    match_id: uuid.UUID
    sender_id: uuid.UUID
    body: str
    created_at: datetime


class ConversationOut(BaseModel):
    match_id: uuid.UUID
    state: MatchState
    messages: list[MessageOut]


class DatePromptStateOut(BaseModel):
    """Prompt state visible to the requesting user.

    counterpart_choice is withheld until both parties have responded to
    preserve the simultaneous-reveal guarantee.
    """

    active: bool
    my_choice: DatePromptChoice | None
    resolved: bool
    # Only populated once resolved (both responded):
    counterpart_choice: DatePromptChoice | None = None
    resolved_state: MatchState | None = None


class DatePromptResponseCreate(BaseModel):
    choice: DatePromptChoice


class AvailabilitySubmit(BaseModel):
    slots: list[str]  # ISO-8601 datetime strings


class AvailabilityOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    match_id: uuid.UUID
    user_id: uuid.UUID
    slots: list[Any]
    updated_at: datetime


class VenueRecommendationOut(BaseModel):
    name: str
    address: str
    cuisine: str
    price_tier: str  # $, $$, $$$, $$$$


class DatePlanCreate(BaseModel):
    venue_name: str
    venue_address: str | None = None
    scheduled_at: datetime


class DatePlanOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    match_id: uuid.UUID
    venue_name: str
    venue_address: str | None
    scheduled_at: datetime
    outcome: DateOutcome | None
    outcome_recorded_at: datetime | None


class DateOutcomeSubmit(BaseModel):
    outcome: DateOutcome
