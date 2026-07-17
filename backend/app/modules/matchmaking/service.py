import uuid

from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.common.enums import AccountState
from app.modules.identity.models import Profile, User
from app.modules.matchmaking.models import Match


class MatchError(Exception):
    pass


async def get_discovery_feed(
    session: AsyncSession, user_id: uuid.UUID, limit: int = 20
) -> list[Profile]:
    """Return profiles of PROFILE_ACTIVE users not already matched with current user.

    v1: simple eligibility filter, no ranking. ML ranking is a later milestone.
    """
    matched_ids_q = select(Match.user_a_id, Match.user_b_id).where(
        or_(Match.user_a_id == user_id, Match.user_b_id == user_id)
    )
    matched_rows = (await session.execute(matched_ids_q)).all()
    already_matched: set[uuid.UUID] = set()
    for row in matched_rows:
        already_matched.add(row.user_a_id)
        already_matched.add(row.user_b_id)
    already_matched.discard(user_id)

    q = (
        select(Profile)
        .join(User, User.id == Profile.user_id)
        .where(User.account_state == AccountState.PROFILE_ACTIVE)
        .where(Profile.user_id != user_id)
        .where(Profile.user_id.not_in(already_matched) if already_matched else True)
        .limit(limit)
    )
    return list(await session.scalars(q))


async def create_match(
    session: AsyncSession, user_a_id: uuid.UUID, user_b_id: uuid.UUID
) -> Match:
    if user_a_id == user_b_id:
        raise MatchError("cannot match with yourself")

    # Canonical ordering so (A,B) and (B,A) are the same row.
    a, b = (user_a_id, user_b_id) if user_a_id < user_b_id else (user_b_id, user_a_id)

    existing = await session.scalar(
        select(Match).where(Match.user_a_id == a, Match.user_b_id == b)
    )
    if existing is not None:
        raise MatchError("match already exists")

    match = Match(user_a_id=a, user_b_id=b)
    session.add(match)
    await session.commit()
    await session.refresh(match)
    return match


async def list_matches(
    session: AsyncSession, user_id: uuid.UUID
) -> list[Match]:
    return list(
        await session.scalars(
            select(Match)
            .where(or_(Match.user_a_id == user_id, Match.user_b_id == user_id))
            .order_by(Match.created_at.desc())
        )
    )


async def get_match(
    session: AsyncSession, match_id: uuid.UUID, user_id: uuid.UUID
) -> Match:
    match = await session.get(Match, match_id)
    if match is None:
        raise MatchError("match not found")
    if match.user_a_id != user_id and match.user_b_id != user_id:
        raise MatchError("not a participant in this match")
    return match
