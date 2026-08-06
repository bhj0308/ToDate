# ToDate

> *Crafted for Connection. Built for Commitment.*

ToDate is a premium, vetted dating platform designed for serious, high-intent individuals. Unlike mainstream apps optimized for volume and engagement metrics, ToDate is built around three core pillars — **Vetted**, **Structured**, and **Intelligent** — to move users from match to real-world date with clarity, safety, and purpose.

***

## The Problem

The $8B+ dating industry has largely failed users who are genuinely serious about finding a committed partner. Three systemic failures define the current landscape:

| Problem | Description |
|---|---|
| **Zero Verification** | No background checks or identity gatekeeping — anyone can join, undermining safety and trust. |
| **No Progression Structure** | Conversations stall indefinitely with no defined path from match to date. Ghosting is normalized. |
| **No Behavioral Intelligence** | Algorithms match on photos and stated preferences, not actual communication compatibility. |

***

## Product Pillars

ToDate's entire product surface is designed around three pillars that map directly to the problems above:

- **Vetted** — Every user passes mandatory background check and income percentile verification before gaining profile access. Trust is non-negotiable.
- **Structured** — A defined date-progression system replaces endless chats. Every match has a clear timeline and a built-in date-prompt trigger.
- **Intelligent** — Behavioral analysis and an AI communication coach personalize every interaction, improving match quality over time.

***

## Core Features

### 🔒 Background Check Gateway
Third-party verified identity, criminal record, and income validation. Required before any profile is activated.

### 🤖 AI Gamification & Coach
Real-time insights on reply cadence, engagement patterns, and compatibility signals — delivered as subtle in-app nudges. Includes competitive milestones, communication strength badges, and dynamic match depth indicators.

### 💼 Income-Tier Filtering
Premium filters allow members to refine by verified income percentile and education level without displaying raw figures.

### 📍 Smart Date Curation
Availability- and location-aware restaurant suggestions using premium venue data and both users' dining preferences, surfaced automatically when a date is confirmed.

### 💬 Structured Chat Progression
Time-boxed conversation windows with automated date-prompt triggers. Mutual availability collection and restaurant curation are built into the flow.

### 🧠 Match Optimization Engine
Behavioral data, communication patterns, and date outcomes feed a continuously learning recommendation model that improves with every interaction.

***

## How It Works — Date Progression

```
01 Match & Chat
   └─ Users matched on verified data + behavioral signals.
      Enter a structured chat window of 3–5 days.

02 Date Prompt Triggered
   └─ After 3–5 days, the app sends both users a "Go on a date?" card.
      Response options: Yes / No / Maybe. Simultaneous and private.

03 Mutual Yes → Schedule
   └─ App collects 2-week availability and surfaces curated restaurant
      suggestions near both users' locations.

04 Maybe → Extended Window
   └─ Yes + Maybe or Maybe + Maybe extends chat 2–3 days for a final decision.
      Any No ends the conversation cleanly.
```

***

## AI Coaching & Intelligence

The AI coach operates between every message — not just at the point of matching.

| Signal | What It Measures |
|---|---|
| **Reply Pattern Analysis** | Engagement peaks, response latency trends, early ghosting-risk signals |
| **Compatibility Signal Mapping** | Linguistic mirroring, shared value markers, communication style alignment |
| **Conversation Coaching** | Real-time nudges at key moments to deepen engagement and avoid drop-off |
| **Dynamic Match Score** | Compatibility scores that update as conversations progress — rewarding depth over first impressions |

> Gamification is intentionally restrained — think Duolingo streaks, not arcade points.

***

## Pricing

A one-time **Initiation Fee of $84.99** applies to all accounts and covers identity and background verification.

| Tier | Monthly | Annual | Key Features |
|---|---|---|---|
| **Premium** | Free | Free | Background check, income verification, structured date progression, standard chat, minimum AI features |
| **Premium+** | $24.99 | $299.88 | Everything in Premium + advanced income/education filters, priority matching queue, extended AI features |
| **Elite** | $149 | $999 | Everything in Premium+ + dedicated AI communication coach, real-time conversation analysis, personalized match insight reports, concierge date-planning assistance |

***

## Revenue Model

ToDate operates a **recurring-first** revenue model with four streams:

| Stream | Revenue Share | Description |
|---|---|---|
| Premium Subscriptions | 51% | Core recurring revenue engine |
| Elite Subscriptions | 24% | High-value, low-churn cohort |
| Activation Fees | 18% | One-time, high-margin after partner check costs |
| Partnership Revenue | 7% | Restaurant bookings, events, privacy-safe referrals |

***

## Competitive Landscape

ToDate outguns all four closest competitors on trust infrastructure, date structure, and AI intelligence:

| Platform | Price / Month | Background Check | Date Structure | AI Coaching |
|---|---|---|---|---|
| **ToDate (Elite)** | $149 | ✅ Criminal + income | ✅ Built-in progression | ✅ Full AI coach |
| The League | $299 – $999 | ❌ Career screening only | ❌ None | ❌ None |
| Hinge+ | $30 – $50 | ❌ No gate at all | ❌ None | ❌ None |
| Raya | $24.99 | ❌ No financial/criminal | ❌ None | ❌ None |
| MillionaireMatch | $70 – $500 | ❌ Identity only | ❌ None | ❌ None |

***

## Go-To-Market Strategy

### Phase 1 · Months 1–6 — Invite-Only Beta
- 500 founding members per city, personally curated — no open sign-up
- Founding member badge + lifetime pricing lock
- Luxury lifestyle press partnerships for launch media

### Phase 2 · Months 7–18 — Metro Expansion
- Open application in 8 cities across North America
- ToDate Events series launched in all markets
- Corporate benefit pilot programs activated
- PR push: success stories and match data insights

### Phase 3 · Year 2–3 — Scale & International
- 15+ North American metros fully operational
- Soft launch in London, Dubai, and Singapore
- Concierge matching tier fully staffed
- Series A / B funding milestones reached

***

## Brand Identity

ToDate's visual language borrows from **luxury goods, not lifestyle aspiration** — think Cartier, not Instagram influencer.

| Element | Value |
|---|---|
| **Primary Background** | Onyx |
| **Accent / CTA** | Champagne Gold |
| **Secondary Accent** | Deep Wine |
| **Light Surfaces / Cards** | Ivory |
| **Body Copy** | Warm Muted |
| **Motion Language** | Slow, weighted transitions |
| **Material Inspiration** | Dark leather, brushed gold hardware, heavy silk |

> Tone in all copy: confident and precise — not warm and fluffy.

***

## Status

> 🏗️ Past ideation — backend and a mobile app scaffold are in active development.

- **Backend** ([`backend/`](backend/README.md)) — Python/FastAPI modular monolith per [ADR-0002](docs/adr/0002-tech-stack.md). Identity/OTP auth, profiles, matchmaking (with income/education filtering), structured date-progression + chat, AI coaching, billing/entitlements (dev-stub payment token), and admin & moderation (invite-only beta gate, manual profile/verified-attributes activation, report/review queue, audit log) are built and tested. Verification is a deliberate stub pending legal sign-off.
- **Mobile app** ([`mobile/`](mobile/README.md)) — Expo/React Native/TypeScript client covering every built backend domain, with realtime WebSocket chat, photo upload (dev-stub storage), dev-stub card capture, and an admin screen. See its README for setup and remaining gaps.
- **Docs** ([`docs/`](docs/README.md)) — architecture, data model, API contract, compliance, and ADRs.

***

## Run It Locally

Two terminals — the backend, then the mobile app pointed at it.

**1. Backend**

```bash
cd backend
uv sync --extra dev
uv run uvicorn app.main:app --reload   # http://127.0.0.1:8000
```

**2. Mobile app** (new terminal)

```bash
cd mobile
npm install
cp .env.example .env                   # defaults to http://localhost:8000
npx expo start --ios                   # or --android
```

This opens the app in an iOS Simulator (needs Xcode) or Android emulator (needs Android
Studio); it also prints a QR code you can scan with the **Expo Go** app on a physical
phone on the same network — for that, set `EXPO_PUBLIC_API_URL` in `mobile/.env` to your
computer's LAN IP instead of `localhost`, and for the Android emulator use
`http://10.0.2.2:8000`.

You should land on the sign-in screen. Enter any email and tap **Send code** — since
there's no real SMS/email vendor wired up yet, the OTP is returned directly in the dev
response and pre-filled on the next screen. Verify it and you're in.

### Becoming an admin

There's no admin UI to grant admin access (no formal RBAC yet — see
[`docs/architecture/security.md`](docs/architecture/security.md)), so the first
admin is bootstrapped via config:

1. In `backend/.env`, set `BOOTSTRAP_ADMIN_EMAILS=you@example.com` (comma-separated
   for more than one).
2. Sign in with that exact email through the normal OTP flow above. **The flag is
   only set at registration** — if that email already has an account, either use a
   fresh email instead, or flip `is_admin` on the existing row directly in the DB
   (there's no re-check on login for existing accounts).
3. An **Admin** tab appears in the app: a pending-activation queue, a moderation
   queue (Action/Dismiss reports), and a beta-invite form.

Any signed-in user (admin or not) can **report a profile** — open a member's profile
and tap **Report** near the bottom.

**Discovery is empty until an admin activates someone.** Verification (the intended
path to a browsable profile) is a deliberate legal-blocked stub, so nobody ever
reaches `PROFILE_ACTIVE` on their own. As an admin, open the **Admin** tab and tap
**Activate** next to a member in "Pending activation" — they'll then show up in
other members' Discovery feed. If you're testing with two accounts and Discovery
looks empty, this is almost always why.

**Income/education discovery filters need verified attributes, which also route
through admin.** Same root cause: nothing sets `income_percentile_tier` or
`education_level` except a human. In the **Admin** tab's "Pending activation" row,
pick an income tier and/or type an education level before (or after) activating —
then a Premium+/Elite member can filter Discovery by them. Without this step the
filters are correctly gated but have nothing to match against.

### Notes for new contributors

- **Registration is open in local dev** — any email can sign up, no invite needed.
  The invite-only beta gate (`BetaInvite` — see backend README) only activates when
  `ENVIRONMENT=production`, so it won't get in your way locally.
- **Regenerate the mobile API client after any backend route/schema change** — see
  [`mobile/README.md`](mobile/README.md) for the command. Forgetting this is the
  most common source of "the field I just added isn't there" confusion.
- **Don't pass `CI=1` to `expo start`** during a real dev session — it disables
  Metro's file watcher. It's fine for one-shot non-interactive invocations only.
- If `npm install` in `mobile/` fails with an `ERESOLVE` peer-dependency error,
  that's expected — `mobile/.npmrc` already sets `legacy-peer-deps=true` to work
  around `openapi-typescript`'s TypeScript 5 peer constraint (Expo needs TS 6). No
  action needed, just don't remove that file.

See [`backend/README.md`](backend/README.md) and [`mobile/README.md`](mobile/README.md)
for what's built, what's stubbed, and known gaps.

***

*ToDate — Crafted for Connection. Built for Commitment.*