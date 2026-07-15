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
import json
import logging
import os
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

from .capture import FilePlaybackSource, HdmiCaptureSource, TestVideoSource
from .config import AgentConfig, load_config
from .transport import WSClient

logger = logging.getLogger("capture.main")


def _resolve_session_id(cli_session_id: str | None) -> str:
    """Resolve the session id for this run.

    Precedence: explicit --session-id > local single-session mode > error.
    In local mode (VAF_LOCAL_SESSION=true, make-it-mine #2) the agent opens-or-
    gets the fixed session on core itself, so it needs no manual pin and works
    regardless of whether a browser opened the session first. Core is the single
    authority on the id (open_or_get returns the same fixed id it hands the
    browser), so both sides converge with no coordination.

    Uses stdlib urllib (not httpx) to keep the production agent's dependency list
    lean — this is a single one-shot POST at startup.
    """
    if cli_session_id:
        return cli_session_id
    if os.environ.get("VAF_LOCAL_SESSION") == "true":
        core = os.environ.get("VAF_CORE_URL", "http://127.0.0.1:8100")
        body = json.dumps(
            {"user_id": "founder", "integrity_mode": "offline_lab", "active_title": "madden26"}
        ).encode("utf-8")
        req = urllib.request.Request(
            f"{core}/api/v1/sessions/open",
            data=body,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        try:
            with urllib.request.urlopen(req, timeout=10.0) as resp:
                sid = str(json.loads(resp.read())["session_id"])
        except (urllib.error.URLError, KeyError, ValueError) as exc:
            raise SystemExit(
                f"VAF_LOCAL_SESSION: could not open the local session on core ({core}): {exc}. "
                "Is core up? (bash scripts/live.sh)"
            )
        logger.info("agent_local_session", extra={"session_id": sid})
        return sid
    raise SystemExit(
        "--session-id is required. For solo local dev, set VAF_LOCAL_SESSION=true "
        "to auto-share the browser's session (no pin) — see docs/runbooks/1a-drill-lab-flag.md §3."
    )


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
        default=None,
        help="Session ID from VAF core /api/v1/sessions/open. Optional when "
        "VAF_LOCAL_SESSION=true (the agent auto-shares the local session).",
    )
    args = parser.parse_args()

    cfg = load_config(args.config)
    logging.basicConfig(
        level=cfg.log_level,
        format="%(asctime)s %(name)s %(levelname)s %(message)s",
    )

    session_id = _resolve_session_id(args.session_id)

    try:
        asyncio.run(run(cfg, session_id))
    except KeyboardInterrupt:
        logger.info("agent_quit_via_keyboard")
        sys.exit(0)


if __name__ == "__main__":
    main()
