# ToDate Background Check & Verification Compliance Requirements

> ⚠️ **Not legal advice.** This document translates commonly-known regulatory patterns (U.S. FCRA, state-level background check laws) into engineering and product requirements so the Vetted domain can be built without an obvious compliance gap. It is a starting point for review, not a substitute for it. **Every requirement below must be validated by actual legal counsel — ideally counsel with FCRA/consumer-reporting experience — before any background check ships to real users.** Requirements will also vary by state and by country if ToDate expands internationally (see Open Questions).

## Why this exists

The [ToDate-Architecture.md](ToDate-Architecture.md) Vetted domain treats identity, criminal background, and income verification as a hard gate before profile activation. That's a product strength, but running criminal background checks and income screening on consumers triggers specific legal obligations in the U.S. under the **Fair Credit Reporting Act (FCRA)** and various state laws. Getting this wrong isn't a bug — it's exposure to statutory damages and regulatory action. This doc exists so those obligations are designed into the system from day one instead of retrofitted after a legal review finds gaps.

## Regulatory landscape (what counsel needs to confirm, not what to assume)

- **FCRA applies when a third party ("consumer reporting agency," e.g. a background check vendor) compiles a report used to make a decision about a consumer.** Criminal background checks used to gate ToDate access very likely qualify. Income verification may or may not, depending on how it's sourced (vendor-compiled report vs. user-provided/Plaid-style bank data) — this needs a legal call before design.
- **State law varies significantly** on what can be reported/used: lookback windows (e.g. 7-year limits in some states), restrictions on arrest-vs-conviction data, "ban the box"-style limits, and outright restrictions on using criminal history for certain purposes in a few states. A dating app is not employment or tenancy screening, so some employment-specific carve-outs won't apply — but this needs explicit confirmation, not assumption.
- **Income data** carries its own sensitivity even outside FCRA — if sourced via a vendor like Plaid, that vendor's own consumer consent and data-use terms apply on top of ToDate's.
- **International expansion** (README lists London, Dubai, Singapore in Phase 3) means GDPR-style consent/purpose-limitation rules and potentially different or nonexistent background-check regimes. Do not assume the U.S. model ports as-is.

## Required system behaviors

These are the concrete things the Verification module must implement, assuming standard FCRA-style obligations apply (to be confirmed):

### 1. Disclosure & authorization (before any check runs)
- A **standalone disclosure** — not bundled with other terms — telling the user a background check will be performed, in clear and conspicuous form.
- **Explicit, separate authorization** capture (checkbox/signature-equivalent) before the check is initiated, timestamped and stored.
- System must not initiate a check for a user record where disclosure/authorization capture failed or is missing — this should be a hard gate in code, not a process convention.

### 2. Adverse action process (if a check leads to denial or restriction)
- **Pre-adverse-action notice**: before final denial, the user must be given the report (or a summary), told they may dispute it, and given a reasonable waiting period before the decision is finalized.
- **Post-adverse-action notice**: if the denial stands, a final notice including the reporting vendor's contact info, a statement of the user's right to dispute, and right to a free copy of the report within a defined window.
- Both notices need to exist as real, trackable states in the Verification state machine (see below), not just a customer-support email template.

### 3. Dispute & reconsideration workflow
- Users must have a defined path to dispute inaccurate report contents, both with ToDate and with the reporting vendor.
- The Verification domain needs a `DISPUTED` / `UNDER_RECONSIDERATION` state that pauses the adverse-action clock and routes to manual review.
- SLA for responding to disputes should be defined (legal will drive the actual number; don't hardcode a guess).

### 4. Data separation and minimization
- Raw verification artifacts (report documents, criminal record details, income figures) must be stored separately from the **decision** derived from them, consistent with [ToDate-Architecture.md](ToDate-Architecture.md)'s existing principle that "verified facts" (e.g. `identity_complete`, `income_percentile_tier`) are system-controlled facts other domains consume — raw artifacts should never be queryable by Matchmaking, Conversation, or AI Coaching.
- Only the minimum derived fact needed downstream should be exposed (e.g. an income *percentile tier*, not a dollar figure, matching the README's stated feature of filtering "without displaying raw figures").

### 5. Retention & deletion
- Define explicit retention periods for: raw report artifacts, authorization records, dispute correspondence, and adverse-action notices. FCRA-adjacent obligations generally push toward *keeping* authorization/adverse-action records for defined periods (to prove compliance) while *minimizing* retention of raw report contents — these can be in tension and need a real retention table, not a single blanket policy.
- Deletion/account-closure flows must account for legal hold requirements — a user requesting account deletion doesn't necessarily mean immediate deletion of compliance-relevant records.

### 6. Audit logging
- Every state transition in the verification lifecycle (submitted → in review → passed/failed → disputed → resolved) must emit an `AuditEvent` with actor, timestamp, and reason — this aligns with the Architecture doc's existing `AuditEvent` entity and "audited privileged access" principle.
- Any manual override by an admin/reviewer must be logged with the reviewer identity and justification — this is what makes an exception process defensible later.

## Suggested state machine additions

The Architecture doc's onboarding flow is:

```
REGISTERED -> PROFILE_INCOMPLETE -> VERIFICATION_PENDING -> VERIFICATION_IN_REVIEW -> VERIFIED_AND_ELIGIBLE -> PROFILE_ACTIVE
```

Compliance requires more granularity inside `VERIFICATION_IN_REVIEW` and a path off the happy path:

```
VERIFICATION_PENDING
  -> DISCLOSURE_PRESENTED
  -> AUTHORIZATION_CAPTURED
  -> CHECK_IN_PROGRESS
  -> CHECK_COMPLETE
    -> VERIFIED_AND_ELIGIBLE                 (pass)
    -> PRE_ADVERSE_ACTION_NOTICE_SENT         (fail path)
       -> DISPUTED -> UNDER_RECONSIDERATION -> (back to CHECK_COMPLETE)
       -> WAITING_PERIOD_ELAPSED
          -> POST_ADVERSE_ACTION_NOTICE_SENT -> VERIFICATION_FAILED
```

Each of these should be a real, persisted state (supporting the `VerificationCase` / `VerificationDecision` entities already in the data model) so the compliance timeline is provable, not inferred from logs.

## Vendor implications

Whatever background check / identity / income verification vendors are selected (see the separate vendor selection doc, still to be written), they need to be evaluated on:
- Whether they are themselves a compliant Consumer Reporting Agency (CRA) under FCRA, or whether ToDate becomes the CRA by compiling the report itself (very different liability posture).
- Whether they provide adverse-action-ready report formats and dispute handling support, or whether ToDate has to build that layer.
- Data residency and retention controls matching the requirements above.

## Open questions for legal counsel

1. Does income verification (via bank-data vendors like Plaid, vs. a compiled "income report") trigger FCRA the same way criminal checks do?
2. What retention periods are required/recommended for each artifact type?
3. Which states (if any) restrict use of criminal history for a non-employment, non-tenancy consumer product like a dating app?
4. What is required for international markets (London, Dubai, Singapore) where FCRA doesn't apply — is there an equivalent regime, or none?
5. Does ToDate need to register/act as a CRA itself, or does vendor selection avoid that entirely?
6. What's the required/acceptable adverse-action waiting period in practice?

## Status

This document defines engineering requirements *pending legal validation*. Treat every numbered requirement above as a placeholder for "what counsel confirms," not a final spec. Do not build the adverse-action or disclosure flows against this doc alone without a legal sign-off pass.
