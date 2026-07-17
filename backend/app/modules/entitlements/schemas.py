import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.common.enums import BillingCycle, Plan, SubscriptionStatus


class SubscriptionCreate(BaseModel):
    plan: Plan
    billing_cycle: BillingCycle


class SubscriptionUpdate(BaseModel):
    plan: Plan | None = None
    billing_cycle: BillingCycle | None = None


class SubscriptionOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    user_id: uuid.UUID
    plan: Plan
    billing_cycle: BillingCycle
    status: SubscriptionStatus
    activation_fee_paid_at: datetime | None
    current_period_start: datetime | None
    current_period_end: datetime | None
    created_at: datetime
    updated_at: datetime
