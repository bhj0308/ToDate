# ToDate Architecture

## Overview

ToDate is best served by a modular, event-driven architecture built around the product's three core pillars: **Vetted**, **Structured**, and **Intelligent**.  The ideation deck defines the platform as a vetted, structured, AI-enhanced dating experience with mandatory verification, time-boxed conversation flows, and continuously improving behavioral intelligence, so the system design should align directly to those product responsibilities rather than a generic social app pattern. 

A strong v1 should favor a modular monolith with explicit domain boundaries and asynchronous event processing, with the option to extract services later as scale and team complexity increase. That approach keeps delivery practical while preserving clean seams for verification, chat, workflow orchestration, AI analysis, billing, and partner integrations. 

## Architectural principles

The product architecture should reflect the three user promises stated in the deck. **Vetted** requires hard gating before profile activation, **Structured** requires deterministic workflow orchestration for every match, and **Intelligent** requires continuous signal collection and downstream analysis across conversations and date outcomes. 

The following principles should guide implementation:

- Trust-critical decisions should be explicit and auditable because identity, criminal background, and income percentile verification are mandatory before profile access is granted. 
- Match progression should be modeled as a state machine because the date-progression flow is the primary product differentiator and includes defined chat windows, a simultaneous private prompt, Maybe extensions, and clean exit paths. 
- AI enrichment should run asynchronously where possible because reply analysis, ghosting-risk detection, compatibility mapping, and dynamic score recalculation can be decoupled from the low-latency user interaction path. 
- Entitlements should be centralized because Premium, Premium+, and Elite each unlock different capabilities, with Elite carrying the most advanced AI and concierge features. 

## System context

At a high level, the platform should consist of client applications, an edge/API layer, domain modules or services, asynchronous event infrastructure, operational tooling, and purpose-specific storage. This shape fits the product because the deck spans onboarding trust checks, structured messaging flows, AI coaching, smart date planning, recurring subscriptions, and partner revenue integrations. 

### Primary components

| Layer | Responsibility |
|---|---|
| Client apps | iOS, Android, and optional web/admin surfaces for members and operations |
| API layer | Authentication, session handling, rate limiting, request orchestration, entitlement checks |
| Domain services | Verification, profiles, matchmaking, chat, date progression, AI, venue curation, billing, notifications, moderation |
| Event bus | Publishes and consumes product events across workflows and analytics |
| Data stores | Relational data, search/indexing, cache, object storage, analytics/feature storage |
| Admin tooling | Invite-only beta controls, manual reviews, support, fraud and moderation operations |

## Domain architecture

The domain model should map directly to the deck's pillars so each major capability owns its own business logic and lifecycle.  This reduces coupling and makes future premium expansions easier, especially for Elite coaching, concierge features, and match optimization. 

### Vetted domain

The Vetted domain owns identity verification, criminal background checks, income percentile verification, education-related verified attributes, and profile activation decisions.  It should produce durable trust decisions that other parts of the system can consume without needing direct access to raw verification artifacts.

Core responsibilities:

- Identity verification
- Criminal record screening
- Income percentile verification
- Verified attribute publication
- Eligibility and activation decisions
- Verification review and exception handling

### Structured domain

The Structured domain owns the lifecycle from match creation to date scheduling. The deck defines a 3–5 day chat window, a simultaneous private "Go on a date?" prompt, a Maybe extension path of 2–3 days, and clean termination on No, so these behaviors should be centrally orchestrated rather than scattered across chat logic. 

Core responsibilities:

- Match lifecycle management
- Chat window timers
- Prompt orchestration and response capture
- Maybe extension rules
- Availability collection
- Date scheduling workflow
- Conversation closure rules

### Intelligent domain

The Intelligent domain owns all behavioral analysis and guidance features described in the deck, including reply pattern analysis, ghosting-risk indicators, compatibility signal mapping, conversation coaching, dynamic match scores, and the continuously learning match optimization engine. 

Core responsibilities:

- Conversation signal extraction
- Engagement and latency analytics
- Compatibility signal modeling
- AI nudges and coaching generation
- Dynamic match score calculation
- Recommendation model training inputs
- Outcome feedback loop from scheduled dates and later results

## Logical service map

For v1, these domains can begin as modules within a modular monolith. As load or organizational complexity grows, the most natural extraction boundaries are verification, chat, AI, and billing because each has distinct scalability and compliance characteristics.

| Service / Module | Purpose | Notes |
|---|---|---|
| Identity & Profile | Accounts, profiles, preferences, membership metadata | Canonical user record |
| Verification | Identity, criminal, income verification workflows | Hard gate before profile activation  |
| Matchmaking | Candidate generation, ranking, eligibility filters | Consumes verified attributes and behavioral signals  |
| Conversation | Messaging, read state, moderation hooks, retention policy | Emits events for AI and workflow timers |
| Date Progression | Structured chat windows, Yes/No/Maybe orchestration, scheduling state | Product differentiator  |
| AI Coaching | Reply analysis, ghosting-risk scoring, nudges, compatibility scoring | Premium feature expansion path  |
| Venue Curation | Restaurant suggestions, location and availability matching, booking hooks | Supports partnership revenue  |
| Billing & Entitlements | Activation fee, subscriptions, plan changes, annual discounts | Unlocks Premium+, Elite  |
| Notifications | Push, email, reminders, operational alerts | Driven heavily by workflow events |
| Admin & Moderation | Invite-only controls, manual review, support, fraud workflows | Needed for curated beta launch  |

## Data architecture

A relational core is the safest foundation because the platform relies on strong consistency for user identity, entitlement state, workflow transitions, moderation actions, and billing. Alongside that, the platform should add specialized stores for search, caching, object storage, and analytics so each workload is handled by the right persistence model.

### Recommended storage pattern

| Store type | Best use |
|---|---|
| Relational database | Users, profiles, subscriptions, matches, workflows, audit trails |
| Search/index store | Discovery, filters, verified attribute lookups, admin search |
| Cache | Session data, hot profile reads, ranking intermediates, rate limiting |
| Object storage | Photos, verification files, generated reports, moderation evidence |
| Analytics warehouse / feature store | Behavioral signals, model features, experiment analysis, revenue analytics |

### Core entities

The following entities form a useful v1 foundation:

- User
- Profile
- VerificationCase
- VerificationDecision
- Subscription
- Entitlement
- Match
- Conversation
- Message
- ConversationSignal
- DateProgressionState
- DatePromptResponse
- AvailabilityWindow
- VenueRecommendation
- DatePlan
- CoachingInsight
- CompatibilityScore
- ModerationCase
- AuditEvent

A key design choice is to keep verified facts separate from user-authored profile claims. Income percentile, identity-complete status, and trust eligibility should be system-controlled facts, while bios, prompts, interests, and lifestyle preferences remain user-managed.

## Event model

The platform's most important workflows are naturally event-driven. The deck repeatedly emphasizes transitions in user state, including profile activation, match creation, prompt triggering, mutual scheduling, and continuous optimization from communication behavior and outcomes, so event publication should be a first-class design concern. 

### Example domain events

- `verification_submitted`
- `verification_passed`
- `verification_failed`
- `profile_activated`
- `subscription_activated`
- `match_created`
- `chat_window_started`
- `message_sent`
- `ghosting_risk_updated`
- `date_prompt_triggered`
- `date_prompt_answered`
- `chat_window_extended`
- `date_confirmed`
- `venue_recommendations_generated`
- `date_scheduled`
- `conversation_closed`
- `match_outcome_recorded`

These events allow decoupled handling for notifications, analytics, AI enrichment, concierge operations, and future experimentation.

## Workflow design

### Onboarding and activation

The onboarding flow should enforce mandatory verification before profile activation because the deck makes trust non-optional.  A user should be able to create an account and begin verification, but should not enter discovery or matching until identity, criminal background, and income percentile checks are complete and approved. 

Suggested state flow:

```text
REGISTERED
  -> PROFILE_INCOMPLETE
  -> VERIFICATION_PENDING
  -> VERIFICATION_IN_REVIEW
  -> VERIFIED_AND_ELIGIBLE
  -> PROFILE_ACTIVE
```

### Match to date progression

The date progression workflow should be implemented as a deterministic state machine because it is central to the product's value proposition.  The app's promise is to move users from match to date instead of leaving them in endless chat, so timers, prompt logic, extensions, and closure need explicit state ownership. 

Suggested state flow:

```text
MATCH_CREATED
  -> CHAT_OPEN
  -> DATE_PROMPT_PENDING
  -> DATE_PROMPT_CAPTURED
    -> EXTENDED_CHAT
    -> SCHEDULE_READY
    -> CLOSED
```

Response handling logic:

- Yes + Yes -> schedule flow begins and mutual availability is collected. 
- Yes + Maybe or Maybe + Maybe -> chat extends 2–3 additional days for a final decision. 
- Any No -> conversation ends cleanly. 

### AI enrichment loop

Conversation activity should emit message and state events that are processed asynchronously by the intelligence pipeline. This lets the user-facing chat experience remain responsive while the platform continuously updates engagement indicators, compatibility insights, coaching suggestions, and ranking features described in the deck. 

Suggested enrichment flow:

```text
message_sent
  -> signal extraction
  -> latency and engagement scoring
  -> compatibility update
  -> coaching insight generation
  -> match score refresh
  -> ranking feature persistence
```

## API and integration boundaries

The external integration surface should remain narrow and policy-driven because the most sensitive workflows involve personal data, verification vendors, partner booking data, and billing. Third-party systems should integrate through dedicated adapters rather than leaking vendor-specific semantics into core domain logic.

### Key external integrations

| Integration type | Purpose |
|---|---|
| Identity verification vendor | Identity proofing and verification status |
| Background check vendor | Criminal screening results |
| Income verification vendor | Percentile or income eligibility validation |
| Payment processor | Activation fee, recurring subscriptions, annual billing |
| Push/email providers | Product reminders and lifecycle notifications |
| Venue/booking partners | Restaurant recommendations and attributed bookings |
| Analytics / observability tools | Funnel, reliability, model and workflow monitoring |

Adapter-based integration keeps the core product portable and makes vendor changes less disruptive.

## Security and privacy

Security should be treated as a product requirement, not an infrastructure afterthought, because ToDate handles identity verification, criminal screening outcomes, income-related trust signals, private conversations, and subscription billing.  The architecture should therefore segment sensitive data, minimize raw document exposure, and enforce audited privileged access.

Key controls:

- Encrypt all sensitive data in transit and at rest.
- Separate raw verification artifacts from application-facing trust decisions.
- Use least-privilege service access between domains.
- Enforce audited admin actions for support, moderation, and manual review.
- Define explicit retention rules for chat, verification evidence, and moderation artifacts.
- Centralize secrets management and key rotation.
- Capture compliance-ready audit events around verification and payment actions.

## Deployment approach

A staged deployment strategy is the most practical choice. The product's feature set is broad, but early traction will come from executing a small number of trust-heavy, workflow-heavy experiences extremely well, especially in an invite-only city-based rollout. 

### Recommended v1 approach

- Start with a modular monolith for core domains.
- Add an event bus from day one for workflow, notifications, and analytics.
- Isolate verification adapters, billing adapters, and AI processing workers early.
- Deploy admin tooling separately if operational access needs tighter control.
- Introduce service extraction only where scale, latency, or compliance justify it.

### Natural extraction order

1. Verification
2. Conversation / realtime messaging
3. AI Coaching and feature pipeline
4. Billing and entitlements
5. Venue curation and concierge operations

## Suggested technology shape

The ideation deck does not prescribe a technology stack, so the exact implementation can vary. A strong engineering choice would be a mobile-first client strategy, a TypeScript-based backend, a relational database, Redis-style caching, managed object storage, a message bus, and a warehouse for analytics and model features because those align well with the product's transactional workflows and enrichment pipelines.

## Architecture summary

The right architecture for ToDate is not a generic dating-app backend. It is a trust-gated, workflow-centric, intelligence-enhanced platform with three dominant domains: Vetted, Structured, and Intelligent.  A modular monolith with event-driven internals provides the best balance of delivery speed, product clarity, and future scalability for the ideated feature set and launch plan described in the deck. 
