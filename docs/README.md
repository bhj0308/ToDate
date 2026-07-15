# ToDate Documentation

Planning and design docs for the ToDate platform. Structure follows two well-known conventions:

- **Architecture Decision Records** live in [`adr/`](adr/) using [Michael Nygard's ADR convention](https://cognitect.com/blog/2011/11/15/documenting-architecture-decisions) — one immutable, numbered `NNNN-title.md` per decision, each with Context / Decision / Consequences. New decisions get the next number; superseded ones are marked, not deleted.
- The rest is grouped by concern (architecture / compliance / product / vendors), in the spirit of keeping the **system design** ([arc42](https://arc42.org/)-style) separate from **decisions**, **compliance**, and **product** specs.

## Map

| Folder | Contents |
|---|---|
| [`architecture/`](architecture/) | System design: [overview](architecture/overview.md), [data model](architecture/data-model.md), [API contract](architecture/api-contract.md), [security & data classification](architecture/security.md) |
| [`adr/`](adr/) | Decisions: [0001 Authentication](adr/0001-authentication.md), [0002 Tech Stack](adr/0002-tech-stack.md) |
| [`compliance/`](compliance/) | [Background-check / verification compliance requirements](compliance/background-checks.md) — ⚠️ needs legal sign-off before the Verification module is built |
| [`product/`](product/) | [Entitlements matrix](product/entitlements-matrix.md) |
| [`vendors/`](vendors/) | [Vendor selection framework](vendors/vendor-selection.md) |

The product pitch/overview remains at the repo root in [`../README.md`](../README.md).

## Status

Accepted stack (ADR-0002): React Native + Python/FastAPI + PostgreSQL + Redis + WebSocket + AWS. Accepted auth (ADR-0001): passwordless phone OTP + email, JWT sessions. Backend implementation started under [`../backend/`](../backend/). Verification logic is stubbed pending legal review of the compliance doc.
