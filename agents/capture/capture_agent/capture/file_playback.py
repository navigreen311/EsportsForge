"""File-playback capture source — plays a local MP4 through the pipeline ONCE.

Phase 1a Day 0 (state-report Prereq P7 / §7.1): promotes the Phase 0
test-video source into a first-class *file-mode ingestion* path so recorded
footage (e.g. curated YouTube Madden 26 clips) drives the **production**
capture → WS → VAF core path — the same path a live HDMI capture would take,
not a bypass harness like `real_footage_harness.py`.

Deltas from the Phase 0 `TestVideoSource` (per state report §7.1):

  1. **Play-once + EOF.** Plays the file through exactly once, then stops and
     records completion (`completed` / `frames_emitted`). `TestVideoSource`
     loops forever, which is wrong for per-clip validation tallying.
  2. **Configurable playback rate.** ``playback_mode="realtime"`` paces
     emission to ``target_fps`` (mimics a live HDMI capture cadence);
     ``playback_mode="max"`` yields unthrottled for throughput validation
     (acceptance criterion #4 — sustain 30 fps-equivalent on file input).
  3. **Resolution normalization.** Non-1080p sources (4K downscaled,
     phone-of-TV, compressed re-uploads) are resized to 1920x1080 before
     emission so the Madden HUD regions (calibrated at 1080p, ADR 0013)
     line up. Aspect ratios other than 16:9 are logged once as a warning
     because a straight resize distorts them.

The source samples the file down to ``target_fps`` with a stride derived from
the file's native FPS (same approach as `real_footage_harness.py`'s
``--frame-stride``), so a 60 fps clip emits ~``target_fps`` frames/sec —
matching what a live capture configured at ``target_fps`` would produce.
"""

from __future__ import annotations

import logging
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterator

import cv2

from .base import Frame

logger = logging.getLogger("capture.file_playback")

TARGET_WIDTH = 1920
TARGET_HEIGHT = 1080
_ASPECT_16_9 = 16 / 9


class FilePlaybackSource:
    """Plays a recorded MP4 once, yielding normalized Frames at ``target_fps``."""

    def __init__(
        self,
        path: str | Path,
        target_fps: int = 12,
        playback_mode: str = "realtime",
        normalize_1080p: bool = True,
    ) -> None:
        if playback_mode not in ("realtime", "max"):
            raise ValueError(
                f"playback_mode must be 'realtime' or 'max'; got {playback_mode!r}"
            )
        self.path = Path(path)
        self.target_fps = max(int(target_fps), 1)
        self.playback_mode = playback_mode
        self.normalize_1080p = normalize_1080p

        self._cap: cv2.VideoCapture | None = None
        self._frame_id = 0
        self._frames_emitted = 0
        self._completed = False
        self._source_fps = 0.0
        self._source_wh: tuple[int, int] = (0, 0)
        self._aspect_warned = False

    @property
    def device_label(self) -> str:
        return f"file:{self.path.name}"

    @property
    def completed(self) -> bool:
        """True once the file has played through to EOF (single pass)."""
        return self._completed

    @property
    def frames_emitted(self) -> int:
        """Count of frames actually yielded downstream (post-stride)."""
        return self._frames_emitted

    def _stride(self) -> int:
        """Frames to skip so emission approximates target_fps (>=1)."""
        if self._source_fps <= 0:
            return 1
        return max(1, round(self._source_fps / self.target_fps))

    def open(self) -> None:
        if not self.path.exists():
            raise FileNotFoundError(f"Playback file not found: {self.path}")
        self._cap = cv2.VideoCapture(str(self.path))
        if not self._cap.isOpened():
            # Most common real cause: the clip is AV1 and this OpenCV build
            # has no AV1 decoder. Procurement downloads H.264 mp4 to avoid it.
            raise RuntimeError(
                f"Failed to open playback file (unopenable or unsupported codec — "
                f"download as H.264 mp4): {self.path}"
            )
        self._source_fps = float(self._cap.get(cv2.CAP_PROP_FPS) or 0.0)
        w = int(self._cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        h = int(self._cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        self._source_wh = (w, h)
        logger.info(
            "file_playback_opened",
            extra={
                "path": str(self.path),
                "source_fps": self._source_fps,
                "source_wh": self._source_wh,
                "target_fps": self.target_fps,
                "stride": self._stride(),
                "playback_mode": self.playback_mode,
                "normalize_1080p": self.normalize_1080p,
            },
        )

    def close(self) -> None:
        if self._cap is not None:
            self._cap.release()
            self._cap = None

    def _normalize(self, image, w: int, h: int):
        """Resize to 1920x1080 for HUD alignment; warn once on non-16:9."""
        if not self.normalize_1080p or (w, h) == (TARGET_WIDTH, TARGET_HEIGHT):
            return image, w, h
        if not self._aspect_warned and h > 0 and abs((w / h) - _ASPECT_16_9) > 0.02:
            logger.warning(
                "non_16_9_source_resize_distorts",
                extra={"source_wh": (w, h)},
            )
            self._aspect_warned = True
        interp = cv2.INTER_AREA if (w > TARGET_WIDTH or h > TARGET_HEIGHT) else cv2.INTER_LINEAR
        resized = cv2.resize(image, (TARGET_WIDTH, TARGET_HEIGHT), interpolation=interp)
        return resized, TARGET_WIDTH, TARGET_HEIGHT

    def frames(self) -> Iterator[Frame]:
        """Yield normalized Frames for a single pass through the file, then stop."""
        if self._cap is None:
            self.open()
        assert self._cap is not None

        stride = self._stride()
        period = 1.0 / self.target_fps
        next_due = time.monotonic()
        read_idx = -1

        while True:
            ok, image = self._cap.read()
            if not ok:
                break  # EOF — single pass, no loop-around.
            read_idx += 1
            if read_idx % stride != 0:
                continue

            image, w, h = self._normalize(image, *self._source_wh)
            self._frame_id += 1
            self._frames_emitted += 1
            yield Frame(
                frame_id=self._frame_id,
                captured_at=datetime.now(timezone.utc),
                image=image,
                width=w,
                height=h,
            )

            if self.playback_mode == "realtime":
                next_due += period
                sleep = next_due - time.monotonic()
                if sleep > 0:
                    time.sleep(sleep)
                else:
                    next_due = time.monotonic()

        self._completed = True
        logger.info(
            "clip_complete",
            extra={"clip": self.device_label, "frames_emitted": self._frames_emitted},
        )
