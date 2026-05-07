"""Capture Agent entry point.

Phase 0: loads config, opens the test-video source (only source supported
in this skeleton), connects to the VAF core via WS, sends frame batches
at the configured cadence, sends heartbeats every 5 s.

Out of scope for this Phase 0 skeleton:
- Capture-card source (Phase 1 M1 final — needs cv2.CAP_DSHOW + Win32 device enumeration)
- PC-monitor source (Phase 1.1 — needs mss)
- System tray UI (Phase 1 M1 final — pystray on Windows)
- Diagnostic window (Phase 1 M1 final — Tk)
- Credential Manager integration (Phase 1 M1 final — ADR 0008, pywin32)
- Reconnect-with-backoff + ring buffer (Phase 1 M8)

Run for dev:
    cd agents/capture
    ESF_CAPTURE_AGENT_CONFIG=./config.dev.toml python -m capture_agent.main
"""

from __future__ import annotations

import argparse
import asyncio
import logging
import sys
import time
from pathlib import Path

from .capture import TestVideoSource
from .config import AgentConfig, load_config
from .transport import WSClient

logger = logging.getLogger("capture.main")


async def run(cfg: AgentConfig, session_id: str) -> None:
    """Single capture session loop."""

    if cfg.capture.source != "test-video":
        raise SystemExit(
            f"Phase 0 capture agent only supports source=test-video; got {cfg.capture.source}. "
            "Capture-card and pc-monitor sources land in Phase 1."
        )

    source = TestVideoSource(
        path=cfg.capture.test_video,
        target_fps=cfg.transport.target_fps,
    )
    source.open()

    ws = WSClient(
        endpoint=cfg.core.endpoint or cfg.core.fallback_endpoint,
        api_key=cfg.auth.api_key,
        session_id=session_id,
    )
    await ws.connect()
    logger.info("agent_connected", extra={"endpoint": cfg.core.endpoint})

    control_task = asyncio.create_task(ws.listen_for_control())
    last_heartbeat = time.monotonic()
    batch: list = []

    try:
        for frame in source.frames():
            batch.append(frame)
            if len(batch) >= cfg.transport.batch_size:
                await ws.send_frame_batch(batch, cfg.transport.jpeg_quality)
                batch = []

            now = time.monotonic()
            if now - last_heartbeat >= 5.0:
                await ws.send_heartbeat(
                    current_fps=cfg.transport.target_fps,
                    capture_status="ok",
                )
                last_heartbeat = now

            await asyncio.sleep(0)  # yield to control_task
    except asyncio.CancelledError:
        logger.info("cancelled")
    finally:
        if batch:
            try:
                await ws.send_frame_batch(batch, cfg.transport.jpeg_quality)
            except Exception:
                pass
        await ws.close()
        source.close()
        control_task.cancel()


def main() -> None:
    parser = argparse.ArgumentParser(description="EsportsForge Capture Agent (Phase 0)")
    parser.add_argument("--config", type=Path, help="Override config path")
    parser.add_argument(
        "--session-id",
        required=True,
        help="Session ID issued by VAF core service /api/v1/sessions/open",
    )
    args = parser.parse_args()

    cfg = load_config(args.config)
    logging.basicConfig(
        level=cfg.log_level,
        format="%(asctime)s %(name)s %(levelname)s %(message)s",
    )

    try:
        asyncio.run(run(cfg, args.session_id))
    except KeyboardInterrupt:
        logger.info("agent_quit_via_keyboard")
        sys.exit(0)


if __name__ == "__main__":
    main()
