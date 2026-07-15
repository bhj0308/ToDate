# ToDate API Contract (v1 Draft)

## Purpose

[Architecture overview](overview.md) defines domain modules but no endpoints. This draft gives mobile and backend teams a shared surface to build against in parallel. Scope is v1 only — endpoints needed to support the flows in the README and Architecture doc, nothing speculative. Request/response bodies are omitted at this stage; this is a resource/endpoint map, not a full OpenAPI spec — write that once the data model in [Data model](data-model.md) is reviewed and stable.

All endpoints are behind the API layer's auth, session, rate limiting, and entitlement checks per the Architecture doc — not restated per-endpoint below unless an endpoint has a *specific* entitlement requirement beyond "logged in."

## Conventions

- Base path: `/v1`
- Auth: bearer token (mechanism TBD — not yet decided in Architecture doc)
- All mutating endpoints emit the corresponding domain event listed in the Architecture doc's event model where one exists.

---

## Identity & Profile

| Method | Path | Purpose |
|---|---|---|
| POST | `/users` | Register account (email/phone) |
| GET | `/users/me` | Current account + `account_state` |
| GET | `/profiles/me` | Own profile |
| PUT | `/profiles/me` | Update profile (bio, photos, prompts, interests, dining prefs) |
| GET | `/profiles/{userId}` | View another user's profile (requires match or discovery context — access rule TBD) |

## Vetted (Verification)

| Method | Path | Purpose |
|---|---|---|
| POST | `/verification-cases` | Start a verification case (`case_type`: identity/criminal/income/education) |
| POST | `/verification-cases/{id}/disclosure-ack` | Record disclosure presented + user acknowledgment |
| POST | `/verification-cases/{id}/authorize` | Record explicit authorization (compliance-critical, see [Background-check compliance](../compliance/background-checks.md)) |
| GET | `/verification-cases/{id}` | Case status |
| GET | `/verification-cases/{id}/decision` | Resulting `VerificationDecision` (never raw artifact) |
| POST | `/verification-cases/{id}/dispute` | File a dispute, moves case to `DISPUTED` |
| GET | `/users/me/verified-attributes` | Current verified facts (identity_verified, criminal_check_status, income_percentile_tier, eligibility) |

Admin-only, separate from member-facing surface:

| Method | Path | Purpose |
|---|---|---|
| GET | `/admin/verification-cases?state=` | Review queue |
| POST | `/admin/verification-cases/{id}/decision` | Manual decision override, requires `decided_by_admin_id` + reason_code |

## Billing & Entitlements

| Method | Path | Purpose |
|---|---|---|
| POST | `/subscriptions` | Create subscription (plan + billing_cycle), triggers activation fee if first-time |
| GET | `/subscriptions/me` | Current plan/status |
| PUT | `/subscriptions/me` | Change plan (upgrade/downgrade) |
| DELETE | `/subscriptions/me` | Cancel |
| GET | `/entitlements/me` | Resolved effective entitlements for current user (plan × status), per [Entitlements matrix](../product/entitlements-matrix.md) |

## Matchmaking

| Method | Path | Purpose |
|---|---|---|
| GET | `/discovery` | Candidate feed (filtered by verified attributes + entitlement-gated filters) |
| POST | `/matches` | Create a match (mutual like/action — exact matching trigger not defined in source docs, TBD) |
| GET | `/matches/{id}` | Match detail incl. current `state` |
| GET | `/matches` | List current user's matches |

## Structured (Date Progression + Conversation)

| Method | Path | Purpose |
|---|---|---|
| GET | `/matches/{id}/conversation` | Conversation + messages |
| POST | `/matches/{id}/messages` | Send message |
| GET | `/matches/{id}/date-prompt` | Current prompt state, if triggered |
| POST | `/matches/{id}/date-prompt/response` | Submit Yes/No/Maybe (private/simultaneous — server must not reveal counterpart's answer until both respond) |
| POST | `/matches/{id}/availability` | Submit 2-week availability window |
| GET | `/matches/{id}/venue-recommendations` | Curated restaurant suggestions once both sides confirm |
| POST | `/matches/{id}/date-plan` | Confirm a date plan (venue + time) |
| POST | `/matches/{id}/date-plan/outcome` | Report date outcome, feeds Intelligent domain feedback loop |

## Intelligent (AI Coaching)

| Method | Path | Purpose |
|---|---|---|
| GET | `/matches/{id}/coaching-insights` | Active nudges/insights for current user in this conversation — entitlement-gated by tier (basic vs. extended vs. dedicated coach per [Entitlements matrix](../product/entitlements-matrix.md)) |
| GET | `/matches/{id}/compatibility-score` | Current dynamic match score |

These are read-only from the client's perspective — score/insight generation happens server-side via the async enrichment pipeline (`message_sent -> signal extraction -> ... -> match score refresh`), not via client-triggered compute.

## Admin & Moderation

| Method | Path | Purpose |
|---|---|---|
| POST | `/admin/moderation-cases` | Open a case (report a user/message) |
| GET | `/admin/moderation-cases?status=` | Queue |
| POST | `/admin/moderation-cases/{id}/action` | Resolve (action or dismiss) |
| GET | `/admin/audit-events?subject_id=` | Audit trail lookup |
| POST | `/admin/beta-invites` | Invite-only beta controls (Phase 1 GTM) |

---

## Open questions

1. **Auth mechanism** — not decided anywhere in source docs (OAuth? magic link? phone OTP given dating-app norms?). Blocks writing real request schemas.
2. **Match creation trigger** — README/Architecture describe what happens *after* a match, not what action creates one (mutual swipe-like action assumed but not stated). Needs product definition before `/matches` POST semantics are final.
3. **Realtime transport for chat** — REST endpoints above assume request/response; actual chat likely needs WebSocket/SSE for delivery, not reflected here. Architecture doc flags Conversation as a likely early extraction target partly for this reason.
4. This is a resource map, not a schema. Once [Data model](data-model.md) is reviewed, follow up with a full OpenAPI spec (request/response bodies, error codes, pagination).
