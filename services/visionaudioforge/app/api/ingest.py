"""WebSocket frame ingestion endpoint.

The capture agent connects here, authenticates, and streams frame batches.
Per docs/specs/01-capture-agent.md §3 wire protocol.

Phase 0: auth is a placeholder (any non-empty Authorization header
accepted, with the header value used as session_id lookup). Real
validation against EsportsForge backend's /api/v1/auth/validate-capture-key
lands in Phase 1.
"""

from __future__ import annotations

import asyncio
import base64
import logging

import cv2
import numpy as np
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, status

from app.core.dispatcher import Dispatcher
from app.core.event_hub import hub
from app.core.session import registry
from app.core.webhook import publisher
from app.schemas.wire import (
    AgentCloseMessage,
    FrameBatchMessage,
    HeartbeatMessage,
    SessionOpenMessage,
)

logger = logging.getLogger("vaf.api.ingest")

router = APIRouter()


@router.websocket("/ws/ingest")
async def ingest(ws: WebSocket) -> None:
    """Per-connection ingestion loop."""

    # Phase 0 auth placeholder. Real auth validates the bearer token
    # against EsportsForge backend's validate-capture-key endpoint and
    # links it to a session_id from the agent's prior /sessions/open.
    auth = ws.headers.get("authorization", "")
    if not auth:
        await ws.close(code=status.WS_1008_POLICY_VIOLATION)
        return

    # Phase 0 convention: agent passes ?session_id=... on connect, OR
    # the caller has already created a session via POST /api/v1/sessions/open
    # and sets the bearer to the session_id directly (dev shortcut).
    session_id = ws.query_params.get("session_id") or auth.removeprefix("Bearer ").strip()
    session = await registry.get(session_id)
    if session is None:
        await ws.close(code=status.WS_1008_POLICY_VIOLATION, reason="unknown_session")
        return

    await ws.accept()

    # Initial handshake to the agent.
    handshake = SessionOpenMessage(
        session_id=session.session_id,
        integrity_mode=session.integrity_mode,
        active_title=session.title,
        capture_allowed=True,
    )
    await ws.send_json(handshake.model_dump(mode="json"))

    dispatcher = Dispatcher(session)
    logger.info("agent_connected", extra={"session_id": session_id})

    try:
        while True:
            raw = await ws.receive_json()
            msg_type = raw.get("type")

            if msg_type == "frame_batch":
                batch = FrameBatchMessage.model_validate(raw)
                for fr in batch.frames:
                    frame_bytes = base64.b64decode(fr.data_b64)
                    arr = np.frombuffer(frame_bytes, dtype=np.uint8)
                    frame = cv2.imdecode(arr, cv2.IMREAD_COLOR)
                    if frame is None:
                        logger.warning("frame_decode_failed")
                        continue
                    events = dispatcher.process_frame(frame)
                    for ev in events:
                        payload = ev.model_dump(mode="json")
                        await publisher.enqueue(payload)  # webhook → backend
                        await hub.publish(session_id, payload)  # WS fan-out → subscribers

            elif msg_type == "heartbeat":
                hb = HeartbeatMessage.model_validate(raw)
                session.last_heartbeat_at = None  # would set datetime.now(timezone.utc)
                logger.debug(
                    "heartbeat",
                    extra={"session_id": session_id, "stats": hb.stats.model_dump()},
                )

            elif msg_type == "session_close":
                AgentCloseMessage.model_validate(raw)
                logger.info("agent_close_received", extra={"session_id": session_id})
                break

            else:
                logger.warning("unknown_wire_type", extra={"type": msg_type})

    except WebSocketDisconnect:
        logger.info("agent_disconnected", extra={"session_id": session_id})
    except Exception as exc:  # noqa: BLE001
        logger.exception("ingest_error", extra={"session_id": session_id})
        try:
            await ws.close(code=status.WS_1011_INTERNAL_ERROR)
        except Exception:
            pass
