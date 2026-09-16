# Deployment Roadmap

Where ToDate runs today, and what has to change before real users touch it. Stack decisions come from [ADR-0002](../adr/0002-tech-stack.md); the demo setup is described in [DEMO.md](../../DEMO.md).

## Stage 0 — Today: local + tunnel (where you are)

| | |
|---|---|
| **Runs on** | Your Mac (uvicorn), shared via a `cloudflared` quick tunnel |
| **Database** | SQLite file |
| **Good for** | Teammate demos, design feedback, showing the flow |
| **Ends when** | You need the link to work while your laptop is closed |

Limits: link dies with your machine, URL changes each restart, data resets, single process. Note `--protocol http2` in [`scripts/share-demo.sh`](../../backend/scripts/share-demo.sh) — the QUIC default half-registers on many networks and silently routes nowhere.

## Stage 1 — Hosted demo (the next step)

Goal: a **permanent URL** that survives your laptop closing, still demo-data only.

- **Platform:** Render (blueprint already written: [`render.yaml`](../../render.yaml)) — or Railway / Fly.io / Cloud Run, same [Dockerfile](../../backend/Dockerfile).
- **Database:** managed Postgres, smallest tier. Switch `DATABASE_URL` to `postgresql+asyncpg://…`; [`start.sh`](../../backend/start.sh) already runs `alembic upgrade head` automatically when it detects Postgres.
- **Effort:** an hour, mostly account setup.

**Already verified locally against real Postgres 14:**
- Alembic migrations apply cleanly (`0001_initial` → `ec68fcccadaa`) using a raw
  `postgresql://` URL exactly as a host supplies it — the app rewrites it to the
  async driver itself (`Settings._use_async_driver`).
- Full journey runs on Postgres with zero errors: OTP auth → profiles →
  discovery → match → messages → date prompt → `SCHEDULE_READY` → date plan.
- Date scheduling verified under a **UTC server** (`TZ=UTC`), matching Render.
- **The Docker image builds and boots** (`docker build -t todate ./backend`) —
  confirmed serving through a tunnel on port 8080.

**Still to confirm:**
1. **Set a real `JWT_SECRET`** — Render's `generateValue: true` handles it. The
   default is a known dev string; anyone could forge tokens with it.
2. Keep `DEMO_MODE=true` **only** while it's a demo. It auto-activates every
   signup and fakes verified attributes. Note `docker run` needs it passed
   explicitly (`-e DEMO_MODE=true`) — it defaults to off, and without it
   discovery is empty and the demo looks broken.

## Stage 2 — Private beta (first real users)

The jump from "demo" to "real people with real data," and the point where the compliance work becomes blocking.

**Must flip:**
- `ENVIRONMENT=production` — this turns on the invite-only gate **and stops `dev_code` being returned in the OTP response**. Leaving it unset would let anyone log in as anyone. Single most important switch.
  - *Test-guarded:* `test_production_never_returns_the_otp_code` and
    `test_production_registration_requires_invite` both fail if this regresses —
    verified by deliberately reintroducing the bug.
- `DEMO_MODE=false` — restores real curation and real verification gating.
  - *Test-guarded:* `test_demo_mode_off_does_not_auto_activate` fails if the gate
    regresses and unvetted accounts reach discovery.
- `CORS_ORIGINS` — pin to your actual domains instead of `*`.

**Must build (each already has a stub and an owner-decision behind it):**

| Stub today | Needs | Blocked on |
|---|---|---|
| OTP logged to console | SMS/email provider (Twilio, SES…) | vendor pick |
| Photos on local disk | S3 or equivalent — **container disks are ephemeral; uploads vanish on redeploy** | vendor pick |
| Payments accept `tok_dev_*` | Real processor (Stripe), tokenized only | vendor pick |
| Verification returns 501 | The whole FCRA flow | **legal sign-off** — see [background-checks.md](../compliance/background-checks.md) |
| Venues hardcoded | Venue partner API | partnerships |

**Already done (hardening that going public required):**
- **Rate limiting** on both OTP endpoints (`SlidingWindowLimiter`, per client
  address) — the Architecture doc lists rate limiting as an API-layer
  responsibility and it was entirely unimplemented. Unlimited guesses against a
  6-digit code is brute-forceable; unlimited sends becomes an SMS-cost/fraud
  vector the moment real delivery is wired in. Limits are deliberately generous
  (15/15min) because users behind one office NAT share an address.
  *Caveat:* counters are per-process, so multiple instances divide the effective
  limit — move to Redis alongside the WebSocket backplane (Stage 3).
- **`/health` verifies the database** and returns `503` when it can't reach it,
  so the host restarts a broken instance instead of routing traffic to it.

**Also needed:** Postgres backups, error tracking (Sentry), structured logs, a real domain + TLS, and a staging environment separate from prod.

> The **verification gate is the long pole.** It's not an engineering estimate — it's how fast counsel answers the open questions in the compliance doc, then vendor selection, then build. Start that conversation before you need it.

## Stage 3 — Public launch (Phase 1 GTM: 500 members/city)

- **Move off the modular monolith only where it hurts.** ADR-0002's extraction order stands: Verification → Conversation/WebSocket → AI workers → Billing. Do it when a specific thing hurts, not on a schedule.
- **WebSocket scaling is the first real constraint.** The current `ws_manager` holds connections in **process memory** — it works on one instance and silently breaks across two (users on different instances stop seeing each other's messages). Multi-instance needs a Redis pub/sub backplane. This is the first thing that breaks when you scale horizontally.
- **Redis** for cache/sessions/rate limiting (ADR-0002, not yet added).
- **RN mobile app** — the real client per ADR-0002; the web client stays a demo/admin surface.
- **Ops:** uptime monitoring, on-call basics, audit-log review, incident process (you're handling Restricted-tier data — see [security.md](security.md)).

## Recommended path

**Stage 1 now** (permanent demo link, an hour's work) → keep gathering teammate feedback → **start the legal conversation in parallel**, since it gates Stage 2 regardless of how fast the code goes.

Don't skip Stage 1 straight to Stage 2: a hosted demo teaches you the deploy pipeline while the stakes are still zero.

## Cost sketch

Free tiers cover Stage 1 (Render free tier sleeps when idle — fine for a demo, wrong for a beta). Stage 2 realistically runs ~$20–50/mo for app + Postgres, plus per-check verification vendor fees, which the $84.99 activation fee is meant to cover (see the revenue model in the [README](../../README.md)).
