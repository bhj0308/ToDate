import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_session
from app.deps import get_current_user
from app.modules.identity.models import User
from app.modules.structured import service
from app.modules.structured.schemas import (
    AvailabilityOut,
    AvailabilitySubmit,
    ConversationOut,
    DateOutcomeSubmit,
    DatePlanCreate,
    DatePlanOut,
    DatePromptResponseCreate,
    DatePromptStateOut,
    MessageCreate,
    MessageOut,
    VenueRecommendationOut,
)

router = APIRouter(tags=["structured"])

_match_prefix = "/matches/{match_id}"


@router.get(_match_prefix + "/conversation", response_model=ConversationOut)
async def get_conversation(
    match_id: uuid.UUID,
    current: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    try:
        return await service.get_conversation(session, match_id, current.id)
    except service.StructuredError as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, str(exc))


@router.post(
    _match_prefix + "/messages",
    response_model=MessageOut,
    status_code=status.HTTP_201_CREATED,
)
async def send_message(
    match_id: uuid.UUID,
    body: MessageCreate,
    current: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    try:
        return await service.send_message(session, match_id, current.id, body.body)
    except service.StructuredError as exc:
        raise HTTPException(status.HTTP_409_CONFLICT, str(exc))


@router.post(
    _match_prefix + "/date-prompt",
    response_model=dict,
    tags=["ops"],
    status_code=status.HTTP_200_OK,
)
async def trigger_date_prompt(
    match_id: uuid.UUID,
    current: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """Advance match to DATE_PROMPT_PENDING.

    System-triggered in production (scheduled after 3-5 days of chat).
    Exposed here so the flow is exercisable without scheduler infrastructure.
    """
    try:
        match = await service.trigger_date_prompt(session, match_id, current.id)
        return {"match_id": str(match.id), "state": match.state.value}
    except service.StructuredError as exc:
        raise HTTPException(status.HTTP_409_CONFLICT, str(exc))


@router.get(_match_prefix + "/date-prompt", response_model=DatePromptStateOut)
async def get_date_prompt(
    match_id: uuid.UUID,
    current: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    try:
        return await service.get_date_prompt_state(session, match_id, current.id)
    except service.StructuredError as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, str(exc))


@router.post(
    _match_prefix + "/date-prompt/response",
    response_model=DatePromptStateOut,
    status_code=status.HTTP_200_OK,
)
async def submit_date_prompt_response(
    match_id: uuid.UUID,
    body: DatePromptResponseCreate,
    current: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    try:
        return await service.submit_date_prompt_response(
            session, match_id, current.id, body.choice
        )
    except service.StructuredError as exc:
        raise HTTPException(status.HTTP_409_CONFLICT, str(exc))


@router.post(
    _match_prefix + "/availability",
    response_model=AvailabilityOut,
    status_code=status.HTTP_200_OK,
)
async def submit_availability(
    match_id: uuid.UUID,
    body: AvailabilitySubmit,
    current: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    try:
        return await service.submit_availability(
            session, match_id, current.id, body.slots
        )
    except service.StructuredError as exc:
        raise HTTPException(status.HTTP_409_CONFLICT, str(exc))


@router.get(
    _match_prefix + "/venue-recommendations",
    response_model=list[VenueRecommendationOut],
)
async def get_venue_recommendations(
    match_id: uuid.UUID,
    current: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    try:
        return await service.get_venue_recommendations(session, match_id, current.id)
    except service.StructuredError as exc:
        raise HTTPException(status.HTTP_409_CONFLICT, str(exc))


@router.post(
    _match_prefix + "/date-plan",
    response_model=DatePlanOut,
    status_code=status.HTTP_201_CREATED,
)
async def create_date_plan(
    match_id: uuid.UUID,
    body: DatePlanCreate,
    current: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    try:
        return await service.create_date_plan(
            session,
            match_id,
            current.id,
            body.venue_name,
            body.venue_address,
            body.scheduled_at,
        )
    except service.StructuredError as exc:
        raise HTTPException(status.HTTP_409_CONFLICT, str(exc))


@router.post(
    _match_prefix + "/date-plan/outcome",
    response_model=DatePlanOut,
    status_code=status.HTTP_200_OK,
)
async def record_date_outcome(
    match_id: uuid.UUID,
    body: DateOutcomeSubmit,
    current: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    try:
        return await service.record_date_outcome(
            session, match_id, current.id, body.outcome
        )
    except service.StructuredError as exc:
        raise HTTPException(status.HTTP_409_CONFLICT, str(exc))
