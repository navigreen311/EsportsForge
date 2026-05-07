"""Test-video capture source — plays a pre-recorded MP4 to the pipeline.

Used for dev / CI / repro testing without needing a capture card or PS5.

Phase 0 ships this; capture-card and pc-monitor sources land in Phase 1.
"""

from __future__ import annotations

import logging
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterator

import cv2

from .base import Frame

logger = logging.getLogger("capture.test_video")


class TestVideoSource:
    """Loops an MP4 file, yielding frames at the file's native rate."""

    def __init__(self, path: str | Path, target_fps: int = 12) -> None:
        self.path = Path(path)
        self.target_fps = target_fps
        self._cap: cv2.VideoCapture | None = None
        self._frame_id = 0

    @property
    def device_label(self) -> str:
        return f"test-video:{self.path.name}"

    def open(self) -> None:
        if not self.path.exists():
            raise FileNotFoundError(f"Test video not found: {self.path}")
        self._cap = cv2.VideoCapture(str(self.path))
        if not self._cap.isOpened():
            raise RuntimeError(f"Failed to open test video: {self.path}")
        logger.info("test_video_opened", extra={"path": str(self.path)})

    def close(self) -> None:
        if self._cap is not None:
            self._cap.release()
            self._cap = None

    def frames(self) -> Iterator[Frame]:
        if self._cap is None:
            self.open()
        assert self._cap is not None

        period = 1.0 / max(self.target_fps, 1)
        next_due = time.monotonic()

        while True:
            ok, image = self._cap.read()
            if not ok:
                # Loop the file.
                self._cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
                continue

            self._frame_id += 1
            h, w = image.shape[:2]
            yield Frame(
                frame_id=self._frame_id,
                captured_at=datetime.now(timezone.utc),
                image=image,
                width=w,
                height=h,
            )

            # Pace ourselves to target_fps.
            next_due += period
            sleep = next_due - time.monotonic()
            if sleep > 0:
                time.sleep(sleep)
            else:
                next_due = time.monotonic()
