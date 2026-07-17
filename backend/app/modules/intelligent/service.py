"""Intelligent domain: signal extraction, compatibility scoring, coaching insights.

v1 approach: all signals are derived from message metadata (count, length,
reply latency). No external ML model is called. The architecture calls for an
async enrichment pipeline; here signals are recomputed lazily on read so the
feature works without background infrastructure.
"""

import uuid
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.intelligent.models import ConversationSignal
from app.modules.intelligent.schemas import (
    CoachingInsightsOut,
    CompatibilityScoreOut,
    InsightItem,
)
from app.modules.matchmaking.models import Match
from app.modules.structured.models import Message


class IntelligentError(Exception):
    pass


# ---------------------------------------------------------------------------
# Tier resolution
# ---------------------------------------------------------------------------

def resolve_ai_tier(features: list[str]) -> str:
    """Map entitlement feature flags to an AI insight tier."""
    if "dedicated_ai_coach" in features:
        return "dedicated"
    if "ai_extended_features" in features:
        return "extended"
    return "basic"


# ---------------------------------------------------------------------------
# Signal computation
# ---------------------------------------------------------------------------

def _extract_raw(
    messages: list[Message], user_a_id: uuid.UUID, user_b_id: uuid.UUID
) -> dict:
    msgs_a = [m for m in messages if m.sender_id == user_a_id]
    msgs_b = [m for m in messages if m.sender_id == user_b_id]

    count_a, count_b = len(msgs_a), len(msgs_b)
    avg_len_a = sum(len(m.body) for m in msgs_a) / count_a if msgs_a else None
    avg_len_b = sum(len(m.body) for m in msgs_b) / count_b if msgs_b else None

    # Reply latency: time between alternating-sender consecutive messages.
    lats_a: list[float] = []  # A's reply time (how fast A responds to B)
    lats_b: list[float] = []  # B's reply time
    prev = None
    for m in sorted(messages, key=lambda x: x.created_at):
        if prev is not None and prev.sender_id != m.sender_id:
            secs = (m.created_at - prev.created_at).total_seconds()
            (lats_a if m.sender_id == user_a_id else lats_b).append(secs)
        prev = m

    last_at = max((m.created_at for m in messages), default=None)

    return {
        "message_count_a": count_a,
        "message_count_b": count_b,
        "avg_message_length_a": avg_len_a,
        "avg_message_length_b": avg_len_b,
        "avg_reply_latency_a_seconds": sum(lats_a) / len(lats_a) if lats_a else None,
        "avg_reply_latency_b_seconds": sum(lats_b) / len(lats_b) if lats_b else None,
        "last_message_at": last_at,
    }


def _compute_score(raw: dict) -> tuple[float, dict]:
    """Derive a 0–100 compatibility score from four equally-weighted signals."""
    score = 50.0
    factors: dict = {}

    count_a = raw["message_count_a"]
    count_b = raw["message_count_b"]
    total = count_a + count_b

    # 1. Engagement balance — how symmetric is participation? (0–25 pts)
    if total > 0:
        balance = min(count_a, count_b) / max(count_a, count_b, 1)
        bal_pts = balance * 25
        score += bal_pts - 12.5
        factors["engagement_balance"] = round(bal_pts, 1)

    # 2. Reply cadence — fast replies signal strong interest (0–25 pts)
    lats = [
        v for v in [
            raw["avg_reply_latency_a_seconds"],
            raw["avg_reply_latency_b_seconds"],
        ]
        if v is not None
    ]
    if lats:
        avg_lat = sum(lats) / len(lats)
        if avg_lat < 300:
            cad_pts = 25.0
        elif avg_lat < 1800:
            cad_pts = 18.0
        elif avg_lat < 7200:
            cad_pts = 10.0
        else:
            cad_pts = 2.0
        score += cad_pts - 12.5
        factors["reply_cadence"] = round(cad_pts, 1)

    # 3. Message depth — longer messages = more investment (0–25 pts)
    lens = [
        v for v in [
            raw["avg_message_length_a"],
            raw["avg_message_length_b"],
        ]
        if v is not None
    ]
    if lens:
        avg_len = sum(lens) / len(lens)
        depth_pts = min(avg_len / 8.0, 25.0)  # 200 chars → full 25 pts
        score += depth_pts - 12.5
        factors["message_depth"] = round(depth_pts, 1)

    # 4. Conversation volume — more messages = more time invested (0–25 pts)
    if total >= 20:
        vol_pts = 25.0
    elif total >= 10:
        vol_pts = 18.0
    elif total >= 5:
        vol_pts = 10.0
    elif total >= 1:
        vol_pts = 5.0
    else:
        vol_pts = 0.0
    score += vol_pts - 12.5
    factors["conversation_volume"] = round(vol_pts, 1)

    return round(max(0.0, min(100.0, score)), 1), factors


def _generate_insights(
    raw: dict, score: float, is_user_a: bool, tier: str
) -> list[InsightItem]:
    insights: list[InsightItem] = []

    count_me = raw["message_count_a"] if is_user_a else raw["message_count_b"]
    count_them = raw["message_count_b"] if is_user_a else raw["message_count_a"]
    lat_me = (
        raw["avg_reply_latency_a_seconds"]
        if is_user_a
        else raw["avg_reply_latency_b_seconds"]
    )
    len_me = (
        raw["avg_message_length_a"] if is_user_a else raw["avg_message_length_b"]
    )
    total = count_me + count_them

    # --- Basic tier: all plans ---
    if score >= 70:
        body = "Strong compatibility signals — this conversation has real momentum."
    elif score >= 45:
        body = "Solid connection developing — consistent engagement will strengthen it."
    else:
        body = "Early stages — open-ended questions can deepen the connection."
    insights.append(InsightItem(type="compatibility", tier="basic", body=body))

    if tier not in ("extended", "dedicated"):
        return insights

    # --- Extended tier: Premium+ ---
    if total > 0:
        if count_me > count_them * 2:
            insights.append(InsightItem(
                type="engagement_balance",
                tier="extended",
                body="You're driving the conversation. Try asking an open question and giving them space to expand.",
            ))
        elif count_them > count_me * 2:
            insights.append(InsightItem(
                type="engagement_balance",
                tier="extended",
                body="They're carrying the conversation. Show equal enthusiasm to create balance.",
            ))

    if lat_me is not None:
        if lat_me > 7200:
            insights.append(InsightItem(
                type="reply_cadence",
                tier="extended",
                body="Your response time is trending slow. Consistent replies signal genuine interest.",
            ))
        elif lat_me < 120:
            insights.append(InsightItem(
                type="reply_cadence",
                tier="extended",
                body="Your quick response rate is a strong engagement signal — keep the momentum.",
            ))

    if tier != "dedicated":
        return insights

    # --- Dedicated tier: Elite ---
    if len_me is not None:
        if len_me < 40:
            insights.append(InsightItem(
                type="message_depth",
                tier="dedicated",
                body=(
                    "Your messages are brief. Sharing a specific personal detail or story "
                    "significantly increases emotional connection at this stage."
                ),
            ))
        elif len_me > 180:
            insights.append(InsightItem(
                type="message_depth",
                tier="dedicated",
                body=(
                    "Your thoughtful, detailed responses are above average — "
                    "this signals high compatibility to the algorithm."
                ),
            ))

    if score >= 75 and total >= 8:
        insights.append(InsightItem(
            type="match_quality",
            tier="dedicated",
            body=(
                "This is a high-compatibility conversation. Your match score places "
                "you in the top 20% of interactions on the platform."
            ),
        ))

    return insights


# ---------------------------------------------------------------------------
# DB interaction
# ---------------------------------------------------------------------------

async def _get_match_for_participant(
    session: AsyncSession, match_id: uuid.UUID, user_id: uuid.UUID
) -> Match:
    match = await session.get(Match, match_id)
    if match is None:
        raise IntelligentError("match not found")
    if match.user_a_id != user_id and match.user_b_id != user_id:
        raise IntelligentError("not a participant in this match")
    return match


async def _refresh_signals(
    session: AsyncSession, match: Match
) -> ConversationSignal:
    messages = list(
        await session.scalars(
            select(Message)
            .where(Message.match_id == match.id)
            .order_by(Message.created_at.asc())
        )
    )

    raw = _extract_raw(messages, match.user_a_id, match.user_b_id)
    score, factors = _compute_score(raw)
    now = datetime.now(timezone.utc)

    signal = await session.scalar(
        select(ConversationSignal).where(ConversationSignal.match_id == match.id)
    )
    if signal is None:
        signal = ConversationSignal(
            match_id=match.id,
            user_a_id=match.user_a_id,
            user_b_id=match.user_b_id,
            computed_at=now,
        )
        session.add(signal)

    signal.message_count_a = raw["message_count_a"]
    signal.message_count_b = raw["message_count_b"]
    signal.avg_message_length_a = raw["avg_message_length_a"]
    signal.avg_message_length_b = raw["avg_message_length_b"]
    signal.avg_reply_latency_a_seconds = raw["avg_reply_latency_a_seconds"]
    signal.avg_reply_latency_b_seconds = raw["avg_reply_latency_b_seconds"]
    signal.last_message_at = raw["last_message_at"]
    signal.compatibility_score = score
    signal.score_factors = factors
    signal.computed_at = now

    await session.commit()
    await session.refresh(signal)
    return signal


# ---------------------------------------------------------------------------
# Public service functions
# ---------------------------------------------------------------------------

async def get_coaching_insights(
    session: AsyncSession,
    match_id: uuid.UUID,
    user_id: uuid.UUID,
    ai_tier: str,
) -> CoachingInsightsOut:
    match = await _get_match_for_participant(session, match_id, user_id)
    signal = await _refresh_signals(session, match)

    is_a = user_id == match.user_a_id
    raw = {
        "message_count_a": signal.message_count_a,
        "message_count_b": signal.message_count_b,
        "avg_message_length_a": signal.avg_message_length_a,
        "avg_message_length_b": signal.avg_message_length_b,
        "avg_reply_latency_a_seconds": signal.avg_reply_latency_a_seconds,
        "avg_reply_latency_b_seconds": signal.avg_reply_latency_b_seconds,
    }
    items = _generate_insights(raw, signal.compatibility_score, is_a, ai_tier)

    return CoachingInsightsOut(
        match_id=match_id, insight_tier=ai_tier, insights=items
    )


async def get_compatibility_score(
    session: AsyncSession,
    match_id: uuid.UUID,
    user_id: uuid.UUID,
    ai_tier: str,
) -> CompatibilityScoreOut:
    match = await _get_match_for_participant(session, match_id, user_id)
    signal = await _refresh_signals(session, match)

    factors = signal.score_factors if ai_tier in ("extended", "dedicated") else None

    signals_summary = None
    if ai_tier == "dedicated":
        is_a = user_id == match.user_a_id
        signals_summary = {
            "my_message_count": signal.message_count_a if is_a else signal.message_count_b,
            "their_message_count": signal.message_count_b if is_a else signal.message_count_a,
            "my_avg_reply_latency_seconds": (
                signal.avg_reply_latency_a_seconds if is_a
                else signal.avg_reply_latency_b_seconds
            ),
            "my_avg_message_length": (
                signal.avg_message_length_a if is_a else signal.avg_message_length_b
            ),
            "last_message_at": (
                signal.last_message_at.isoformat() if signal.last_message_at else None
            ),
        }

    return CompatibilityScoreOut(
        match_id=match_id,
        score=signal.compatibility_score,
        factors=factors,
        signals_summary=signals_summary,
    )
