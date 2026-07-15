# ToDate Entitlements Matrix

## Purpose

The README's pricing table describes tiers in marketing language ("advanced income/education filters," "extended AI features"). This doc turns that into a literal feature-flag table the Billing & Entitlements module can enforce, backing the `entitlements` table in [ToDate-Data-Model.md](ToDate-Data-Model.md). Every row here is a candidate `feature_key`.

Some feature boundaries below are **inferred**, not stated outright in the README (marked with 🟡). Those need a product decision, not an engineering guess, before they're built.

## Tier feature flags

| feature_key | Premium | Premium+ | Elite | Source |
|---|---|---|---|---|
| `background_check_gate` | ✅ | ✅ | ✅ | README: required for all accounts |
| `income_verification_gate` | ✅ | ✅ | ✅ | README: required for all accounts |
| `structured_date_progression` | ✅ | ✅ | ✅ | README: core to all tiers |
| `standard_chat` | ✅ | ✅ | ✅ | README |
| `ai_basic_nudges` | ✅ (minimum) | ✅ (extended) | ✅ (full coach) | README: "minimum AI features" → "extended AI features" → "dedicated AI communication coach" |
| `income_filter_basic` | 🟡 not specified | ✅ | ✅ | README only says Premium+ adds "advanced income/education filters" — unclear if Premium has *any* income filter or none |
| `income_filter_advanced` | ❌ | ✅ | ✅ | README |
| `education_filter` | ❌ | ✅ | ✅ | README, bundled with income filter language |
| `priority_matching_queue` | ❌ | ✅ | ✅ | README |
| `dedicated_ai_coach` | ❌ | ❌ | ✅ | README |
| `realtime_conversation_analysis` | ❌ | ❌ | ✅ | README |
| `personalized_match_insight_reports` | ❌ | ❌ | ✅ | README |
| `concierge_date_planning` | ❌ | ❌ | ✅ | README |
| `smart_date_curation` | 🟡 assumed all tiers | ✅ | ✅ | README lists this as a core feature, not tier-gated — confirm Premium gets it too |

## Open product questions

1. **Does Premium get any income/education filtering, or none at all?** The README's tier table only lists the filter as a Premium+/Elite addition, but doesn't say Premium has zero filtering — could mean "basic filter included, advanced filter is the upsell." Needs a product call; affects `income_filter_basic` above.
2. **Is Smart Date Curation gated by tier, or available to everyone once a date is confirmed?** It's listed under "Core Features" in the README (not under a specific tier), which suggests all tiers, but Elite's "concierge date-planning assistance" implies a materially different/higher-touch version. Needs clarification on whether that's the same feature with a concierge layer on top, or a distinct feature.
3. **What exactly differs between "minimum," "extended," and "full" AI features across tiers?** The README names are directional, not a feature list. Suggest expanding `ai_basic_nudges` into discrete sub-features (e.g. `reply_pattern_analysis`, `ghosting_risk_alerts`, `dynamic_match_score`, `compatibility_signal_mapping`) and deciding per-tier availability for each, rather than one blanket flag.
4. **Grandfathering**: README's GTM section mentions "founding member badge + lifetime pricing lock" for Phase 1 beta members. That implies a `subscriptions` record needs to support a locked historical price distinct from the current plan price table — not yet reflected in the data model.

## Enforcement notes

- Entitlement checks should happen in the API layer (per Architecture doc's "API layer... entitlement checks" responsibility), not scattered in domain logic — every domain service should treat entitlement as a yes/no input it receives, not something it looks up itself.
- `entitlements` table in the data model is a static plan→feature map; a user's *effective* entitlement also depends on `subscriptions.status` (an expired/past_due subscription should collapse a user to no entitlements or a defined grace-period state — grace period policy not yet defined, another open question).
