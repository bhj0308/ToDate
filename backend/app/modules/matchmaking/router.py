import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.common.enums import IncomePercentileTier
from app.db import get_session
from app.deps import get_current_user
from app.modules.entitlements.service import has_feature, resolve_effective_entitlements
from app.modules.identity.models import User
from app.modules.matchmaking import service
from app.modules.matchmaking.schemas import (
    DiscoveryProfileOut,
    MatchCreate,
    MatchOut,
)

router = APIRouter(tags=["matchmaking"])


@router.get("/discovery", response_model=list[DiscoveryProfileOut])
async def discovery(
    min_income_tier: IncomePercentileTier | None = None,
    education_level: str | None = None,
    current: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    ent = await resolve_effective_entitlements(session, current.id)
    if min_income_tier is not None and not has_feature(ent, "income_filter_advanced"):
        raise HTTPException(
            status.HTTP_403_FORBIDDEN, "income filtering requires Premium+"
        )
    if education_level is not None and not has_feature(ent, "education_filter"):
        raise HTTPException(
            status.HTTP_403_FORBIDDEN, "education filtering requires Premium+"
        )
    return await service.get_discovery_feed(
        session, current.id, min_income_tier, education_level
    )


@router.post("/matches", response_model=MatchOut, status_code=status.HTTP_201_CREATED)
async def create_match(
    body: MatchCreate,
    current: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    try:
        return await service.create_match(session, current.id, body.target_user_id)
    except service.MatchError as exc:
        raise HTTPException(status.HTTP_409_CONFLICT, str(exc))


@router.get("/matches", response_model=list[MatchOut])
async def list_matches(
    current: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    return await service.list_matches(session, current.id)


@router.get("/matches/{match_id}", response_model=MatchOut)
async def get_match(
    match_id: uuid.UUID,
    current: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    try:
        return await service.get_match(session, match_id, current.id)
    except service.MatchError as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, str(exc))
