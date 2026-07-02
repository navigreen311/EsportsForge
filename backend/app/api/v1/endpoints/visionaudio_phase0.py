"""EsportsForge backend integration endpoints for VisionAudioForge.

Phase 0 — supports the M3 integration milestone:
- POST /api/v1/auth/validate-capture-key  — capture agent's bearer token
- POST /api/v1/visionaudio/events         — webhook receiver from VAF core
- GET  /api/v1/visionaudio/sessions/active — frontend reads to show "live"

NOTE: this is an additional module. The existing /api/v1/visionaudio
mount (the deprecated mock-proxy endpoints) stays in place during the
parallel-run window per docs/specs/03-mock-removal-and-page-wiring.md.
This module's routes are mounted under /api/v1 directly so they do not
collide with the legacy /api/v1/visionaudio prefix.
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field

logger = logging.getLogger("esportsforge.visionaudio_phase0")

# In-memory state for Phase 0. Real state moves to a dedicated DB table
# (capture_keys, vision_sessions) in Phase 1.
_VALID_CAPTURE_KEYS: dict[str, str] = {
    # Phase 0 dev key — replaced by issued tokens in Phase 1.
    "esf-cap-dev-placeholder": "5041bbe7-5d16-47c4-8f70-211935da55ea",
}
_RECENT_EVENTS: list[dict] = []  # for /sessions/active visibility
_RECENT_EVENTS_CAP = 200

# Mounted at /api/v1 by the central router via `_mount(... prefix="")`. The
# routes' full paths are spelled out below.
router = APIRouter(tags=["VisionAudioForge — Phase 0"])


# ---------------------------------------------------------------------------
# /api/v1/auth/validate-capture-key
# ---------------------------------------------------------------------------


class ValidateCaptureKeyRequest(BaseModel):
    api_key: str


class ValidateCaptureKeyResponse(BaseModel):
    valid: bool
    user_id: str | None = None


@router.post(
    "/auth/capture-key/validate",
    response_model=ValidateCaptureKeyResponse,
    summary="Validate a capture-agent bearer token",
    name="capture_key_validate",
)
async def validate_capture_key(req: ValidateCaptureKeyRequest) -> ValidateCaptureKeyResponse:
    user_id = _VALID_CAPTURE_KEYS.get(req.api_key)
    if user_id is None:
        return ValidateCaptureKeyResponse(valid=False)
    return ValidateCaptureKeyResponse(valid=True, user_id=user_id)


# ---------------------------------------------------------------------------
# /api/v1/visionaudio/events  (webhook receiver from VAF core)
# ---------------------------------------------------------------------------


class IngestEventBatch(BaseModel):
    events: list[dict[str, Any]] = Field(default_factory=list)


class IngestAck(BaseModel):
    accepted: int


@router.post(
    "/visionaudio/events",
    response_model=IngestAck,
    summary="Receive a batch of events from the VAF core",
    name="vaf_events_webhook",
)
async def ingest_events(batch: IngestEventBatch) -> IngestAck:
    """Per ADR 0003: in-process v1 with per-session delivery-failure
    instrumentation. Phase 0 just buffers + logs; Phase 1 wires per-page
    agent dispatch (GameplanAgent, OpponentScout, etc.).
    """
    for ev in batch.events:
        _RECENT_EVENTS.append(ev)
    # Cap the buffer.
    if len(_RECENT_EVENTS) > _RECENT_EVENTS_CAP:
        del _RECENT_EVENTS[: len(_RECENT_EVENTS) - _RECENT_EVENTS_CAP]
    logger.info("vaf_events_received", extra={"count": len(batch.events)})
    return IngestAck(accepted=len(batch.events))


# ---------------------------------------------------------------------------
# /api/v1/visionaudio/sessions/active
# ---------------------------------------------------------------------------


class ActiveSessionsResponse(BaseModel):
    recent_event_count: int
    last_event_ts: datetime | None
    titles_seen: list[str]


@router.get(
    "/visionaudio/sessions/active",
    response_model=ActiveSessionsResponse,
    summary="Frontend reads this to show 'vision live' indicator",
)
async def active_sessions() -> ActiveSessionsResponse:
    titles = sorted({ev.get("title") for ev in _RECENT_EVENTS if ev.get("title")})
    last_ts = None
    if _RECENT_EVENTS:
        ts = _RECENT_EVENTS[-1].get("timestamp")
        if ts:
            try:
                last_ts = datetime.fromisoformat(ts.replace("Z", "+00:00"))
            except Exception:
                last_ts = None
    return ActiveSessionsResponse(
        recent_event_count=len(_RECENT_EVENTS),
        last_event_ts=last_ts,
        titles_seen=[t for t in titles if isinstance(t, str)],
    )
