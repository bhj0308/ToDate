from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.common.security import issue_access_token, issue_refresh_token
from app.config import get_settings
from app.db import get_session
from app.deps import get_current_user
from app.modules.identity import service
from app.modules.identity.models import User
from app.modules.identity.schemas import (
    OtpStartRequest,
    OtpStartResponse,
    OtpVerifyRequest,
    ProfileOut,
    ProfileUpdate,
    RegisterRequest,
    TokenPair,
    UserOut,
)

router = APIRouter(tags=["identity"])
_settings = get_settings()


@router.post("/users", response_model=UserOut, status_code=status.HTTP_201_CREATED)
async def register(
    body: RegisterRequest, session: AsyncSession = Depends(get_session)
):
    try:
        return await service.register_user(session, body.email, body.phone)
    except service.IdentityError as exc:
        raise HTTPException(status.HTTP_409_CONFLICT, str(exc))


@router.post("/auth/otp/start", response_model=OtpStartResponse)
async def otp_start(
    body: OtpStartRequest, session: AsyncSession = Depends(get_session)
):
    challenge, code = await service.start_otp(
        session, body.destination, body.channel
    )
    dev_code = None if _settings.environment == "production" else code
    return OtpStartResponse(challenge_id=challenge.id, dev_code=dev_code)


@router.post("/auth/otp/verify", response_model=TokenPair)
async def otp_verify(
    body: OtpVerifyRequest, session: AsyncSession = Depends(get_session)
):
    try:
        user = await service.verify_otp_challenge(
            session, body.challenge_id, body.code
        )
    except service.IdentityError as exc:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, str(exc))
    return TokenPair(
        access_token=issue_access_token(user.id),
        refresh_token=issue_refresh_token(user.id),
    )


@router.get("/users/me", response_model=UserOut)
async def me(current: User = Depends(get_current_user)):
    return current


@router.get("/profiles/me", response_model=ProfileOut)
async def my_profile(
    current: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    return await service.get_profile(session, current.id)


@router.put("/profiles/me", response_model=ProfileOut)
async def update_my_profile(
    body: ProfileUpdate,
    current: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    return await service.update_profile(
        session, current.id, body.model_dump(exclude_unset=True)
    )
