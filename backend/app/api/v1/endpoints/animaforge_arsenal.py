"""AnimaForge Arsenal endpoints — animated play diagrams for Secret Weapons.

Per contract §4 and blueprint Section 2:
  - POST /api/v1/animaforge/arsenal       — request a render (or return cache)
  - GET  /api/v1/animaforge/arsenal/status — most recent job for a weapon

Owner: Agent #4 (arsenal-backend).

Imports of `AnimaForgeJob` (Agent #1) and `AnimaForgeService` (Agent #1) are
lazy inside the handlers so this module can be imported even before Agent #1
lands on `main`. The router mount in `app/api/v1/router.py` is wrapped in
try/except so a missing dependency only disables this slice — never the
whole app.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import JSONResponse
from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import get_current_user
from app.db.base import get_db
from app.models.secret_weapon import SecretWeapon
from app.models.user import User
from app.schemas.animaforge import (
    WeaponRenderRequest,
    WeaponRenderResponse,
    WeaponJobStatusResponse,
)
from app.services.animaforge.weapon_spec import build_weapon_animation_spec

router = APIRouter()

# Constants mirror Agent #1's contract (`backend/app/models/animaforge.py`).
# Hard-coded here to avoid coupling — Agent #1's module exports the same
# values, but importing them creates a circular dependency on merge order.
_TYPE_WEAPON = "weapon-diagram"
_STATUS_PENDING = "pending"
_STATUS_COMPLETE = "complete"


def _import_animaforge_runtime() -> tuple[Any, Any]:
    """Lazy import for Agent #1's runtime modules.

    Returns `(AnimaForgeJob_model, AnimaForgeService_class)`. Raises
    HTTPException(503) if either module is missing on the current branch
    (e.g. running this branch in isolation before Agent #1 merges).
    """
    try:
        from app.models.animaforge import AnimaForgeJob
    except ImportError as exc:  # pragma: no cover - merge-order guard
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={
                "available": False,
                "reason": f"AnimaForgeJob model unavailable: {exc}",
            },
        ) from exc

    try:
        from app.services.animaforge.client import AnimaForgeService
    except ImportError:
        # Fall back to the stub in `app.services.animaforge.__init__`
        from app.services.animaforge import AnimaForgeService

    return AnimaForgeJob, AnimaForgeService


# ---------------------------------------------------------------------------
# POST /api/v1/animaforge/arsenal
# ---------------------------------------------------------------------------


@router.post(
    "/arsenal",
    response_model=WeaponRenderResponse,
    summary="Request (or fetch cached) Arsenal weapon animation",
)
async def request_weapon_animation(
    payload: WeaponRenderRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """Request a render for a saved Secret Weapon.

    Behavior (per blueprint Section 2):
      1. If a complete job already exists for this weapon → return the
         cached video_url + thumbnail_url with `cached: true`.
      2. Otherwise load the weapon, build the spec, request a render,
         persist the job row, and return `{job_id, estimated_seconds,
         status: "pending"}`.

    If `AnimaForgeService.is_available()` returns False → 503
    `{"available": false}` so the frontend can hide the UI silently.
    """
    AnimaForgeJob, AnimaForgeService = _import_animaforge_runtime()

    # 1. Service availability gate — frontend hides UI on 503.
    try:
        available = await AnimaForgeService.is_available()
    except Exception:  # noqa: BLE001 - any error == unavailable
        available = False

    if not available:
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={"available": False},
        )

    # 2. Cache check — most recent COMPLETE job for this weapon.
    cached_q = (
        select(AnimaForgeJob)
        .where(
            AnimaForgeJob.source_id == payload.weapon_id,
            AnimaForgeJob.type == _TYPE_WEAPON,
            AnimaForgeJob.status == _STATUS_COMPLETE,
        )
        .order_by(desc(AnimaForgeJob.completed_at))
        .limit(1)
    )
    cached = (await db.execute(cached_q)).scalar_one_or_none()
    if cached is not None and cached.video_url:
        return WeaponRenderResponse(
            video_url=cached.video_url,
            thumbnail_url=cached.thumbnail_url,
            cached=True,
        )

    # 3. Load weapon — must exist.
    weapon = (
        await db.execute(
            select(SecretWeapon).where(SecretWeapon.id == payload.weapon_id)
        )
    ).scalar_one_or_none()
    if weapon is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": "weapon_not_found", "weapon_id": payload.weapon_id},
        )

    # 4. Build spec + request render.
    spec = build_weapon_animation_spec(weapon)
    try:
        render = await AnimaForgeService.request_render(
            type=_TYPE_WEAPON,
            title_id=weapon.title_id,
            spec=spec,
            user_id=current_user.id,
        )
    except NotImplementedError:
        # Agent #1's stub — surface as 503 so frontend hides UI.
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={"available": False, "reason": "animaforge stub"},
        )
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail={"error": "animaforge_render_failed", "message": str(exc)},
        ) from exc

    job_id = render.get("job_id")
    estimated_seconds = render.get("estimated_seconds", 60)
    if not job_id:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail={
                "error": "animaforge_missing_job_id",
                "message": "request_render returned no job_id",
            },
        )

    # 5. Persist the job row.
    job = AnimaForgeJob(
        user_id=current_user.id,
        job_id=job_id,
        type=_TYPE_WEAPON,
        source_id=payload.weapon_id,
        title_id=weapon.title_id,
        status=_STATUS_PENDING,
        spec=spec,
    )
    db.add(job)
    await db.commit()

    return WeaponRenderResponse(
        job_id=job_id,
        estimated_seconds=estimated_seconds,
        status=_STATUS_PENDING,
    )


# ---------------------------------------------------------------------------
# GET /api/v1/animaforge/arsenal/status?weapon_id=...
# ---------------------------------------------------------------------------


@router.get(
    "/arsenal/status",
    response_model=WeaponJobStatusResponse,
    summary="Look up the most recent animation job for a weapon",
)
async def get_weapon_animation_status(
    weapon_id: str = Query(..., min_length=1, description="Secret Weapon ID"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """Return the most recent AnimaForge job for *weapon_id* (any status).

    Used by the frontend `useEffect` when the weapon detail panel opens —
    so it can immediately render the player if an animation already exists.

    Response shape:
      - `{}` if no job exists for this weapon.
      - `{job_id, status, video_url?, thumbnail_url?, completed_at?}` otherwise.
    """
    AnimaForgeJob, _ = _import_animaforge_runtime()

    q = (
        select(AnimaForgeJob)
        .where(
            AnimaForgeJob.source_id == weapon_id,
            AnimaForgeJob.type == _TYPE_WEAPON,
        )
        .order_by(desc(AnimaForgeJob.created_at))
        .limit(1)
    )
    job = (await db.execute(q)).scalar_one_or_none()
    if job is None:
        return JSONResponse(content={})

    completed_at: str | None = None
    if job.completed_at is not None:
        ts = job.completed_at
        if ts.tzinfo is None:
            ts = ts.replace(tzinfo=timezone.utc)
        completed_at = ts.isoformat()

    return WeaponJobStatusResponse(
        job_id=job.job_id,
        status=job.status,
        video_url=job.video_url,
        thumbnail_url=job.thumbnail_url,
        completed_at=completed_at,
    )
