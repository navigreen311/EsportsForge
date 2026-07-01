"""Cheap (non-OCR) HUD-context detector — M5c sub-task 7.5.1.

Answers "is the pre-snap play-call overlay up, or is this live gameplay?" in
~0.7ms (measured), replacing the second per-frame EasyOCR pass
(`is_play_call_screen`, ~340ms) that the OCR-of-overlay pivot added — a ~500x
cut to the state check. The cadence scheduler (7.5.2) calls
this on the hot path so a full OCR pass runs only for the one context on screen.

Calibration (scripts/hud_calibration/calibrate_context_detector.py, GT =
OCRPipeline.is_play_call_screen; report: context_detector_calibration.json):

  Two grayscale features, both game-mode-independent:
    banner_mean — mean luma of the formation_name band. The play-call banner is
                  a lit text panel: play_call >= 153, live usually << that.
    dark_frac   — fraction of the whole frame below luma 50. The play-call menu
                  DIMS the field behind it (a title-UI constant): play_call
                  >= 0.368, live median ~0.15.

  Rule: play_call  <=>  banner_mean >= 150  AND  dark_frac >= 0.30
  Result over 174 GT-labelled real frames (8 matchup + 8 playcall + exhibition):
    0 false-negatives (no play-call screen ever missed -> no formation-read/C5
    regression), 1 false-positive (a single play<->live TRANSITION frame in the
    exhibition mixed stream, which the downstream read_formation_name "N Plays"
    OCR guard rejects anyway). All 16 dedicated clips are 100% clean.

  A single-feature banner-only rule matched this on the sample, but dark_frac is
  kept for defense-in-depth: a live frame with a bright object in the banner band
  (white jersey, stadium light) can spike banner_mean without dimming the field;
  requiring dark_frac too rejects it. Cost is one extra (subsampled) frame mean.

  REJECTED second feature: scorebar_mean (scoreboard-band darkness). Clean on the
  dedicated playcall clips (~30) but BRIGHT (~110) on real-game play-call screens
  -> 7 false-negatives on the exhibition clip. Game-mode-dependent; dark_frac (the
  field dimming) is the UI-constant replacement.

If Madden's play-call UI changes and this drifts, the rollback ladder is:
banner-only -> banner+dark_frac (here) -> add a template-match on the banner
region -> recalibrate. See ADR 0013 (HUD calibration is recurring maintenance).
"""

from __future__ import annotations

import json
from enum import Enum
from pathlib import Path

import cv2
import numpy as np


class HudContext(str, Enum):
    PLAY_CALL = "play_call"
    LIVE_GAMEPLAY = "live_gameplay"


class ContextDetector:
    """Per-adapter cheap context detector. Stateless; safe to share."""

    # Calibrated thresholds (7.5.1). Margin below the play_call GT floors
    # (banner 153.3 -> 150, dark_frac 0.368 -> 0.30).
    BANNER_MEAN_MIN = 150.0
    DARK_FRAC_MIN = 0.30
    DARK_LUMA = 50            # pixel < this counts toward dark_frac
    DARK_FRAC_STRIDE = 4      # subsample the frame for dark_frac (16x fewer pixels)

    def __init__(self, hud_regions_path: str | Path | None = None) -> None:
        if hud_regions_path is None:
            hud_regions_path = Path(__file__).parent / "hud_regions.json"
        with open(hud_regions_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        contexts = data.get("hud_contexts", {})
        pc = contexts.get("play_call", {}).get("regions", {})
        banner = pc.get("formation_name")
        # bbox is [x, y, w, h]; None if the play_call context is absent (pre-v2.2.0).
        self._banner_bbox = tuple(banner["bbox"]) if banner else None

    def features(self, frame: np.ndarray) -> dict[str, float]:
        """The two cheap features — exposed for calibration / debugging."""
        gray = frame if frame.ndim == 2 else cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        # dark_frac on a strided subsample — statistically equivalent, ~16x cheaper.
        s = self.DARK_FRAC_STRIDE
        return {"banner_mean": _region_mean(gray, self._banner_bbox),
                "dark_frac": float((gray[::s, ::s] < self.DARK_LUMA).mean())}

    def detect(self, frame: np.ndarray) -> HudContext:
        """Classify a frame's HUD context in ~0.1ms (no OCR)."""
        if self._banner_bbox is None:
            # No play_call region calibrated -> we can't see the banner; treat as
            # live (the OCR path's own "N Plays" guard remains the safety net).
            return HudContext.LIVE_GAMEPLAY
        f = self.features(frame)
        if f["banner_mean"] >= self.BANNER_MEAN_MIN and f["dark_frac"] >= self.DARK_FRAC_MIN:
            return HudContext.PLAY_CALL
        return HudContext.LIVE_GAMEPLAY


def _region_mean(gray: np.ndarray, bbox) -> float:
    if bbox is None:
        return 0.0
    x, y, w, h = bbox
    H, W = gray.shape[:2]
    x0, y0 = max(0, int(x)), max(0, int(y))
    x1, y1 = min(W, int(x + w)), min(H, int(y + h))
    if x1 <= x0 or y1 <= y0:
        return 0.0
    return float(gray[y0:y1, x0:x1].mean())
