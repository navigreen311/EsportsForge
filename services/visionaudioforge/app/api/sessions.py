"""Session HTTP endpoints — open / close / integrity-mode update.

Called by the EsportsForge backend when a player starts a vision
session or changes Integrity Mode.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel
from ulid import ULID

from app.core.session import local_session_enabled, local_session_id, registry
from app.schemas.enums import IntegrityMode, TitleEnum

router = APIRouter(prefix="/api/v1/sessions")


class OpenSessionRequest(BaseModel):
    user_id: str
    integrity_mode: IntegrityMode
    active_title: TitleEnum | None = None
    # No per-session webhook_url: core delivers events via one global publisher
    # targeting ESF_BACKEND_URL (see app/core/webhook.py). A per-session field
    # here was dead/ignored and implied routing that doesn't exist (Finding 1).


class OpenSessionResponse(BaseModel):
    session_id: str
    agent_endpoint: str
    expires_at: datetime


class IntegrityModeUpdate(BaseModel):
    integrity_mode: IntegrityMode


@router.post("/open", response_model=OpenSessionResponse)
async def open_session(req: OpenSessionRequest) -> OpenSessionResponse:
    if local_session_enabled():
        # Local single-session mode: one fixed id, get-or-create, so every
        # browser surface + the capture agent share it with no pin. See
        # app/core/session.py for the rationale + the flag contract.
        session_id = local_session_id()
        await registry.open_or_get(
            session_id=session_id,
            user_id=req.user_id,
            integrity_mode=req.integrity_mode,
            active_title_hint=req.active_title,
        )
    else:
        session_id = f"ses_{ULID()}"
        await registry.open(
            session_id=session_id,
            user_id=req.user_id,
            integrity_mode=req.integrity_mode,
            active_title_hint=req.active_title,
        )
    return OpenSessionResponse(
        session_id=session_id,
        agent_endpoint="ws://127.0.0.1:8100/ws/ingest",
        expires_at=datetime.now(timezone.utc) + timedelta(hours=4),
    )


@router.post("/{session_id}/close")
async def close_session(session_id: str) -> dict:
    await registry.close(session_id)
    return {"closed": session_id}


@router.post("/{session_id}/integrity-mode")
async def update_integrity_mode(
    session_id: str, body: IntegrityModeUpdate
) -> dict:
    ctx = await registry.update_integrity_mode(session_id, body.integrity_mode)
    if ctx is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="session_not_found")
    return {"session_id": session_id, "integrity_mode": ctx.integrity_mode.value}
