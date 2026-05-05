"""AnimaForge — drill demonstration endpoints.

Drill demos are SHARED across all users (cached on the AnimaForgeJob row
by ``source_id = f"{title_id}:{drill_type}"`` with ``user_id="system"``).
Frontend gates UI off ``available: false`` when no spec exists for the
(title, drill) combo.

Owner: Agent #6 — see `docs/integrations/animaforge_contract.md` §4.
"""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, Query
from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import get_current_user
from app.db.base import get_db
from app.models.animaforge import (
    AnimaForgeJob,
    JOB_TYPE_DRILL,
    STATUS_COMPLETE,
    STATUS_PENDING,
)
from app.models.user import User
from app.schemas.animaforge import DrillRenderRequest
from app.services.animaforge import AnimaForgeService, AnimaForgeUnavailable
from app.services.animaforge.drill_spec import build_drill_animation_spec

router = APIRouter()


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_SHARED_USER_ID = "system"


def _source_id(title_id: str, drill_type: str) -> str:
    """Canonical source_id used in the AnimaForgeJob row."""
    return f"{title_id}:{drill_type}"


# ---------------------------------------------------------------------------
# POST /api/v1/animaforge/drill
# ---------------------------------------------------------------------------

@router.post("/drill")
async def render_drill_demo(
    body: DrillRenderRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """Request a drill-demo render (or return cached).

    Returns one of:
      - ``{video_url, thumbnail_url, cached: true}`` — completed render exists.
      - ``{job_id, estimated_seconds, status: "pending"}`` — new job submitted.
      - ``{available: false, reason: "spec-not-found"}`` — no spec for combo.
      - ``{available: false, reason: "service-unavailable"}`` — AnimaForge down.
    """
    title_id = body.title_id
    drill_type = body.drill_type
    source_id = _source_id(title_id, drill_type)

    # 1. Spec lookup first — combos without a spec hide UI silently.
    spec = build_drill_animation_spec(title_id, drill_type)
    if spec is None:
        return {"available": False, "reason": "spec-not-found"}

    # 2. Look up an already-complete shared render.
    existing = await db.scalar(
        select(AnimaForgeJob)
        .where(AnimaForgeJob.source_id == source_id)
        .where(AnimaForgeJob.type == JOB_TYPE_DRILL)
        .where(AnimaForgeJob.status == STATUS_COMPLETE)
        .order_by(desc(AnimaForgeJob.completed_at))
        .limit(1)
    )
    if existing is not None and existing.video_url:
        return {
            "video_url": existing.video_url,
            "thumbnail_url": existing.thumbnail_url,
            "cached": True,
        }

    # 3. Submit a new render job to AnimaForge.
    try:
        result = await AnimaForgeService.request_render(
            type=JOB_TYPE_DRILL,
            title_id=title_id,
            spec=spec,
            user_id=_SHARED_USER_ID,
        )
    except AnimaForgeUnavailable:
        return {"available": False, "reason": "service-unavailable"}

    job_id = result.get("job_id")
    estimated_seconds = int(result.get("estimated_seconds", 60))
    if not job_id:
        return {"available": False, "reason": "service-unavailable"}

    # 4. Persist the row (shared user_id="system").
    row = AnimaForgeJob(
        user_id=_SHARED_USER_ID,
        job_id=job_id,
        type=JOB_TYPE_DRILL,
        source_id=source_id,
        title_id=title_id,
        status=STATUS_PENDING,
        spec=spec,
    )
    db.add(row)
    await db.commit()

    return {
        "job_id": job_id,
        "estimated_seconds": estimated_seconds,
        "status": "pending",
    }


# ---------------------------------------------------------------------------
# GET /api/v1/animaforge/drill/status
# ---------------------------------------------------------------------------

@router.get("/drill/status")
async def drill_status(
    title_id: str = Query(..., min_length=1),
    drill_type: str = Query(..., min_length=1),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """Most-recent shared drill-demo job for the (title_id, drill_type) combo.

    Returns ``{}`` when no job exists yet. If no spec is defined for the
    combo, returns ``{available: false, reason: "spec-not-found"}`` so the
    frontend can hide the UI without a follow-up POST.
    """
    spec = build_drill_animation_spec(title_id, drill_type)
    if spec is None:
        return {"available": False, "reason": "spec-not-found"}

    source_id = _source_id(title_id, drill_type)
    job = await db.scalar(
        select(AnimaForgeJob)
        .where(AnimaForgeJob.source_id == source_id)
        .where(AnimaForgeJob.type == JOB_TYPE_DRILL)
        .order_by(desc(AnimaForgeJob.created_at))
        .limit(1)
    )
    if job is None:
        return {}

    return {
        "job_id": job.job_id,
        "status": job.status,
        "video_url": job.video_url,
        "thumbnail_url": job.thumbnail_url,
        "title_id": job.title_id,
        "drill_type": drill_type,
    }


__all__ = ["router"]
