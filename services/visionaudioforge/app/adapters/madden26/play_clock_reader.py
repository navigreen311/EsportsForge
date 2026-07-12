"""Madden 26 play-clock reader — a small 2-head CNN (M5b follow-up).

The play-clock is the "third polarity": DARK digits on a BRIGHT white box with a
colon and a chrome bar. The patch-NCC technique that reads the white-on-dark
fields (clock / distance / quarter / down) was RULED OUT here — the constant box
dominates the NCC and per-digit segmentation doesn't generalise across clips
(see docs/phase-completions/play-clock-reader-findings.md). A CNN *learns* to
attend to the digit region and ignore the constant box, which is exactly the
failure mode that sinks NCC.

The net is a 2-head classifier (tens 0-4, ones 0-9) on the whole-value patch,
trained on ~5k auto-labelled patches from 8 live capture clips (countdown-
monotonicity labelling). Held-out-by-clip it reads **72% exact / 82% within-±1**
per frame — 2x the 40% NCC baseline. That is best-effort (the field is
informational and smoothed downstream), NOT a precise reader. Its high-value use
is the snap-detector reset-vs-resume discriminator, where only the DIRECTION of
change matters (reset toward :40 vs resume counting down): held-out that decision
is **94%** accurate — robust because the reset gap (10-25) dwarfs per-read noise.

Inference is ONNX via onnxruntime (the service does not import torch at runtime,
ADR note in requirements.txt). If onnxruntime or the model file is absent the
reader load returns None and the caller falls back to a null play_clock —
graceful, same contract as the patch-NCC template readers.
"""

from __future__ import annotations

import logging
from pathlib import Path

import cv2
import numpy as np

logger = logging.getLogger("vaf.adapters.madden26.play_clock")

# The white two-digit value box in absolute 1920x1080 v2.3.0-live coords. This is
# TIGHTER and lower than the hud_regions `play_clock` zone [1450,1002,96,44],
# which clips the digit bottoms (the box extends below it) — measured off the
# live refs by rendering the crop back onto the frame.
_VALBOX = (1448, 1022, 88, 38)
_IN_H, _IN_W = 48, 96          # net input size (must match training)
_TAU = 0.55                    # min per-digit softmax confidence to emit a value
_BOX_MIN_MEAN = 110.0          # min crop brightness => the white box is present
_RED_MAX = 0.06                # max red fraction => not a delay-of-game red clock


def _softmax(x: np.ndarray) -> np.ndarray:
    e = np.exp(x - x.max(axis=-1, keepdims=True))
    return e / e.sum(axis=-1, keepdims=True)


class PlayClockReader:
    """ONNX 2-head play-clock digit reader. Construct via :meth:`load` (returns
    None if onnxruntime or the model is unavailable — never raises at import)."""

    def __init__(self, session: object) -> None:
        self._sess = session

    @classmethod
    def load(cls, onnx_path: str | Path) -> "PlayClockReader | None":
        p = Path(onnx_path)
        if not p.exists():
            return None
        try:
            import onnxruntime as ort  # lazy: runtime-only, may be absent in some envs

            sess = ort.InferenceSession(str(p), providers=["CPUExecutionProvider"])
            return cls(sess)
        except Exception:  # onnxruntime missing / bad model -> graceful null reader
            logger.exception("play_clock_reader_load_failed")
            return None

    @staticmethod
    def _crop(frame: np.ndarray) -> np.ndarray:
        x, y, w, h = _VALBOX
        return frame[y : y + h, x : x + w]

    @staticmethod
    def _is_white_box(crop: np.ndarray) -> bool:
        """A live white play-clock box is bright; grass / dark HUD / absent box is
        not. Also reject a red (delay-of-game) clock — its own single digit is not
        what this 2-digit reader was trained on."""
        if crop is None or crop.size == 0:
            return False
        gray = cv2.cvtColor(crop, cv2.COLOR_BGR2GRAY)
        if float(gray.mean()) < _BOX_MIN_MEAN:
            return False
        roi = crop.astype(int)
        b, g, r = roi[..., 0], roi[..., 1], roi[..., 2]
        red = float(((r > g + 40) & (r > b + 40) & (r > 90)).mean())
        return red < _RED_MAX

    def read_value(self, frame: np.ndarray) -> tuple[int | None, float]:
        """Read the play-clock value. Returns ``(value, confidence)`` with value in
        0-40, or ``(None, 0.0)`` when the box is absent/red or the net abstains
        (per-digit softmax below tau). Never fabricates."""
        crop = self._crop(frame)
        if not self._is_white_box(crop):
            return None, 0.0
        gray = cv2.cvtColor(crop, cv2.COLOR_BGR2GRAY)
        x = cv2.resize(gray, (_IN_W, _IN_H)).astype(np.float32) / 255.0
        x = x[None, None, :, :]
        tens, ones = self._sess.run(None, {"patch": x})  # type: ignore[attr-defined]
        pt, po = _softmax(tens[0]), _softmax(ones[0])
        conf = float(min(pt.max(), po.max()))
        if conf < _TAU:
            return None, conf
        return int(pt.argmax()) * 10 + int(po.argmax()), conf
