import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.config import get_settings
from app.db import engine
from app.models import Base
from app.modules.entitlements.router import router as entitlements_router
from app.modules.identity.router import router as identity_router
from app.modules.intelligent.router import router as intelligent_router
from app.modules.matchmaking.router import router as matchmaking_router
from app.modules.structured.router import router as structured_router
from app.modules.verification.router import router as verification_router

logging.basicConfig(level=logging.INFO)
settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    # DEV convenience: auto-create tables on SQLite so the app boots with no
    # migration step. Production uses Alembic migrations (see migrations/).
    if settings.is_sqlite:
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
    yield


def create_app() -> FastAPI:
    app = FastAPI(
        title=settings.app_name,
        version="0.1.0",
        lifespan=lifespan,
    )

    @app.get("/health", tags=["ops"])
    async def health():
        return {"status": "ok", "environment": settings.environment}

    app.include_router(identity_router, prefix="/v1")
    app.include_router(entitlements_router, prefix="/v1")
    app.include_router(verification_router, prefix="/v1")
    app.include_router(matchmaking_router, prefix="/v1")
    app.include_router(structured_router, prefix="/v1")
    app.include_router(intelligent_router, prefix="/v1")
    return app


app = create_app()
