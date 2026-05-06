"""AnimaForge webhook receiver.

Endpoint:
    POST /api/v1/animaforge/webhook

AnimaForge calls this when a render job changes state (``rendering``,
``complete``, ``failed``). The request is unauthenticated; instead we
verify an HMAC-SHA256 signature in the ``X-AnimaForge-Signature`` header
computed over the raw request body using ``settings.animaforge_webhook_secret``.

On ``complete`` we:
    1. Update the matching ``AnimaForgeJob`` row (video/thumbnail urls,
       status, ``completed_at``).
    2. Create a ``Notification`` row for the owning user (skipped when
       ``user_id == "system"`` — drill demos are shared across all users).
    3. Fire ``send_animaforge_push`` so the user gets a push if they have
       a subscription.

Always responds 200 ``{"received": true}`` on success so AnimaForge stops
retrying. Errors return 401 (bad signature), 400 (malformed JSON), or 404
(unknown job).
"""

from __future__ import annotations

import hashlib
import hmac
import json
import logging
from datetime import datetime, timezone

from fastapi import APIRouter, Header, HTTPException, Request, status
from fastapi.params import Depends
from pydantic import ValidationError
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.db.base import get_db
from app.models.animaforge import (
    AnimaForgeJob,
    JOB_TYPE_DRILL,
    JOB_TYPE_PLAY,
    JOB_TYPE_SHARE,
    JOB_TYPE_WEAPON,
    STATUS_COMPLETE,
    TERMINAL_STATUSES,
)
from app.models.notification import Notification
from app.schemas.animaforge import WebhookPayload, WebhookResponse
from app.services.animaforge.notifications import send_animaforge_push

logger = logging.getLogger(__name__)
router = APIRouter()


# ---------------------------------------------------------------------------
# Notification copy table (blueprint Section 1)
# ---------------------------------------------------------------------------

_NOTIFICATION_BODIES: dict[str, str] = {
    JOB_TYPE_WEAPON: (
        "Your Arsenal animation is ready — watch before your next game"
    ),
    JOB_TYPE_DRILL: "Your drill demonstration video is ready",
    JOB_TYPE_PLAY: "Your play animation is ready in Gameplan",
    JOB_TYPE_SHARE: "Your achievement card is ready to share",
}

_NOTIFICATION_TITLE = "Animation Ready"
_NOTIFICATION_TYPE = "animaforge-complete"
_SYSTEM_USER_ID = "system"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _get_action_url(job: AnimaForgeJob) -> str:
    """Map a completed job to the page that should open on notification tap."""
    if job.type == JOB_TYPE_WEAPON:
        return f"/dashboard/arsenal?weaponId={job.source_id}"
    if job.type == JOB_TYPE_DRILL:
        return f"/dashboard/drills?drillKey={job.source_id}"
    if job.type == JOB_TYPE_PLAY:
        return f"/dashboard/gameplan?playId={job.source_id}"
    if job.type == JOB_TYPE_SHARE:
        return f"/dashboard?shareWin={job.job_id}"
    # Defensive default — should be unreachable given JOB_TYPES is closed.
    return "/dashboard"


def _get_webhook_secret() -> str:
    """Read the AnimaForge webhook HMAC secret from settings.

    Wrapped so tests can monkeypatch this single function rather than the
    pydantic-settings object (which rejects unknown fields). At merge,
    ``settings.animaforge_webhook_secret`` is added by Agent #1's config
    update and this helper resolves transparently.
    """
    return getattr(settings, "animaforge_webhook_secret", "") or ""


def _verify_signature(raw_body: bytes, signature_header: str | None) -> bool:
    """Constant-time verify ``X-AnimaForge-Signature`` against ``raw_body``.

    The expected signature is the lowercase hex HMAC-SHA256 of the raw
    body keyed with the webhook secret. A leading ``"sha256="`` prefix is
    tolerated for compatibility with common webhook conventions.
    """
    if not signature_header:
        return False

    secret = _get_webhook_secret()
    if not secret:
        # No secret configured — refuse rather than accept anything.
        logger.warning(
            "animaforge.webhook signature check failed: secret not configured"
        )
        return False

    provided = signature_header.strip()
    if provided.lower().startswith("sha256="):
        provided = provided.split("=", 1)[1]

    expected = hmac.new(
        secret.encode("utf-8"), raw_body, hashlib.sha256
    ).hexdigest()
    return hmac.compare_digest(expected, provided.lower())


# ---------------------------------------------------------------------------
# Endpoint
# ---------------------------------------------------------------------------


@router.post(
    "/webhook",
    response_model=WebhookResponse,
    include_in_schema=False,
)
async def animaforge_webhook(
    request: Request,
    x_animaforge_signature: str | None = Header(default=None),
    db: AsyncSession = Depends(get_db),
) -> WebhookResponse:
    """Receive an AnimaForge render-status callback."""
    raw_body = await request.body()

    if not _verify_signature(raw_body, x_animaforge_signature):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="invalid signature",
        )

    # Parse + validate body.
    try:
        body_json = json.loads(raw_body or b"{}")
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="invalid json")

    try:
        payload = WebhookPayload.model_validate(body_json)
    except ValidationError as exc:
        raise HTTPException(status_code=400, detail=exc.errors())

    # Look up the job.
    result = await db.execute(
        select(AnimaForgeJob).where(AnimaForgeJob.job_id == payload.jobId)
    )
    job = result.scalar_one_or_none()
    if job is None:
        raise HTTPException(status_code=404, detail="job not found")

    # Update mutable fields.
    job.status = payload.status
    if payload.videoUrl is not None:
        job.video_url = payload.videoUrl
    if payload.thumbnailUrl is not None:
        job.thumbnail_url = payload.thumbnailUrl
    if payload.errorMessage is not None:
        job.error_message = payload.errorMessage
    if payload.status in TERMINAL_STATUSES:
        job.completed_at = datetime.now(timezone.utc)

    db.add(job)
    await db.flush()

    # Notify (only on successful completion + only for real users).
    if payload.status == STATUS_COMPLETE and job.user_id != _SYSTEM_USER_ID:
        body_text = _NOTIFICATION_BODIES.get(
            job.type, "Your animation is ready"
        )
        action_url = _get_action_url(job)

        notification = Notification(
            user_id=job.user_id,
            type=_NOTIFICATION_TYPE,
            title=_NOTIFICATION_TITLE,
            body=body_text,
            action_url=action_url,
        )
        db.add(notification)
        await db.flush()

        try:
            await send_animaforge_push(
                user_id=job.user_id,
                title=_NOTIFICATION_TITLE,
                body=body_text,
                action_url=action_url,
            )
        except Exception as exc:  # noqa: BLE001
            # Push failures must not fail the webhook — AnimaForge would retry.
            logger.warning(
                "animaforge.push send failed for user=%s job=%s: %s",
                job.user_id,
                job.job_id,
                exc,
            )

    return WebhookResponse(received=True)
