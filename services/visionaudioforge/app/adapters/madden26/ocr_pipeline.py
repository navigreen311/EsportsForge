"""Madden 26 OCR pipeline — score / clock / down / distance / field position.

Uses EasyOCR (pure-Python) since Tesseract isn't installable without admin
on the dev machine. EasyOCR is heavier on first run (downloads ~64MB model)
but produces equivalent accuracy on HUD digits.

Region cropping reads coords from hud_regions.json. The pipeline is called
from Madden26Adapter.process_frame on every frame; cache hits are dominant
in steady state (clock and down/distance change rarely between frames).
"""

from __future__ import annotations

import json
import logging
import re
import threading
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import cv2
import numpy as np

logger = logging.getLogger("vaf.adapters.madden26.ocr")

# EasyOCR is loaded lazily on first call — model download + GPU init can
# block ~30 s on cold start.
_easyocr_reader = None
_easyocr_lock = threading.Lock()


def _get_reader():
    global _easyocr_reader
    if _easyocr_reader is None:
        with _easyocr_lock:
            if _easyocr_reader is None:
                import easyocr  # imported lazily so unit tests that don't
                                # need OCR don't pay the cost
                _easyocr_reader = easyocr.Reader(["en"], gpu=False, verbose=False)
                logger.info("easyocr_loaded")
    return _easyocr_reader


@dataclass(frozen=True)
class OCRReading:
    value: str | None
    confidence: float


@dataclass(frozen=True)
class OCRSnapshot:
    score_home: int | None
    score_away: int | None
    quarter: int | None
    clock: str | None
    down: int | None
    distance: int | None
    field_position: str | None
    team_home_abbr: str | None
    team_away_abbr: str | None
    confidence_overall: float


# Field-position pattern: "OWN 35", "OPP 22", "MIDFIELD".
_FIELD_POS_RE = re.compile(r"^(OWN|OPP|MIDFIELD)(?:\s+(\d{1,2}))?$")


def _crop(frame: np.ndarray, bbox: list[int]) -> np.ndarray:
    """Crop bbox=[x, y, w, h] from a 1080p-assumed frame."""
    x, y, w, h = bbox
    h_full, w_full = frame.shape[:2]
    if (h_full, w_full) != (1080, 1920):
        # Resize-or-skip: scale bbox to actual frame.
        sx, sy = w_full / 1920.0, h_full / 1080.0
        x, y, w, h = int(x * sx), int(y * sy), int(w * sx), int(h * sy)
    return frame[y : y + h, x : x + w]


def _read_text(img: np.ndarray, allowlist: str | None = None) -> tuple[str, float]:
    """Run EasyOCR on a region. Returns (concatenated text, mean confidence)."""
    if img.size == 0:
        return ("", 0.0)
    reader = _get_reader()
    # Upscale 3x — EasyOCR handles small text better with more pixels.
    scaled = cv2.resize(img, None, fx=3.0, fy=3.0, interpolation=cv2.INTER_CUBIC)
    results = reader.readtext(
        scaled,
        allowlist=allowlist,
        paragraph=False,
        detail=1,
    )
    if not results:
        return ("", 0.0)
    texts: list[str] = []
    confs: list[float] = []
    for _bbox, text, conf in results:
        texts.append(str(text).strip())
        confs.append(float(conf))
    return (" ".join(texts).strip(), sum(confs) / len(confs))


def _parse_int(text: str, lo: int, hi: int) -> tuple[int | None, float]:
    """Validate text → int within [lo, hi]. Returns (value, retain-confidence)."""
    if not text:
        return (None, 0.0)
    digits = re.sub(r"[^0-9]", "", text)
    if not digits:
        return (None, 0.0)
    try:
        v = int(digits)
    except ValueError:
        return (None, 0.0)
    if not (lo <= v <= hi):
        return (None, 0.0)
    return (v, 1.0)


class OCRPipeline:
    """Loads HUD region map at construction; reads frames by-region."""

    def __init__(self, hud_regions_path: str | Path | None = None) -> None:
        if hud_regions_path is None:
            hud_regions_path = Path(__file__).parent / "hud_regions.json"
        with open(hud_regions_path, "r", encoding="utf-8") as f:
            self.regions: dict[str, Any] = json.load(f)["regions"]

    def read_frame(self, frame: np.ndarray) -> OCRSnapshot:
        """Read every HUD region. Returns a snapshot."""
        scoreboard = self.regions["scoreboard"]["subregions"]
        dnd = self.regions["down_distance"]["subregions"]

        # Numeric reads.
        s_home_text, s_home_conf = _read_text(_crop(frame, scoreboard["score_home"]), "0123456789")
        s_away_text, s_away_conf = _read_text(_crop(frame, scoreboard["score_away"]), "0123456789")
        q_text, q_conf = _read_text(_crop(frame, scoreboard["quarter"]), "0123456789")
        clock_text, clock_conf = _read_text(_crop(frame, scoreboard["clock"]), "0123456789:")
        down_text, down_conf = _read_text(_crop(frame, dnd["down"]), "0123456789")
        dist_text, dist_conf = _read_text(_crop(frame, dnd["distance"]), "0123456789&")

        score_home_v, _ = _parse_int(s_home_text, 0, 199)
        score_away_v, _ = _parse_int(s_away_text, 0, 199)
        quarter_v, _ = _parse_int(q_text, 1, 5)
        down_v, _ = _parse_int(down_text, 1, 4)
        # Distance can be e.g. "& 7" — strip & and space.
        dist_clean = re.sub(r"[^0-9]", "", dist_text)
        distance_v, _ = _parse_int(dist_clean, 0, 99)

        # Clock — accept "M:SS" or "MM:SS".
        clock_v: str | None = None
        m = re.match(r"(\d{1,2}):(\d{2})", clock_text.strip())
        if m:
            mins, secs = int(m.group(1)), int(m.group(2))
            if 0 <= mins <= 99 and 0 <= secs <= 59:
                clock_v = f"{mins}:{secs:02d}"

        # Field position.
        fp_text, fp_conf = _read_text(_crop(frame, dnd["field_position"]))
        fp_v: str | None = None
        m = _FIELD_POS_RE.match(fp_text.upper().strip())
        if m:
            label, num = m.group(1), m.group(2)
            fp_v = label if num is None else f"{label}_{num}"

        # Team abbreviations.
        ha_text, ha_conf = _read_text(
            _crop(frame, scoreboard["team_home_abbr"]),
            "ABCDEFGHIJKLMNOPQRSTUVWXYZ",
        )
        aa_text, aa_conf = _read_text(
            _crop(frame, scoreboard["team_away_abbr"]),
            "ABCDEFGHIJKLMNOPQRSTUVWXYZ",
        )
        home_abbr = ha_text.upper().strip() or None
        away_abbr = aa_text.upper().strip() or None

        # Aggregate confidence — average of the per-region confidences. Used
        # by the assembler as the event-level confidence floor.
        confs = [
            c for c in [s_home_conf, s_away_conf, q_conf, clock_conf, down_conf, fp_conf]
            if c > 0
        ]
        overall = sum(confs) / len(confs) if confs else 0.0

        return OCRSnapshot(
            score_home=score_home_v,
            score_away=score_away_v,
            quarter=quarter_v,
            clock=clock_v,
            down=down_v,
            distance=distance_v,
            field_position=fp_v,
            team_home_abbr=home_abbr,
            team_away_abbr=away_abbr,
            confidence_overall=round(overall, 3),
        )
