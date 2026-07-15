# ADR-0002: Backend & Client Tech Stack

**Status:** Accepted (2026-07-15)
**Date:** 2026-07-15
**Related:** [ToDate-Architecture.md](ToDate-Architecture.md), [ToDate-Data-Model.md](ToDate-Data-Model.md), [ToDate-API-Contract.md](ToDate-API-Contract.md)

## Context

The Architecture doc suggests but doesn't decide a stack ("a strong choice would be a TypeScript-based backend, a relational database, Redis-style caching..."). We need an actual decision so the first commit has a shape. Constraints from the product docs:

- **Relational-consistency-heavy** — the data model is built on strong consistency for verification state, entitlements, billing, and the date-progression state machine. This is not a document-store-shaped product.
- **AI/behavioral analysis is a core pillar**, not a side feature — the Intelligent domain runs an async enrichment pipeline.
- **Modular monolith first** (Architecture doc), extracting Verification / Conversation / AI / Billing later.
- Client preference stated: **React Native**.

### What comparable dating apps run

| App | Frontend | Backend | Database | Why it's relevant to ToDate |
|---|---|---|---|---|
| **Hinge** | React Native | Python (Django) | PostgreSQL | **Closest analog** — serious-intent, matchmaking-precision, ML-driven. Relational core, not NoSQL. |
| Tinder | React Native | Node.js | MongoDB + Redis | Optimized for swipe *volume* — the opposite of ToDate's positioning; NoSQL fits their high-churn profile reads, not our consistency needs. |
| Bumble | Swift/Kotlin native | Node.js | DynamoDB + Redis | Also volume-optimized; uses Python/TensorFlow *separately* for the ML/personalization layer. |

The pattern worth noting: the volume-optimized apps (Tinder, Bumble) chose NoSQL and Node; the **precision/intent-optimized app closest to ToDate (Hinge) chose relational Postgres**, which matches our data model. Bumble's split — Node backend + separate Python ML layer — also validates isolating AI processing regardless of the primary language.

Sources: [getstream.io Tinder stack](https://getstream.io/blog/tinder-app-tech-stack/), [datingpro.com stack guide](https://www.datingpro.com/blog/choosing-a-technology-stack-for-your-dating-startup-backend-frontend-mobile), [jploft.com 2025 stack](https://www.jploft.com/blog/dating-app-tech-stack).

## Decision

| Layer | Choice | Rationale |
|---|---|---|
| **Mobile client** | React Native | Stated preference; matches Hinge; one codebase for iOS+Android fits a solo developer. |
| **Backend core** | **Python (FastAPI)** modular monolith | One runtime that covers *both* the transactional core and the AI pillar — no second language ever required. Async-native (fits the event-driven design), Pydantic gives strong typing, matches the Hinge model. See "The real tradeoff" below. |
| **AI enrichment** | **Python (same runtime)** | The Intelligent pillar is the product differentiator and its entire ecosystem is Python. Runs as async workers in the *same* language as the core — no polyglot seam to maintain. |
| **Backend framework** | FastAPI over Django | Async/event-driven fit is native in FastAPI; the modular-monolith-with-domain-boundaries shape suits its flexibility. Django's free admin panel (useful for the Admin & Moderation ops tooling) is the one real counterargument — noted, not decisive. |
| **ORM / migrations** | SQLAlchemy (or SQLModel) + Alembic | Standard Python relational tooling; Alembic migrations back the data model. |
| **API typing → client** | Generate TS client types from FastAPI's OpenAPI schema | Recovers the end-to-end typing that a TS backend would have given, without writing the backend in TS. |
| **Primary database** | PostgreSQL | Relational core per Architecture doc + data model; matches Hinge; strong consistency for verification/billing/state. |
| **Cache** | Redis | Sessions, hot profile reads, rate limiting, ranking intermediates (Architecture doc). |
| **Object storage** | Cloud provider blob store (S3-compatible) | Verification artifacts, photos — kept out of the relational DB per data model. |
| **Realtime chat transport** | WebSocket | Chat needs push delivery; the API contract's REST endpoints cover everything *except* live message delivery. |
| **Event bus** | Start with a lightweight broker (e.g. Redis streams / managed queue), not Kafka | Architecture doc wants an event bus "from day one" but v1 volume doesn't justify Kafka's operational weight — revisit at extraction time. |
| **Cloud** | AWS | Industry default across all three reference apps; deepest managed-service coverage for the pieces above. |

### The real tradeoff: why Python-core and not polyglot

Context that decided this: **solo senior developer, Python-comfortable, also fluent in TypeScript.** Given that, the "don't limit ourselves" instinct actually points *away* from a polyglot TS-core + Python-AI split:

- For **one person**, two runtimes / two dependency systems / two deploy pipelines is the *limiting* choice — it spreads a solo maintainer thin. The expansive choice is the single runtime that can do everything.
- Python is that runtime here, because the **Intelligent pillar is the product differentiator** and its whole ecosystem is Python. A TS core would eventually force either a second language or ML-in-TS — *that* is the real limit.
- The one thing TS-core would have won — shared types with the RN client — is recovered by generating TS client types from FastAPI's OpenAPI schema. No advantage lost.
- CLAUDE.md's "simplicity first" agrees: one language, one runtime, for one developer.

TypeScript-core remains a perfectly defensible choice in the abstract (it's what the Architecture doc suggested), but for *this* developer and *this* AI-centric product, Python-core is both simpler now and less limiting later.

## Consequences

- **Positive:** One language across core + AI + workers for a solo maintainer; relational core matches the doc everything else is built on; AI pillar is native, not bolted on; end-to-end typing preserved via generated OpenAPI client; matches the Hinge precedent.
- **Negative / watch:** FastAPI is less batteries-included than Django — you build more of the admin/ops surface yourself (relevant for the Admin & Moderation module during the invite-only beta). If that ops tooling becomes a time sink, reconsider Django-admin or a standalone admin tool then. WebSocket infra is new surface area not covered by the API contract's REST map and needs its own design pass.
- **Deferred decisions:** specific secrets-manager, managed-Postgres vs. self-hosted, specific queue product — infra-level, settled during environment setup, don't block application code.

## Remaining confirmations

1. Native (Swift/Kotlin) is explicitly *not* recommended despite Bumble using it — confirm there's no device-capability requirement that would force native over React Native.
2. Django-admin's free ops panel was weighed against FastAPI's async fit and FastAPI won — revisit only if the custom admin tooling proves more expensive than expected.
