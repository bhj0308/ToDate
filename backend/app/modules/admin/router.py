import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.common.enums import AccountState, ModerationStatus
from app.db import get_session
from app.deps import get_current_admin, get_current_user
from app.modules.admin import service
from app.modules.admin.schemas import (
    AdminUserOut,
    AuditEventOut,
    BetaInviteCreate,
    BetaInviteOut,
    ModerationCaseAction,
    ModerationCaseCreate,
    ModerationCaseOut,
    VerifiedAttributesUpdate,
)
from app.modules.identity.models import User
from app.modules.identity.schemas import UserOut, VerifiedAttributesOut

router = APIRouter(prefix="/admin", tags=["admin"])


@router.post(
    "/moderation-cases",
    response_model=ModerationCaseOut,
    status_code=status.HTTP_201_CREATED,
)
async def report(
    body: ModerationCaseCreate,
    current: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """Open a case — any authenticated member can report a user/message/profile."""
    return await service.open_moderation_case(
        session, current.id, body.subject_type, body.subject_id, body.reason
    )


@router.get("/moderation-cases", response_model=list[ModerationCaseOut])
async def moderation_queue(
    status: ModerationStatus | None = None,
    current: User = Depends(get_current_admin),
    session: AsyncSession = Depends(get_session),
):
    return await service.list_moderation_cases(session, status)


@router.post("/moderation-cases/{case_id}/action", response_model=ModerationCaseOut)
async def action_case(
    case_id: uuid.UUID,
    body: ModerationCaseAction,
    current: User = Depends(get_current_admin),
    session: AsyncSession = Depends(get_session),
):
    try:
        return await service.action_moderation_case(
            session, case_id, current.id, body.decision
        )
    except service.AdminError as exc:
        raise HTTPException(status.HTTP_409_CONFLICT, str(exc))


@router.get("/audit-events", response_model=list[AuditEventOut])
async def audit_events(
    subject_id: uuid.UUID | None = None,
    current: User = Depends(get_current_admin),
    session: AsyncSession = Depends(get_session),
):
    return await service.list_audit_events(session, subject_id)


@router.post(
    "/beta-invites", response_model=BetaInviteOut, status_code=status.HTTP_201_CREATED
)
async def create_invite(
    body: BetaInviteCreate,
    current: User = Depends(get_current_admin),
    session: AsyncSession = Depends(get_session),
):
    try:
        return await service.create_beta_invite(session, body.email, current.id)
    except service.AdminError as exc:
        raise HTTPException(status.HTTP_409_CONFLICT, str(exc))


@router.get("/users", response_model=list[AdminUserOut])
async def curation_queue(
    account_state: AccountState = AccountState.REGISTERED,
    current: User = Depends(get_current_admin),
    session: AsyncSession = Depends(get_session),
):
    """Members awaiting manual activation (see service.activate_profile)."""
    return await service.list_users_by_state(session, account_state)


@router.post("/users/{user_id}/activate", response_model=UserOut)
async def activate_user(
    user_id: uuid.UUID,
    current: User = Depends(get_current_admin),
    session: AsyncSession = Depends(get_session),
):
    try:
        return await service.activate_profile(session, user_id, current.id)
    except service.AdminError as exc:
        raise HTTPException(status.HTTP_409_CONFLICT, str(exc))


@router.post("/users/{user_id}/verified-attributes", response_model=VerifiedAttributesOut)
async def set_verified_attributes(
    user_id: uuid.UUID,
    body: VerifiedAttributesUpdate,
    current: User = Depends(get_current_admin),
    session: AsyncSession = Depends(get_session),
):
    try:
        return await service.set_verified_attributes(
            session, user_id, current.id, body.model_dump(exclude_unset=True)
        )
    except service.AdminError as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, str(exc))
