"""AnimaForge Gameplan-play-diagram endpoints (Agent #8).

Routes:
  POST /api/v1/animaforge/play
       Body: { play_id, opponent_coverage? }
       - Looks up a complete cached job for `(play_id, opponent_coverage)` and
         returns the video_url if found.
       - Otherwise builds a play-diagram spec and submits a render job.

  GET /api/v1/animaforge/play/status?play_id=...&opponent_coverage=...
       - Returns the most recent job for the (play, coverage) variant.
"""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import get_current_user
from app.db.base import get_db
from app.models.animaforge import (
    JOB_TYPE_PLAY,
    STATUS_COMPLETE,
    STATUS_FAILED,
    STATUS_PENDING,
    AnimaForgeJob,
)
from app.models.gameplan import Gameplan
from app.models.user import User
from app.schemas.animaforge import (
    PlayDiagramRenderRequest,
    PlayDiagramRenderResponse,
    PlayDiagramStatusResponse,
)
from app.services.animaforge.client import (
    AnimaForgeService,
    AnimaForgeUnavailable,
)
from app.services.animaforge.play_spec import build_play_diagram_spec

router = APIRouter(tags=["AnimaForge Play"])


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _source_id(play_id: str, opponent_coverage: str | None) -> str:
    """Cache-key form: `{play_id}:{coverage_or_none}`."""
    return f"{play_id}:{opponent_coverage or 'none'}"


async def _find_play_in_user_gameplans(
    db: AsyncSession, user_id: str, play_id: str
) -> tuple[dict[str, Any] | None, str | None]:
    """Scan a user's gameplans for a play matching `play_id`.

    Returns `(play_dict, title_id)` — both `None` if not found. We deliberately
    don't 404 the caller when this misses: the spec builder tolerates sparse
    inputs and still produces a reasonable universal-tactic-diagram.
    """
    rows = (
        await db.execute(
            select(Gameplan).where(
                Gameplan.user_id == user_id,
                Gameplan.is_archived.is_(False),
            )
        )
    ).scalars().all()

    for gp in rows:
        plays = gp.plays or []
        for play in plays:
            if not isinstance(play, dict):
                continue
            if str(play.get("id") or play.get("play_id") or "") == play_id:
                title_id = (
                    play.get("title_id")
                    or play.get("titleId")
                    # gameplan-level title (model column is named `title`)
                    or getattr(gp, "title", None)
                )
                return play, str(title_id) if title_id else None
    return None, None


def _coerce_play_to_spec_params(
    play: dict[str, Any] | None,
    *,
    play_id: str,
    title_id: str | None,
    opponent_coverage: str | None,
) -> dict[str, Any]:
    """Build the param dict consumed by `build_play_diagram_spec`.

    Tolerates camelCase or snake_case keys on the play dict.
    """
    play = play or {}
    return {
        "play_name": play.get("name") or play.get("play_name") or play_id,
        "formation": play.get("formation"),
        "tags": play.get("conceptTags")
        or play.get("concept_tags")
        or play.get("tags")
        or [],
        "call_structure": play.get("callStructure")
        or play.get("call_structure")
        or {},
        "title_id": title_id or "",
        "opponent_coverage": opponent_coverage,
    }


async def _latest_job_for_variant(
    db: AsyncSession, *, user_id: str, source_id: str
) -> AnimaForgeJob | None:
    """Most recent job (any status) for this user + source variant."""
    return (
        await db.execute(
            select(AnimaForgeJob)
            .where(
                AnimaForgeJob.user_id == user_id,
                AnimaForgeJob.type == JOB_TYPE_PLAY,
                AnimaForgeJob.source_id == source_id,
            )
            .order_by(desc(AnimaForgeJob.created_at))
            .limit(1)
        )
    ).scalar_one_or_none()


async def _latest_complete_job(
    db: AsyncSession, *, user_id: str, source_id: str
) -> AnimaForgeJob | None:
    """Most recent COMPLETE job for cache-hit resolution."""
    return (
        await db.execute(
            select(AnimaForgeJob)
            .where(
                AnimaForgeJob.user_id == user_id,
                AnimaForgeJob.type == JOB_TYPE_PLAY,
                AnimaForgeJob.source_id == source_id,
                AnimaForgeJob.status == STATUS_COMPLETE,
            )
            .order_by(desc(AnimaForgeJob.completed_at))
            .limit(1)
        )
    ).scalar_one_or_none()


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------


@router.post("/play", response_model=PlayDiagramRenderResponse)
async def render_play_diagram(
    body: PlayDiagramRenderRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> PlayDiagramRenderResponse:
    """Trigger (or reuse) an animated play diagram render."""
    play_id = body.play_id
    opponent_coverage = body.opponent_coverage
    source_id = _source_id(play_id, opponent_coverage)
    user_id = str(current_user.id)

    # 1. Cache hit — same play + same coverage already rendered.
    cached = await _latest_complete_job(
        db, user_id=user_id, source_id=source_id
    )
    if cached and cached.video_url:
        return PlayDiagramRenderResponse(
            job_id=cached.job_id,
            status=cached.status,
            video_url=cached.video_url,
            thumbnail_url=cached.thumbnail_url,
            cached=True,
            play_id=play_id,
            opponent_coverage=opponent_coverage,
        )

    # 2. Build spec from the user's gameplans (best effort).
    play, title_id = await _find_play_in_user_gameplans(
        db, user_id=user_id, play_id=play_id
    )
    spec = build_play_diagram_spec(
        _coerce_play_to_spec_params(
            play,
            play_id=play_id,
            title_id=title_id,
            opponent_coverage=opponent_coverage,
        )
    )

    # 3. Request a render. If AnimaForge is offline, surface a soft error;
    #    the frontend gates the button via /animaforge/status so this branch
    #    is rare in practice.
    try:
        result = await AnimaForgeService.request_render(
            type=JOB_TYPE_PLAY,
            title_id=title_id or "unknown",
            spec=spec,
            user_id=user_id,
        )
    except AnimaForgeUnavailable as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"AnimaForge unavailable: {exc}",
        ) from exc

    job_id = str(result.get("job_id") or uuid.uuid4())
    estimated = int(result.get("estimated_seconds") or 45)

    # 4. Persist a tracking row so the webhook + status endpoint can find it.
    row = AnimaForgeJob(
        user_id=user_id,
        job_id=job_id,
        type=JOB_TYPE_PLAY,
        source_id=source_id,
        title_id=title_id or "unknown",
        status=STATUS_PENDING,
        spec=spec,
    )
    db.add(row)
    await db.flush()

    return PlayDiagramRenderResponse(
        job_id=job_id,
        estimated_seconds=estimated,
        status=STATUS_PENDING,
        cached=False,
        play_id=play_id,
        opponent_coverage=opponent_coverage,
    )


@router.get("/play/status", response_model=PlayDiagramStatusResponse)
async def get_play_diagram_status(
    play_id: str = Query(..., description="ID of the play."),
    opponent_coverage: Optional[str] = Query(
        default=None,
        description="Coverage shell variant (cover-3, cover-2, ...).",
    ),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> PlayDiagramStatusResponse:
    """Return the most recent job for this (play, coverage) variant."""
    source_id = _source_id(play_id, opponent_coverage)
    job = await _latest_job_for_variant(
        db, user_id=str(current_user.id), source_id=source_id
    )

    if job is None:
        return PlayDiagramStatusResponse(
            play_id=play_id,
            opponent_coverage=opponent_coverage,
            job_id=None,
            status=None,
        )

    completed_at: datetime | None = job.completed_at
    return PlayDiagramStatusResponse(
        play_id=play_id,
        opponent_coverage=opponent_coverage,
        job_id=job.job_id,
        status=job.status,
        video_url=job.video_url,
        thumbnail_url=job.thumbnail_url,
        completed_at=completed_at,
        spec=job.spec if isinstance(job.spec, dict) else None,
    )


# Suppress lint warning on unused imports referenced by tests / future use.
_ = (STATUS_FAILED,)
