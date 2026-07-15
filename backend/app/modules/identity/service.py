import logging
import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.common.enums import AccountState
from app.common.security import (
    generate_otp_code,
    hash_otp,
    verify_otp,
)
from app.config import get_settings
from app.modules.identity.models import (
    OtpChallenge,
    Profile,
    User,
    VerifiedAttributes,
)

logger = logging.getLogger("todate.identity")
_settings = get_settings()


class IdentityError(Exception):
    """Domain error surfaced by the router as a 4xx."""


async def register_user(
    session: AsyncSession, email: str, phone: str | None
) -> User:
    existing = await session.scalar(select(User).where(User.email == email))
    if existing is not None:
        raise IdentityError("email already registered")

    user = User(email=email, phone=phone, account_state=AccountState.REGISTERED)
    session.add(user)
    await session.flush()

    # Create empty companion rows so downstream reads never null-check them.
    session.add(Profile(user_id=user.id))
    session.add(VerifiedAttributes(user_id=user.id))
    await session.commit()
    await session.refresh(user)
    return user


async def start_otp(
    session: AsyncSession, destination: str, channel: str
) -> tuple[OtpChallenge, str]:
    code = generate_otp_code()
    challenge = OtpChallenge(
        destination=destination,
        channel=channel,
        code_hash=hash_otp(code),
    )
    session.add(challenge)
    await session.commit()
    await session.refresh(challenge)

    # DEV: log instead of sending. Real delivery is a vendor integration.
    logger.info("OTP for %s (%s): %s", destination, channel, code)
    return challenge, code


async def verify_otp_challenge(
    session: AsyncSession, challenge_id: uuid.UUID, code: str
) -> User:
    challenge = await session.get(OtpChallenge, challenge_id)
    if challenge is None or challenge.consumed:
        raise IdentityError("invalid or expired challenge")
    if not verify_otp(code, challenge.code_hash):
        raise IdentityError("incorrect code")

    challenge.consumed = True

    # Resolve the user by the verified destination; auto-register on first
    # login by email so the OTP flow is self-contained for v1.
    user = await _find_user_by_destination(
        session, challenge.destination, challenge.channel
    )
    if user is None:
        if challenge.channel == "email":
            user = await register_user(session, challenge.destination, None)
        else:
            raise IdentityError("no account for this phone number")

    await session.commit()
    return user


async def _find_user_by_destination(
    session: AsyncSession, destination: str, channel: str
) -> User | None:
    column = User.email if channel == "email" else User.phone
    return await session.scalar(select(User).where(column == destination))


async def get_profile(session: AsyncSession, user_id: uuid.UUID) -> Profile:
    profile = await session.scalar(
        select(Profile).where(Profile.user_id == user_id)
    )
    if profile is None:
        raise IdentityError("profile not found")
    return profile


async def update_profile(
    session: AsyncSession, user_id: uuid.UUID, fields: dict
) -> Profile:
    profile = await get_profile(session, user_id)
    for key, value in fields.items():
        if value is not None:
            setattr(profile, key, value)
    await session.commit()
    await session.refresh(profile)
    return profile
