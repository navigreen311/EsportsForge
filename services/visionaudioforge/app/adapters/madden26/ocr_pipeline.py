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
    play_clock: str | None
    down: int | None
    distance: int | None
    field_position: str | None
    team_home_abbr: str | None
    team_away_abbr: str | None
    confidence_overall: float


# Madden 26 displays ordinals ("1ST", "2ND", "3RD", "4TH") in quarter
# and down panels — not bare digits. Map ordinal text → int.
# After _normalise_ocr_chars, "IST" → "1ST", "2ND" stays "2ND" (no I/L/O).
_ORDINAL_MAP = {
    "1ST": 1, "2ND": 2, "3RD": 3, "4TH": 4, "5TH": 5,
    # Common EasyOCR misreads on the same panels
    "1S": 1, "2N": 2, "3R": 3, "4T": 4,
    # v2.1.0 centered-scorebug font (M5c sub-task 1b): the down/quarter
    # ordinals render in a tighter italic where "2"->"Z" and "4"->"A"
    # are the dominant single-glyph confusions ("2ND"->"ZND", "4TH"->"ATR").
    "ZND": 2, "ZN": 2, "ATH": 4, "ATR": 4, "ATF": 4, "AT": 4,
}

# Madden 26 field-position panel renders "▲<yards>" with a triangle
# arrow indicator pointing toward the team's own end zone. EasyOCR
# typically reads the triangle as a "4" / "▲" / extra digit, so we
# anchor on the TRAILING 1-2 digits of the read (the actual yard
# number is always rightmost).
_FIELD_POS_DIGITS_RE = re.compile(r"(\d{1,2})\s*$")
# Madden 26 down/distance panel renders "1ST & 10" / "2ND & 7" /
# "KICKOFF" / "PUNT". Distance is the digits after "&" / "AND".
_DISTANCE_RE = re.compile(r"(?:&|AND)\s*(\d{1,2})")


def _parse_ordinal_to_int(text: str, lo: int, hi: int) -> int | None:
    """Map '1ST', '2ND', etc. to int. Madden's HUD font confuses '1'
    with '7' and 'I'/'L' under EasyOCR; try multiple substitution
    variants and accept the first that parses to an in-range value.

    Variants tried, in order:
      1. Raw text as-is.
      2. Normalised: I/L→1, O/Q→0.
      3. Normalised + 7→1 (Madden's '1' often reads as '7').
    Then fall back to: leading digit, then trailing digit.
    """
    if not text:
        return None
    variants = [
        text,
        _normalise_ocr_chars(text),
        _normalise_ocr_chars(text).replace("7", "1"),
    ]
    for variant in variants:
        upper = re.sub(r"\s+", "", variant.upper())
        if upper in _ORDINAL_MAP and lo <= _ORDINAL_MAP[upper] <= hi:
            return _ORDINAL_MAP[upper]
        # Leading-digit fallback (e.g., "1ST" → "1")
        m_lead = re.match(r"^(\d)", upper)
        if m_lead:
            try:
                v = int(m_lead.group(1))
            except ValueError:
                v = None
            if v is not None and lo <= v <= hi:
                return v
        # Trailing-digit fallback (e.g., "751" → "1" after 7→1 fails to
        # produce "1ST" but the trailing "1" is what we want).
        m_trail = re.search(r"(\d)$", upper)
        if m_trail:
            try:
                v = int(m_trail.group(1))
            except ValueError:
                v = None
            if v is not None and lo <= v <= hi:
                return v
    return None


def _parse_distance(text: str) -> int | None:
    """Extract digits after '&' or 'AND'. Returns None on KICKOFF/PUNT.

    Madden's digit-confusion (1↔7, 0↔8) means '& 10' often reads as
    '7 870' or similar. Tries variant substitutions, accepts the
    first in-range result. Realistic distance is 1–25 yards.
    """
    if not text:
        return None
    variants = [
        text.upper(),
        text.upper().replace("7", "1"),
        text.upper().replace("8", "0"),
        text.upper().replace("7", "1").replace("8", "0"),
    ]
    for variant in variants:
        m = _DISTANCE_RE.search(variant)
        if m:
            try:
                v = int(m.group(1))
            except ValueError:
                continue
            if 0 <= v <= 99:
                return v
        # Madden's distance often reads with the '&' lost — try trailing
        # digits after a space or as a standalone digit pair.
        trailing = re.search(r"(\d{1,2})\s*$", variant)
        if trailing:
            try:
                v = int(trailing.group(1))
            except ValueError:
                continue
            if 1 <= v <= 25:  # tighter range for "trailing digit"
                return v
    return None


def _parse_clock(text: str) -> str | None:
    """Parse 'M:SS' or 'MM:SS' clock. Tolerates 1↔7 and missing colon.

    Variants:
      1. As-is.
      2. 7→1 substitution.
      3. Digits-only (insert colon between minute and seconds).
    """
    if not text:
        return None
    candidates = [
        text.strip(),
        text.strip().replace("7", "1"),
    ]
    # NFL quarter is 15 minutes max, so reject reads with mins > 15.
    for variant in candidates:
        m = re.match(r"(\d{1,2}):(\d{2})", variant)
        if m:
            mins, secs = int(m.group(1)), int(m.group(2))
            if 0 <= mins <= 15 and 0 <= secs <= 59:
                return f"{mins}:{secs:02d}"
    # No colon? EasyOCR sometimes drops the colon AND inserts a stray
    # digit. Take first-digit-as-minute + last-2-digits-as-seconds —
    # works even when the OCR returns 4 digits "MXSS" where X is noise.
    for variant in candidates:
        digits = re.sub(r"[^0-9]", "", variant)
        if len(digits) >= 3:
            mins_s = digits[0]
            secs_s = digits[-2:]
            try:
                mins, secs = int(mins_s), int(secs_s)
            except ValueError:
                continue
            if 0 <= mins <= 15 and 0 <= secs <= 59:
                return f"{mins}:{secs:02d}"
    return None


def _parse_play_clock(text: str) -> str | None:
    """Parse Madden play clock — typically '00'-'40', or '--' pre-snap.

    Variants:
      1. Digits only as-is.
      2. With 7→1 substitution.
      3. With 8→0 substitution.
      4. Both substitutions.
    Falls back to trailing 1-2 digits (Madden HUD often picks up the
    leading panel boundary as a stray digit).
    """
    if not text:
        return None
    # Prefer 7→1 first (Madden's '1' often reads as '7'), then raw.
    # Skip single-digit fallback — Madden play clock is always 2-digit
    # display, so a 1-digit read is unreliable.
    sub_variants = [
        text.replace("7", "1"),
        text,
    ]
    for var in sub_variants:
        digits = re.sub(r"[^0-9]", "", var)
        if len(digits) < 2:
            continue
        # Trailing 2 digits: "812" → "12", "828" → "28".
        tail = digits[-2:]
        try:
            v = int(tail)
            if 0 <= v <= 40:
                return str(v)
        except ValueError:
            continue
    return None


def _parse_field_position(text: str) -> str | None:
    """Madden 26 numeric format. Returns '+<n>' on a successful read.

    EasyOCR commonly reads the triangle glyph as a leading digit (e.g.,
    "▲47" → "447"), so we anchor on the trailing 1–2 digits. The
    yard number itself is always 0–50 (own/opp halves of the field).
    """
    if not text:
        return None
    cleaned = text.strip().upper()
    m = _FIELD_POS_DIGITS_RE.search(cleaned)
    if m:
        try:
            v = int(m.group(1))
        except ValueError:
            return None
        # Madden 26 displays 0-99 (own end zone = 0, opponent = 99).
        if 0 <= v <= 99:
            return f"+{v}"
    return None


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
    """Run EasyOCR on a region. Returns (concatenated text, mean confidence).

    Preprocessing pipeline (per M4.5 calibration findings):
      1. Convert to grayscale.
      2. CLAHE contrast enhancement — preserves stroke shape (which Otsu
         threshold mangled — "1" became "7"-like after binarization).
      3. Invert if the text is light-on-dark (HUD panels typically are).
      4. Upscale 5× via cubic interpolation. EasyOCR struggles below
         ~150 px-tall text; 5× of a 40 px crop = 200 px which gives
         the digit recognizer enough strokes to disambiguate "1" / "7" / "I".
    """
    if img.size == 0:
        return ("", 0.0)
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY) if img.ndim == 3 else img
    # Invert if dark-text-on-light isn't the natural orientation.
    if gray.mean() < 127:
        gray = cv2.bitwise_not(gray)
    # CLAHE contrast enhancement keeps stroke detail, unlike threshold.
    clahe = cv2.createCLAHE(clipLimit=2.5, tileGridSize=(4, 4))
    enhanced = clahe.apply(gray)
    scaled = cv2.resize(enhanced, None, fx=5.0, fy=5.0, interpolation=cv2.INTER_CUBIC)
    reader = _get_reader()
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


def _normalise_ocr_chars(text: str) -> str:
    """Map common EasyOCR character confusions back to expected chars.
    Applied before ordinal/digit parsing — e.g., '1ST' frequently reads
    as 'IST' or 'lST' on small HUD crops."""
    if not text:
        return text
    return (
        text.upper()
        .replace("I", "1")
        .replace("L", "1")
        .replace("O", "0")
        .replace("Q", "0")
    )


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


# v2.1.0 centered-scorebug score glyphs read freely (no allowlist). The
# large italic numerals have stable single-glyph confusions: "0"->U/O/Q,
# "1"->I/L, "2"->Z, "5"->S, "6"->G, "7"->T, "8"->B. Scores are pure
# numbers in [0, 199] so this aggressive digit-substitution is safe here
# (it is NOT applied to alphanumeric fields like team abbreviations).
_SCORE_GLYPH_SUB = str.maketrans(
    {"U": "0", "O": "0", "Q": "0", "D": "0", "I": "1", "L": "1",
     "Z": "2", "S": "5", "G": "6", "T": "7", "B": "8", "A": "4"}
)


def _parse_score(text: str) -> int | None:
    """Map stylised score glyphs to digits, then parse an int in [0, 199]."""
    if not text:
        return None
    digits = re.sub(r"[^0-9]", "", text.upper().translate(_SCORE_GLYPH_SUB))
    if not digits or len(digits) > 3:
        return None
    v = int(digits)
    return v if 0 <= v <= 199 else None


class OCRPipeline:
    """Loads HUD region map at construction; reads frames by-region."""

    def __init__(self, hud_regions_path: str | Path | None = None) -> None:
        if hud_regions_path is None:
            hud_regions_path = Path(__file__).parent / "hud_regions.json"
        with open(hud_regions_path, "r", encoding="utf-8") as f:
            self.regions: dict[str, Any] = json.load(f)["regions"]

    def read_frame(self, frame: np.ndarray) -> OCRSnapshot:
        """Read every HUD region. Returns a snapshot.

        Per M4.5 calibration:
          - quarter/down panels render ordinals ("1ST", "2ND") not bare
            digits. Read without an allowlist; map via _parse_ordinal_to_int.
          - distance panel renders "& <n>". Allowlist permits "&" + digits;
            extracted via _parse_distance.
          - field_position panel renders "▲<n>" or "<n>". Read freely;
            extracted via _parse_field_position.
          - play_clock panel renders "<n>" or "--" (pre-snap). Parsed
            same way as score numbers.
        """
        scoreboard = self.regions["scoreboard"]["subregions"]
        dnd = self.regions["down_distance"]["subregions"]

        # Scores — read WITHOUT a digit allowlist. The v2.1.0 centered
        # scorebug renders "0" as a ring that EasyOCR recognises as "U"/"O";
        # a digit-only allowlist drops it entirely. Read freely and let
        # _parse_score map the stylised glyphs back to digits.
        s_home_text, s_home_conf = _read_text(_crop(frame, scoreboard["score_home"]))
        s_away_text, s_away_conf = _read_text(_crop(frame, scoreboard["score_away"]))
        clock_text, clock_conf = _read_text(_crop(frame, scoreboard["clock"]), "0123456789:")

        # Quarter / down — ordinal text. No allowlist (EasyOCR drops
        # results when allowlist excludes letters in "1ST"/"2ND" etc.).
        q_text, q_conf = _read_text(_crop(frame, scoreboard["quarter"]))
        down_text, down_conf = _read_text(_crop(frame, dnd["down"]))

        # Distance — read freely; regex pulls digits after "&"/"AND".
        dist_text, dist_conf = _read_text(_crop(frame, dnd["distance"]))

        # Play clock — digit-only; can be "--" → null.
        pc_text, pc_conf = _read_text(_crop(frame, dnd["play_clock"]), "0123456789")

        # Field position — Madden 26 numeric form, possibly preceded by
        # an arrow glyph. Read freely so EasyOCR captures the glyph as
        # noise and our regex pulls the digits.
        fp_text, fp_conf = _read_text(_crop(frame, dnd["field_position"]))

        score_home_v = _parse_score(s_home_text)
        score_away_v = _parse_score(s_away_text)
        quarter_v = _parse_ordinal_to_int(q_text, 1, 5)
        down_v = _parse_ordinal_to_int(down_text, 1, 4)
        distance_v = _parse_distance(dist_text)
        play_clock_v = _parse_play_clock(pc_text)
        clock_v = _parse_clock(clock_text)
        fp_v = _parse_field_position(fp_text)

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

        # Aggregate confidence — average of the per-region confidences.
        confs = [
            c for c in [s_home_conf, s_away_conf, q_conf, clock_conf,
                        down_conf, dist_conf, pc_conf, fp_conf,
                        ha_conf, aa_conf]
            if c > 0
        ]
        overall = sum(confs) / len(confs) if confs else 0.0

        return OCRSnapshot(
            score_home=score_home_v,
            score_away=score_away_v,
            quarter=quarter_v,
            clock=clock_v,
            play_clock=play_clock_v,
            down=down_v,
            distance=distance_v,
            field_position=fp_v,
            team_home_abbr=home_abbr,
            team_away_abbr=away_abbr,
            confidence_overall=round(overall, 3),
        )
