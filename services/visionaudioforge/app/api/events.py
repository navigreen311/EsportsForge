"""WebSocket event subscriber surface (Phase 1a Day 1).

The frontend (`useVisionEvents` hook — Day 2) connects here to receive
the live stream of `EventEnvelope`s for a session: the same envelopes the
webhook publisher delivers to the backend, fanned out in-process via
`app.core.event_hub`. Event-display-only — envelopes stream as-is, with
no coaching transform (the coaching engine is Phase 1b).

Auth mirrors `/ws/ingest` (`app/api/ingest.py`): Phase 0 session-scoped
placeholder — a non-empty `Authorization` header, `session_id` from the
path validated against the session registry. No user-JWT in VAF core
(state report Q5–6). Per state report §8: no server-side event filtering
— the client hook predicate-filters.
"""

from __future__ import annotations

import asyncio
import logging

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, status

from app.core.event_hub import hub
from app.core.session import registry

logger = logging.getLogger("vaf.api.events")

router = APIRouter()


async def _await_disconnect(ws: WebSocket) -> None:
    """Resolve when the client disconnects.

    A subscriber never sends application data, so any received frame that
    is a disconnect (or a closed transport) ends the stream.
    """
    try:
        while True:
            msg = await ws.receive()
            if msg.get("type") == "websocket.disconnect":
                return
    except WebSocketDisconnect:
        return
    except RuntimeError:
        # "Cannot call receive once a disconnect message has been received."
        return


@router.websocket("/ws/events/{session_id}")
async def events(ws: WebSocket, session_id: str) -> None:
    """Stream a session's event envelopes to a connected subscriber."""
    # Phase 0 session-scoped placeholder auth (mirrors /ws/ingest).
    if not ws.headers.get("authorization", ""):
        await ws.close(code=status.WS_1008_POLICY_VIOLATION)
        return
    session = await registry.get(session_id)
    if session is None:
        await ws.close(code=status.WS_1008_POLICY_VIOLATION, reason="unknown_session")
        return

    # Subscribe BEFORE accept so an event published immediately after the
    # client connects is not missed.
    queue = hub.subscribe(session_id)
    await ws.accept()
    logger.info("events_subscriber_connected", extra={"session_id": session_id})

    disconnect_task = asyncio.ensure_future(_await_disconnect(ws))
    try:
        while True:
            get_task = asyncio.ensure_future(queue.get())
            done, _pending = await asyncio.wait(
                {get_task, disconnect_task}, return_when=asyncio.FIRST_COMPLETED
            )
            if disconnect_task in done:
                get_task.cancel()
                break
            await ws.send_json(get_task.result())
    except WebSocketDisconnect:
        pass
    except Exception:  # noqa: BLE001
        logger.exception("events_stream_error", extra={"session_id": session_id})
        try:
            await ws.close(code=status.WS_1011_INTERNAL_ERROR)
        except Exception:
            pass
    finally:
        disconnect_task.cancel()
        hub.unsubscribe(session_id, queue)
        logger.info("events_subscriber_disconnected", extra={"session_id": session_id})
