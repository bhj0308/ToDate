from functools import lru_cache

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings, loaded from environment / .env.

    Defaults are dev-friendly (SQLite) so the app boots without external
    infrastructure. Production must set DATABASE_URL to the async Postgres URL
    and JWT_SECRET to a real secret (see ADR-0002).
    """

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    app_name: str = "ToDate API"
    environment: str = "development"

    # Async SQLAlchemy URL. SQLite default lets the app boot locally with no
    # Postgres; production is postgresql+asyncpg://... per ADR-0002.
    database_url: str = "sqlite+aiosqlite:///./todate_dev.db"

    # Auth (ADR-0001): passwordless OTP + JWT sessions.
    jwt_secret: str = "dev-only-insecure-secret-change-me"
    jwt_algorithm: str = "HS256"
    access_token_ttl_minutes: int = 15
    refresh_token_ttl_days: int = 30
    otp_ttl_seconds: int = 300

    # Dev-stub local photo storage — real impl needs an object-storage vendor
    # (S3 per ADR-0002) once one is set up. Served statically at /uploads.
    upload_dir: str = "uploads"

    # Invite-only beta gate (Phase 1 GTM) is enforced in production only, so
    # local dev keeps the frictionless "any email registers" demo flow.
    # Comma-separated emails auto-flagged is_admin on registration — the
    # bootstrap path since there's no admin UI to grant the first admin.
    bootstrap_admin_emails: str = ""

    # DEMO_MODE: for teammate demos only. When true, every new sign-in is
    # auto-activated (PROFILE_ACTIVE) and given seeded verified attributes, so
    # discovery is populated the moment people join — no admin curation step.
    # Off by default; production behavior (manual activation) is untouched.
    demo_mode: bool = False

    # Rate limits for the abuse-prone auth endpoints (per client address).
    # `verify` guards brute-forcing a 6-digit code; `start` guards spamming
    # OTP sends (a real cost once SMS delivery is wired up).
    # Limits are per client address, and users behind one office NAT share an
    # address — so these are set high enough not to lock out a team, while still
    # making brute force of a 6-digit code (1e6 space) hopeless.
    otp_start_max_per_window: int = 15
    otp_verify_max_per_window: int = 15
    rate_limit_window_seconds: int = 900

    # Comma-separated allowed CORS origins, or "*" for all. Same-origin serving
    # (web client mounted on the API) needs none, but this keeps a separate
    # frontend possible.
    cors_origins: str = "*"

    @field_validator("database_url")
    @classmethod
    def _use_async_driver(cls, v: str) -> str:
        """Normalize a sync Postgres URL to the asyncpg driver.

        Hosting providers (Render, Railway, Heroku, Fly) hand out
        `postgresql://…` — or the legacy `postgres://…` — but this app runs on
        SQLAlchemy's async engine and needs `postgresql+asyncpg://…`. Rewriting
        it here means you can paste a provider's connection string (or wire it
        straight through from a Render blueprint) without it failing at boot.
        """
        if v.startswith("postgres://"):
            return v.replace("postgres://", "postgresql+asyncpg://", 1)
        if v.startswith("postgresql://"):
            return v.replace("postgresql://", "postgresql+asyncpg://", 1)
        return v

    @property
    def is_sqlite(self) -> bool:
        return self.database_url.startswith("sqlite")

    @property
    def cors_origin_list(self) -> list[str]:
        raw = self.cors_origins.strip()
        if raw == "*":
            return ["*"]
        return [o.strip() for o in raw.split(",") if o.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
