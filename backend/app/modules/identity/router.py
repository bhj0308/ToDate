import uuid

from fastapi import APIRouter, Depends, File, HTTPException, Request, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession

import jwt

from app.common.security import decode_token, issue_access_token, issue_refresh_token
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
    RefreshRequest,
    RegisterRequest,
    TokenPair,
    UserOut,
    VerifiedAttributesOut,
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


@router.post("/auth/refresh", response_model=TokenPair)
async def refresh_token(
    body: RefreshRequest, session: AsyncSession = Depends(get_session)
):
    try:
        user_id = decode_token(body.refresh_token, "refresh")
    except (jwt.PyJWTError, ValueError):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "invalid or expired refresh token")

    user = await session.get(User, user_id)
    if user is None:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "user not found")

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
        return await service.get_public_profile(session, user_id)
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
