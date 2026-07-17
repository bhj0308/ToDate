import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_session
from app.deps import get_current_user
from app.modules.entitlements.service import resolve_effective_entitlements
from app.modules.identity.models import User
from app.modules.intelligent import service
from app.modules.intelligent.schemas import CoachingInsightsOut, CompatibilityScoreOut

router = APIRouter(tags=["intelligent"])

_match_prefix = "/matches/{match_id}"


async def _ai_tier(
    current: User,
    session: AsyncSession,
) -> str:
    """Resolve the requesting user's AI insight tier from their entitlements."""
    ent = await resolve_effective_entitlements(session, current.id)
    return service.resolve_ai_tier(ent["features"])


@router.get(_match_prefix + "/coaching-insights", response_model=CoachingInsightsOut)
async def coaching_insights(
    match_id: uuid.UUID,
    current: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    ai_tier = await _ai_tier(current, session)
    try:
        return await service.get_coaching_insights(
            session, match_id, current.id, ai_tier
        )
    except service.IntelligentError as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, str(exc))


@router.get(_match_prefix + "/compatibility-score", response_model=CompatibilityScoreOut)
async def compatibility_score(
    match_id: uuid.UUID,
    current: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    ai_tier = await _ai_tier(current, session)
    try:
        return await service.get_compatibility_score(
            session, match_id, current.id, ai_tier
        )
    except service.IntelligentError as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, str(exc))
