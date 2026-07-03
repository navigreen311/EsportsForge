"""WebSocket transport to the VAF core service.

Phase 0 ships the basics: connect with Authorization header, send frame
batches, send heartbeats every 5 s. Reconnect-with-backoff and ring
buffer drain-on-reconnect land in Phase 1.

Wire protocol: docs/specs/01-capture-agent.md §3.
"""

from __future__ import annotations

import asyncio
import base64
import logging
import time
from datetime import datetime, timezone
from typing import Awaitable, Callable

import cv2
import websockets

from capture_agent.capture.base import Frame

logger = logging.getLogger("capture.ws_client")

HEARTBEAT_INTERVAL_SEC = 5.0


class WSClient:
    """Per-session WS connection. One client per agent process."""

    def __init__(
        self,
        endpoint: str,
        api_key: str,
        session_id: str,
        on_control: Callable[[dict], Awaitable[None]] | None = None,
    ) -> None:
        self._endpoint = endpoint
        self._api_key = api_key
        self._session_id = session_id
        self._on_control = on_control or (lambda _msg: asyncio.sleep(0))

        self._ws: websockets.WebSocketClientProtocol | None = None
        self._batch_seq = 0
        self._frames_captured = 0
        self._frames_sent = 0
        self._frames_dropped = 0
        self._uptime_start = time.monotonic()

    async def connect(self) -> None:
        # Phase 0: query-string session_id. Real auth is the bearer token.
        url = f"{self._endpoint}?session_id={self._session_id}"
        self._ws = await websockets.connect(
            url,
            extra_headers={"Authorization": f"Bearer {self._api_key}"},
        )
        # Server sends session_open on connect.
        first = await self._ws.recv()
        logger.info("session_open", extra={"raw": first[:200]})

    async def close(self) -> None:
        if self._ws is not None:
            try:
                await self._ws.send(
                    self._encode({"type": "session_close", "reason": "agent_quit"})
                )
            except Exception:
                pass
            await self._ws.close()
            self._ws = None

    async def send_frame_batch(self, frames: list[Frame], jpeg_quality: int) -> None:
        """Encode + send a frame batch. Increments dropped count on encode failures."""
        assert self._ws is not None
        encoded = []
        for fr in frames:
            try:
                ok, buf = cv2.imencode(
                    ".jpg",
                    fr.image,
                    [cv2.IMWRITE_JPEG_QUALITY, jpeg_quality],
                )
                if not ok:
                    self._frames_dropped += 1
                    continue
                encoded.append(
                    {
                        "frame_id": fr.frame_id,
                        "captured_at": fr.captured_at.isoformat(),
                        "width": fr.width,
                        "height": fr.height,
                        "format": "jpeg",
                        "data_b64": base64.b64encode(buf.tobytes()).decode("ascii"),
                    }
                )
            except Exception as exc:  # noqa: BLE001
                logger.warning("frame_encode_failed", extra={"exc_type": type(exc).__name__})
                self._frames_dropped += 1

        if not encoded:
            return

        self._batch_seq += 1
        self._frames_captured += len(frames)
        self._frames_sent += len(encoded)

        await self._ws.send(
            self._encode(
                {
                    "type": "frame_batch",
                    "session_id": self._session_id,
                    "batch_seq": self._batch_seq,
                    "frames": encoded,
                }
            )
        )

    async def send_heartbeat(self, current_fps: float, capture_status: str) -> None:
        assert self._ws is not None
        await self._ws.send(
            self._encode(
                {
                    "type": "heartbeat",
                    "session_id": self._session_id,
                    "stats": {
                        "frames_captured": self._frames_captured,
                        "frames_sent": self._frames_sent,
                        "frames_dropped": self._frames_dropped,
                        "current_fps": round(current_fps, 1),
                        "capture_device_status": capture_status,
                        "uptime_sec": int(time.monotonic() - self._uptime_start),
                    },
                }
            )
        )

    async def listen_for_control(self) -> None:
        """Receive loop — dispatches control messages to the on_control callback."""
        assert self._ws is not None
        try:
            async for raw in self._ws:
                try:
                    import json

                    msg = json.loads(raw)
                except Exception:
                    logger.warning("control_decode_failed")
                    continue
                await self._on_control(msg)
        except websockets.ConnectionClosed:
            logger.info("ws_closed_by_server")

    def _encode(self, payload: dict) -> str:
        import json

        return json.dumps(payload)
