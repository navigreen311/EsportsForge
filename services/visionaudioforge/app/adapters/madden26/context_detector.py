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

  Rule (v2.3.0-live, 54 live frames, 0 FP / 0 FN across both play-call
  sub-views + gameplay/pause/replay/corrupted):
      play_call  <=>  0.30 <= dark_frac <= 0.78  AND  bar_mean >= 60
  (bar_mean = bottom broadcast-bar luma; hidden by the pause overlay, so it
  rejects the pause menu that dark_frac 0.89 alone can't. The old
  banner_mean>=150 rule below was tuned on CPU-vs-CPU clips and false-negatived
  the real feed. Superseded — see the ContextDetector class for the live rule.)
  [Historical] Rule: play_call  <=>  banner_mean >= 150  AND  dark_frac >= 0.30
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

    # v2.3.0-live recalibration (52 live PS5 frames across formation-select +
    # play-select play-call, in-game gameplay, pause menu, replay, corrupted).
    # The v2.2.0 banner-luma rule keyed on the '<Formation> - N Plays' bander and
    # false-negatived the real feed (play-select has no banner; formation-select's
    # banner blanks mid-scroll). Two robust, game-mode-independent features instead:
    #   dark_frac — fraction of the frame dimmed (< DARK_LUMA). The play-call menu
    #     DIMS the field: play_call 0.44-0.60, gameplay 0.03-0.16, replay 0.20-0.25,
    #     corrupted 0.10. A floor of 0.30 cleanly separates play-call from those.
    #   bar_mean  — luma of the persistent bottom broadcast bar. Present in BOTH
    #     play-call and gameplay (~104-135) but HIDDEN by the full-screen pause /
    #     menu dim (~25). So it rejects the pause menu, which dark_frac (0.89) can't.
    # Rule: play_call  <=>  0.30 <= dark_frac <= 0.78  AND  bar_mean >= 60.
    # The upper dark_frac bound rejects near-black transition/menu frames (~0.89)
    # that still have the bar drawn; real play-call caps at ~0.60 (field dim only).
    DARK_FRAC_MIN = 0.30
    DARK_FRAC_MAX = 0.78
    BAR_MEAN_MIN = 60.0
    DARK_LUMA = 50            # pixel < this counts toward dark_frac
    DARK_FRAC_STRIDE = 4      # subsample the frame for dark_frac (16x fewer pixels)
    # Bottom broadcast-bar band (full-width), the "is the in-play/play-call HUD
    # bar on screen?" signal. Matches the v2.3.0-live scoreboard band.
    BAR_BBOX = (280, 985, 1500, 80)

    def __init__(self, hud_regions_path: str | Path | None = None) -> None:
        # hud_regions_path kept for signature compatibility; the detector's
        # features are fixed bboxes (detector calibration, not HUD-region coords).
        self._bar_bbox = self.BAR_BBOX

    def features(self, frame: np.ndarray) -> dict[str, float]:
        """The two cheap features — exposed for calibration / debugging."""
        gray = frame if frame.ndim == 2 else cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        # dark_frac on a strided subsample — statistically equivalent, ~16x cheaper.
        s = self.DARK_FRAC_STRIDE
        return {"dark_frac": float((gray[::s, ::s] < self.DARK_LUMA).mean()),
                "bar_mean": _region_mean(gray, self._bar_bbox)}

    def detect(self, frame: np.ndarray) -> HudContext:
        """Classify a frame's HUD context in ~0.1ms (no OCR)."""
        f = self.features(frame)
        if (self.DARK_FRAC_MIN <= f["dark_frac"] <= self.DARK_FRAC_MAX
                and f["bar_mean"] >= self.BAR_MEAN_MIN):
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
