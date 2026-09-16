"""Member-to-member blocking.

App Store review requires apps with user-generated content to let people block
abusive users (reporting already exists in the admin module).
"""

import uuid

from sqlalchemy import and_, delete, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.common.enums import AuditActorType, MatchState
from app.modules.admin.service import log_audit_event
from app.modules.identity.models import User
from app.modules.matchmaking.models import Match
from app.modules.safety.models import UserBlock


class SafetyError(Exception):
    pass


async def block_user(
    session: AsyncSession, blocker_id: uuid.UUID, blocked_id: uuid.UUID
) -> None:
    if blocker_id == blocked_id:
        raise SafetyError("cannot block yourself")
    if await session.get(User, blocked_id) is None:
        raise SafetyError("user not found")

    existing = await session.scalar(
        select(UserBlock).where(
            UserBlock.blocker_id == blocker_id, UserBlock.blocked_id == blocked_id
        )
    )
    if existing is not None:
        return  # idempotent

    session.add(UserBlock(blocker_id=blocker_id, blocked_id=blocked_id))

    # End any conversation between them. CLOSED already stops messages and the
    # date prompt, so no other module needs to know about blocks.
    a, b = sorted((blocker_id, blocked_id))
    match = await session.scalar(
        select(Match).where(Match.user_a_id == a, Match.user_b_id == b)
    )
    if match is not None:
        match.state = MatchState.CLOSED

    await log_audit_event(
        session,
        AuditActorType.USER,
        blocker_id,
        event_type="user_blocked",
        subject_type="user",
        subject_id=blocked_id,
    )
    await session.commit()


async def unblock_user(
    session: AsyncSession, blocker_id: uuid.UUID, blocked_id: uuid.UUID
) -> None:
    """Lifts the block. A match it closed stays closed."""
    await session.execute(
        delete(UserBlock).where(
            UserBlock.blocker_id == blocker_id, UserBlock.blocked_id == blocked_id
        )
    )
    await session.commit()


async def list_blocked(session: AsyncSession, user_id: uuid.UUID) -> list[uuid.UUID]:
    return list(
        await session.scalars(
            select(UserBlock.blocked_id)
            .where(UserBlock.blocker_id == user_id)
            .order_by(UserBlock.created_at.desc())
        )
    )


async def hidden_user_ids(session: AsyncSession, user_id: uuid.UUID) -> set[uuid.UUID]:
    """Everyone this user blocked plus everyone who blocked them."""
    rows = await session.execute(
        select(UserBlock.blocker_id, UserBlock.blocked_id).where(
            or_(UserBlock.blocker_id == user_id, UserBlock.blocked_id == user_id)
        )
    )
    hidden = {uid for row in rows for uid in row}
    hidden.discard(user_id)
    return hidden


async def is_blocked_between(
    session: AsyncSession, a: uuid.UUID, b: uuid.UUID
) -> bool:
    row = await session.scalar(
        select(UserBlock.id).where(
            or_(
                and_(UserBlock.blocker_id == a, UserBlock.blocked_id == b),
                and_(UserBlock.blocker_id == b, UserBlock.blocked_id == a),
            )
        )
    )
    return row is not None
