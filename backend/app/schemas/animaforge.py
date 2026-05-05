"""Pydantic schemas for AnimaForge integration.

NOTE: This file is shared across agents. Agent #1 creates the canonical
header + core schemas (Job, JobStatusResponse). Each feature agent appends a
`# === <feature> ===` block.

Agent #8 placed an initial scaffold here as a stub since Agent #1 hasn't
landed yet — Agent #1 will harmonize on merge.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# Core (Agent #1 owns; stub here so the file imports cleanly).
# ---------------------------------------------------------------------------


class JobStatusResponse(BaseModel):
    """Generic job status response."""

    job_id: str
    type: str
    status: str
    video_url: Optional[str] = None
    thumbnail_url: Optional[str] = None
    progress: Optional[int] = None
    completed_at: Optional[datetime] = None


class RenderResponse(BaseModel):
    """Response for any POST /animaforge/<feature> render-trigger endpoint."""

    job_id: Optional[str] = None
    estimated_seconds: Optional[int] = None
    status: Optional[str] = None
    video_url: Optional[str] = None
    thumbnail_url: Optional[str] = None
    cached: bool = False


# === Play Diagram (Agent #8) ===


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


class PlayDiagramRenderResponse(RenderResponse):
    """Same shape as RenderResponse but typed locally for OpenAPI clarity."""

    play_id: Optional[str] = None
    opponent_coverage: Optional[str] = None


class PlayDiagramStatusResponse(BaseModel):
    """GET /api/v1/animaforge/play/status response.

    Returns the most recent job for the (play, coverage) variant, plus a
    convenience `available` flag the frontend uses to show/hide the Watch
    button without firing a network request.
    """

    play_id: str
    opponent_coverage: Optional[str] = None
    job_id: Optional[str] = None
    status: Optional[str] = None
    video_url: Optional[str] = None
    thumbnail_url: Optional[str] = None
    completed_at: Optional[datetime] = None
    spec: Optional[dict[str, Any]] = None
