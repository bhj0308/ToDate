"""Feature catalog — the source of truth mapping plans to feature flags.

Encodes docs/product/entitlements-matrix.md. Kept as code (not a seeded DB
table) for v1 so it's version-controlled and reviewable in diffs; can be moved
to the `entitlements` table later without changing the resolver's interface.

Items marked with a matrix "open question" are annotated; do not treat those as
final product decisions.
"""

from app.common.enums import Plan

# feature_key -> set of plans that unlock it
FEATURE_MATRIX: dict[str, set[Plan]] = {
    # Universal — required for all accounts
    "background_check_gate": {Plan.PREMIUM, Plan.PREMIUM_PLUS, Plan.ELITE},
    "income_verification_gate": {Plan.PREMIUM, Plan.PREMIUM_PLUS, Plan.ELITE},
    "structured_date_progression": {Plan.PREMIUM, Plan.PREMIUM_PLUS, Plan.ELITE},
    "standard_chat": {Plan.PREMIUM, Plan.PREMIUM_PLUS, Plan.ELITE},
    "ai_basic_nudges": {Plan.PREMIUM, Plan.PREMIUM_PLUS, Plan.ELITE},
    # Assumed all-tier pending confirmation (matrix open question #2)
    "smart_date_curation": {Plan.PREMIUM, Plan.PREMIUM_PLUS, Plan.ELITE},
    # Premium+ and up
    "income_filter_advanced": {Plan.PREMIUM_PLUS, Plan.ELITE},
    "education_filter": {Plan.PREMIUM_PLUS, Plan.ELITE},
    "priority_matching_queue": {Plan.PREMIUM_PLUS, Plan.ELITE},
    "ai_extended_features": {Plan.PREMIUM_PLUS, Plan.ELITE},
    # Elite only
    "dedicated_ai_coach": {Plan.ELITE},
    "realtime_conversation_analysis": {Plan.ELITE},
    "personalized_match_insight_reports": {Plan.ELITE},
    "concierge_date_planning": {Plan.ELITE},
    # NOTE: `income_filter_basic` (matrix open question #1) is intentionally
    # omitted — undecided whether Premium gets any filter. Add here once
    # product confirms.
}

ALL_FEATURES: list[str] = sorted(FEATURE_MATRIX.keys())


def features_for_plan(plan: Plan) -> set[str]:
    return {key for key, plans in FEATURE_MATRIX.items() if plan in plans}
