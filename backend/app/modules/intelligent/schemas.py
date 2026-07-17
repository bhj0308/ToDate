import uuid
from typing import Any

from pydantic import BaseModel


class InsightItem(BaseModel):
    type: str    # e.g. "compatibility", "engagement_balance", "reply_cadence", "message_depth"
    tier: str    # "basic" | "extended" | "dedicated"
    body: str    # the nudge text shown to the user


class CoachingInsightsOut(BaseModel):
    match_id: uuid.UUID
    insight_tier: str
    insights: list[InsightItem]


class CompatibilityScoreOut(BaseModel):
    match_id: uuid.UUID
    score: float                        # 0–100
    factors: dict[str, Any] | None     # populated for extended+ tier
    signals_summary: dict[str, Any] | None  # populated for dedicated tier only
