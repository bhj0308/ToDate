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
    entitlements/      plan→feature catalog + effective-entitlement resolver  ✅ working
    verification/      models + adapter interface  ⛔ blocked (returns 501)
migrations/            Alembic (initial migration = 0001_initial)
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
- **Not yet built:** Matchmaking, Conversation, Date Progression, and the
  Intelligent (AI) domain — next modules per the data model.

## Endpoints (v1)

| Method | Path | Notes |
|---|---|---|
| GET | `/health` | liveness |
| POST | `/v1/users` | register |
| POST | `/v1/auth/otp/start` | begin passwordless login |
| POST | `/v1/auth/otp/verify` | exchange OTP for JWT pair |
| GET | `/v1/users/me` | current account (auth) |
| GET/PUT | `/v1/profiles/me` | own profile (auth) |
| GET | `/v1/entitlements/catalog` | public plan→feature map |
| GET | `/v1/entitlements/me` | effective entitlements (auth) |
| POST | `/v1/verification-cases` | ⛔ 501 pending legal sign-off |
