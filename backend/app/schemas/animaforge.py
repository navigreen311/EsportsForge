"""Pydantic schemas for AnimaForge integration.

TODO: Agent #1 will provide the canonical core schemas (Job, JobStatusResponse,
StatusResponse) at the top of this file. This Agent #2 placeholder exists so
the webhook endpoint can import its schemas independently on this branch.
At merge, Agent #1's core block will be prepended above the
``# === Webhook (Agent #2) ===`` section header.
"""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


# === Webhook (Agent #2) ===

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
