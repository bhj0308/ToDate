import uuid
from datetime import datetime

from sqlalchemy import DateTime
from sqlalchemy import ForeignKey
from sqlalchemy import JSON
from sqlalchemy.orm import Mapped, mapped_column

from app.common.base import GUID, Base, TimestampMixin, UUIDPrimaryKeyMixin


class ConversationSignal(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """Derived metrics for a match conversation. Recomputed on each insight request.

    In production these would be maintained by an async enrichment pipeline
    (message_sent → signal extraction → score refresh). For v1 they are
    recomputed lazily on read so no background worker is required.
    """

    __tablename__ = "conversation_signals"

    match_id: Mapped[uuid.UUID] = mapped_column(
        GUID(), ForeignKey("matches.id"), unique=True, nullable=False
    )
    # Which user is A vs B mirrors the canonical match ordering.
    user_a_id: Mapped[uuid.UUID] = mapped_column(GUID(), nullable=False)
    user_b_id: Mapped[uuid.UUID] = mapped_column(GUID(), nullable=False)

    message_count_a: Mapped[int] = mapped_column(default=0, nullable=False)
    message_count_b: Mapped[int] = mapped_column(default=0, nullable=False)
    avg_message_length_a: Mapped[float | None]
    avg_message_length_b: Mapped[float | None]
    avg_reply_latency_a_seconds: Mapped[float | None]
    avg_reply_latency_b_seconds: Mapped[float | None]
    last_message_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True)
    )

    compatibility_score: Mapped[float] = mapped_column(default=0.0, nullable=False)
    score_factors: Mapped[dict | None] = mapped_column(JSON)
    computed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
