import uuid

from sqlalchemy import ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column

from app.common.base import GUID, Base, TimestampMixin, UUIDPrimaryKeyMixin


class PushToken(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """An Expo push token for one device. A user can have several devices."""

    __tablename__ = "push_tokens"

    user_id: Mapped[uuid.UUID] = mapped_column(
        GUID(), ForeignKey("users.id"), nullable=False
    )
    # Unique across users: a device belongs to whoever signed in on it last.
    token: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    platform: Mapped[str | None] = mapped_column(String(16))
