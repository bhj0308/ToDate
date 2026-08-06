# ToDate Backend

Python/FastAPI modular monolith per [ADR-0002](../docs/adr/0002-tech-stack.md). Auth is passwordless OTP + JWT per [ADR-0001](../docs/adr/0001-authentication.md).

## Quickstart

```bash
uv sync --extra dev          # install deps
uv run pytest                # run the smoke test suite
uv run uvicorn app.main:app --reload   # http://127.0.0.1:8000  (docs at /docs)
```

The dev default DB is SQLite (no infra needed); on SQLite the app auto-creates
tables on startup. For Postgres, set `DATABASE_URL` (see `.env.example`) and run
migrations instead:

```bash
uv run alembic upgrade head
```

## Layout

```
app/
  config.py            settings (env-driven; dev defaults to SQLite)
  db.py                async SQLAlchemy engine/session
  deps.py              FastAPI deps (current-user from bearer token)
  main.py              app factory + router wiring + /health
  models.py            imports all ORM models (metadata registry for Alembic)
  common/              base mixins (portable UUID pk, timestamps), enums, JWT/OTP
  modules/
    identity/          users, profiles, verified-attributes, OTP login  ✅ working
    entitlements/      plan→feature catalog, effective-entitlement resolver, subscriptions  ✅ working
    verification/      models + adapter interface  ⛔ blocked (returns 501)
    matchmaking/       discovery feed, match creation/listing  ✅ working
    structured/        conversation + date-progression state machine, availability, venue recs (stub), date plans  ✅ working
    intelligent/       coaching insights + compatibility score, tiered by entitlement  ✅ working
    admin/             moderation cases, audit log, beta-invite gate (production-only)  ✅ working
migrations/            Alembic — 0001_initial + ec68fcccadaa (also catches up tables 0001_initial missed)
tests/                 end-to-end smoke tests
```

## Status & what's intentionally NOT built

- **Verification is a deliberate stub.** `POST /v1/verification-cases` returns
  `501`, and the vendor adapter raises `NotYetApprovedError`. The disclosure /
  authorization / adverse-action / dispute flows are compliance-critical and
  must not be built against the draft requirements — they wait on legal sign-off
  of [docs/compliance/background-checks.md](../docs/compliance/background-checks.md)
  and vendor selection. The models and route exist so the block is explicit.
- **OTP delivery is dev-stubbed** — the code is logged (and returned as
  `dev_code` outside production) instead of sent by SMS/email. Real delivery is
  a vendor-selection item.
- **Location** is stored as lat/lng columns for v1; PostGIS `geography(point)`
  is a later migration.
- **Venue recommendations are hardcoded stub data** — real implementation
  needs the venue partner API (vendor-selection item).
- **Photo storage is dev-stubbed to local disk** (`POST /v1/profiles/me/photos`,
  served at `/uploads/...`) — real implementation needs an object-storage
  vendor (S3 per ADR-0002). Fine for local dev; not durable/scalable storage.
- **Admin access has no formal RBAC** — a single `users.is_admin` flag, set via
  `BOOTSTRAP_ADMIN_EMAILS` (comma-separated env var) since there's no admin UI
  to grant the first admin. Matches the "small ops team" footprint the
  invite-only beta needs; see the open question in
  [docs/architecture/security.md](../docs/architecture/security.md).
- **Beta-invite gate is production-only** — `register_user` requires an
  unredeemed `BetaInvite` for the email when `ENVIRONMENT=production`; local
  dev stays open (any email registers) so the existing OTP demo flow keeps
  working unmodified.
- **Profile activation is a manual admin action, not verification.** `GET
  /v1/discovery` only returns `PROFILE_ACTIVE` users, and nothing else in the
  codebase ever sets that state — real activation is meant to run through
  Verification (blocked, see above). `POST /v1/admin/users/{id}/activate` is
  the substitute: a human curator reviews and activates directly, which
  actually fits "personally curated, invite-only" better than an automated
  gate would. Until an admin activates someone, discovery stays empty for
  everyone — that's expected, not a bug.
- **Income/education discovery filters are entitlement-gated but data-empty
  by default.** `GET /v1/discovery` accepts `min_income_tier` (at-or-above the
  given `IncomePercentileTier`) and `education_level` (exact match), 403s if
  the caller lacks `income_filter_advanced`/`education_filter` (Premium+/Elite
  only — see [entitlements-matrix.md](../docs/product/entitlements-matrix.md)).
  Same root cause as profile activation: `VerifiedAttributes.income_percentile_tier`/
  `education_level` are otherwise never set (Verification is blocked), so
  `POST /v1/admin/users/{id}/verified-attributes` is the manual substitute —
  without it, these filters have real gating but no real data to filter.
- **Payments are dev-stubbed with a fake token, not a real processor.**
  `POST /v1/subscriptions` requires `payment_token`, which must look like
  `tok_dev_*` (anything else → `402`) — a real integration would swap this for
  a real processor's actual token, never raw card data, keeping ToDate out of
  PCI scope either way. No money moves; it's a format check standing in for
  "a real processor verified this," same spirit as the OTP/photo-storage
  dev-stubs. Successful creation now also stamps `activation_fee_paid_at`
  (previously dead — nothing ever set it), though nothing yet tracks
  "has this account ever paid the one-time fee" across cancel/re-subscribe.

## Endpoints (v1)

| Method | Path | Notes |
|---|---|---|
| GET | `/health` | liveness |
| POST | `/v1/users` | register |
| POST | `/v1/auth/otp/start` | begin passwordless login |
| POST | `/v1/auth/otp/verify` | exchange OTP for JWT pair |
| GET | `/v1/users/me` | current account (auth) |
| GET/PUT | `/v1/profiles/me` | own profile (auth) |
| GET | `/v1/profiles/{user_id}` | another user's profile (auth) |
| GET | `/v1/users/me/verified-attributes` | verified facts (auth) |
| POST | `/v1/profiles/me/photos` | upload a photo (multipart), dev-stub local storage (auth) |
| GET | `/v1/entitlements/catalog` | public plan→feature map |
| GET | `/v1/entitlements/me` | effective entitlements (auth) |
| POST | `/v1/subscriptions` | create subscription; needs dev-stub `payment_token` (auth) |
| GET/PUT/DELETE | `/v1/subscriptions/me` | manage own subscription (auth) |
| POST | `/v1/verification-cases` | ⛔ 501 pending legal sign-off |
| GET | `/v1/discovery` | candidate feed; `min_income_tier`/`education_level` filters need Premium+ (auth) |
| POST | `/v1/matches` | create a match (auth) |
| GET | `/v1/matches` / `/v1/matches/{id}` | list / get matches (auth) |
| GET | `/v1/matches/{id}/conversation` | conversation + messages (auth) |
| POST | `/v1/matches/{id}/messages` | send message (auth) |
| WS | `/v1/matches/{id}/ws` | realtime message send/broadcast; auth via `?token=` query param (ADR-0002) |
| GET/POST | `/v1/matches/{id}/date-prompt` | date-prompt state / trigger (auth) |
| POST | `/v1/matches/{id}/date-prompt/response` | submit Yes/No/Maybe (auth) |
| POST | `/v1/matches/{id}/availability` | submit availability (auth) |
| GET | `/v1/matches/{id}/venue-recommendations` | curated venues, stub data (auth) |
| GET/POST | `/v1/matches/{id}/date-plan` | fetch (null if none yet) / confirm a date plan (auth) |
| POST | `/v1/matches/{id}/date-plan/outcome` | report date outcome (auth) |
| GET | `/v1/matches/{id}/coaching-insights` | AI nudges, entitlement-tiered (auth) |
| GET | `/v1/matches/{id}/compatibility-score` | dynamic match score (auth) |
| POST | `/v1/admin/moderation-cases` | report a user/message/profile (any authed member) |
| GET | `/v1/admin/moderation-cases?status=` | review queue (admin) |
| POST | `/v1/admin/moderation-cases/{id}/action` | resolve: actioned / dismissed (admin) |
| GET | `/v1/admin/audit-events?subject_id=` | audit trail lookup, most recent 50 (admin) |
| POST | `/v1/admin/beta-invites` | invite an email to the beta (admin) |
| GET | `/v1/admin/users?account_state=` | curation queue, default REGISTERED (admin) |
| POST | `/v1/admin/users/{id}/activate` | manually activate a profile → PROFILE_ACTIVE (admin) |
| POST | `/v1/admin/users/{id}/verified-attributes` | manually set income tier/education/etc. (admin) |
