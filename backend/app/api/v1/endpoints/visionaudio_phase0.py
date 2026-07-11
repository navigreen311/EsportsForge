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
import os
from datetime import datetime, timezone
from typing import Any

import httpx
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field

from app.core.deps import get_current_user
from app.models.user import User

logger = logging.getLogger("esportsforge.visionaudio_phase0")

# Phase 1a Day-2/3 broker config. Core is backend-facing (its sessions.py
# docstring: "Called by the EsportsForge backend"), so the browser never talks
# to core over HTTP — it asks THIS backend to broker a session.
VAF_CORE_URL = os.environ.get("VAF_CORE_URL", "http://127.0.0.1:8100")
# Note: core routes webhooks GLOBALLY via its own ESF_BACKEND_URL (a single
# publisher), not per-session — so the broker does NOT pass a per-session
# webhook_url (that param was ignored; removed in Finding 1). Align core's
# ESF_BACKEND_URL to this backend for #8 audit. See docs/runbooks.

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
    titles = sorted({ev["title"] for ev in _RECENT_EVENTS if ev.get("title")})
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


# ---------------------------------------------------------------------------
# /api/v1/visionaudio/sessions/start  (Phase 1a broker — browser -> backend -> core)
# ---------------------------------------------------------------------------


class StartSessionResponse(BaseModel):
    session_id: str
    token: str
    ws_url: str


@router.post(
    "/visionaudio/sessions/start",
    response_model=StartSessionResponse,
    summary="Broker a Drill Lab vision session (browser -> backend -> core)",
    name="vaf_session_start",
)
async def start_session(current_user: User = Depends(get_current_user)) -> StartSessionResponse:
    """Provision a session for the authenticated user by brokering to VAF core.

    Fits the service boundary (core is backend-facing): the browser calls this
    authed endpoint; the backend calls core POST /sessions/open and returns the
    session_id + browser WS token. OFFLINE_LAB (FORMATION-emitting, §3). Core
    delivers events back to THIS backend via its global ESF_BACKEND_URL (#8
    audit) — routing is global, not per-session.
    """
    if os.environ.get("VAF_DRILL_LAB_ENABLED") != "true":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="drill_lab_disabled")
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.post(
                f"{VAF_CORE_URL}/api/v1/sessions/open",
                json={
                    "user_id": str(current_user.id),
                    "integrity_mode": "offline_lab",
                    "active_title": "madden26",
                },
            )
            resp.raise_for_status()
            session_id = resp.json()["session_id"]
    except httpx.HTTPError as exc:
        logger.error("vaf_session_start_broker_failed", extra={"err": str(exc)})
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail="core_unavailable")
    logger.info("vaf_session_started", extra={"session_id": session_id, "user": str(current_user.id)})
    return StartSessionResponse(
        session_id=session_id,
        token="esf-cap-dev-placeholder",  # Phase 0 placeholder browser WS ?token=
        ws_url=VAF_CORE_URL.replace("http://", "ws://").replace("https://", "wss://"),
    )
