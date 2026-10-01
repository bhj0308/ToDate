import uuid

from fastapi import APIRouter, Depends, File, HTTPException, Request, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession

import jwt

from app.common.ratelimit import SlidingWindowLimiter, rate_limit
from app.common.security import decode_token, issue_access_token, issue_refresh_token
from app.config import get_settings
from app.db import get_session
from app.deps import ensure_active, get_current_user
from app.modules.identity import service
from app.modules.identity.models import User
from app.modules.identity.schemas import (
    DateOfBirthIn,
    OtpStartRequest,
    OtpStartResponse,
    OtpVerifyRequest,
    ProfileOut,
    ProfileUpdate,
    RefreshRequest,
    RegisterRequest,
    TokenPair,
    UserOut,
    VerifiedAttributesOut,
)

router = APIRouter(tags=["identity"])
_settings = get_settings()

_otp_start_limiter = SlidingWindowLimiter(
    _settings.otp_start_max_per_window, _settings.rate_limit_window_seconds
)
_otp_verify_limiter = SlidingWindowLimiter(
    _settings.otp_verify_max_per_window, _settings.rate_limit_window_seconds
)


@router.post("/users", response_model=UserOut, status_code=status.HTTP_201_CREATED)
async def register(
    body: RegisterRequest, session: AsyncSession = Depends(get_session)
):
    try:
        return await service.register_user(session, email=body.email, phone=body.phone)
    except service.IdentityError as exc:
        raise HTTPException(status.HTTP_409_CONFLICT, str(exc))


@router.post(
    "/auth/otp/start",
    response_model=OtpStartResponse,
    dependencies=[Depends(rate_limit(_otp_start_limiter, "otp_start"))],
)
async def otp_start(
    body: OtpStartRequest, session: AsyncSession = Depends(get_session)
):
    challenge, code = await service.start_otp(
        session, body.destination, body.channel
    )
    dev_code = None if _settings.environment == "production" else code
    return OtpStartResponse(challenge_id=challenge.id, dev_code=dev_code)


@router.post(
    "/auth/otp/verify",
    response_model=TokenPair,
    dependencies=[Depends(rate_limit(_otp_verify_limiter, "otp_verify"))],
)
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


@router.post("/auth/refresh", response_model=TokenPair)
async def refresh_token(
    body: RefreshRequest, session: AsyncSession = Depends(get_session)
):
    try:
        user_id = decode_token(body.refresh_token, "refresh")
    except (jwt.PyJWTError, ValueError):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "invalid or expired refresh token")

    user = await session.get(User, user_id)
    ensure_active(user)

    return TokenPair(
        access_token=issue_access_token(user.id),
        refresh_token=issue_refresh_token(user.id),
    )


@router.get("/users/me", response_model=UserOut)
async def me(current: User = Depends(get_current_user)):
    return current


@router.put("/users/me/date-of-birth", response_model=UserOut)
async def set_date_of_birth(
    body: DateOfBirthIn,
    current: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """One-time, self-reported. Under 18 suspends the account."""
    try:
        return await service.set_date_of_birth(session, current, body.date_of_birth)
    except service.UnderageError as exc:
        raise HTTPException(status.HTTP_403_FORBIDDEN, str(exc))
    except service.IdentityError as exc:
        raise HTTPException(status.HTTP_409_CONFLICT, str(exc))
    except ValueError as exc:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_CONTENT, str(exc))


@router.delete("/users/me", status_code=status.HTTP_204_NO_CONTENT)
async def delete_my_account(
    current: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """Permanently anonymize this account (ADR-0003). Not reversible."""
    await service.delete_account(session, current)


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


@router.post("/profiles/me/photos", response_model=ProfileOut)
async def upload_profile_photo(
    request: Request,
    file: UploadFile = File(...),
    current: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    content = await file.read()
    return await service.add_profile_photo(
        session,
        current.id,
        filename=file.filename or "photo.jpg",
        content=content,
        base_url=str(request.base_url),
    )


@router.get("/profiles/{user_id}", response_model=ProfileOut)
async def get_profile_by_id(
    user_id: uuid.UUID,
    current: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    try:
        return await service.get_public_profile(session, user_id, current.id)
    except service.IdentityError as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, str(exc))


@router.get("/users/me/verified-attributes", response_model=VerifiedAttributesOut)
async def my_verified_attributes(
    current: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    try:
        return await service.get_verified_attributes(session, current.id)
    except service.IdentityError as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, str(exc))
