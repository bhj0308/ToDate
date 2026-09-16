import logging
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy import text

from app.common.versioning import is_below
from app.config import get_settings
from app.db import engine
from app.models import Base
from app.modules.admin.router import router as admin_router
from app.modules.entitlements.router import router as entitlements_router
from app.modules.identity.router import router as identity_router
from app.modules.intelligent.router import router as intelligent_router
from app.modules.matchmaking.router import router as matchmaking_router
from app.modules.notifications.router import router as notifications_router
from app.modules.safety.router import router as safety_router
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

    @app.middleware("http")
    async def minimum_app_version(request: Request, call_next):
        """Refuse builds older than MIN_APP_VERSION with 426 Upgrade Required.

        A shipped app can't be force-updated, so this is how a breaking API
        change avoids stranding old installs with confusing errors. Only
        requests that identify an app version are gated.
        """
        client_version = request.headers.get("x-app-version")
        if (
            settings.min_app_version
            and client_version
            and request.url.path != "/health"
            and is_below(client_version, settings.min_app_version)
        ):
            return JSONResponse(
                {
                    "detail": "app update required",
                    "min_app_version": settings.min_app_version,
                },
                status_code=426,
            )
        return await call_next(request)

    # Added after the version gate so CORS is the outermost layer and even a
    # 426 response carries CORS headers.
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origin_list,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.get("/health", tags=["ops"])
    async def health():
        """Liveness + database reachability.

        The host's health check routes traffic based on this, so it has to fail
        when the database is unreachable — otherwise a broken instance keeps
        receiving requests instead of being restarted.
        """
        body = {
            "status": "ok",
            "environment": settings.environment,
            "demo_mode": settings.demo_mode,
            "database": "ok",
        }
        try:
            async with engine.connect() as conn:
                await conn.execute(text("SELECT 1"))
        except Exception:
            logging.exception("health check: database unreachable")
            body["status"] = "degraded"
            body["database"] = "unreachable"
            return JSONResponse(body, status_code=503)
        return body

    app.include_router(identity_router, prefix="/v1")
    app.include_router(admin_router, prefix="/v1")
    app.include_router(entitlements_router, prefix="/v1")
    app.include_router(verification_router, prefix="/v1")
    app.include_router(matchmaking_router, prefix="/v1")
    app.include_router(structured_router, prefix="/v1")
    app.include_router(intelligent_router, prefix="/v1")
    app.include_router(safety_router, prefix="/v1")
    app.include_router(notifications_router, prefix="/v1")

    # Dev-stub photo storage (see identity/service.py) — real impl needs an
    # object-storage vendor (S3 per ADR-0002).
    Path(settings.upload_dir).mkdir(parents=True, exist_ok=True)
    app.mount("/uploads", StaticFiles(directory=settings.upload_dir), name="uploads")

    # Demo web client — a single self-contained page served from the API so the
    # whole demo is one origin (no CORS) and one deployable unit.
    _web_index = Path(__file__).parent / "web" / "index.html"

    @app.get("/", include_in_schema=False)
    async def web_client():
        return FileResponse(_web_index)

    return app


app = create_app()
