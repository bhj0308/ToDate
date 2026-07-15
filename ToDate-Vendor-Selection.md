# ToDate Vendor Selection Framework

## Purpose

The Architecture doc calls for "adapter-based integration" for identity verification, background checks, income verification, payments, and venue/booking partners, so vendor changes don't leak into core domain logic. This doc is the **evaluation framework**, not a vendor decision — actual vendor pricing, terms, and capabilities need current research (this doc wasn't built from live vendor data) and a real procurement conversation before anything is picked.

## Why this can't just be "pick the popular one"

Two of these vendor categories carry compliance weight, not just feature weight (see [ToDate-Compliance-Background-Checks.md](ToDate-Compliance-Background-Checks.md)):

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

1. Legal counsel resolves the open questions in [ToDate-Compliance-Background-Checks.md](ToDate-Compliance-Background-Checks.md) — specifically whether income verification triggers FCRA, and what CRA liability model is preferred.
2. Engineering + product shortlist 2-3 vendors per category against the criteria table above.
3. Compliance-sensitive categories (criminal background, income) get a legal review of the shortlist before final selection, not just a technical/commercial one.
4. Selected vendors get wrapped in an adapter per the Architecture doc's integration boundary guidance, so a later vendor swap doesn't touch core domain logic.

## Status

No vendors are selected as of this writing. This document should be revisited once legal input is available and real vendor research (pricing, current terms, jurisdiction coverage) has been done — none of that research is included here.
