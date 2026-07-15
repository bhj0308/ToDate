# ToDate Security & Data Classification

## Purpose

[ToDate-Architecture.md](ToDate-Architecture.md) states security principles at a high level (encrypt in transit/at rest, least-privilege, audited admin access, retention rules, centralized secrets). This doc makes those concrete against the actual entities defined in [ToDate-Data-Model.md](ToDate-Data-Model.md), so engineering has a real classification table instead of a principle to interpret.

## Data classification table

| Data category | Classification | Entities | Handling requirement |
|---|---|---|---|
| Verification raw artifacts | **Restricted** (highest) | `verification_artifacts` | Object storage only, never in relational queries outside Vetted domain, access logged per-read, retention per compliance doc's retention table |
| Criminal/income verification decisions | **Restricted** | `verification_decisions`, `verified_attributes.criminal_check_status`, `verified_attributes.income_percentile_tier` | Encrypted at rest, least-privilege read (Vetted domain + entitlement-driven consumers only), no direct end-user export without going through the compliance-defined dispute/access process |
| Identity documents / ID scans | **Restricted** | `verification_artifacts` (artifact_type = id_scan) | Same as raw artifacts; additionally should never be included in any analytics export |
| Payment/billing data | **Restricted** | `subscriptions` (any raw payment method data) | Should not be stored directly at all if a PCI-scope-avoiding payment processor (tokenized) is used — this is the default assumption; if raw card data ever touches ToDate's own storage, that's a materially bigger compliance lift (PCI-DSS) and should be treated as a explicit decision, not a default |
| Private messages | **Sensitive** | `messages` | Encrypted at rest, access limited to conversation participants + moderation workflow (with audit log entry on any moderation access), retention policy needed (not yet defined — open question below) |
| Behavioral/AI signal data | **Sensitive** | `conversation_signals`, `compatibility_scores`, `coaching_insights` | Derived from private messages, inherits sensitivity; should be excluded from any cross-user analytics that could re-identify conversation content, even though it's "just scores" |
| Profile content | **Internal** | `profiles` | User-authored, already intended for display to matches; standard access controls, no special handling beyond normal auth |
| Location | **Sensitive** | `profiles.location` | Precise location tied to a person's real-time whereabouts; should be truncated/fuzzed for anything beyond immediate matching/venue-distance use (e.g. never expose raw lat/long to the other user, only distance/city) |
| Account/auth data | **Restricted** | `users` (email, phone, credentials) | Standard auth security practices, encrypted at rest, rate-limited access |
| Audit events | **Internal**, append-only | `audit_events` | Write-once, no update/delete path in normal operation; needed as evidence for the compliance audit trail |

## Access control principles (concrete version of Architecture doc's "least privilege")

- **Vetted domain data (Restricted tier) should not be directly queryable by Matchmaking, Conversation, or AI Coaching services.** Those domains consume only the derived `verified_attributes` fields (e.g. `eligibility`, `income_percentile_tier`), never `verification_artifacts` or case-level detail. This is already a data-model-level separation (see [ToDate-Data-Model.md](ToDate-Data-Model.md)); this doc makes it an access-control requirement, not just a schema convention.
- **Admin access to Restricted data requires per-access audit logging**, not just role-based gating — a role check alone doesn't produce the compliance-defensible trail the background-check doc requires for adverse-action and dispute handling.
- **Service-to-service access should be scoped per domain**, not via a shared superuser database credential — each domain module/service should hold credentials limited to its own tables plus explicitly exposed cross-domain read views (e.g. Matchmaking's read access to `verified_attributes` only).

## Retention (placeholder pending compliance + legal input)

Retention periods are **not yet defined** for most categories — this is intentionally left incomplete rather than guessed, since:
- Verification artifact retention depends on legal counsel's answers in [ToDate-Compliance-Background-Checks.md](ToDate-Compliance-Background-Checks.md).
- Message retention has no stated product requirement yet (moderation needs some window; there's no stated user-facing message-deletion promise in the README to design against).
- Account deletion flows need to reconcile "user wants to delete account" against legal-hold requirements on compliance-relevant records (again, per the compliance doc).

Recommend: build the retention *mechanism* (per-record `retention_expires_at` fields, deletion jobs, legal-hold override flag) now, since it's cheap to build generically, but leave actual retention *durations* as configuration to be set once legal/product answers land — don't hardcode a guessed number into application logic.

## Secrets & encryption

- Centralize secrets management (Architecture doc already states this) — specific tool not decided, tag as an infra decision alongside the "Suggested technology shape" section of the Architecture doc.
- Standard practice for a Restricted/Sensitive-heavy system: encrypt at rest at the storage layer (DB-level or disk-level encryption) as a baseline, with field-level encryption considered specifically for `verification_artifacts` references and payment tokens given their classification above — field-level encryption for every table is likely overkill for v1 and should be scoped to Restricted-tier data only.

## Open questions

1. What message retention period, if any, does product want to commit to?
2. Is field-level (as opposed to storage-level) encryption required for any category beyond verification artifacts and payment data, or is storage-level encryption sufficient for v1?
3. Who has legitimate admin access to Restricted-tier verification data day one — is there a defined reviewer role, or does this fall to a small operations team without formal RBAC yet? (Relevant given the invite-only beta's small initial ops footprint per the GTM plan.)
