"""Push notifications via the Expo Push Service (chosen for v1 release).

Delivery never blocks or fails a user's request: routers schedule `notify`
as a background task, and every error here is logged and swallowed.

Notification text is deliberately generic ("You have a new message") so nothing
personal shows on a lock screen — this is a dating app.
"""

import asyncio
import logging
import uuid

import httpx
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.db import SessionLocal
from app.modules.notifications.models import PushToken

logger = logging.getLogger("todate.notifications")
_settings = get_settings()

EXPO_PUSH_URL = "https://exp.host/--/api/v2/push/send"
_EXPO_BATCH_SIZE = 100  # Expo's documented per-request message limit


async def register_token(
    session: AsyncSession, user_id: uuid.UUID, token: str, platform: str | None
) -> None:
    existing = await session.scalar(select(PushToken).where(PushToken.token == token))
    if existing is None:
        session.add(PushToken(user_id=user_id, token=token, platform=platform))
    else:
        existing.user_id = user_id
        existing.platform = platform
    await session.commit()


async def unregister_token(
    session: AsyncSession, user_id: uuid.UUID, token: str
) -> None:
    await session.execute(
        delete(PushToken).where(PushToken.user_id == user_id, PushToken.token == token)
    )
    await session.commit()


async def delete_all_tokens(session: AsyncSession, user_id: uuid.UUID) -> None:
    """Used by account deletion; caller commits."""
    await session.execute(delete(PushToken).where(PushToken.user_id == user_id))


async def _deliver(messages: list[dict]) -> list[dict]:
    """POST to Expo; returns one ticket per message. Patched in tests."""
    headers = {"Accept": "application/json", "Content-Type": "application/json"}
    if _settings.expo_access_token:
        headers["Authorization"] = f"Bearer {_settings.expo_access_token}"
    tickets: list[dict] = []
    async with httpx.AsyncClient(timeout=10) as client:
        for i in range(0, len(messages), _EXPO_BATCH_SIZE):
            batch = messages[i : i + _EXPO_BATCH_SIZE]
            response = await client.post(EXPO_PUSH_URL, json=batch, headers=headers)
            response.raise_for_status()
            tickets.extend(response.json().get("data", []))
    return tickets


async def notify(
    user_ids: list[uuid.UUID], title: str, body: str, data: dict | None = None
) -> None:
    """Send a push to every device of the given users. Never raises."""
    if not _settings.push_enabled or not user_ids:
        return
    try:
        # Background tasks outlive the request, so use a fresh session.
        async with SessionLocal() as session:
            tokens = list(
                await session.scalars(
                    select(PushToken.token).where(PushToken.user_id.in_(user_ids))
                )
            )
            if not tokens:
                return
            messages = [
                {"to": t, "title": title, "body": body, "data": data or {}, "sound": "default"}
                for t in tokens
            ]
            tickets = await _deliver(messages)

            # Expo reports uninstalled apps as DeviceNotRegistered; stop sending there.
            dead = [
                msg["to"]
                for msg, ticket in zip(messages, tickets)
                if ticket.get("status") == "error"
                and (ticket.get("details") or {}).get("error") == "DeviceNotRegistered"
            ]
            if dead:
                await session.execute(delete(PushToken).where(PushToken.token.in_(dead)))
                await session.commit()
    except Exception:
        logger.exception("push notification delivery failed")


_background: set[asyncio.Task] = set()


def notify_later(
    user_ids: list[uuid.UUID], title: str, body: str, data: dict | None = None
) -> None:
    """Fire-and-forget `notify` for code paths without BackgroundTasks (WebSockets)."""
    task = asyncio.create_task(notify(user_ids, title, body, data))
    _background.add(task)  # hold a reference so the task isn't garbage-collected
    task.add_done_callback(_background.discard)
