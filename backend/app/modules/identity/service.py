import logging
import uuid
from pathlib import Path

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.common.enums import AccountState
from app.common.security import (
    generate_otp_code,
    hash_otp,
    verify_otp,
)
from app.config import get_settings
from app.modules.admin import service as admin_service
from app.modules.identity.models import (
    OtpChallenge,
    Profile,
    User,
    VerifiedAttributes,
)

logger = logging.getLogger("todate.identity")
_settings = get_settings()
_upload_dir = Path(_settings.upload_dir)


class IdentityError(Exception):
    """Domain error surfaced by the router as a 4xx."""


def _is_bootstrap_admin(email: str) -> bool:
    admins = {e.strip().lower() for e in _settings.bootstrap_admin_emails.split(",") if e.strip()}
    return email.lower() in admins


async def register_user(
    session: AsyncSession, email: str, phone: str | None
) -> User:
    existing = await session.scalar(select(User).where(User.email == email))
    if existing is not None:
        raise IdentityError("email already registered")

    is_bootstrap_admin = _is_bootstrap_admin(email)
    # Invite-only beta (Phase 1 GTM) — enforced in production only, so local
    # dev keeps the frictionless "any email registers" demo flow.
    if _settings.environment == "production" and not is_bootstrap_admin:
        if not await admin_service.is_email_invited(session, email):
            raise IdentityError("this beta is invite-only")

    user = User(
        email=email,
        phone=phone,
        account_state=AccountState.REGISTERED,
        is_admin=is_bootstrap_admin,
    )
    session.add(user)
    await session.flush()

    # Create empty companion rows so downstream reads never null-check them.
    session.add(Profile(user_id=user.id))
    session.add(VerifiedAttributes(user_id=user.id))
    await admin_service.redeem_invite(session, email)
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


async def add_profile_photo(
    session: AsyncSession,
    user_id: uuid.UUID,
    filename: str,
    content: bytes,
    base_url: str,
) -> Profile:
    """Dev-stub photo storage: saves to local disk, served at /uploads/<name>.

    Real impl needs an object-storage vendor (S3 per ADR-0002).
    """
    _upload_dir.mkdir(parents=True, exist_ok=True)
    ext = Path(filename).suffix or ".jpg"
    stored_name = f"{uuid.uuid4().hex}{ext}"
    (_upload_dir / stored_name).write_bytes(content)

    profile = await get_profile(session, user_id)
    photos = list(profile.photos or [])
    photos.append(f"{base_url.rstrip('/')}/uploads/{stored_name}")
    profile.photos = photos
    await session.commit()
    await session.refresh(profile)
    return profile


async def get_verified_attributes(
    session: AsyncSession, user_id: uuid.UUID
) -> VerifiedAttributes:
    va = await session.scalar(
        select(VerifiedAttributes).where(VerifiedAttributes.user_id == user_id)
    )
    if va is None:
        raise IdentityError("verified attributes not found")
    return va


async def get_public_profile(
    session: AsyncSession, target_user_id: uuid.UUID
) -> Profile:
    profile = await session.scalar(
        select(Profile).where(Profile.user_id == target_user_id)
    )
    if profile is None:
        raise IdentityError("profile not found")
    return profile
