"""Pydantic schemas for the AnimaForge integration.

This file is shared across all 10 AnimaForge agents. Each agent appends
their own block under a ``# === <feature> ===`` header — DO NOT overwrite
or reorganize blocks owned by other agents.

Section ownership:
  * ``# === Core (Agent #1) ===``     — Job, JobStatusResponse, RenderRequestResponse, AvailabilityResponse
  * ``# === Webhook (Agent #2) ===``  — webhook payload schemas
  * ``# === Arsenal (Agent #4) ===``  — weapon-diagram render schemas
  * ``# === Drill (Agent #6) ===``    — drill-demo render schemas
  * ``# === Play (Agent #8) ===``     — play-diagram render schemas
  * ``# === Share (Agent #9) ===``    — share-win render schemas
  * ``# === Settings (Agent #10) ===``— settings/admin schemas
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Literal, Optional

from pydantic import BaseModel, ConfigDict, Field


# ---------------------------------------------------------------------------
# === Core (Agent #1) ===
# ---------------------------------------------------------------------------

class AvailabilityResponse(BaseModel):
    """Response for ``GET /api/v1/animaforge/status``."""

    available: bool


class JobStatusResponse(BaseModel):
    """Detailed view of a single AnimaForge render job.

    Returned by ``GET /api/v1/animaforge/jobs/{job_id}``. Merges the local
    DB row with live status from AnimaForge when the job is still pending.
    """

    model_config = ConfigDict(from_attributes=True)

    id: str
    job_id: str
    user_id: str
    type: str
    source_id: str
    title_id: str
    status: str
    video_url: str | None = None
    thumbnail_url: str | None = None
    progress: int | None = None
    error_message: str | None = None
    created_at: datetime
    completed_at: datetime | None = None


class JobListResponse(BaseModel):
    """Paginated list of jobs for the current user.

    Returned by ``GET /api/v1/animaforge/jobs``.
    """

    items: list[JobStatusResponse]
    total: int
    limit: int
    offset: int


class RenderRequestResponse(BaseModel):
    """Response shape for any ``POST /api/v1/animaforge/<feature>`` endpoint.

    Two valid populations (per contract §4):
      * Cache hit:   ``{video_url, thumbnail_url, cached: true}``
      * New job:     ``{job_id, estimated_seconds, status: "pending"}``

    All fields are optional so a single schema covers both shapes.
    """

    model_config = ConfigDict(extra="allow")

    # Cache-hit fields
    video_url: str | None = None
    thumbnail_url: str | None = None
    cached: bool | None = None

    # New-job fields
    job_id: str | None = None
    estimated_seconds: int | None = None
    status: str | None = None


class JobDeleteResponse(BaseModel):
    """Response for ``DELETE /api/v1/animaforge/jobs/{job_id}``."""

    deleted: bool
    job_id: str


# ---------------------------------------------------------------------------
# === Webhook (Agent #2) ===
# ---------------------------------------------------------------------------

class WebhookPayload(BaseModel):
    """Body shape AnimaForge sends to ``POST /api/v1/animaforge/webhook``.

    Mirrors the spec in the integration blueprint Section 1 / contract §4.
    """

    jobId: str = Field(..., description="AnimaForge's external job id")
    status: Literal["complete", "failed", "rendering"]
    videoUrl: str | None = None
    thumbnailUrl: str | None = None
    errorMessage: str | None = None


class WebhookResponse(BaseModel):
    """Echoed back to AnimaForge so it stops retrying."""

    received: bool = True


# ---------------------------------------------------------------------------
# === Arsenal (Agent #4) ===
# ---------------------------------------------------------------------------

class WeaponRenderRequest(BaseModel):
    """Body for `POST /api/v1/animaforge/arsenal`."""

    weapon_id: str = Field(..., min_length=1, description="Secret Weapon ID")


class WeaponRenderResponse(BaseModel):
    """Response for `POST /api/v1/animaforge/arsenal`.

    Either the cached `video_url` block OR the pending `job_id` block is
    populated — never both. Frontend branches on `cached`.
    """

    # Cached path
    video_url: Optional[str] = None
    thumbnail_url: Optional[str] = None
    cached: Optional[bool] = None

    # Pending path
    job_id: Optional[str] = None
    estimated_seconds: Optional[int] = None
    status: Optional[str] = None


class WeaponJobStatusResponse(BaseModel):
    """Response for `GET /api/v1/animaforge/arsenal/status?weapon_id=...`.

    All fields are optional so the endpoint can also return `{}` (no job
    exists yet for this weapon).
    """

    job_id: Optional[str] = None
    status: Optional[str] = None
    video_url: Optional[str] = None
    thumbnail_url: Optional[str] = None
    completed_at: Optional[str] = None


# ---------------------------------------------------------------------------
# === Drill (Agent #6) ===
# ---------------------------------------------------------------------------

class DrillRenderRequest(BaseModel):
    """Body for POST /api/v1/animaforge/drill."""

    title_id: str = Field(..., description="Canonical title id (e.g. 'madden-26').")
    drill_type: str = Field(
        ..., description="Drill type slug (e.g. 'pre-snap-reads').",
    )


class DrillRenderPending(BaseModel):
    """Returned when a new render job was created and is pending."""

    job_id: str
    estimated_seconds: int
    status: str = "pending"


class DrillRenderCached(BaseModel):
    """Returned when a completed render exists for this title+drill_type."""

    video_url: str
    thumbnail_url: str | None = None
    cached: bool = True


class DrillRenderUnavailable(BaseModel):
    """Returned when no spec exists for the (title_id, drill_type) combo.

    Frontend treats this as "hide UI silently" per blueprint graceful-
    degradation rule.
    """

    available: bool = False
    reason: str = "spec-not-found"


class DrillStatusResponse(BaseModel):
    """Response for GET /api/v1/animaforge/drill/status.

    Either an empty dict (no job exists yet) or a populated record.
    """

    job_id: str | None = None
    status: str | None = None
    video_url: str | None = None
    thumbnail_url: str | None = None
    title_id: str | None = None
    drill_type: str | None = None
    spec_available: bool | None = Field(
        default=None,
        description="False when build_drill_animation_spec returns None.",
    )

    # Allow the empty-dict shape `{}` per contract §4 spec.
    model_config = ConfigDict(extra="ignore")


# ---------------------------------------------------------------------------
# === Play (Agent #8) ===
# ---------------------------------------------------------------------------

class PlayDiagramRenderRequest(BaseModel):
    """POST /api/v1/animaforge/play body.

    Cache key includes opponent_coverage so PA Crossers vs Cover 3 renders a
    different animation than PA Crossers vs Cover 2. If no coverage is known,
    the spec builder falls back to "standard-reads".
    """

    play_id: str = Field(..., description="ID of the Play to animate.")
    opponent_coverage: Optional[str] = Field(
        default=None,
        description=(
            "Optional opponent coverage shell (cover-3, cover-2, man, ...). "
            "Used to bias void-zone overlay and read-progression animation."
        ),
    )


class PlayDiagramRenderResponse(BaseModel):
    """Response for POST /api/v1/animaforge/play."""

    play_id: Optional[str] = None
    opponent_coverage: Optional[str] = None
    job_id: Optional[str] = None
    estimated_seconds: Optional[int] = None
    status: Optional[str] = None
    video_url: Optional[str] = None
    thumbnail_url: Optional[str] = None
    cached: bool = False


class PlayDiagramStatusResponse(BaseModel):
    """GET /api/v1/animaforge/play/status response.

    Returns the most recent job for the (play, coverage) variant.
    """

    play_id: str
    opponent_coverage: Optional[str] = None
    job_id: Optional[str] = None
    status: Optional[str] = None
    video_url: Optional[str] = None
    thumbnail_url: Optional[str] = None
    completed_at: Optional[datetime] = None
    spec: Optional[dict[str, Any]] = None
