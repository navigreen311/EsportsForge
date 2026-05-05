"""AnimaForge settings, connection test, and admin stats — Agent #10.

Endpoints (mounted by Agent #1's pre-registered prefix `/animaforge`):

- GET    /api/v1/animaforge/settings        — fetch the user's toggles
- POST   /api/v1/animaforge/settings        — persist the user's toggles (best effort)
- POST   /api/v1/animaforge/test-connection — probe AnimaForge availability + latency
- GET    /api/v1/animaforge/admin/stats     — admin dashboard counters

The file is defensive against missing dependencies: ``AnimaForgeService`` and
``AnimaForgeJob`` are owned by Agent #1 and may not exist yet on a given
worktree. We import them lazily and fall back to safe defaults so the service
never crashes when AnimaForge code has not landed.
"""

from __future__ import annotations

import asyncio
import logging
import time
from datetime import datetime, timedelta, timezone
from typing import Any, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings as app_settings
from app.core.deps import get_current_user, get_db
from app.models.user import User, UserRole
from app.schemas.animaforge import (
    AdminStatsResponse,
    AnimaForgeSettingsResponse,
    AnimaForgeSettingsUpdate,
    TestConnectionResponse,
)

logger = logging.getLogger("esportsforge.animaforge.settings")

router = APIRouter()


# ---------------------------------------------------------------------------
# In-memory fallback store
# ---------------------------------------------------------------------------
# The User model does not currently expose a JSON settings column, so we keep
# a process-local cache so a freshly persisted toggle round-trips for the
# duration of the FastAPI process. The frontend additionally mirrors values in
# localStorage to survive process restarts. When a JSON column is added on
# User, swap the dict for a real DB write.

_SETTINGS_CACHE: dict[str, dict[str, Any]] = {}


def _default_settings() -> dict[str, Any]:
    return {
        "auto_arsenal": True,
        "auto_drill": True,
        "auto_share": True,
        "quality": (app_settings.animaforge_default_quality
                    if hasattr(app_settings, "animaforge_default_quality")
                    else "standard"),
    }


# ---------------------------------------------------------------------------
# Lazy imports (Agent #1's surfaces)
# ---------------------------------------------------------------------------

def _try_import_service() -> Optional[Any]:
    """Return ``AnimaForgeService`` or ``None`` when Agent #1 has not landed."""
    try:
        from app.services.animaforge.client import AnimaForgeService  # noqa: WPS433

        return AnimaForgeService
    except Exception as exc:  # noqa: BLE001
        logger.debug("AnimaForgeService unavailable: %s", exc)
        return None


def _try_import_job_model() -> Optional[Any]:
    """Return ``AnimaForgeJob`` or ``None`` when the model is not yet present."""
    try:
        from app.models.animaforge import AnimaForgeJob  # noqa: WPS433

        return AnimaForgeJob
    except Exception as exc:  # noqa: BLE001
        logger.debug("AnimaForgeJob model unavailable: %s", exc)
        return None


# ---------------------------------------------------------------------------
# Admin gate
# ---------------------------------------------------------------------------

def _require_admin(user: User) -> None:
    """Raise 403 if the user is not on the TEAM tier (the platform's admin tier)."""
    if user.role != UserRole.TEAM:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required.",
        )


# ---------------------------------------------------------------------------
# GET /settings
# ---------------------------------------------------------------------------

@router.get(
    "/settings",
    response_model=AnimaForgeSettingsResponse,
    summary="Get the current user's AnimaForge preferences",
)
async def get_settings(
    current_user: User = Depends(get_current_user),
) -> AnimaForgeSettingsResponse:
    """Return the user's stored toggles, falling back to defaults."""
    cached = _SETTINGS_CACHE.get(str(current_user.id))
    if cached is not None:
        return AnimaForgeSettingsResponse(**cached)
    return AnimaForgeSettingsResponse(**_default_settings())


# ---------------------------------------------------------------------------
# POST /settings
# ---------------------------------------------------------------------------

@router.post(
    "/settings",
    response_model=AnimaForgeSettingsResponse,
    summary="Update the current user's AnimaForge preferences",
)
async def update_settings(
    payload: AnimaForgeSettingsUpdate,
    current_user: User = Depends(get_current_user),
) -> AnimaForgeSettingsResponse:
    """Persist the toggles in the in-memory cache (best effort)."""
    record = payload.model_dump()
    _SETTINGS_CACHE[str(current_user.id)] = record
    return AnimaForgeSettingsResponse(**record)


# ---------------------------------------------------------------------------
# POST /test-connection
# ---------------------------------------------------------------------------

@router.post(
    "/test-connection",
    response_model=TestConnectionResponse,
    summary="Probe AnimaForge availability and round-trip latency",
)
async def test_connection(
    current_user: User = Depends(get_current_user),  # noqa: ARG001
) -> TestConnectionResponse:
    """Run an availability probe through ``AnimaForgeService.is_available()``."""
    service = _try_import_service()
    if service is None:
        return TestConnectionResponse(
            available=False,
            latency_ms=0,
            message="AnimaForge service wrapper not yet available.",
        )

    start = time.monotonic()
    try:
        available = bool(await service.is_available())
    except Exception as exc:  # noqa: BLE001
        logger.warning("AnimaForge connection probe failed: %s", exc)
        return TestConnectionResponse(
            available=False,
            latency_ms=0,
            message="AnimaForge unreachable.",
        )

    latency_ms = max(0, int((time.monotonic() - start) * 1000))
    if available:
        return TestConnectionResponse(
            available=True,
            latency_ms=latency_ms,
            message=f"Connected — {latency_ms} ms round-trip.",
        )
    return TestConnectionResponse(
        available=False,
        latency_ms=latency_ms,
        message="AnimaForge is offline.",
    )


# ---------------------------------------------------------------------------
# GET /admin/stats
# ---------------------------------------------------------------------------

@router.get(
    "/admin/stats",
    response_model=AdminStatsResponse,
    summary="AnimaForge counters for the admin dashboard",
)
async def admin_stats(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> AdminStatsResponse:
    """Return jobs_today / avg_render_seconds / storage_mb / queue_depth."""
    _require_admin(current_user)

    job_model = _try_import_job_model()

    jobs_today = 0
    avg_render_seconds = 0.0
    storage_mb = 0.0

    if job_model is not None:
        try:
            since = datetime.now(timezone.utc) - timedelta(hours=24)
            jobs_today = await _count_jobs_since(db, job_model, since)
            avg_render_seconds = await _avg_render_seconds(db, job_model, since)
            storage_mb = await _storage_estimate_mb(db, job_model)
        except Exception as exc:  # noqa: BLE001
            # Degrade gracefully — admin page still loads with zeros.
            logger.warning("AnimaForge admin stats query failed: %s", exc)

    queue_depth = await _queue_depth()

    return AdminStatsResponse(
        jobs_today=jobs_today,
        avg_render_seconds=round(avg_render_seconds, 2),
        storage_mb=round(storage_mb, 2),
        queue_depth=queue_depth,
    )


# ---------------------------------------------------------------------------
# DB helpers (kept module-level so tests can monkeypatch them individually)
# ---------------------------------------------------------------------------

async def _count_jobs_since(
    db: AsyncSession, job_model: Any, since: datetime
) -> int:
    """Count rows created in the last 24h, regardless of status."""
    created_col = getattr(job_model, "created_at", None)
    stmt = select(func.count()).select_from(job_model)
    if created_col is not None:
        stmt = stmt.where(created_col >= since)
    result = await db.execute(stmt)
    return int(result.scalar() or 0)


async def _avg_render_seconds(
    db: AsyncSession, job_model: Any, since: datetime
) -> float:
    """Average render duration over the last 24h of completed jobs."""
    created_col = getattr(job_model, "created_at", None)
    completed_col = getattr(job_model, "completed_at", None)
    status_col = getattr(job_model, "status", None)
    if created_col is None or completed_col is None:
        return 0.0
    stmt = select(created_col, completed_col).where(completed_col.isnot(None))
    if status_col is not None:
        stmt = stmt.where(status_col == "complete")
    stmt = stmt.where(created_col >= since)
    rows = (await db.execute(stmt)).all()
    if not rows:
        return 0.0
    deltas = [
        (completed - created).total_seconds()
        for created, completed in rows
        if created is not None and completed is not None
    ]
    if not deltas:
        return 0.0
    return float(sum(deltas) / len(deltas))


async def _storage_estimate_mb(db: AsyncSession, job_model: Any) -> float:
    """Estimate storage as `count(complete jobs) * AVG_CLIP_MB`.

    AnimaForge does not expose per-row sizes yet; assume ~3.5 MB per finished
    short clip. Adjust when the service starts returning sizes.
    """
    AVG_CLIP_MB = 3.5
    status_col = getattr(job_model, "status", None)
    video_col = getattr(job_model, "video_url", None)
    stmt = select(func.count()).select_from(job_model)
    if status_col is not None:
        stmt = stmt.where(status_col == "complete")
    if video_col is not None:
        stmt = stmt.where(video_col.isnot(None))
    result = await db.execute(stmt)
    finished = int(result.scalar() or 0)
    return finished * AVG_CLIP_MB


async def _queue_depth() -> int:
    """Best-effort queue depth from ``AnimaForgeService.queue_depth()``."""
    service = _try_import_service()
    if service is None:
        return 0
    fn = getattr(service, "queue_depth", None)
    if fn is None:
        return 0
    try:
        result = fn()
        if asyncio.iscoroutine(result):
            result = await result
        return max(0, int(result or 0))
    except Exception as exc:  # noqa: BLE001
        logger.debug("AnimaForge queue_depth failed: %s", exc)
        return 0
