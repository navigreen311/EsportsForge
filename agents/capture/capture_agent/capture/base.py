"""Capture-source protocol.

Three implementations (Phase 0 ships test-video only):
- HDMI capture card via cv2.CAP_DSHOW (M1 final)
- PC monitor via mss (Phase 1.1)
- Test video file (Phase 0 ships this for dev)
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Iterator, Protocol

import numpy as np


@dataclass(frozen=True)
class Frame:
    """One captured frame plus its metadata."""

    frame_id: int
    captured_at: datetime
    image: np.ndarray  # BGR; agent encodes JPEG before transport
    width: int
    height: int


class CaptureSource(Protocol):
    """Implementations yield Frames at the configured cadence."""

    def open(self) -> None: ...
    def close(self) -> None: ...
    def frames(self) -> Iterator[Frame]: ...
    @property
    def device_label(self) -> str: ...
