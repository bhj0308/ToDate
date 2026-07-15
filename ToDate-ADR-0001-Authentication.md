# ADR-0001: Authentication Mechanism

**Status:** Proposed (needs sign-off before first commit)
**Date:** 2026-07-15
**Related:** [ToDate-Architecture.md](ToDate-Architecture.md), [ToDate-API-Contract.md](ToDate-API-Contract.md), [ToDate-Data-Model.md](ToDate-Data-Model.md), [ToDate-Security-Data-Classification.md](ToDate-Security-Data-Classification.md)

## Context

The API contract flags auth as undecided, and it blocks real request schemas and every "who can call this" check. The choice is shaped by three ToDate-specific constraints:

- **Vetted pillar** — ToDate ties accounts to *real, verified identity* (identity + criminal + income checks). The auth identifier should anchor to something real, not a throwaway.
- **Dating-app norms** — Tinder, Bumble, and Hinge all use **phone-number-based signup** as the primary path. Phone number is a light first-layer identity signal and the category-standard UX.
- **Prohibited-action boundary** — ToDate must never itself store passwords or act as a password-authenticator (per operating constraints). A passwordless model isn't just convenient here, it sidesteps a whole class of credential-handling risk.

## Decision

**Phone OTP as the primary authentication method, with email as a secondary/recovery channel, and token-based sessions. No passwords.**

| Element | Choice | Rationale |
|---|---|---|
| Primary identifier | Phone number | Dating-app standard; light real-identity anchor supporting the Vetted pillar; maps to `users.phone` in the data model. |
| Primary auth | OTP (one-time code via SMS) | Passwordless — no password ever stored or handled by ToDate. Category-standard UX. |
| Secondary channel | Email (also OTP / magic link) | Recovery + notification address; maps to `users.email`. |
| Session tokens | Short-lived JWT access token + longer-lived refresh token | Standard for RN clients; refresh token rotation on use. |
| Social login (Apple/Google) | **Optional, deferred** | Common in the category but *not* v1-critical, and pure social login weakens the real-identity anchor ToDate depends on. If added, treat as a linked identity on top of phone, not a replacement. |

### Why not passwords / why not password-first

- Operating constraints prohibit ToDate from acting as a password authenticator or storing credentials — passwordless OTP avoids this entirely.
- Passwords are the weakest link for a product holding Restricted-tier data (verification artifacts, income tier); not having them removes credential-stuffing and breach-of-password-hash risk outright.

### Relationship to identity verification

Auth (phone OTP) is a *lightweight* gate — it proves control of a phone number, nothing more. It is **not** the same as the Vetted domain's identity verification (`verification_cases` of `case_type = identity`), which is the heavyweight real-identity proof. The `users.account_state` machine already models this: a user is authenticated (`REGISTERED`) long before they're verified (`VERIFIED_AND_ELIGIBLE`). Don't conflate the two — auth lets you *into the app*; verification lets you *into discovery*.

## Consequences

- **Positive:** No password storage (compliance + security win, aligns with prohibited-action boundary); matches category UX; phone anchor supports Vetted positioning; clean separation between auth and identity-verification.
- **Negative / watch:**
  - SMS OTP has real costs and delivery/fraud considerations (SIM-swap, OTP interception) — for a premium product holding sensitive data, consider whether step-up auth (re-verify on sensitive actions like viewing verification status or changing billing) is needed. Flagged, not decided here.
  - Phone-number-primary means account recovery on lost number needs a defined flow (email fallback covers part of this) — design during implementation.
  - International expansion (README Phase 3: London/Dubai/Singapore) means SMS deliverability and phone-format handling across regions — not a v1 blocker but on the radar.
- **Data model impact:** none beyond what exists — `users.email` and `users.phone` are already present. No `password_hash` column, by design.

## Open questions for sign-off

1. **SIM-swap / step-up auth** — do sensitive actions (billing changes, viewing verification decisions) require re-authentication beyond the session token? Recommend yes for billing + verification surfaces given the data classification, but it's a product/security call.
2. **Social login in v1 or not** — recommend deferring, but if the beta's founding-member UX wants one-tap Apple sign-in, it can be added as a *linked* identity. Confirm.
3. **SMS provider** — ties into the vendor selection framework ([ToDate-Vendor-Selection.md](ToDate-Vendor-Selection.md)); the push/email/SMS provider row there should cover OTP delivery.
