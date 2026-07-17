import uuid

from sqlalchemy import Enum as SAEnum
from sqlalchemy import ForeignKey, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.common.base import GUID, Base, TimestampMixin, UUIDPrimaryKeyMixin
from app.common.enums import MatchState


class Match(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """A mutual connection between two users.

    user_a_id < user_b_id (enforced in service layer) so the pair has exactly
    one canonical row regardless of who initiated.
    """

    __tablename__ = "matches"
    __table_args__ = (UniqueConstraint("user_a_id", "user_b_id"),)

    user_a_id: Mapped[uuid.UUID] = mapped_column(
        GUID(), ForeignKey("users.id"), nullable=False
    )
    user_b_id: Mapped[uuid.UUID] = mapped_column(
        GUID(), ForeignKey("users.id"), nullable=False
    )
    state: Mapped[MatchState] = mapped_column(
        SAEnum(MatchState, name="match_state"),
        default=MatchState.CHAT_OPEN,
        nullable=False,
    )
