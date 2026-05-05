"""Pydantic schemas for the AnimaForge integration.

Owned originally by Agent #1, who creates the file with imports + core schemas.
Each feature agent appends their own block under a `# === <feature> ===`
section header. This file is shared/append-only — see the integration contract
(`docs/integrations/animaforge_contract.md`, section 7).

If Agent #1 has not yet created the file, Agent #10 bootstraps the minimal
schemas they need. When Agent #1's branch lands first, the imports/core block
should be merged so duplicate definitions are removed.
"""

from __future__ import annotations

from datetime import datetime
from typing import Literal, Optional

from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# Shared/core schemas (Agent #1 owns; bootstrapped here so Agent #10 can ship
# independently). When Agent #1's PR merges, deduplicate any overlap.
# ---------------------------------------------------------------------------

JobType = Literal["weapon-diagram", "drill-demo", "play-diagram", "share-win"]
JobStatus = Literal["pending", "rendering", "complete", "failed"]
QualityLevel = Literal["standard", "high", "low"]


class JobStatusResponse(BaseModel):
    """Returned by GET /api/v1/animaforge/jobs/{job_id}."""

    job_id: str
    type: JobType
    status: JobStatus
    video_url: Optional[str] = None
    thumbnail_url: Optional[str] = None
    progress: Optional[int] = None
    completed_at: Optional[datetime] = None


class StatusResponse(BaseModel):
    """Returned by GET /api/v1/animaforge/status."""

    available: bool


# === Settings & Admin (Agent #10) ===

class AnimaForgeSettingsResponse(BaseModel):
    """User's per-user AnimaForge preferences.

    Persistence is best-effort. The User model does not currently expose a JSON
    settings column, so the backend may simply echo the defaults from
    ``settings.animaforge_default_quality``. The frontend mirrors the values in
    localStorage so they survive across sessions even when the backend cannot
    persist them.
    """

    auto_arsenal: bool = Field(
        default=True,
        description="Auto-generate weapon-diagram animations when a weapon is saved.",
    )
    auto_drill: bool = Field(
        default=True,
        description="Auto-generate the drill demo before the first rep.",
    )
    auto_share: bool = Field(
        default=True,
        description="Auto-generate Share Your Win cards on milestone events.",
    )
    quality: QualityLevel = Field(
        default="standard",
        description="Default render quality (standard | high | low).",
    )


class AnimaForgeSettingsUpdate(BaseModel):
    """Inbound payload for POST /api/v1/animaforge/settings."""

    auto_arsenal: bool
    auto_drill: bool
    auto_share: bool
    quality: QualityLevel


class TestConnectionResponse(BaseModel):
    """Returned by POST /api/v1/animaforge/test-connection."""

    available: bool
    latency_ms: int = Field(
        ..., description="Round-trip latency in milliseconds, or 0 when offline."
    )
    message: str = Field(
        ..., description="Human-readable status message for the UI to display."
    )


class AdminStatsResponse(BaseModel):
    """Returned by GET /api/v1/animaforge/admin/stats — admin only."""

    jobs_today: int = Field(..., ge=0)
    avg_render_seconds: float = Field(..., ge=0.0)
    storage_mb: float = Field(..., ge=0.0)
    queue_depth: int = Field(..., ge=0)
