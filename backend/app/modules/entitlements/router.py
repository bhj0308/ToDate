from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_session
from app.deps import get_current_user
from app.modules.entitlements import service
from app.modules.entitlements.catalog import FEATURE_MATRIX
from app.modules.entitlements.schemas import (
    SubscriptionCreate,
    SubscriptionOut,
    SubscriptionUpdate,
)
from app.modules.identity.models import User

router = APIRouter(tags=["entitlements"])


@router.get("/entitlements/catalog")
async def catalog():
    """Public feature catalog: which plans unlock each feature."""
    return {
        key: sorted(p.value for p in plans)
        for key, plans in FEATURE_MATRIX.items()
    }


@router.get("/entitlements/me")
async def my_entitlements(
    current: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    return await service.resolve_effective_entitlements(session, current.id)


@router.post(
    "/subscriptions",
    response_model=SubscriptionOut,
    status_code=status.HTTP_201_CREATED,
)
async def create_subscription(
    body: SubscriptionCreate,
    current: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    try:
        return await service.create_subscription(
            session, current.id, body.plan, body.billing_cycle
        )
    except service.EntitlementError as exc:
        raise HTTPException(status.HTTP_409_CONFLICT, str(exc))


@router.get("/subscriptions/me", response_model=SubscriptionOut)
async def get_my_subscription(
    current: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    sub = await service.get_active_subscription(session, current.id)
    if sub is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "no active subscription")
    return sub


@router.put("/subscriptions/me", response_model=SubscriptionOut)
async def update_my_subscription(
    body: SubscriptionUpdate,
    current: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    try:
        return await service.update_subscription(
            session, current.id, body.model_dump(exclude_unset=True)
        )
    except service.EntitlementError as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, str(exc))


@router.delete("/subscriptions/me", status_code=status.HTTP_204_NO_CONTENT)
async def cancel_my_subscription(
    current: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    try:
        await service.cancel_subscription(session, current.id)
    except service.EntitlementError as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, str(exc))
