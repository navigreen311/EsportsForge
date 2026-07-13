"""Capture Agent entry point.

Phase 0: loads config, opens a frame source, connects to the VAF core via
WS, sends frame batches at the configured cadence, sends heartbeats every 5 s.

Phase 1a Day 0 adds source="file" (FilePlaybackSource) — plays a recorded
MP4 once through this same production path for playback validation. The
legacy source="test-video" (infinite loop) is retained for the smoke fixture.

The capture-card source (source="capture-card", HdmiCaptureSource via ffmpeg/dshow —
OpenCV can't grab the on-hand card) is wired in _build_source; config.capture-card.toml
is the runnable config (first live end-to-end run 2026-07-13).

Out of scope for this Phase 0 skeleton:
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

from .capture import FilePlaybackSource, HdmiCaptureSource, TestVideoSource
from .config import AgentConfig, load_config
from .transport import WSClient

logger = logging.getLogger("capture.main")


def _build_source(cfg: AgentConfig):
    """Select the capture source. Phase 1a adds file-mode ingestion."""
    src = cfg.capture.source
    if src == "test-video":
        return TestVideoSource(
            path=cfg.capture.test_video,
            target_fps=cfg.transport.target_fps,
        )
    if src == "file":
        return FilePlaybackSource(
            path=cfg.capture.file or cfg.capture.test_video,
            target_fps=cfg.transport.target_fps,
            playback_mode=cfg.capture.playback_mode,
            normalize_1080p=cfg.capture.normalize_1080p,
        )
    if src == "capture-card":
        return HdmiCaptureSource(
            device_name=cfg.capture.device_name,
            target_fps=cfg.transport.target_fps,
        )
    raise SystemExit(
        f"Capture agent supports source in {{test-video, file, capture-card}}; got {src}. "
        "pc-monitor source lands in Phase 1.1."
    )


async def run(cfg: AgentConfig, session_id: str) -> None:
    """Single capture session loop."""

    source = _build_source(cfg)
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

        # File-mode sources play once and reach EOF here; flush the tail
        # batch before signalling completion so no frames are lost.
        if batch:
            await ws.send_frame_batch(batch, cfg.transport.jpeg_quality)
            batch = []
        if getattr(source, "completed", False):
            logger.info(
                "clip_complete",
                extra={
                    "clip": source.device_label,
                    "frames_emitted": getattr(source, "frames_emitted", None),
                },
            )
            try:
                await ws.send_heartbeat(
                    current_fps=cfg.transport.target_fps,
                    capture_status="completed",
                )
            except Exception:
                pass
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
