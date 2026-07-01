"""Cheap non-OCR play-boundary trigger (M5c sub-task 7.5.5).

A "play boundary" is roughly "a new play just started, so down/distance/field-
position have changed and should be re-OCR'd." The cadence scheduler keys the
`on_play_boundary` group and the smoother's play-epoch reset on this signal.

Phase 0 proxy (no OCR): frame-difference on the down/distance HUD sub-band. The
digits there change exactly when a new play begins; between plays the band is
static. Three firing paths:

  * bootstrap    — the first live frame fires once, so down/distance get an
                   initial read (there's no prior play-call screen on broadcast
                   footage to trigger from).
  * left_playcall— returning from the play-call overlay to live = a snap = a new
                   play (reliable when the play-call screen is captured).
  * band-change  — mean abs grayscale diff on the sub-band exceeds a threshold,
                   gated by a cooldown so a mid-render transition fires once.

The play-clock and field-position sub-regions are deliberately EXCLUDED from the
diff band: the play clock ticks every second and would over-fire.

Stub-compatible with the future real snap detector (M5b): same
`update(frame, *, context, left_play_call) -> bool` interface, so it drops in
behind this without a cadence rewrite.
"""

from __future__ import annotations

import cv2
import numpy as np

# down + distance digits only: x 752..866, y 1035..1059 (from hud_regions v2.2.0).
_DND_BAND = (752, 1035, 114, 24)


class PlayBoundaryTrigger:
    """Per-session. Tracks the prior down/distance band to detect changes."""

    DIFF_THRESHOLD = 12.0     # mean abs gray diff (0-255) on the sub-band
    COOLDOWN_FRAMES = 18      # ~1.5s at 12fps: one boundary per play, not per frame

    def __init__(self, band_bbox: tuple[int, int, int, int] = _DND_BAND) -> None:
        self._bbox = band_bbox
        self._prev: np.ndarray | None = None
        self._cooldown = 0
        self._bootstrapped = False

    def _band(self, frame: np.ndarray) -> np.ndarray:
        x, y, w, h = self._bbox
        H, W = frame.shape[:2]
        crop = frame[max(0, y):min(H, y + h), max(0, x):min(W, x + w)]
        if crop.size == 0:
            return np.zeros((1, 1), dtype=np.uint8)
        gray = crop if crop.ndim == 2 else cv2.cvtColor(crop, cv2.COLOR_BGR2GRAY)
        return gray

    def update(self, frame: np.ndarray, *, context: str,
               left_play_call: bool = False) -> bool:
        # Off live gameplay the scorebug/down-distance is hidden; drop the ref so
        # the first frame back re-bootstraps rather than diffing across the gap.
        if context != "live_gameplay":
            self._prev = None
            if self._cooldown > 0:
                self._cooldown -= 1
            return False

        band = self._band(frame)
        fired = False
        if not self._bootstrapped:
            fired = True
            self._bootstrapped = True
        elif left_play_call:
            fired = True
        elif self._prev is not None and self._cooldown == 0 \
                and self._prev.shape == band.shape:
            diff = float(np.abs(band.astype(np.int16) - self._prev.astype(np.int16)).mean())
            if diff >= self.DIFF_THRESHOLD:
                fired = True

        self._prev = band
        if fired:
            self._cooldown = self.COOLDOWN_FRAMES
        elif self._cooldown > 0:
            self._cooldown -= 1
        return fired
