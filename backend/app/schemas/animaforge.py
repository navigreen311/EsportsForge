# STUB — Agent #1 owns the canonical header (imports, core Job /
# JobStatusResponse schemas).  This file currently only contains
# Agent #6's drill block.  At merge, Agent #1's header replaces the
# stub header here while preserving the # === Drill (Agent #6) === block.
"""Pydantic schemas for AnimaForge integration.

Shared file — each agent appends a `# === <feature> ===` block.
"""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


# === Drill (Agent #6) ===

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
    model_config = {"extra": "ignore"}


__all__ = [
    "DrillRenderRequest",
    "DrillRenderPending",
    "DrillRenderCached",
    "DrillRenderUnavailable",
    "DrillStatusResponse",
]
