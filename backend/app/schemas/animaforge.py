"""AnimaForge integration — Pydantic schemas.

TODO (Agent #1): This file is owned by Agent #1, who will replace it at merge
with the canonical core schemas (Job, JobStatusResponse, StatusResponse, etc.)
plus the agreed file header. Each feature agent then appends their block under
a `# === <feature> ===` marker per contract §7.

Until Agent #1 lands, Agent #4 ships this file with just the Arsenal block
so the endpoint module imports cleanly. Agent #1 should preserve the
`# === Arsenal (Agent #4) ===` block verbatim when they replace this file.
"""

from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, Field


# === Arsenal (Agent #4) =====================================================


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
