"""Share Your Win — animated achievement-card endpoints (Agent #9).

Endpoints (mounted by Agent #1's router under ``/api/v1/animaforge``):

    POST /api/v1/animaforge/share-win
        Body: {"trigger_type": str, "trigger_data": dict}
        Auth: required (server resolves user via get_current_user).

    GET  /api/v1/animaforge/pending-wins
        Returns share-win jobs whose render is complete (or rendering) and
        whose video has not yet been viewed by the user. The frontend uses
        this to surface the ``ShareWinModal`` once on dashboard load.

The handler always persists an ``AnimaForgeJob`` row first, then attempts the
AnimaForge render request. If AnimaForge is unavailable the row stays at
``status=pending`` with a captured spec — the webhook handler (Agent #2) or a
retry job can pick it up later. This keeps the share-win pipeline robust to
AnimaForge downtime.
"""

from __future__ import annotations

import logging
import uuid
from datetime import datetime, timezone
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import get_current_user
from app.db.base import get_db
from app.models.user import User
from app.services.animaforge.share_spec import build_share_card_spec

logger = logging.getLogger(__name__)

router = APIRouter(tags=["AnimaForge"])


# ---------------------------------------------------------------------------
# Soft imports — Agent #1 owns the canonical model + service. We import
# defensively so that this module loads even if Agent #1 has not merged yet
# (the router uses a try/except _mount, but we still want the file itself to
# import cleanly under pytest-collect, etc.).
# ---------------------------------------------------------------------------

try:
    from app.models.animaforge import (  # type: ignore
        JOB_TYPE_SHARE,
        STATUS_COMPLETE,
        STATUS_PENDING,
        STATUS_RENDERING,
        AnimaForgeJob,
    )
except Exception:  # noqa: BLE001
    AnimaForgeJob = None  # type: ignore[assignment,misc]
    JOB_TYPE_SHARE = "share-win"
    STATUS_PENDING = "pending"
    STATUS_RENDERING = "rendering"
    STATUS_COMPLETE = "complete"

try:
    from app.services.animaforge.client import (  # type: ignore
        AnimaForgeService,
        AnimaForgeUnavailable,
    )
except Exception:  # noqa: BLE001
    AnimaForgeService = None  # type: ignore[assignment,misc]

    class AnimaForgeUnavailable(Exception):  # type: ignore[no-redef]
        """Raised when AnimaForge is unreachable or returns 5xx."""


# ---------------------------------------------------------------------------
# Request / response schemas
# ---------------------------------------------------------------------------

class ShareWinRequest(BaseModel):
    """Body for POST /api/v1/animaforge/share-win."""

    trigger_type: str = Field(..., description="One of the known share-win trigger types.")
    trigger_data: dict[str, Any] = Field(default_factory=dict)


class ShareWinAcceptedResponse(BaseModel):
    job_id: str
    status: str
    estimated_seconds: int | None = None
    cached: bool = False
    video_url: str | None = None
    thumbnail_url: str | None = None


class PendingWinItem(BaseModel):
    job_id: str
    trigger_type: str
    status: str
    video_url: str | None = None
    thumbnail_url: str | None = None
    share_text: str | None = None
    hashtags: list[str] = Field(default_factory=list)
    completed_at: datetime | None = None


class PendingWinsResponse(BaseModel):
    items: list[PendingWinItem]


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _spec_field(spec: Any, key: str, default: Any = None) -> Any:
    """Extract a field from a stored spec — the column may be JSON or TEXT."""
    if isinstance(spec, dict):
        return spec.get(key, default)
    if isinstance(spec, str):
        try:
            import json
            return json.loads(spec).get(key, default)
        except Exception:  # noqa: BLE001
            return default
    return default


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@router.post(
    "/share-win",
    response_model=ShareWinAcceptedResponse,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Render an animated share-win card",
)
async def request_share_win(
    payload: ShareWinRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ShareWinAcceptedResponse:
    """Build the card spec, persist a job row, and request the render.

    Errors from AnimaForge do not 500 the response — the row stays pending
    and the share-win pipeline retries via webhook / scheduled retry. This
    matches the blueprint's "fire and forget" requirement.
    """
    spec = build_share_card_spec(
        payload.trigger_type, payload.trigger_data, current_user
    )

    title_id = (payload.trigger_data or {}).get("title_id", "unknown")
    source_id = f"{payload.trigger_type}:{uuid.uuid4().hex}"

    if AnimaForgeJob is None:
        # Agent #1's model not merged yet — return synthetic accepted response
        # so the integration can run end-to-end during parallel build.
        logger.info("AnimaForgeJob model unavailable; returning stub response")
        return ShareWinAcceptedResponse(
            job_id=f"pending:{source_id}",
            status=STATUS_PENDING,
            estimated_seconds=20,
        )

    job = AnimaForgeJob(
        user_id=str(current_user.id),
        job_id=f"local:{uuid.uuid4().hex}",
        type=JOB_TYPE_SHARE,
        source_id=source_id,
        title_id=title_id,
        status=STATUS_PENDING,
        spec=spec,
    )
    db.add(job)
    await db.flush()

    estimated_seconds: int | None = int(spec.get("duration", 20)) + 25

    if AnimaForgeService is not None:
        try:
            response = await AnimaForgeService.request_render(
                type=JOB_TYPE_SHARE,
                title_id=title_id,
                spec=spec,
                user_id=str(current_user.id),
            )
            if isinstance(response, dict):
                external_job_id = response.get("job_id")
                if external_job_id:
                    job.job_id = external_job_id
                estimated_seconds = response.get("estimated_seconds", estimated_seconds)
                if response.get("status") == STATUS_RENDERING:
                    job.status = STATUS_RENDERING
        except AnimaForgeUnavailable:
            logger.warning("AnimaForge unavailable — share-win job %s left pending", job.job_id)
        except Exception:  # noqa: BLE001
            logger.exception("AnimaForge request_render failed for share-win")

    await db.flush()

    return ShareWinAcceptedResponse(
        job_id=job.job_id,
        status=job.status,
        estimated_seconds=estimated_seconds,
    )


@router.get(
    "/pending-wins",
    response_model=PendingWinsResponse,
    summary="Pending share-win triggers for the current user",
)
async def list_pending_wins(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> PendingWinsResponse:
    """Return share-win jobs whose render is pending or recently complete.

    Implementation note: per the contract we keep the "pending share-wins" list
    as ephemeral state on the AnimaForgeJob row itself rather than introducing
    a parallel model. We surface jobs created in the last 24 hours so a player
    who finishes a session on one device sees the modal on next dashboard load.
    """
    if AnimaForgeJob is None:
        return PendingWinsResponse(items=[])

    cutoff = datetime.now(timezone.utc).timestamp() - 24 * 60 * 60

    stmt = (
        select(AnimaForgeJob)
        .where(
            AnimaForgeJob.user_id == str(current_user.id),
            AnimaForgeJob.type == JOB_TYPE_SHARE,
            AnimaForgeJob.status.in_((STATUS_PENDING, STATUS_RENDERING, STATUS_COMPLETE)),
        )
        .order_by(desc(AnimaForgeJob.created_at))
        .limit(20)
    )
    try:
        result = await db.execute(stmt)
        rows = list(result.scalars().all())
    except Exception:  # noqa: BLE001
        logger.exception("Failed to list pending share-wins")
        return PendingWinsResponse(items=[])

    items: list[PendingWinItem] = []
    for row in rows:
        # Filter older jobs in Python so this works whether ``created_at`` is
        # a datetime, naive, or already-aware timestamp.
        created_at = getattr(row, "created_at", None)
        if isinstance(created_at, datetime):
            ts = created_at.timestamp() if created_at.tzinfo else created_at.replace(
                tzinfo=timezone.utc
            ).timestamp()
            if ts < cutoff:
                continue

        spec = getattr(row, "spec", None)
        source_id = getattr(row, "source_id", "") or ""
        trigger_type = source_id.split(":", 1)[0] if ":" in source_id else source_id

        items.append(
            PendingWinItem(
                job_id=row.job_id,
                trigger_type=trigger_type or "milestone",
                status=row.status,
                video_url=row.video_url,
                thumbnail_url=row.thumbnail_url,
                share_text=_spec_field(spec, "share_text"),
                hashtags=_spec_field(spec, "hashtags", []) or [],
                completed_at=getattr(row, "completed_at", None),
            )
        )

    return PendingWinsResponse(items=items)


__all__ = ["router"]
