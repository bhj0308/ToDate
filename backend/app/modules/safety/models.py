import uuid

from sqlalchemy import ForeignKey, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.common.base import GUID, Base, TimestampMixin, UUIDPrimaryKeyMixin


class UserBlock(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """One member blocking another.

    Directional as recorded, symmetric in effect: neither person appears in the
    other's discovery, can match, or keeps an open conversation.
    """

    __tablename__ = "user_blocks"
    __table_args__ = (UniqueConstraint("blocker_id", "blocked_id"),)

    blocker_id: Mapped[uuid.UUID] = mapped_column(
        GUID(), ForeignKey("users.id"), nullable=False
    )
    blocked_id: Mapped[uuid.UUID] = mapped_column(
        GUID(), ForeignKey("users.id"), nullable=False
    )
