"""Pydantic schemas for the AnimaForge integration.

Shared file — multiple agents append blocks under their own ``# === <feature> ===``
headers per the contract (``docs/integrations/animaforge_contract.md`` §7).

Agent #1 owns the file scaffolding and the core ``AnimaForgeJob`` /
``JobStatusResponse`` schemas at the top. Each feature agent appends below.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


# === Share Win (Agent #9) ===

class ShareWinTrigger(BaseModel):
    """A single share-win trigger fired during session-end detection."""

    type: str = Field(..., description="Trigger type — see VALID_TRIGGER_TYPES.")
    data: dict[str, Any] = Field(default_factory=dict)


class ShareWinRenderRequest(BaseModel):
    """Body for POST /api/v1/animaforge/share-win."""

    trigger_type: str
    trigger_data: dict[str, Any] = Field(default_factory=dict)


class ShareWinRenderResponse(BaseModel):
    """Response for POST /api/v1/animaforge/share-win."""

    job_id: str
    status: str
    estimated_seconds: int | None = None
    cached: bool = False
    video_url: str | None = None
    thumbnail_url: str | None = None


class PendingShareWin(BaseModel):
    """A single share-win surfaced for the dashboard ShareWinModal."""

    job_id: str
    trigger_type: str
    status: str
    video_url: str | None = None
    thumbnail_url: str | None = None
    share_text: str | None = None
    hashtags: list[str] = Field(default_factory=list)
    completed_at: datetime | None = None


class PendingShareWinsResponse(BaseModel):
    """Response for GET /api/v1/animaforge/pending-wins."""

    items: list[PendingShareWin] = Field(default_factory=list)


__all__ = [
    "PendingShareWin",
    "PendingShareWinsResponse",
    "ShareWinRenderRequest",
    "ShareWinRenderResponse",
    "ShareWinTrigger",
]
