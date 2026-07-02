"""Real-footage validation harness for D3 + D4 pre-merge review.

Plays a local 1080p MP4 of Madden 26 footage through the full Phase 0
pipeline (capture-style frame → core dispatcher → Madden adapter) and
reports:

  - Title detection: which title locked, confidence, time-to-lock.
  - Per-frame adapter latency: p50 / p95 / p99 (measured, not estimated).
  - OCR readings: a sample of score / clock / down / distance / field-pos
    pulled from the real HUD via EasyOCR.
  - Failure modes: dropped frames, budget breaches, adapter exceptions.

This script bypasses the websocket transport entirely — it constructs a
SessionContext + Dispatcher in-process and feeds it raw frames. That
keeps the harness independent of the :8001/:8002 zombie issue (D2) and
isolates the adapter from any network jitter.

Usage (from repo root, with the visionaudioforge service venv active):

    python agents/capture/real_footage_harness.py \
        --video agents/capture/fixtures/real/madden26.mp4 \
        --max-frames 600 \
        --report real_footage_report.json
"""

from __future__ import annotations

import argparse
import json
import logging
import statistics
import sys
import time
from dataclasses import asdict
from pathlib import Path

import cv2
import numpy as np

# Make the VAF service package importable.
SERVICE_ROOT = Path(__file__).resolve().parents[2] / "services" / "visionaudioforge"
if str(SERVICE_ROOT) not in sys.path:
    sys.path.insert(0, str(SERVICE_ROOT))

from app.core.dispatcher import Dispatcher  # noqa: E402
from app.core.session import SessionContext  # noqa: E402
from app.schemas.enums import IntegrityMode, TitleEnum  # noqa: E402

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s | %(message)s")
log = logging.getLogger("harness")


def _percentile(values: list[float], p: float) -> float:
    if not values:
        return 0.0
    ordered = sorted(values)
    idx = min(len(ordered) - 1, int(p * len(ordered)))
    return round(ordered[idx], 3)


def run(video_path: Path, max_frames: int, frame_stride: int, with_hint: bool) -> dict:
    cap = cv2.VideoCapture(str(video_path))
    if not cap.isOpened():
        raise RuntimeError(f"Could not open video: {video_path}")

    fps = cap.get(cv2.CAP_PROP_FPS)
    total_frames_in_file = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    log.info(
        "video_opened",
        extra={"path": str(video_path), "fps": fps, "frames": total_frames_in_file, "wh": (width, height)},
    )

    session = SessionContext.open(
        session_id="harness-session-1",
        user_id="harness-user",
        integrity_mode=IntegrityMode.OFFLINE_LAB,
        active_title_hint=TitleEnum.MADDEN26 if with_hint else None,
    )
    dispatcher = Dispatcher(session)

    title_lock: dict | None = None
    sample_ocr: list[dict] = []
    sample_events: list[dict] = []
    budget_breaches = 0
    adapter_errors = 0
    frames_dispatched = 0
    frames_dropped_pre_dispatch = 0
    detector_calls_before_lock = 0
    overall_start = time.monotonic()

    frame_idx = -1
    while True:
        ok, frame = cap.read()
        if not ok:
            break
        frame_idx += 1
        if frame_idx % frame_stride != 0:
            continue
        if frames_dispatched >= max_frames:
            break

        # Convert BGR → BGR (already BGR from OpenCV) — adapters accept
        # either; passing through.
        if title_lock is None:
            detector_calls_before_lock += 1

        try:
            events = dispatcher.process_frame(frame)
        except Exception as exc:  # noqa: BLE001
            adapter_errors += 1
            log.warning("dispatcher_raised", extra={"frame_idx": frame_idx, "exc": str(exc)})
            continue
        frames_dispatched += 1

        # Title-lock detection: dispatcher sets session.title once locked.
        if title_lock is None and session.title is not None:
            title_lock = {
                "title": session.title.value,
                "confidence": round(session.title_confidence, 3),
                "frames_to_lock": frames_dispatched,
                "wallclock_to_lock_sec": round(time.monotonic() - overall_start, 3),
            }
            log.info("title_locked", extra=title_lock)

        if not events:
            frames_dropped_pre_dispatch += 1

        # Sample readings — keep a few for the report.
        if events and len(sample_events) < 5:
            for ev in events[:1]:
                sample_events.append(json.loads(ev.model_dump_json()))

        # Reach into adapter OCR for ground-truth visibility.
        if frames_dispatched in (5, 50, 200, 500, 1000):
            try:
                from app.adapters.madden26.ocr_pipeline import OCRPipeline

                snap = OCRPipeline().read_frame(frame)
                sample_ocr.append({"frame_idx": frame_idx, **asdict(snap)})
            except Exception as exc:  # noqa: BLE001
                log.warning("ocr_sample_failed", extra={"exc": str(exc)})

    cap.release()
    elapsed = round(time.monotonic() - overall_start, 3)
    pcts = dispatcher.latency_percentiles()
    latency_window = list(dispatcher.latency_ms)

    breach_count = sum(1 for v in latency_window if v > 80.0)
    budget_breaches = breach_count
    breach_pct = round(100.0 * breach_count / max(len(latency_window), 1), 2)

    report = {
        "video": str(video_path),
        "video_fps": fps,
        "video_resolution": [width, height],
        "frames_in_file": total_frames_in_file,
        "frames_dispatched": frames_dispatched,
        "frames_dropped_pre_dispatch": frames_dropped_pre_dispatch,
        "adapter_errors": adapter_errors,
        "elapsed_sec": elapsed,
        "title_lock": title_lock,
        "detector_calls_before_lock": detector_calls_before_lock,
        "latency_ms": {
            "count": pcts["count"],
            "p50": pcts["p50_ms"],
            "p95": pcts["p95_ms"],
            "p99": pcts["p99_ms"],
            "max": round(max(latency_window), 3) if latency_window else 0.0,
            "mean": round(statistics.fmean(latency_window), 3) if latency_window else 0.0,
        },
        "budget_breaches_80ms": budget_breaches,
        "budget_breaches_pct": breach_pct,
        "sample_ocr_readings": sample_ocr,
        "sample_events": sample_events,
    }
    return report


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--video", required=True, type=Path)
    p.add_argument("--max-frames", type=int, default=600)
    p.add_argument("--frame-stride", type=int, default=5,
                   help="Process every Nth frame (default 5 → ~12 fps from a 60-fps source)")
    p.add_argument("--no-hint", action="store_true",
                   help="Skip the Madden hint to test pure detection")
    p.add_argument("--report", type=Path, default=None)
    args = p.parse_args()

    report = run(
        video_path=args.video,
        max_frames=args.max_frames,
        frame_stride=args.frame_stride,
        with_hint=not args.no_hint,
    )

    output = json.dumps(report, indent=2, default=str)
    if args.report:
        args.report.write_text(output)
        log.info("report_written", extra={"path": str(args.report)})
    print(output)
    return 0


if __name__ == "__main__":
    sys.exit(main())
