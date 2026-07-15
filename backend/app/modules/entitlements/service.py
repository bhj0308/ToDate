import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.common.enums import Plan, SubscriptionStatus
from app.modules.entitlements.catalog import features_for_plan
from app.modules.entitlements.models import Subscription

# A user whose subscription has lapsed collapses to the free Premium tier's
# universal features rather than losing app access outright. Grace-period
# policy is an open question (entitlements-matrix.md) — this is the v1 default.
_ACTIVE_STATUSES = {SubscriptionStatus.ACTIVE, SubscriptionStatus.PAST_DUE}


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
