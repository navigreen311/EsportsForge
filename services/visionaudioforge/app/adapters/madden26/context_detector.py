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

from enum import Enum
from pathlib import Path

import cv2
import numpy as np


class HudContext(str, Enum):
    PLAY_CALL = "play_call"
    LIVE_GAMEPLAY = "live_gameplay"


class ContextDetector:
    """Per-adapter cheap context detector. Stateless; safe to share."""

    # v2.4.0-ps5 recalibration (2026-07-13; PS5 1080p PRACTICE feed — the source
    # the live spine actually runs on; first live end-to-end run). The v2.3.0-live
    # rule (dark_frac in [0.30,0.78] AND bar_mean>=60) was tuned on a real-GAME
    # broadcast feed and false-negatived EVERY practice-mode play-call screen: on
    # that source the play-call bottom band is a DARK button-hint bar (bar_mean ~28,
    # not the bright broadcast bar), so bar_mean>=60 rejected it — and bar_mean is
    # source-INVERTED (practice: play_call ~28 dark, live ~93 bright field), so no
    # single threshold works across sources. Replaced bar_mean with a robust,
    # game-mode-independent second feature:
    #   dark_frac — fraction of the frame dimmed (< DARK_LUMA). play_call 0.50-0.61
    #     (dark card/list UI + dimmed field), live 0.06-0.14, menu/pause/black
    #     0.92-1.00. The [0.30,0.78] band isolates play_call from both (holds on the
    #     broadcast source too: play_call 0.44-0.60, live 0.03-0.16, replay 0.20-0.25).
    #   green_low — fraction of GREEN field pixels in the lower-middle "card band".
    #     Play-call cards COVER the field (green_low ~0.00-0.02); a live field /
    #     coach-cam / gameplay view shows grass (green_low 0.81-0.87). Semantic and
    #     source-robust (green grass = live on any feed), and it defends against a
    #     dark live frame that lands in the dark_frac band (its field still reads green).
    # Rule: play_call  <=>  0.30 <= dark_frac <= 0.78  AND  green_low < GREEN_LOW_MAX.
    # Verified 0 FP / 0 FN across 15 labelled PS5 frames (5 play-call: def-cards,
    # formation-picker, off-select; 5 live: coach-cam, pre-snap field, gameplay;
    # 5 menu/pause/black). NOTE: the coach-cam coverage view is correctly LIVE (green
    # field) — v0.3 coverage reads on the live path, gated by the play_call->live
    # _presnap transition, so play-call MUST be recognised first (this fix).
    DARK_FRAC_MIN = 0.30
    DARK_FRAC_MAX = 0.78
    GREEN_LOW_MAX = 0.30     # play_call ~0.02, live ~0.85 — wide margin
    DARK_LUMA = 50           # pixel < this counts toward dark_frac
    DARK_FRAC_STRIDE = 4     # subsample the frame for the features (16x fewer pixels)
    # Lower-middle "card band" (fractional y) where play-call cards sit over — vs —
    # where the field grass shows on a live/coach-cam view.
    CARD_BAND = (0.55, 0.86)

    def __init__(self, hud_regions_path: str | Path | None = None) -> None:
        # hud_regions_path kept for signature compatibility; the detector's
        # features are fixed (detector calibration, not HUD-region coords).
        pass

    def features(self, frame: np.ndarray) -> dict[str, float]:
        """The two cheap features — exposed for calibration / debugging."""
        gray = frame if frame.ndim == 2 else cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        s = self.DARK_FRAC_STRIDE
        dark_frac = float((gray[::s, ::s] < self.DARK_LUMA).mean())
        # green_low needs colour; a grayscale frame (tests) reports no field so it
        # never false-positives play_call on green alone (dark_frac still gates).
        if frame.ndim == 3:
            h = frame.shape[0]
            y0, y1 = int(h * self.CARD_BAND[0]), int(h * self.CARD_BAND[1])
            band = frame[y0:y1:s, ::s]
            b = band[:, :, 0].astype(np.int32)
            g = band[:, :, 1].astype(np.int32)
            r = band[:, :, 2].astype(np.int32)
            green = (g > 60) & (g > b + 15) & (g > r + 10)
            green_low = float(green.mean()) if green.size else 1.0
        else:
            green_low = 1.0
        return {"dark_frac": dark_frac, "green_low": green_low}

    def detect(self, frame: np.ndarray) -> HudContext:
        """Classify a frame's HUD context in ~0.1ms (no OCR)."""
        f = self.features(frame)
        if (self.DARK_FRAC_MIN <= f["dark_frac"] <= self.DARK_FRAC_MAX
                and f["green_low"] < self.GREEN_LOW_MAX):
            return HudContext.PLAY_CALL
        return HudContext.LIVE_GAMEPLAY
