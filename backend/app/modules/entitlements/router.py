from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_session
from app.deps import get_current_user
from app.modules.entitlements import service
from app.modules.entitlements.catalog import FEATURE_MATRIX
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
