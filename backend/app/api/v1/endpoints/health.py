"""Detailed health check endpoint — DB, Redis, version, uptime."""

from __future__ import annotations

import time
from datetime import datetime, timezone

from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter(tags=["Health"])

# ---------------------------------------------------------------------------
# Startup timestamp for uptime calculation
# ---------------------------------------------------------------------------

_STARTUP_TIME = time.monotonic()
_STARTUP_UTC = datetime.now(timezone.utc)


# ---------------------------------------------------------------------------
# Schemas
# ---------------------------------------------------------------------------

class ServiceHealth(BaseModel):
    """Health status of an individual backing service."""

    status: str
    latency_ms: float | None = None
    detail: str | None = None


class HealthResponse(BaseModel):
    """Full health check response."""

    status: str
    version: str
    uptime_seconds: float
    started_at: str
    database: ServiceHealth
    redis: ServiceHealth


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

async def _check_db() -> ServiceHealth:
    """Probe database connectivity (mock — replace with real check)."""
    # TODO: Replace with actual DB ping when wired up
    # async with get_db() as db:
    #     await db.execute(text("SELECT 1"))
    return ServiceHealth(
        status="healthy",
        latency_ms=1.2,
        detail="Mock DB check — replace with real probe.",
    )


async def _check_redis() -> ServiceHealth:
    """Probe Redis connectivity (mock — replace with real check)."""
    # TODO: Replace with actual Redis ping when wired up
    # redis = await get_redis()
    # await redis.ping()
    return ServiceHealth(
        status="healthy",
        latency_ms=0.4,
        detail="Mock Redis check — replace with real probe.",
    )


# ---------------------------------------------------------------------------
# Endpoint
# ---------------------------------------------------------------------------

@router.get(
    "/health",
    response_model=HealthResponse,
    summary="Detailed health check",
)
async def detailed_health() -> HealthResponse:
    """Return DB connectivity, Redis connectivity, API version, and uptime."""
    db_health = await _check_db()
    redis_health = await _check_redis()

    overall = "healthy"
    if db_health.status != "healthy" or redis_health.status != "healthy":
        overall = "degraded"

    return HealthResponse(
        status=overall,
        version="0.1.0",
        uptime_seconds=round(time.monotonic() - _STARTUP_TIME, 2),
        started_at=_STARTUP_UTC.isoformat(),
        database=db_health,
        redis=redis_health,
    )
