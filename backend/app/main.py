"""EsportsForge Backend — FastAPI Application Entry Point."""

from app.middleware.rate_limit import RateLimitMiddleware
from app.middleware.security import SecurityHeadersMiddleware
import logging
import time
from contextlib import asynccontextmanager

logger = logging.getLogger("esportsforge.main")

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from sqlalchemy import text

from app.core.config import settings
from app.core.logging import setup_logging
from app.core.startup import validate_config
from app.db.base import engine, Base
from app.api.v1.router import api_router

_start_time: float = 0.0


@asynccontextmanager
async def lifespan(app: FastAPI):
    global _start_time
    # Import all models so Base.metadata knows about them.
    # Use importlib to avoid shadowing the `app: FastAPI` lifespan parameter.
    import importlib
    importlib.import_module("app.models")
    # Schema is managed by Alembic migrations (single source of truth), not
    # create_all. env.py runs asyncio.run() internally, so run the sync command
    # in a worker thread to avoid nesting it in this already-running event loop.
    import asyncio
    from pathlib import Path

    from alembic import command
    from alembic.config import Config

    _backend_dir = Path(__file__).resolve().parent.parent
    _cfg = Config(str(_backend_dir / "alembic.ini"))
    _cfg.set_main_option("script_location", str(_backend_dir / "alembic"))
    await asyncio.to_thread(command.upgrade, _cfg, "head")
    validate_config(settings)
    setup_logging(log_level=settings.log_level, json_format=settings.environment == "production")
    _start_time = time.time()
    yield


app = FastAPI(
    title="EsportsForge API",
    description="AI-powered competitive gaming intelligence platform",
    version="0.1.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


app.add_middleware(SecurityHeadersMiddleware)
app.add_middleware(
    RateLimitMiddleware,
    paths=["/api/v1/auth/login", "/api/v1/auth/register"],
    max_requests=5,
    window_seconds=900,
)


app.include_router(api_router, prefix="/api/v1")


@app.get("/api/health")
async def health_check():
    """Health check endpoint with comprehensive service status."""
    db_status = "connected"
    try:
        async with engine.begin() as conn:
            await conn.execute(text("SELECT 1"))
    except Exception as exc:
        # Log so CI / ops can see *why* the probe failed instead of staring at
        # an unexplained "degraded" status.
        logger.warning("health_check: database probe failed: %s", exc)
        db_status = "disconnected"

    api_key = settings.anthropic_api_key
    ai_configured = bool(api_key and api_key != "YOUR_ANTHROPIC_API_KEY_HERE")

    animaforge_status = "offline"
    try:
        from app.services.animaforge.client import AnimaForgeService
        if await AnimaForgeService.is_available():
            animaforge_status = "online"
    except Exception:
        animaforge_status = "offline"

    uptime_seconds = round(time.time() - _start_time, 2) if _start_time else 0.0

    overall = "healthy" if db_status == "connected" else "degraded"

    return {
        "status": overall,
        "version": "0.1.0",
        "service": "esportsforge",
        "environment": settings.environment,
        "uptime_seconds": uptime_seconds,
        "services": {
            "database": db_status,
            "ai": "configured" if ai_configured else "not_configured",
            "animaforge": animaforge_status,
        },
    }


@app.get("/api/v1/status")
async def platform_status():
    """Platform status with backbone system states."""
    return {
        "platform": "EsportsForge",
        "phase": "1-mvp",
        "backbone": {
            "forge_data_fabric": "initializing",
            "forge_core": "initializing",
            "player_twin": "initializing",
            "impact_rank": "initializing",
            "truth_engine": "initializing",
            "loop_ai": "initializing",
        },
        "titles": {
            "madden26": "initializing",
            "cfb26": "initializing",
        },
    }
