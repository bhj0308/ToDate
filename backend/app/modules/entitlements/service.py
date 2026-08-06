import uuid
from datetime import datetime, timedelta, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.common.enums import BillingCycle, Plan, SubscriptionStatus
from app.modules.entitlements.catalog import features_for_plan
from app.modules.entitlements.models import Subscription

# A user whose subscription has lapsed collapses to the free Premium tier's
# universal features rather than losing app access outright. Grace-period
# policy is an open question (entitlements-matrix.md) — this is the v1 default.
_ACTIVE_STATUSES = {SubscriptionStatus.ACTIVE, SubscriptionStatus.PAST_DUE}


class EntitlementError(Exception):
    pass


class PaymentError(EntitlementError):
    """Raised for a malformed/missing dev-stub payment token — 402, not 409."""


async def resolve_effective_entitlements(
    session: AsyncSession, user_id: uuid.UUID
) -> dict:
    """Return the user's effective feature set: plan × subscription status.

    Every registered user gets at least the free Premium tier. An active
    Premium+/Elite subscription unlocks its additional features; a
    canceled/expired one falls back to Premium.
    """
    subscription = await session.scalar(
        select(Subscription)
        .where(Subscription.user_id == user_id)
        .order_by(Subscription.created_at.desc())
    )

    effective_plan = Plan.PREMIUM
    if subscription is not None and subscription.status in _ACTIVE_STATUSES:
        effective_plan = subscription.plan

    return {
        "effective_plan": effective_plan.value,
        "subscription_status": (
            subscription.status.value if subscription else None
        ),
        "features": sorted(features_for_plan(effective_plan)),
    }


def has_feature(entitlements: dict, feature_key: str) -> bool:
    return feature_key in entitlements.get("features", [])


async def get_active_subscription(
    session: AsyncSession, user_id: uuid.UUID
) -> Subscription | None:
    return await session.scalar(
        select(Subscription)
        .where(Subscription.user_id == user_id)
        .where(Subscription.status.in_(list(_ACTIVE_STATUSES)))
        .order_by(Subscription.created_at.desc())
    )


async def create_subscription(
    session: AsyncSession,
    user_id: uuid.UUID,
    plan: Plan,
    billing_cycle: BillingCycle,
    payment_token: str,
) -> Subscription:
    # Dev-stub tokenized-payment check — a real processor's token would be
    # verified with that processor instead of a format check. Rejecting
    # anything that isn't obviously a dev token keeps this from being
    # mistaken for real payment verification.
    if not payment_token.startswith("tok_dev_"):
        raise PaymentError("invalid payment token")

    existing = await get_active_subscription(session, user_id)
    if existing is not None:
        raise EntitlementError("active subscription already exists")

    now = datetime.now(timezone.utc)
    period_days = 365 if billing_cycle == BillingCycle.ANNUAL else 30
    sub = Subscription(
        user_id=user_id,
        plan=plan,
        billing_cycle=billing_cycle,
        status=SubscriptionStatus.ACTIVE,
        # README's $84.99 initiation fee is one-time-per-account, but nothing
        # here tracks "has this user ever paid it" across canceled/re-created
        # subscriptions — v1 stamps it on every new subscription record.
        activation_fee_paid_at=now,
        current_period_start=now,
        current_period_end=now + timedelta(days=period_days),
    )
    session.add(sub)
    await session.commit()
    await session.refresh(sub)
    return sub


async def update_subscription(
    session: AsyncSession, user_id: uuid.UUID, fields: dict
) -> Subscription:
    sub = await get_active_subscription(session, user_id)
    if sub is None:
        raise EntitlementError("no active subscription")
    for key, value in fields.items():
        if value is not None:
            setattr(sub, key, value)
    await session.commit()
    await session.refresh(sub)
    return sub


async def cancel_subscription(
    session: AsyncSession, user_id: uuid.UUID
) -> Subscription:
    sub = await get_active_subscription(session, user_id)
    if sub is None:
        raise EntitlementError("no active subscription")
    sub.status = SubscriptionStatus.CANCELED
    await session.commit()
    await session.refresh(sub)
    return sub
