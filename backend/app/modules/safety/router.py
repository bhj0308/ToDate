import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_session
from app.deps import get_current_user
from app.modules.identity.models import User
from app.modules.safety import service

router = APIRouter(tags=["safety"])


@router.get("/users/me/blocks", response_model=list[uuid.UUID])
async def list_my_blocks(
    current: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    return await service.list_blocked(session, current.id)


@router.post("/users/{user_id}/block", status_code=status.HTTP_204_NO_CONTENT)
async def block_user(
    user_id: uuid.UUID,
    current: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    try:
        await service.block_user(session, current.id, user_id)
    except service.SafetyError as exc:
        code = status.HTTP_404_NOT_FOUND if "not found" in str(exc) else status.HTTP_400_BAD_REQUEST
        raise HTTPException(code, str(exc))


@router.delete("/users/{user_id}/block", status_code=status.HTTP_204_NO_CONTENT)
async def unblock_user(
    user_id: uuid.UUID,
    current: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    await service.unblock_user(session, current.id, user_id)
