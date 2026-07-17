import uuid
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.common.enums import DateOutcome, DatePromptChoice, MatchState
from app.modules.matchmaking.models import Match
from app.modules.structured.models import (
    AvailabilityWindow,
    DatePlan,
    DatePromptResponse,
    Message,
)
from app.modules.structured.schemas import (
    ConversationOut,
    DatePlanOut,
    DatePromptStateOut,
    VenueRecommendationOut,
)

# States in which chat is open for new messages.
_CHAT_STATES = {MatchState.CHAT_OPEN, MatchState.EXTENDED_CHAT}


class StructuredError(Exception):
    pass


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

async def _get_match_for_participant(
    session: AsyncSession, match_id: uuid.UUID, user_id: uuid.UUID
) -> Match:
    match = await session.get(Match, match_id)
    if match is None:
        raise StructuredError("match not found")
    if match.user_a_id != user_id and match.user_b_id != user_id:
        raise StructuredError("not a participant in this match")
    return match


def _counterpart(match: Match, user_id: uuid.UUID) -> uuid.UUID:
    return match.user_b_id if match.user_a_id == user_id else match.user_a_id


# ---------------------------------------------------------------------------
# Conversation / Messages
# ---------------------------------------------------------------------------

async def send_message(
    session: AsyncSession, match_id: uuid.UUID, sender_id: uuid.UUID, body: str
) -> Message:
    match = await _get_match_for_participant(session, match_id, sender_id)
    if match.state not in _CHAT_STATES:
        raise StructuredError(
            f"cannot send messages in match state {match.state.value}"
        )
    msg = Message(match_id=match_id, sender_id=sender_id, body=body)
    session.add(msg)
    await session.commit()
    await session.refresh(msg)
    return msg


async def get_conversation(
    session: AsyncSession, match_id: uuid.UUID, user_id: uuid.UUID
) -> ConversationOut:
    match = await _get_match_for_participant(session, match_id, user_id)
    messages = list(
        await session.scalars(
            select(Message)
            .where(Message.match_id == match_id)
            .order_by(Message.created_at.asc())
        )
    )
    return ConversationOut(
        match_id=match_id, state=match.state, messages=messages
    )


# ---------------------------------------------------------------------------
# Date prompt
# ---------------------------------------------------------------------------

async def trigger_date_prompt(
    session: AsyncSession, match_id: uuid.UUID, user_id: uuid.UUID
) -> Match:
    """Advance match to DATE_PROMPT_PENDING.

    In production this is called by a background scheduler after 3-5 days of
    chat; exposed here so the flow is exercisable without infrastructure.
    Only participants may trigger (ops/admin enforcement is a later layer).
    """
    match = await _get_match_for_participant(session, match_id, user_id)
    if match.state not in _CHAT_STATES:
        raise StructuredError(
            f"date prompt requires CHAT_OPEN or EXTENDED_CHAT, got {match.state.value}"
        )
    match.state = MatchState.DATE_PROMPT_PENDING
    await session.commit()
    await session.refresh(match)
    return match


async def get_date_prompt_state(
    session: AsyncSession, match_id: uuid.UUID, user_id: uuid.UUID
) -> DatePromptStateOut:
    match = await _get_match_for_participant(session, match_id, user_id)
    active = match.state == MatchState.DATE_PROMPT_PENDING

    my_row = await session.scalar(
        select(DatePromptResponse).where(
            DatePromptResponse.match_id == match_id,
            DatePromptResponse.user_id == user_id,
        )
    )
    cp_id = _counterpart(match, user_id)
    cp_row = await session.scalar(
        select(DatePromptResponse).where(
            DatePromptResponse.match_id == match_id,
            DatePromptResponse.user_id == cp_id,
        )
    )

    resolved = my_row is not None and cp_row is not None
    return DatePromptStateOut(
        active=active,
        my_choice=my_row.choice if my_row else None,
        resolved=resolved,
        counterpart_choice=cp_row.choice if resolved else None,
        resolved_state=match.state if resolved and not active else None,
    )


def _resolve_match_state(
    a: DatePromptChoice, b: DatePromptChoice
) -> MatchState:
    if DatePromptChoice.NO in (a, b):
        return MatchState.CLOSED
    if a == DatePromptChoice.YES and b == DatePromptChoice.YES:
        return MatchState.SCHEDULE_READY
    # YES+MAYBE or MAYBE+MAYBE → extended window
    return MatchState.EXTENDED_CHAT


async def submit_date_prompt_response(
    session: AsyncSession,
    match_id: uuid.UUID,
    user_id: uuid.UUID,
    choice: DatePromptChoice,
) -> DatePromptStateOut:
    match = await _get_match_for_participant(session, match_id, user_id)
    if match.state != MatchState.DATE_PROMPT_PENDING:
        raise StructuredError("date prompt is not active for this match")

    existing = await session.scalar(
        select(DatePromptResponse).where(
            DatePromptResponse.match_id == match_id,
            DatePromptResponse.user_id == user_id,
        )
    )
    if existing is not None:
        raise StructuredError("already responded to this date prompt")

    row = DatePromptResponse(match_id=match_id, user_id=user_id, choice=choice)
    session.add(row)

    cp_id = _counterpart(match, user_id)
    cp_row = await session.scalar(
        select(DatePromptResponse).where(
            DatePromptResponse.match_id == match_id,
            DatePromptResponse.user_id == cp_id,
        )
    )

    if cp_row is not None:
        # Both have answered — resolve and transition.
        match.state = MatchState.DATE_PROMPT_CAPTURED
        await session.flush()
        new_state = _resolve_match_state(row.choice, cp_row.choice)
        match.state = new_state

    await session.commit()
    await session.refresh(match)

    resolved = cp_row is not None
    return DatePromptStateOut(
        active=match.state == MatchState.DATE_PROMPT_PENDING,
        my_choice=choice,
        resolved=resolved,
        counterpart_choice=cp_row.choice if resolved else None,
        resolved_state=match.state if resolved else None,
    )


# ---------------------------------------------------------------------------
# Availability
# ---------------------------------------------------------------------------

async def submit_availability(
    session: AsyncSession,
    match_id: uuid.UUID,
    user_id: uuid.UUID,
    slots: list[str],
) -> AvailabilityWindow:
    match = await _get_match_for_participant(session, match_id, user_id)
    if match.state != MatchState.SCHEDULE_READY:
        raise StructuredError("availability can only be submitted in SCHEDULE_READY state")

    existing = await session.scalar(
        select(AvailabilityWindow).where(
            AvailabilityWindow.match_id == match_id,
            AvailabilityWindow.user_id == user_id,
        )
    )
    if existing is not None:
        existing.slots = slots
        await session.commit()
        await session.refresh(existing)
        return existing

    window = AvailabilityWindow(match_id=match_id, user_id=user_id, slots=slots)
    session.add(window)
    await session.commit()
    await session.refresh(window)
    return window


# ---------------------------------------------------------------------------
# Venue recommendations (stub — real impl requires venue partner API)
# ---------------------------------------------------------------------------

_STUB_VENUES: list[VenueRecommendationOut] = [
    VenueRecommendationOut(
        name="The Penthouse",
        address="1 Luxury Ave",
        cuisine="Modern American",
        price_tier="$$$$",
    ),
    VenueRecommendationOut(
        name="Osteria Classica",
        address="22 Via Roma",
        cuisine="Italian",
        price_tier="$$$",
    ),
    VenueRecommendationOut(
        name="Sakura Omakase",
        address="8 Cherry Blossom Ln",
        cuisine="Japanese",
        price_tier="$$$$",
    ),
]


async def get_venue_recommendations(
    session: AsyncSession, match_id: uuid.UUID, user_id: uuid.UUID
) -> list[VenueRecommendationOut]:
    match = await _get_match_for_participant(session, match_id, user_id)
    if match.state != MatchState.SCHEDULE_READY:
        raise StructuredError(
            "venue recommendations are only available in SCHEDULE_READY state"
        )
    # v1 stub: returns hardcoded venues. Real implementation queries the
    # venue partner API using both users' dining preferences and location.
    return _STUB_VENUES


# ---------------------------------------------------------------------------
# Date plan
# ---------------------------------------------------------------------------

async def create_date_plan(
    session: AsyncSession,
    match_id: uuid.UUID,
    user_id: uuid.UUID,
    venue_name: str,
    venue_address: str | None,
    scheduled_at: datetime,
) -> DatePlan:
    match = await _get_match_for_participant(session, match_id, user_id)
    if match.state != MatchState.SCHEDULE_READY:
        raise StructuredError("date plan requires SCHEDULE_READY state")

    existing = await session.scalar(
        select(DatePlan).where(DatePlan.match_id == match_id)
    )
    if existing is not None:
        raise StructuredError("date plan already exists for this match")

    plan = DatePlan(
        match_id=match_id,
        venue_name=venue_name,
        venue_address=venue_address,
        scheduled_at=scheduled_at,
    )
    session.add(plan)
    await session.commit()
    await session.refresh(plan)
    return plan


async def record_date_outcome(
    session: AsyncSession,
    match_id: uuid.UUID,
    user_id: uuid.UUID,
    outcome: DateOutcome,
) -> DatePlan:
    await _get_match_for_participant(session, match_id, user_id)
    plan = await session.scalar(
        select(DatePlan).where(DatePlan.match_id == match_id)
    )
    if plan is None:
        raise StructuredError("no date plan found for this match")
    if plan.outcome is not None:
        raise StructuredError("outcome already recorded")

    plan.outcome = outcome
    plan.outcome_recorded_at = datetime.now(timezone.utc)
    await session.commit()
    await session.refresh(plan)
    return plan
