import uuid

import jwt
from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    WebSocket,
    WebSocketDisconnect,
    status,
)
from sqlalchemy.ext.asyncio import AsyncSession

from app.common.security import decode_token
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
from app.modules.structured.ws_manager import manager

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


@router.websocket(_match_prefix + "/ws")
async def conversation_ws(
    websocket: WebSocket,
    match_id: uuid.UUID,
    session: AsyncSession = Depends(get_session),
):
    """Realtime conversation transport (ADR-0002).

    Auth via `?token=<access token>` query param — native WebSocket clients
    can't set an Authorization header on the handshake request.
    """
    token = websocket.query_params.get("token")
    user = None
    if token:
        try:
            user_id = decode_token(token, "access")
            user = await session.get(User, user_id)
        except (jwt.PyJWTError, ValueError):
            user = None
    if user is None:
        await websocket.close(code=4401)
        return

    try:
        await service.get_match_for_participant(session, match_id, user.id)
    except service.StructuredError:
        await websocket.close(code=4404)
        return

    await manager.connect(match_id, websocket)
    try:
        while True:
            raw = await websocket.receive_text()
            try:
                body = MessageCreate.model_validate_json(raw).body
            except ValueError:
                await websocket.send_json({"type": "error", "detail": "invalid payload"})
                continue
            try:
                msg = await service.send_message(session, match_id, user.id, body)
            except service.StructuredError as exc:
                await websocket.send_json({"type": "error", "detail": str(exc)})
                continue
            out = MessageOut.model_validate(msg).model_dump(mode="json")
            await manager.broadcast(match_id, {"type": "message", "data": out})
    except WebSocketDisconnect:
        pass
    finally:
        manager.disconnect(match_id, websocket)


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


@router.get(_match_prefix + "/date-plan", response_model=DatePlanOut | None)
async def get_date_plan(
    match_id: uuid.UUID,
    current: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """Null (not 404) until a plan exists — normal state while still scheduling."""
    try:
        return await service.get_date_plan(session, match_id, current.id)
    except service.StructuredError as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, str(exc))


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
