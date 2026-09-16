from fastapi import APIRouter, Depends, status
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_session
from app.deps import get_current_user
from app.modules.identity.models import User
from app.modules.notifications import service

router = APIRouter(tags=["notifications"])


class PushTokenIn(BaseModel):
    token: str = Field(min_length=1, max_length=255)
    platform: str | None = Field(default=None, pattern="^(ios|android)$")


@router.post("/users/me/push-tokens", status_code=status.HTTP_204_NO_CONTENT)
async def register_push_token(
    body: PushTokenIn,
    current: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    await service.register_token(session, current.id, body.token, body.platform)


@router.delete("/users/me/push-tokens", status_code=status.HTTP_204_NO_CONTENT)
async def unregister_push_token(
    body: PushTokenIn,
    current: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """Call on sign-out so the device stops receiving this account's pushes."""
    await service.unregister_token(session, current.id, body.token)
