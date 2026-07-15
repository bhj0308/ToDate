from functools import lru_cache

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

    @property
    def is_sqlite(self) -> bool:
        return self.database_url.startswith("sqlite")


@lru_cache
def get_settings() -> Settings:
    return Settings()
