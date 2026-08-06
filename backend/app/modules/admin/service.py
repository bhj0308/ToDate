import uuid
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.common.enums import AccountState, AuditActorType, ModerationStatus
from app.modules.admin.models import AuditEvent, BetaInvite, ModerationCase
from app.modules.identity.models import Profile, User, VerifiedAttributes


class AdminError(Exception):
    pass


# ---------------------------------------------------------------------------
# Profile activation
# ---------------------------------------------------------------------------
#
# Real activation is meant to run through Verification (REGISTERED -> ... ->
# VERIFIED_AND_ELIGIBLE -> PROFILE_ACTIVE), but that domain is a deliberate
# 501 stub pending legal sign-off. This is the beta's substitute: a human
# curator (matches "personally curated, invite-only" in the GTM plan) reviews
# and activates directly, skipping the verification-specific states.

async def list_users_by_state(
    session: AsyncSession, account_state: AccountState
) -> list[dict]:
    rows = await session.execute(
        select(User.id, User.email, User.account_state, Profile.display_name)
        .join(Profile, Profile.user_id == User.id)
        .where(User.account_state == account_state)
        .order_by(User.created_at.asc())
    )
    return [
        {
            "id": row.id,
            "email": row.email,
            "account_state": row.account_state,
            "display_name": row.display_name,
        }
        for row in rows
    ]


async def activate_profile(
    session: AsyncSession, user_id: uuid.UUID, admin_id: uuid.UUID
) -> User:
    user = await session.get(User, user_id)
    if user is None:
        raise AdminError("user not found")
    if user.account_state == AccountState.PROFILE_ACTIVE:
        raise AdminError("already active")

    user.account_state = AccountState.PROFILE_ACTIVE
    await session.commit()
    await session.refresh(user)

    await log_audit_event(
        session,
        AuditActorType.ADMIN,
        admin_id,
        event_type="profile_activated",
        subject_type="user",
        subject_id=user.id,
    )
    await session.commit()
    return user


async def set_verified_attributes(
    session: AsyncSession, user_id: uuid.UUID, admin_id: uuid.UUID, fields: dict
) -> VerifiedAttributes:
    """Manual override for the same reason activation is manual: Verification
    is blocked, so this is the only way `income_percentile_tier` /
    `education_level` ever get set, which the discovery filters depend on.
    """
    va = await session.scalar(
        select(VerifiedAttributes).where(VerifiedAttributes.user_id == user_id)
    )
    if va is None:
        raise AdminError("verified attributes not found")

    for key, value in fields.items():
        setattr(va, key, value)
    await session.commit()
    await session.refresh(va)

    await log_audit_event(
        session,
        AuditActorType.ADMIN,
        admin_id,
        event_type="verified_attributes_updated",
        subject_type="user",
        subject_id=user_id,
        metadata={k: str(v) for k, v in fields.items()},
    )
    await session.commit()
    return va


# ---------------------------------------------------------------------------
# Audit log
# ---------------------------------------------------------------------------

async def log_audit_event(
    session: AsyncSession,
    actor_type: AuditActorType,
    actor_id: uuid.UUID | None,
    event_type: str,
    subject_type: str,
    subject_id: uuid.UUID,
    metadata: dict | None = None,
) -> AuditEvent:
    event = AuditEvent(
        actor_type=actor_type,
        actor_id=actor_id,
        event_type=event_type,
        subject_type=subject_type,
        subject_id=subject_id,
        event_metadata=metadata,
    )
    session.add(event)
    await session.flush()
    return event


async def list_audit_events(
    session: AsyncSession, subject_id: uuid.UUID | None, limit: int = 50
) -> list[AuditEvent]:
    query = select(AuditEvent).order_by(AuditEvent.occurred_at.desc()).limit(limit)
    if subject_id is not None:
        query = query.where(AuditEvent.subject_id == subject_id)
    return list(await session.scalars(query))


# ---------------------------------------------------------------------------
# Moderation
# ---------------------------------------------------------------------------

async def open_moderation_case(
    session: AsyncSession,
    reporter_id: uuid.UUID,
    subject_type,
    subject_id: uuid.UUID,
    reason: str,
) -> ModerationCase:
    case = ModerationCase(
        reporter_id=reporter_id,
        subject_type=subject_type,
        subject_id=subject_id,
        reason=reason,
    )
    session.add(case)
    await session.commit()
    await session.refresh(case)
    return case


async def list_moderation_cases(
    session: AsyncSession, status_filter: ModerationStatus | None
) -> list[ModerationCase]:
    query = select(ModerationCase).order_by(ModerationCase.created_at.desc())
    if status_filter is not None:
        query = query.where(ModerationCase.status == status_filter)
    return list(await session.scalars(query))


async def action_moderation_case(
    session: AsyncSession,
    case_id: uuid.UUID,
    admin_id: uuid.UUID,
    decision: ModerationStatus,
) -> ModerationCase:
    if decision == ModerationStatus.OPEN:
        raise AdminError("decision must be actioned or dismissed")

    case = await session.get(ModerationCase, case_id)
    if case is None:
        raise AdminError("moderation case not found")
    if case.status != ModerationStatus.OPEN:
        raise AdminError("case already resolved")

    case.status = decision
    case.assigned_admin_id = admin_id
    case.resolved_at = datetime.now(timezone.utc)
    await session.commit()
    await session.refresh(case)

    await log_audit_event(
        session,
        AuditActorType.ADMIN,
        admin_id,
        event_type=f"moderation_case_{decision.value}",
        subject_type=case.subject_type.value,
        subject_id=case.subject_id,
        metadata={"case_id": str(case.id)},
    )
    await session.commit()
    return case


# ---------------------------------------------------------------------------
# Beta invites
# ---------------------------------------------------------------------------

async def is_email_invited(session: AsyncSession, email: str) -> bool:
    invite = await session.scalar(
        select(BetaInvite).where(
            BetaInvite.email == email, BetaInvite.redeemed_at.is_(None)
        )
    )
    return invite is not None


async def redeem_invite(session: AsyncSession, email: str) -> None:
    invite = await session.scalar(
        select(BetaInvite).where(
            BetaInvite.email == email, BetaInvite.redeemed_at.is_(None)
        )
    )
    if invite is not None:
        invite.redeemed_at = datetime.now(timezone.utc)


async def create_beta_invite(
    session: AsyncSession, email: str, invited_by: uuid.UUID
) -> BetaInvite:
    existing = await session.scalar(
        select(BetaInvite).where(BetaInvite.email == email)
    )
    if existing is not None:
        raise AdminError("an invite for this email already exists")

    invite = BetaInvite(email=email, invited_by=invited_by)
    session.add(invite)
    await session.commit()
    await session.refresh(invite)

    await log_audit_event(
        session,
        AuditActorType.ADMIN,
        invited_by,
        event_type="beta_invite_created",
        subject_type="beta_invite",
        subject_id=invite.id,
        metadata={"email": email},
    )
    await session.commit()
    return invite
