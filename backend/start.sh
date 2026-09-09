#!/usr/bin/env bash
# Production/demo start: run migrations on Postgres, then serve.
# On SQLite the app auto-creates tables at startup, so migrations are skipped.
set -e

if [[ "${DATABASE_URL:-}" == postgres* ]]; then
  echo "[start] Postgres detected — running Alembic migrations…"
  uv run alembic upgrade head
fi

exec uv run uvicorn app.main:app --host 0.0.0.0 --port "${PORT:-8000}"
