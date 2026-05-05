"""AnimaForge core endpoints (Agent #1).

Mounted at prefix ``/animaforge`` (see ``app.api.v1.router``).

Endpoints:
  * GET    ``/status``            — public availability probe (no auth)
  * GET    ``/jobs``              — list current user's jobs (paginated)
  * GET    ``/jobs/{job_id}``     — single job detail (live-merged when pending)
  * DELETE ``/jobs/{job_id}``     — soft-delete user's own job
"""

from __future__ import annotations

import logging

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import get_current_user
from app.db.base import get_db
from app.models.animaforge import (
    STATUS_COMPLETE,
    STATUS_FAILED,
    STATUS_PENDING,
    STATUS_RENDERING,
    AnimaForgeJob,
)
from app.models.user import User
from app.schemas.animaforge import (
    AvailabilityResponse,
    JobDeleteResponse,
    JobListResponse,
    JobStatusResponse,
)
from app.services.animaforge import AnimaForgeService, AnimaForgeUnavailable

logger = logging.getLogger(__name__)

router = APIRouter()


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _row_to_response(
    row: AnimaForgeJob, *, progress: int | None = None
) -> JobStatusResponse:
    return JobStatusResponse(
        id=row.id,
        job_id=row.job_id,
        user_id=row.user_id,
        type=row.type,
        source_id=row.source_id,
        title_id=row.title_id,
        status=row.status,
        video_url=row.video_url,
        thumbnail_url=row.thumbnail_url,
        progress=progress,
        error_message=row.error_message,
        created_at=row.created_at,
        completed_at=row.completed_at,
    )


# ---------------------------------------------------------------------------
# GET /status — public, no auth
# ---------------------------------------------------------------------------

@router.get("/status", response_model=AvailabilityResponse)
async def animaforge_status() -> AvailabilityResponse:
    """Probe AnimaForge health.

    Returns ``{"available": false}`` whenever the service can't be reached or
    isn't configured. Frontend uses this to silently hide AnimaForge UI.
    """
    return AvailabilityResponse(available=await AnimaForgeService.is_available())


# ---------------------------------------------------------------------------
# GET /jobs — list current user's jobs
# ---------------------------------------------------------------------------

@router.get("/jobs", response_model=JobListResponse)
async def list_jobs(
    type: str | None = Query(default=None, description="Filter by job type."),
    status_filter: str | None = Query(
        default=None, alias="status", description="Filter by status."
    ),
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> JobListResponse:
    """List the current user's AnimaForge render jobs (most recent first)."""
    base = select(AnimaForgeJob).where(AnimaForgeJob.user_id == current_user.id)
    count_stmt = select(func.count()).select_from(
        AnimaForgeJob
    ).where(AnimaForgeJob.user_id == current_user.id)

    if type:
        base = base.where(AnimaForgeJob.type == type)
        count_stmt = count_stmt.where(AnimaForgeJob.type == type)
    if status_filter:
        base = base.where(AnimaForgeJob.status == status_filter)
        count_stmt = count_stmt.where(AnimaForgeJob.status == status_filter)

    total = (await db.execute(count_stmt)).scalar_one()

    rows = (
        await db.execute(
            base.order_by(AnimaForgeJob.created_at.desc())
            .offset(offset)
            .limit(limit)
        )
    ).scalars().all()

    return JobListResponse(
        items=[_row_to_response(r) for r in rows],
        total=int(total),
        limit=limit,
        offset=offset,
    )


# ---------------------------------------------------------------------------
# GET /jobs/{job_id} — single job, live-merged when still pending
# ---------------------------------------------------------------------------

async def _find_job(
    db: AsyncSession, *, current_user_id: str, job_id: str
) -> AnimaForgeJob:
    """Look up a job by either its AnimaForge id or our internal uuid."""
    stmt = select(AnimaForgeJob).where(
        (AnimaForgeJob.job_id == job_id) | (AnimaForgeJob.id == job_id)
    )
    rows = (await db.execute(stmt)).scalars().all()
    if not rows:
        raise HTTPException(status_code=404, detail="Job not found")
    # Caller must own the job (drill demos use user_id="system" — they're
    # readable by everyone, since they're shared platform assets).
    for row in rows:
        if row.user_id == current_user_id or row.user_id == "system":
            return row
    raise HTTPException(status_code=404, detail="Job not found")


@router.get("/jobs/{job_id}", response_model=JobStatusResponse)
async def get_job(
    job_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> JobStatusResponse:
    """Return a single job. If still pending, merge in live AnimaForge status."""
    row = await _find_job(db, current_user_id=current_user.id, job_id=job_id)

    progress: int | None = None

    # Only hit AnimaForge if our local copy is non-terminal — saves traffic.
    if row.status in (STATUS_PENDING, STATUS_RENDERING):
        try:
            live = await AnimaForgeService.get_job_status(row.job_id)
        except AnimaForgeUnavailable as exc:
            logger.debug(
                "Live status fetch failed for %s — falling back to DB row: %s",
                row.job_id,
                exc,
            )
        else:
            # Merge live values onto the row in-memory (don't persist here —
            # that's the webhook's job).
            new_status = live.get("status")
            if isinstance(new_status, str):
                row.status = new_status
            new_video = live.get("video_url") or live.get("videoUrl")
            if isinstance(new_video, str):
                row.video_url = new_video
            new_thumb = live.get("thumbnail_url") or live.get("thumbnailUrl")
            if isinstance(new_thumb, str):
                row.thumbnail_url = new_thumb
            prog = live.get("progress")
            if isinstance(prog, (int, float)):
                progress = int(prog)

    return _row_to_response(row, progress=progress)


# ---------------------------------------------------------------------------
# DELETE /jobs/{job_id} — hard-delete user's own job row
# ---------------------------------------------------------------------------

@router.delete(
    "/jobs/{job_id}",
    response_model=JobDeleteResponse,
    status_code=status.HTTP_200_OK,
)
async def delete_job(
    job_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> JobDeleteResponse:
    """Delete a job row owned by the current user.

    "system" jobs (shared drill demos) cannot be deleted via this endpoint —
    they're shared platform assets and only an admin task should remove them.
    """
    stmt = select(AnimaForgeJob).where(
        (AnimaForgeJob.job_id == job_id) | (AnimaForgeJob.id == job_id)
    )
    row = (await db.execute(stmt)).scalar_one_or_none()
    if row is None or row.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Job not found")

    await db.delete(row)
    await db.commit()
    return JobDeleteResponse(deleted=True, job_id=row.job_id)
