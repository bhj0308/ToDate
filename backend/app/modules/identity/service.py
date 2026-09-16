import logging
import uuid
from datetime import date
from pathlib import Path

from sqlalchemy import delete, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.common.age import is_adult, is_plausible
from app.common.enums import (
    AccountState,
    AuditActorType,
    CriminalCheckStatus,
    Eligibility,
    IncomePercentileTier,
    MatchState,
    SubscriptionStatus,
    UserStatus,
)
from app.common.security import (
    generate_otp_code,
    hash_otp,
    verify_otp,
)
from app.config import get_settings
from app.modules.admin import service as admin_service
from app.modules.admin.models import AuditEvent, BetaInvite
from app.modules.entitlements.models import Subscription
from app.modules.identity.models import (
    OtpChallenge,
    Profile,
    User,
    VerifiedAttributes,
)
from app.modules.matchmaking.models import Match
from app.modules.notifications.service import delete_all_tokens
from app.modules.safety.service import is_blocked_between
from app.modules.structured.models import AvailabilityWindow, Message

logger = logging.getLogger("todate.identity")
_settings = get_settings()
_upload_dir = Path(_settings.upload_dir)


class IdentityError(Exception):
    """Domain error surfaced by the router as a 4xx."""


def _is_bootstrap_admin(email: str) -> bool:
    admins = {e.strip().lower() for e in _settings.bootstrap_admin_emails.split(",") if e.strip()}
    return email.lower() in admins


# Income tiers cycled deterministically by email so a demo crowd shows variety
# in the (entitlement-gated) discovery filters. Skewed toward higher tiers to
# fit ToDate's positioning.
_DEMO_TIERS = [
    IncomePercentileTier.T50_75,
    IncomePercentileTier.T75_90,
    IncomePercentileTier.T90_PLUS,
]
_DEMO_EDUCATION = ["Undergraduate", "Graduate", "Postgraduate"]
_DEMO_DATE_OF_BIRTH = date(1994, 6, 15)


def _new_verified_attributes(user_id: uuid.UUID, email: str) -> VerifiedAttributes:
    """Blank attributes normally; seeded 'verified' facts under DEMO_MODE."""
    if not _settings.demo_mode:
        return VerifiedAttributes(user_id=user_id)

    idx = sum(email.encode()) % len(_DEMO_TIERS)
    return VerifiedAttributes(
        user_id=user_id,
        identity_verified=True,
        criminal_check_status=CriminalCheckStatus.PASSED,
        income_percentile_tier=_DEMO_TIERS[idx],
        education_level=_DEMO_EDUCATION[idx],
        eligibility=Eligibility.ELIGIBLE,
    )


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

    # DEMO_MODE: skip the manual curation/verification gate so teammates who
    # sign in immediately appear in each other's discovery feed. Real flow
    # (REGISTERED -> admin activation, Verification-driven attributes) is
    # unchanged when demo_mode is off.
    account_state = (
        AccountState.PROFILE_ACTIVE
        if _settings.demo_mode
        else AccountState.REGISTERED
    )

    user = User(
        email=email,
        phone=phone,
        account_state=account_state,
        is_admin=is_bootstrap_admin,
        # DEMO_MODE fakes the Vetted pillar, including a stated adult birth date,
        # so demo accounts pass the age gate without an onboarding step.
        date_of_birth=_DEMO_DATE_OF_BIRTH if _settings.demo_mode else None,
    )
    session.add(user)
    await session.flush()

    # Create empty companion rows so downstream reads never null-check them.
    session.add(Profile(user_id=user.id))
    session.add(_new_verified_attributes(user.id, email))
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
    elif user.status != UserStatus.ACTIVE:
        raise IdentityError("this account is not active")

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
    session: AsyncSession, target_user_id: uuid.UUID, viewer_id: uuid.UUID
) -> Profile:
    # Deleted accounts and anyone on either side of a block read as not found,
    # so a block can't be detected from the response.
    profile = await session.scalar(
        select(Profile)
        .join(User, User.id == Profile.user_id)
        .where(Profile.user_id == target_user_id)
        .where(User.status != UserStatus.DELETED)
    )
    if profile is None or await is_blocked_between(session, viewer_id, target_user_id):
        raise IdentityError("profile not found")
    return profile


class UnderageError(IdentityError):
    pass


async def set_date_of_birth(
    session: AsyncSession, user: User, date_of_birth: date
) -> User:
    """Record a self-reported birth date. One attempt only.

    Immutable once set, and an under-18 answer suspends the account — otherwise
    anyone refused could simply retry with an earlier year. The birth date of an
    under-18 person is deliberately not stored; the audit event records why the
    account was suspended. ID verification confirms age once it ships.
    """
    if user.date_of_birth is not None:
        raise IdentityError("date of birth is already set")
    if not is_plausible(date_of_birth):
        raise ValueError("date of birth is not a valid date")

    if not is_adult(date_of_birth):
        user.status = UserStatus.SUSPENDED
        await admin_service.log_audit_event(
            session,
            AuditActorType.SYSTEM,
            None,
            event_type="account_suspended_underage",
            subject_type="user",
            subject_id=user.id,
        )
        await session.commit()
        raise UnderageError("you must be 18 or older to use ToDate")

    user.date_of_birth = date_of_birth
    await session.commit()
    await session.refresh(user)
    return user


async def delete_account(session: AsyncSession, user: User) -> None:
    """Anonymize an account on the member's request (ADR-0003).

    Removes what identifies the person or what they wrote; keeps the system and
    compliance records (verification cases/decisions, moderation cases, audit
    events) under their own retention rules. Irreversible.
    """
    user_id = user.id
    old_email, old_phone = user.email, user.phone

    # Photos on disk (dev-stub storage).
    profile = await session.scalar(select(Profile).where(Profile.user_id == user_id))
    if profile is not None:
        for url in profile.photos or []:
            (_upload_dir / Path(str(url)).name).unlink(missing_ok=True)
        for field in (
            "display_name", "bio", "prompts", "photos", "interests",
            "dining_preferences", "latitude", "longitude", "city_market",
        ):
            setattr(profile, field, None)

    va = await session.scalar(
        select(VerifiedAttributes).where(VerifiedAttributes.user_id == user_id)
    )
    if va is not None:
        va.income_percentile_tier = None
        va.education_level = None

    # Everything they wrote or scheduled, and every conversation they were in.
    await session.execute(delete(Message).where(Message.sender_id == user_id))
    await session.execute(
        delete(AvailabilityWindow).where(AvailabilityWindow.user_id == user_id)
    )
    for match in await session.scalars(
        select(Match).where(or_(Match.user_a_id == user_id, Match.user_b_id == user_id))
    ):
        match.state = MatchState.CLOSED

    for sub in await session.scalars(
        select(Subscription).where(
            Subscription.user_id == user_id,
            Subscription.status.in_([SubscriptionStatus.ACTIVE, SubscriptionStatus.PAST_DUE]),
        )
    ):
        sub.status = SubscriptionStatus.CANCELED

    await delete_all_tokens(session, user_id)

    # Contact details also live outside the users row.
    destinations = [d for d in (old_email, old_phone) if d]
    await session.execute(
        delete(OtpChallenge).where(OtpChallenge.destination.in_(destinations))
    )
    invite_ids = list(
        await session.scalars(select(BetaInvite.id).where(BetaInvite.email == old_email))
    )
    if invite_ids:
        # Audit events are append-only, but invite events carry the raw email.
        # Redact that one field and keep the event (ADR-0003).
        for event in await session.scalars(
            select(AuditEvent).where(
                AuditEvent.subject_type == "beta_invite",
                AuditEvent.subject_id.in_(invite_ids),
            )
        ):
            if event.event_metadata and "email" in event.event_metadata:
                event.event_metadata = {**event.event_metadata, "email": "[redacted]"}
        await session.execute(delete(BetaInvite).where(BetaInvite.id.in_(invite_ids)))

    user.email = f"deleted+{user_id.hex}@deleted.invalid"  # unique, never deliverable
    user.phone = None
    user.date_of_birth = None
    user.is_admin = False
    user.status = UserStatus.DELETED
    user.account_state = AccountState.REGISTERED  # never in discovery again

    await admin_service.log_audit_event(
        session,
        AuditActorType.USER,
        user_id,
        event_type="account_deleted",
        subject_type="user",
        subject_id=user_id,
    )
    await session.commit()
