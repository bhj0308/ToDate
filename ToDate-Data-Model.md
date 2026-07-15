# ToDate Data Model

## Purpose

[ToDate-Architecture.md](ToDate-Architecture.md) lists the core entities needed for v1 but not their fields or relationships. This doc turns that list into a concrete relational schema so backend work can start. It follows the architecture doc's storage recommendation (relational core, with search/cache/object storage/analytics layered on top) and its key design principle: **verified facts stay separate from user-authored claims**, and **raw verification artifacts stay separate from the decisions derived from them** (see [ToDate-Compliance-Background-Checks.md](ToDate-Compliance-Background-Checks.md)).

Types below are illustrative (Postgres-flavored) — the actual DB choice isn't decided yet, but the shapes should translate directly.

## Conventions

- Every table has `id` (UUID, PK), `created_at`, `updated_at`.
- Foreign keys are named `<entity>_id`.
- Enums are written as `enum(...)`; implement as DB enum or constrained varchar depending on final stack.
- Money-adjacent fields are avoided at raw-value granularity where the product intentionally hides raw figures (see Verification section).

---

## Identity & Profile

### `users`
Canonical account record — separate from `profiles` because account/auth concerns (email, credentials, status) shouldn't mix with dating-facing profile content.

| Field | Type | Notes |
|---|---|---|
| id | uuid | PK |
| email | text | unique |
| phone | text | nullable, unique |
| status | enum(active, suspended, deleted, banned) | |
| account_state | enum(REGISTERED, PROFILE_INCOMPLETE, VERIFICATION_PENDING, VERIFICATION_IN_REVIEW, VERIFIED_AND_ELIGIBLE, PROFILE_ACTIVE) | mirrors onboarding state machine in Architecture doc |
| created_at, updated_at | timestamptz | |

### `profiles`
User-authored, dating-facing content. Explicitly does **not** contain verified facts.

| Field | Type | Notes |
|---|---|---|
| id | uuid | PK |
| user_id | uuid | FK -> users, unique (1:1) |
| display_name | text | |
| bio | text | |
| prompts | jsonb | array of {prompt, answer} |
| photos | jsonb | array of object-storage refs |
| interests | text[] | |
| dining_preferences | jsonb | consumed by Venue Curation |
| location | geography(point) | for discovery + venue matching |
| city_market | text | maps to GTM city rollout |
| created_at, updated_at | timestamptz | |

### `verified_attributes`
System-controlled facts, separate table from `profiles` by design — nothing here is user-editable.

| Field | Type | Notes |
|---|---|---|
| id | uuid | PK |
| user_id | uuid | FK -> users, unique (1:1) |
| identity_verified | boolean | |
| criminal_check_status | enum(passed, failed, pending, disputed) | |
| income_percentile_tier | enum(tier bands, e.g. 0-25/25-50/50-75/75-90/90+) | never raw dollar figure — matches README's "without displaying raw figures" |
| education_level | text | nullable, only if user opted to verify it |
| eligibility | enum(eligible, ineligible, exception_granted) | derived, drives profile_activated eligibility |
| updated_at | timestamptz | |

---

## Vetted domain (Verification)

### `verification_cases`
One per verification attempt/cycle. A user could have more than one over time (re-verification, disputes).

| Field | Type | Notes |
|---|---|---|
| id | uuid | PK |
| user_id | uuid | FK -> users |
| case_type | enum(identity, criminal, income, education) | |
| state | enum(...) | full state list per [ToDate-Compliance-Background-Checks.md](ToDate-Compliance-Background-Checks.md) state machine (VERIFICATION_PENDING → DISCLOSURE_PRESENTED → AUTHORIZATION_CAPTURED → CHECK_IN_PROGRESS → CHECK_COMPLETE → ... ) |
| vendor | text | which external vendor handled this case |
| vendor_reference_id | text | vendor's own case/report ID |
| disclosure_presented_at | timestamptz | nullable |
| authorization_captured_at | timestamptz | nullable — compliance-critical, must be non-null before check runs |
| submitted_at | timestamptz | |
| resolved_at | timestamptz | nullable |
| created_at, updated_at | timestamptz | |

### `verification_decisions`
The durable, consumable output of a case. Other domains read *this*, never raw artifacts.

| Field | Type | Notes |
|---|---|---|
| id | uuid | PK |
| verification_case_id | uuid | FK -> verification_cases |
| user_id | uuid | FK -> users, denormalized for read convenience |
| decision | enum(pass, fail, exception_granted) | |
| decided_by | enum(system, admin) | |
| decided_by_admin_id | uuid | nullable, FK -> admin users, required if decided_by = admin |
| reason_code | text | structured reason, not free text, for auditability |
| adverse_action_required | boolean | |
| pre_adverse_notice_sent_at | timestamptz | nullable |
| post_adverse_notice_sent_at | timestamptz | nullable |
| dispute_state | enum(none, disputed, under_reconsideration, resolved) | |
| created_at | timestamptz | |

### `verification_artifacts`
Raw vendor output — documents, report payloads. Deliberately **not** joined to anything outside the Vetted domain; other domains must never query this table.

| Field | Type | Notes |
|---|---|---|
| id | uuid | PK |
| verification_case_id | uuid | FK -> verification_cases |
| artifact_type | enum(report_document, id_scan, raw_payload) | |
| storage_ref | text | object storage pointer, not inline content |
| retention_expires_at | timestamptz | drives deletion jobs per compliance retention table |
| created_at | timestamptz | |

---

## Billing & Entitlements

### `subscriptions`

| Field | Type | Notes |
|---|---|---|
| id | uuid | PK |
| user_id | uuid | FK -> users |
| plan | enum(premium, premium_plus, elite) | maps to README pricing tiers |
| billing_cycle | enum(monthly, annual) | |
| status | enum(active, past_due, canceled, expired) | |
| activation_fee_paid_at | timestamptz | one-time $84.99 fee per README |
| current_period_start, current_period_end | timestamptz | |
| created_at, updated_at | timestamptz | |

### `entitlements`
Centralized, per the Architecture doc's principle that entitlements shouldn't be scattered — this table (or an equivalent config-driven feature table) is the single source of truth other domains check against.

| Field | Type | Notes |
|---|---|---|
| id | uuid | PK |
| plan | enum(premium, premium_plus, elite) | |
| feature_key | text | e.g. `advanced_income_filter`, `dedicated_ai_coach`, `concierge_date_planning` — see [ToDate-Entitlements-Matrix.md](ToDate-Entitlements-Matrix.md) for the full key list |
| enabled | boolean | |

---

## Structured domain (Match & Date Progression)

### `matches`

| Field | Type | Notes |
|---|---|---|
| id | uuid | PK |
| user_a_id, user_b_id | uuid | FK -> users, both directions |
| state | enum(MATCH_CREATED, CHAT_OPEN, DATE_PROMPT_PENDING, DATE_PROMPT_CAPTURED, EXTENDED_CHAT, SCHEDULE_READY, CLOSED) | per Architecture doc state machine |
| chat_window_started_at | timestamptz | |
| chat_window_expires_at | timestamptz | 3-5 days per README, extendable |
| closed_at | timestamptz | nullable |
| closed_reason | enum(no_response, mutual_no, timeout, one_no) | |
| created_at, updated_at | timestamptz | |

### `conversations`

| Field | Type | Notes |
|---|---|---|
| id | uuid | PK |
| match_id | uuid | FK -> matches, unique (1:1) |
| created_at, updated_at | timestamptz | |

### `messages`

| Field | Type | Notes |
|---|---|---|
| id | uuid | PK |
| conversation_id | uuid | FK -> conversations |
| sender_id | uuid | FK -> users |
| body | text | |
| sent_at | timestamptz | |
| read_at | timestamptz | nullable |

### `date_prompt_responses`

| Field | Type | Notes |
|---|---|---|
| id | uuid | PK |
| match_id | uuid | FK -> matches |
| user_id | uuid | FK -> users |
| response | enum(yes, no, maybe) | |
| responded_at | timestamptz | |

Unique constraint on `(match_id, user_id)` per prompt cycle — need a `prompt_cycle` counter/column if Maybe extensions trigger a second prompt round.

### `availability_windows`

| Field | Type | Notes |
|---|---|---|
| id | uuid | PK |
| match_id | uuid | FK -> matches |
| user_id | uuid | FK -> users |
| available_slots | jsonb | array of date/time ranges, 2-week collection window per README |
| submitted_at | timestamptz | |

### `date_plans`

| Field | Type | Notes |
|---|---|---|
| id | uuid | PK |
| match_id | uuid | FK -> matches, unique (1:1) |
| venue_recommendation_id | uuid | FK -> venue_recommendations, nullable until chosen |
| scheduled_at | timestamptz | nullable |
| status | enum(pending, confirmed, completed, canceled) | |
| outcome_reported_at | timestamptz | feeds Intelligent domain's outcome feedback loop |

### `venue_recommendations`

| Field | Type | Notes |
|---|---|---|
| id | uuid | PK |
| match_id | uuid | FK -> matches |
| venue_partner_ref | text | external partner/venue ID |
| name, address | text | |
| generated_at | timestamptz | |
| selected | boolean | |

---

## Intelligent domain (AI Coaching)

### `conversation_signals`
Raw per-message signal extraction — high volume, candidate for the analytics/feature store rather than the relational core long-term, but modeled relationally for v1 per the Architecture doc's staged approach.

| Field | Type | Notes |
|---|---|---|
| id | uuid | PK |
| message_id | uuid | FK -> messages |
| conversation_id | uuid | FK -> conversations, denormalized |
| reply_latency_seconds | integer | nullable, null for first message in a thread |
| sentiment_score | numeric | |
| linguistic_mirroring_score | numeric | |
| created_at | timestamptz | |

### `coaching_insights`

| Field | Type | Notes |
|---|---|---|
| id | uuid | PK |
| conversation_id | uuid | FK -> conversations |
| user_id | uuid | FK -> users, who the nudge is shown to |
| insight_type | enum(engagement_nudge, ghosting_risk_alert, milestone_badge, ...) | |
| payload | jsonb | nudge copy / badge metadata |
| shown_at | timestamptz | nullable |
| created_at | timestamptz | |

### `compatibility_scores`

| Field | Type | Notes |
|---|---|---|
| id | uuid | PK |
| match_id | uuid | FK -> matches |
| score | numeric | dynamic, recalculated per README |
| score_version | text | model/version that produced it, for reproducibility |
| calculated_at | timestamptz | |

---

## Admin & Moderation

### `moderation_cases`

| Field | Type | Notes |
|---|---|---|
| id | uuid | PK |
| subject_type | enum(user, message, profile) | |
| subject_id | uuid | polymorphic reference |
| reason | text | |
| status | enum(open, actioned, dismissed) | |
| assigned_admin_id | uuid | nullable |
| created_at, resolved_at | timestamptz | |

### `audit_events`
Append-only. Backs both general admin auditability and the compliance audit trail required in [ToDate-Compliance-Background-Checks.md](ToDate-Compliance-Background-Checks.md).

| Field | Type | Notes |
|---|---|---|
| id | uuid | PK |
| actor_type | enum(system, admin, user) | |
| actor_id | uuid | nullable for system-originated events |
| event_type | text | matches Architecture doc's domain event names where applicable (`verification_passed`, `date_confirmed`, etc.) |
| subject_type | text | |
| subject_id | uuid | |
| metadata | jsonb | |
| occurred_at | timestamptz | |

---

## Relationship summary

```
users 1───1 profiles
users 1───1 verified_attributes
users 1───N verification_cases 1───N verification_decisions
verification_cases 1───N verification_artifacts
users 1───N subscriptions
matches N───2 users (user_a_id, user_b_id)
matches 1───1 conversations 1───N messages 1───1 conversation_signals
matches 1───N date_prompt_responses
matches 1───N availability_windows
matches 1───1 date_plans ───1 venue_recommendations
matches 1───N compatibility_scores
conversations 1───N coaching_insights
```

## Open questions

1. Should `conversation_signals` and `compatibility_scores` live in the relational core at all, or go straight to the analytics/feature store the Architecture doc calls out? Relational is simpler for v1; revisit at scale.
2. Does `date_prompt_responses` need a `prompt_cycle` field now, or is a single Yes/No/Maybe per match sufficient for v1 (with Extended Chat just delaying `CLOSED`, not triggering a literal second prompt row)?
3. Photo/document storage refs assume object storage is chosen — no decision recorded yet on which provider.
