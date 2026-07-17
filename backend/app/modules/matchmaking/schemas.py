import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict

from app.common.enums import MatchState


class MatchCreate(BaseModel):
    target_user_id: uuid.UUID


class MatchOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    user_a_id: uuid.UUID
    user_b_id: uuid.UUID
    state: MatchState
    created_at: datetime
    updated_at: datetime


class DiscoveryProfileOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    user_id: uuid.UUID
    display_name: str | None
    bio: str | None
    photos: list[Any] | None
    interests: list[Any] | None
    city_market: str | None
