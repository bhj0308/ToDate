# ToDate Vendor Selection Framework

## Purpose

The Architecture doc calls for "adapter-based integration" for identity verification, background checks, income verification, payments, and venue/booking partners, so vendor changes don't leak into core domain logic. This doc is the **evaluation framework**, not a vendor decision — actual vendor pricing, terms, and capabilities need current research (this doc wasn't built from live vendor data) and a real procurement conversation before anything is picked.

## Why this can't just be "pick the popular one"

Two of these vendor categories carry compliance weight, not just feature weight (see [Background-check compliance](../compliance/background-checks.md)):

- The **background check vendor** determines whether ToDate is directly liable as a Consumer Reporting Agency (CRA) or whether the vendor absorbs that role — this is a legal/liability decision disguised as a vendor choice.
- The **income verification** approach (vendor-compiled report vs. bank-data aggregator like a Plaid-style connection) may or may not trigger FCRA obligations depending on which model is chosen — the compliance doc flags this as unresolved.

So vendor selection for these two categories should happen *after* legal counsel answers the open questions in the compliance doc, not before.

## Evaluation criteria (apply to every vendor category)

| Criterion | Why it matters here |
|---|---|
| Compliance posture | Is the vendor itself a compliant CRA (for background/income)? Do they provide adverse-action-ready report formats and dispute-handling support, or does ToDate have to build that layer? |
| Data residency & retention controls | Must support the retention table to be defined in the compliance doc; matters more for international expansion (README's London/Dubai/Singapore phase). |
| Adapter fit | Can the vendor's API be wrapped cleanly behind ToDate's internal domain interface without vendor-specific semantics leaking into core logic (Architecture doc's stated goal)? |
| Turnaround time | Verification is a hard gate before profile activation — slow turnaround directly delays activation and hurts conversion in the invite-only beta. |
| Cost structure | Per-check pricing needs to be weighed against the $84.99 one-time activation fee (README: "Activation Fees — 18% of revenue... after partner check costs") — vendor cost has a direct margin impact on that revenue line. |
| Coverage / jurisdiction support | Must cover the launch markets in the GTM plan — starts North America-only, later needs London/Dubai/Singapore support. |

## Vendor categories to evaluate

### Identity verification
Vendors in this space typically handle ID document scanning, liveness/selfie matching, and sometimes phone/email verification. Evaluate for: false-reject rate (a bad experience here is the first thing a new user hits), and whether they bundle criminal-check capability or need to be paired with a separate vendor.

### Criminal background check
This is the compliance-sensitive one. Evaluate specifically for: whether they act as the CRA of record, whether they provide FCRA-compliant adverse-action tooling out of the box, jurisdiction coverage (criminal record availability and legal restrictions vary significantly by state), and dispute-handling SLA.

### Income verification
Two structurally different approaches to evaluate against each other, not just vendor-to-vendor within one approach:
1. **Bank-data aggregation** (user connects a bank account, vendor derives an income signal) — likely faster/cheaper, but raises its own consent/data-scope questions.
2. **Compiled income report** (vendor produces a report from external sources) — closer to a traditional consumer report, more likely to trigger FCRA-style obligations directly.

This choice should be made jointly with legal counsel, not by engineering/product alone, since it changes which compliance requirements apply.

### Payment processor
Needs to support: one-time activation fee, recurring monthly/annual subscriptions, plan upgrades/downgrades (proration), and (per GTM) locked "lifetime pricing" for founding beta members — confirm the processor's subscription model can represent a price that diverges from the current public price table per-customer.

### Venue/booking partners
Lower compliance risk, more of a business-development/data-quality evaluation: restaurant data coverage in launch cities, real-time availability data quality, and whether booking attribution (for the Partnership Revenue stream) is supported natively or needs custom tracking.

## Decision process

1. Legal counsel resolves the open questions in [Background-check compliance](../compliance/background-checks.md) — specifically whether income verification triggers FCRA, and what CRA liability model is preferred.
2. Engineering + product shortlist 2-3 vendors per category against the criteria table above.
3. Compliance-sensitive categories (criminal background, income) get a legal review of the shortlist before final selection, not just a technical/commercial one.
4. Selected vendors get wrapped in an adapter per the Architecture doc's integration boundary guidance, so a later vendor swap doesn't touch core domain logic.

## Vendor evaluations

### Turn (turn.ai) — criminal background check

**Source:** Turn sales email (Level 3 API terms) and *USA Screening Services Rate
Table 2026* (pricing effective March 2026). Evaluated 2026-09-30. **Status: not
signed. Do not sign the API Agreement until the blockers below are resolved.**

**What Turn offered**

| Item | Terms |
|---|---|
| Integration | **Level 3 — full white-label API.** ToDate writes and hosts the consent UI; Turn handles submission, adjudication and status via webhooks. Turn's hosted consent flows (Levels 1/2) use employment language and don't fit a dating platform. |
| Platform fee | **$500 flat for 60 days** of unlimited staging + production API access, *"reassessed at the end of that window"* — ongoing price unknown. |
| Basic package | **$19.95** — SSN trace, address history, national criminal, sex offender, global watchlist, FCRA disclosure tracking, pre-adverse and adverse action letters, candidate communications. |
| Add-ons | County criminal **$3/county** (contingent, current, 7-yr or 10-yr lookback) · Federal district **$10/district** · Statewide **$20** current / **$30** 7-yr · Continuous criminal monitoring **$2** (unit not stated) · plus pass-through court/DMV fees at cost. |
| Turnaround | ~1.5 h median for criminal; 2–5 days for full reports. |
| Compliance claims | FCRA workflows (adverse action, disputes), SOC 2 Type II, GDPR, CCPA. |
| Next steps (theirs) | Diligence form → API Agreement → demo sign-up link. |

Not relevant to ToDate: drug tests, MVR, FMCSA, healthcare sanctions, employment/education verification.

**Estimated cost per applicant:** basic $19.95 + 2–3 county searches ($6–9) + court
pass-through fees ≈ **$25–40**, before volume discounts. That leaves margin
inside the $84.99 activation fee (README), including if the fee goes through
Apple In-App Purchase at 15–30%.

**Where Turn fits**

- Adverse-action letters and disputes are **included** — the compliance doc
  assumed ToDate would build these.
- Turn acts as the consumer reporting agency, which answers the compliance
  doc's "is ToDate the CRA?" question in the lower-liability direction.
- Level 3 matches the planned architecture: our own consent screens, the vendor
  behind the `VerificationVendorAdapter` interface, status pushed by webhook
  into the `VerificationState` machine.
- A 2–5 day full report fits the curated, invite-only beta; it needs an
  "application under review" state in the app (not yet designed).

**Blockers and open questions — most serious first**

1. **Permissible purpose.** The product is *Employment Screening Services*, and
   Turn's own rep says their hosted consent assumes employment. The FCRA only
   permits these reports for specific purposes; dating isn't employment. The
   likely basis is the consumer's own written instructions — **counsel must
   confirm, and the API Agreement must name it.**
2. **No income verification.** Nothing in the rate table verifies income. A soft
   credit inquiry is *not* income verification, and using credit data to gate
   dating eligibility is ethically and legally fraught. The income pillar needs
   a separate vendor.
3. **No real identity proofing.** "Identity" here is an SSN trace — no photo ID or
   selfie/liveness match, so it doesn't prevent catfishing. It also means
   **ToDate collects Social Security numbers**: the most sensitive data the
   platform would hold, and a real sign-up deterrent for a dating app.
4. **US-only.** "USA Screening Services", built on SSNs. **Canadian applicants
   can't be screened.** Matters if any launch city is in Canada — the design
   mockups all use a 613 (Ottawa) number.
5. **Post-60-day pricing.** Get the ongoing platform fee in writing before signing.
6. **Continuous monitoring ($2).** Unit unstated (per person per month?), and
   ongoing monitoring needs its own consent language.
7. **Adjudication criteria are ToDate's decision.** Turn "handles adjudication",
   but which records disqualify someone from a dating platform is ToDate policy
   and needs counsel review and consistent, documented application.

**Recommendation:** filling in the diligence form is fine — it's Turn vetting
ToDate, and an honest answer ("consumer-initiated checks for a dating platform")
tests blocker 1 early. Hold the API Agreement until counsel signs off on 1 and
the pricing in 5 is in writing. Turn could cover the **criminal** check; identity
proofing and income verification still need other vendors.

### Certn — awaiting reply

Ask Certn the same seven questions so the quotes compare directly. Lead with
**Canada coverage** (Certn is Canadian-headquartered) and whether they offer
**identity proofing** and **income verification** — either would reduce the
number of vendors needed.

## Status

**No vendor selected.** Turn has been evaluated (above) and is a credible
option for the criminal check only, pending legal review. Certn has not replied.
Identity proofing and income verification have no candidate yet.
