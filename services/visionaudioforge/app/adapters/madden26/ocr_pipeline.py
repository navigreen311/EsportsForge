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
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from .coverage_classifier import CoverageReading

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
                # imported lazily so unit tests that don't need OCR don't pay the cost
                import easyocr
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


# This HUD's italic numeral font confuses glyphs on EasyOCR. Substitutions
# observed on the live broadcast bar (v2.3.0-live, ~9 clean gameplay frames):
#   2->Z, 1->7, 5->S, 0->O, 8->B, 6->G, 7->T, and '&' commonly reads as a
#   leading '8'. INFERRED FROM A SMALL SAMPLE — an unseen digit could need more;
#   the live run is the real test.
_HUD_DIGIT_SUB = str.maketrans(
    {"Z": "2", "S": "5", "I": "1", "L": "1", "O": "0", "B": "8", "G": "6", "T": "7"}
)
_ORD_TOKEN_RE = re.compile(r"([0-9ZSILOB])?\s*(ST|ND|RD|TH)")
_ORD_SUFFIX = {"ST": 1, "ND": 2, "RD": 3, "TH": 4}


def _ord_to_int(lead: str | None, suffix: str, lo: int, hi: int) -> int | None:
    """Map an ordinal token (leading glyph + ST/ND/RD/TH) to an int in [lo, hi].
    Prefers the leading digit (glyph-corrected, 7->1); falls back to the suffix."""
    val = None
    if lead:
        d = lead.translate(_HUD_DIGIT_SUB).replace("7", "1")
        try:
            val = int(d)
        except ValueError:
            val = None
    if val is None:
        val = _ORD_SUFFIX.get(suffix)
    return val if (val is not None and lo <= val <= hi) else None


def _parse_right_cluster(text: str) -> dict:
    """Positionally parse the WIDE right-cluster HUD box.

    On the live PS5 broadcast bar the cluster reads (left->right):
        <quarter-ordinal> <clock> [<play_clock>] <down-ordinal> & <distance>
    e.g. '2nd 1:02 :32 2ND & 6'. Tight per-element boxes don't OCR on this bar
    (EasyOCR's detector needs the wider context), so we read the whole cluster
    once and split it on the TWO ordinal tokens: the first is the quarter, the
    last is the down; the clock sits between them, the distance after the down.
    Returns {quarter, clock, play_clock, down, distance} (any may be None).
    """
    out: dict[str, Any] = {"quarter": None, "clock": None, "play_clock": None,
                           "down": None, "distance": None}
    if not text:
        return out
    up = text.upper()
    ords = list(_ORD_TOKEN_RE.finditer(up))
    if ords:
        out["quarter"] = _ord_to_int(ords[0].group(1), ords[0].group(2), 1, 5)
        if len(ords) > 1:
            out["down"] = _ord_to_int(ords[-1].group(1), ords[-1].group(2), 1, 4)
    down_tok = ords[-1] if len(ords) > 1 else None
    mid = up[ords[0].end():down_tok.start()] if (ords and down_tok) else (up[ords[0].end():] if ords else up)
    tail = up[down_tok.end():] if down_tok else ""

    # clock: first 3-4 char digit-ish run in the middle. This HUD reads '1' as
    # '7' pervasively, so apply 7->1 (consistent with _parse_play_clock/
    # _parse_distance). AMBIGUITY: a genuine 7-minute/second collides — biased to
    # '1' from a 1-heavy sample; the live run (known clock) is the real test.
    for grp in re.findall(r"[0-9OISLBZ][0-9OISLBZ:.]{1,3}[0-9OISLBZ]", mid):
        c = _parse_clock(grp.translate(_HUD_DIGIT_SUB).replace("7", "1"))
        if c:
            out["clock"] = c
            break

    # distance: after the down ordinal. Two glyph quirks on this HUD:
    #   - '&' reads as EITHER a literal '&' ('& 6') OR a leading '8' ('84' = '&4').
    #   - '1' reads as '7' ('& 10' -> '&70').
    # Realistic distance is 1-25, so a 2-digit value that's impossible (>25)
    # disambiguates: leading '8' was the '&' glyph; leading '7' was a '1'.
    if any(w in up for w in ("KICK", "PUNT", "GOAL")):
        out["distance"] = None
    else:
        dt = tail.translate(_HUD_DIGIT_SUB)
        m = re.search(r"(\d{1,2})\s*$", dt.strip()) or re.search(r"(\d{1,2})", dt)
        if m:
            ds = m.group(1)
            if len(ds) == 2 and ds[0] == "8":       # leading '8' = the '&' glyph
                ds = ds[1]
            if len(ds) == 2 and ds[0] == "7" and int(ds) > 25:  # '7X' impossible -> '1X'
                ds = "1" + ds[1]
            try:
                v = int(ds)
                if 1 <= v <= 25:
                    out["distance"] = v
            except ValueError:
                pass

    # play_clock: best-effort, least reliable (a 2-digit run in mid that isn't
    # the clock). A null play_clock is acceptable — don't force a bad value.
    clock_digits = re.sub(r"\D", "", out["clock"] or "")
    for grp in re.findall(r"(?<![0-9OISLBZ])([0-9OISLBZ]{2})(?![0-9OISLBZ])", mid):
        cand = grp.translate(_HUD_DIGIT_SUB)
        if cand == clock_digits[-2:]:
            continue
        pc = _parse_play_clock(cand)
        if pc is not None:
            out["play_clock"] = pc
            break
    return out


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


def _parse_scores_pair(text: str) -> tuple[int | None, int | None]:
    """Split a combined '<home> x <home>' broadcast-bar score box into
    (home, away). The live PS5 bar shows the two scores either side of an 'x'
    separator (e.g. '7 x 7', '14  10'). EasyOCR drops the isolated italic score
    glyph, so reading the wider pair box gives the detector more to latch onto
    (v2.3.0-live, E5). Returns (None, None) when fewer than two numbers survive
    — the caller then degrades scores to null."""
    if not text:
        return (None, None)
    subbed = text.upper().translate(_SCORE_GLYPH_SUB)
    nums = re.findall(r"\d{1,3}", subbed)
    if len(nums) >= 2:
        home, away = int(nums[0]), int(nums[-1])
        if 0 <= home <= 199 and 0 <= away <= 199:
            return (home, away)
    return (None, None)


# --- Play-call overlay formation-name reading (M5c sub-task 4 pivot, ADR 0014) ---
# Madden's play-call banner reads "<Formation Name> - N Plays" (e.g. "Trips TE
# Offset - 12 Plays"). The full name is the primary label; the canonical-8 family
# is derived from the LEADING family word. Keyword list tolerates the OCR char
# errors seen in feasibility (Trips->'rips', Doubles->'Doubies', Wing->'Wving').
_FORMATION_CANON: tuple[tuple[str, str], ...] = (
    ("TRIP", "shotgun_trips"), ("RIPS", "shotgun_trips"),
    ("BUNCH", "shotgun_bunch"), ("BUNC", "shotgun_bunch"),
    ("EMPTY", "shotgun_empty"), ("EMPT", "shotgun_empty"),
    ("DOUBLE", "shotgun_doubles"), ("DOUB", "shotgun_doubles"),
    ("ACE", "singleback_ace"),
    ("WING", "singleback_wing"), ("VING", "singleback_wing"),
    ("PRO", "i_form_pro"),
    ("STRONG", "pistol_strong"), ("STRON", "pistol_strong"),
)
# "N Plays" suffix — its presence is also the play-call-screen state signal.
_PLAYS_RE = re.compile(r"[-_]?\s*\d+\s*P[il1]ay", re.IGNORECASE)


def _parse_formation_name(text: str) -> str | None:
    """Strip the '- N Plays' suffix (and any trailing play-art digits) from the
    banner OCR to isolate the formation name."""
    if not text:
        return None
    name = _PLAYS_RE.split(text, 1)[0]
    name = re.sub(r"\s+\d.*$", "", name).strip(" -_")  # drop trailing stray digits
    return name or None


def _formation_to_canonical(name: str | None) -> str | None:
    """Map a play-call formation name to a canonical-8 family. Prefer the leading
    (family) word, then fall back to anywhere in the name."""
    if not name:
        return None
    up = name.upper()
    first = up.split()[0] if up.split() else ""
    for kw, fam in _FORMATION_CANON:
        if kw in first:
            return fam
    for kw, fam in _FORMATION_CANON:
        if kw in up:
            return fam
    return None


@dataclass(frozen=True)
class FormationNameReading:
    full_name: str | None      # e.g. "Trips TE Offset" (primary label)
    canonical: str | None      # e.g. "shotgun_trips" (secondary family tag)
    confidence: float
    is_play_call_screen: bool


@dataclass(frozen=True)
class DefensiveFrontReading:
    front: str | None          # canonical front, e.g. "3-4" / "Nickel" (v0.2)
    full_name: str | None      # raw card-subtitle text, e.g. "3-4 Under"
    confidence: float
    is_defensive_play_call: bool


class OCRPipeline:
    """Loads HUD region map at construction; reads frames by-region."""

    def __init__(self, hud_regions_path: str | Path | None = None) -> None:
        if hud_regions_path is None:
            hud_regions_path = Path(__file__).parent / "hud_regions.json"
        with open(hud_regions_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        # v2.2.0+ groups regions under hud_contexts (live_gameplay vs play_call);
        # v2.0/2.1 used a flat top-level "regions". Support both.
        contexts = data.get("hud_contexts")
        if contexts:
            self.regions: dict[str, Any] = contexts["live_gameplay"]["regions"]
            self.play_call_regions: dict[str, Any] = contexts.get("play_call", {}).get("regions", {})
        else:
            self.regions = data["regions"]
            self.play_call_regions = {}

        # Style-aware clock-SECONDS reader (patch-NCC). EasyOCR's blanket 7->1
        # clock sub collapses a real :17->:11 in the seconds; this reader replaces
        # ONLY the two seconds digits with abstain-over-guess. Minutes/colon stay
        # on the EasyOCR path. Loaded from the committed template set; if absent,
        # clock falls back to the pure-EasyOCR read (no crash).
        self._clock_seconds_reader = None
        tmpl = Path(__file__).parent / "digit_templates" / "gcsec_templates.npz"
        if tmpl.exists():
            try:
                from .digit_reader import GCSEC, DigitReader

                self._clock_seconds_reader = DigitReader.load(str(tmpl), GCSEC)
            except Exception:  # never let the reader break pipeline init
                logger.exception("clock_seconds_reader_load_failed")

        # Style-aware single-digit DISTANCE reader (patch-NCC). Fixes the ADR-0019
        # single-digit `1<->7` distance collision. Applied via an agreement-or-1<->7
        # gate (see _reader_distance) so it never fabricates on the confusable
        # 3/5/6/8 cluster. Loaded from the committed template set (digits 1-9).
        self._distance_reader = None
        dtmpl = Path(__file__).parent / "digit_templates" / "dist_templates.npz"
        if dtmpl.exists():
            try:
                from .digit_reader import DIST, DigitReader

                self._distance_reader = DigitReader.load(str(dtmpl), DIST)
            except Exception:
                logger.exception("distance_reader_load_failed")

        # Play-clock reader (dark-on-white 2-head CNN, ONNX). The patch-NCC
        # technique is ruled out for this polarity (findings doc); a small CNN
        # reads it best-effort. Loaded from the committed ONNX; if onnxruntime or
        # the model is absent the reader is None and play_clock stays null.
        from .play_clock_reader import PlayClockReader

        self._play_clock_reader = PlayClockReader.load(
            Path(__file__).parent / "models" / "play_clock_v0_2.onnx"
        )

    def warmup(self) -> None:
        """Force the EasyOCR model load + first-inference JIT now, so the ~2.8s cold
        start doesn't land on the first LIVE OCR frame (where it breaches the OCR-tier
        budget and drops that frame). Called at adapter construction, which runs before
        the dispatcher's per-frame budget window — so the cost is paid off the hot path.
        Guarded: a headless/CI env without easyocr just skips (OCR then warms lazily).
        Warms the EasyOCR model load + detector JIT (the ~2s one-time cost that would
        otherwise land on the first frame). NOTE: the per-read cost itself is large on CPU
        (formation ~765ms, coverage ~2200ms warm) and is bounded by max_ocr_tier_ms, not by
        this warmup — see the adapter budget."""
        try:
            _read_text(np.zeros((40, 120, 3), dtype=np.uint8))
            logger.info("ocr_warmed")
        except Exception:  # never let warmup break construction (e.g. easyocr absent)
            logger.debug("ocr_warmup_skipped", exc_info=True)

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

        # Scores — read WITHOUT a digit allowlist. The v2.1.0 centered
        # scorebug renders "0" as a ring that EasyOCR recognises as "U"/"O";
        # a digit-only allowlist drops it entirely. Read freely and let
        # _parse_score map the stylised glyphs back to digits.
        s_home_text, s_home_conf = _read_text(_crop(frame, scoreboard["score_home"]))
        s_away_text, s_away_conf = _read_text(_crop(frame, scoreboard["score_away"]))

        # Quarter / clock / down / distance — patch-NCC per-field reads, the SAME
        # readers the live read_fields path uses (v0.2 migration). This drops EasyOCR
        # from the digit cluster on the non-live path too, so both paths share the
        # ADR-0019 `1<->7` fix and neither re-introduces the ~694 ms wide-cluster
        # EasyOCR read. Each abstains -> None (never fabricate); if a template set is
        # absent the reader returns None (graceful, same as read_fields).
        quarter_v = self._read_leading_digit("quarter_digit", frame, 1, 5)
        clock_v = self._read_clock(frame)
        down_v = self._read_leading_digit("down_digit", frame, 1, 4)
        distance_v = self._read_distance(frame)

        # Play clock — dark-on-white 2-head CNN (patch-NCC ruled out for this
        # polarity; see docs/phase-completions/play-clock-reader-findings.md).
        # Abstains (None) when the box is absent/red or the net is unsure.
        play_clock_v = self._read_play_clock(frame)
        pc_conf = 0.0

        score_home_v = _parse_score(s_home_text)
        score_away_v = _parse_score(s_away_text)
        fp_v = None  # field_position parked for the live path (no analog on the bar)

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

        # Aggregate confidence — average of the per-region EasyOCR confidences
        # still on that path (scores / play_clock / abbrs). The patch-NCC cluster
        # fields (quarter/clock/down/distance) carry their own NCC margins, not an
        # EasyOCR confidence, so they don't contribute here.
        confs = [
            c for c in [s_home_conf, s_away_conf, pc_conf, ha_conf, aa_conf]
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

    _ABBR_ALLOW = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"

    def read_fields(self, frame: np.ndarray, fields) -> dict:
        """Read ONLY the requested HUD fields (the cadence-sampled path).

        v2.3.0-live broadcast-bar reads: scores come from the combined
        'scores_combined' pair box split into home/away (falling back to the
        individual boxes), and down+distance from the single merged
        'down_distance' box split into both. field_position is parked (no analog
        on the bar). Returns {field: parsed_value, ...} for the requested fields
        plus "_confidence" (mean over the read regions); unrequested fields are
        absent so the caller carries their last value forward.
        """
        want = set(fields)
        sb = self.regions["scoreboard"]["subregions"]
        out: dict = {}
        confs: list[float] = []

        def rd(bbox, allow=None):
            text, conf = _read_text(_crop(frame, bbox), allow)
            if conf > 0:
                confs.append(conf)
            return text

        # Scores — the large italic score numeral does NOT reliably OCR on this
        # bar (EasyOCR's detector drops it: a known-7-7 frame reads None/None, and
        # combined-box attempts return spurious 0/5 noise). Per the pre-agreed E5
        # stopping point: NULL scores rather than emit misreads; the payload is
        # nullable so SNAPSHOT still flows. BANKED FOLLOW-UP: scores need a
        # dedicated pass (digit template match / small classifier), not a glyph
        # tweak. _parse_scores_pair / scores_combined are kept for that revisit.
        if "score_home" in want:
            out["score_home"] = None
        if "score_away" in want:
            out["score_away"] = None
        if "team_home_abbr" in want:
            out["team_home_abbr"] = (rd(sb["team_home_abbr"], self._ABBR_ALLOW).upper().strip() or None)
        if "team_away_abbr" in want:
            out["team_away_abbr"] = (rd(sb["team_away_abbr"], self._ABBR_ALLOW).upper().strip() or None)
        # quarter / clock / play_clock / down / distance — read the WIDE right
        # cluster in ONE box and split positionally. Tight per-element crops don't
        # OCR on this broadcast bar (EasyOCR's detector needs the wider context);
        # the wide box reads at c~0.65-0.97 where the tight boxes read nothing.
        cluster_fields = ("quarter", "clock", "play_clock", "down", "distance")
        if want.intersection(cluster_fields):
            # v0.2 — patch-NCC PER-FIELD reads REPLACE the EasyOCR wide right_cluster
            # read (~694 ms/frame, the live throughput ceiling; ADR-0015 budget). Each
            # field reads from its own hud_regions zone with the shared white-on-dark
            # templates (quarter/down/minutes/seconds) or the distance templates.
            # EasyOCR is no longer called on the cluster. Every field abstains -> None
            # (never fabricate); the smoother/adapter carries the last good value.
            if "quarter" in want:
                out["quarter"] = self._read_leading_digit("quarter_digit", frame, 1, 5)
            if "clock" in want:
                out["clock"] = self._read_clock(frame)
            if "down" in want:
                out["down"] = self._read_leading_digit("down_digit", frame, 1, 4)
            if "distance" in want:
                out["distance"] = self._read_distance(frame)
            if "play_clock" in want:
                out["play_clock"] = self._read_play_clock(frame)  # dark-on-white 2-head CNN
        # field_position: parked for the live path (no analog on the broadcast bar).
        out["_confidence"] = round(sum(confs) / len(confs), 3) if confs else 0.0
        return out

    def _read_leading_digit(
        self, zone_name: str, frame: np.ndarray, lo: int, hi: int
    ) -> int | None:
        """Read one white-on-dark leading digit (quarter/down ordinal) with the
        shared clock-seconds templates. Returns int in [lo, hi] or None (abstain or
        out-of-range -> null; never fabricate)."""
        reader = self._clock_seconds_reader
        if reader is None:
            return None
        sb = self.regions["scoreboard"]["subregions"]
        dd = self.regions["down_distance"]["subregions"]
        sub = sb.get(zone_name) or dd.get(zone_name)
        if sub is None:
            return None
        s, _ = reader.read_patch(_crop(frame, sub), n_slots=1)
        if s is None:
            return None
        v = int(s)
        return v if lo <= v <= hi else None

    def _read_clock(self, frame: np.ndarray) -> str | None:
        """Read M:SS entirely from patch-NCC — minutes (1 digit) + seconds (2
        digits), both the shared white-on-dark templates. Either half abstaining ->
        None (null clock; the smoother carries the last good value)."""
        reader = self._clock_seconds_reader
        if reader is None:
            return None
        sb = self.regions["scoreboard"]["subregions"]
        if "clock_minutes" not in sb or "clock_seconds" not in sb:
            return None
        mins, _ = reader.read_patch(_crop(frame, sb["clock_minutes"]), n_slots=1)
        secs, _ = reader.read_patch(_crop(frame, sb["clock_seconds"]), n_slots=2)
        if mins is None or secs is None:
            return None
        m = int(mins)
        if not 0 <= m <= 15:
            return None
        return f"{m}:{secs}"

    def _read_distance(self, frame: np.ndarray) -> int | None:
        """Read the 1-2 digit distance (1-25) with the distance templates. With the
        EasyOCR cross-check gone, safety rests on abstain + the 1-25 validity rule;
        the `1<->7` fix is intrinsic (the reader reads the real glyph). Marginal or
        out-of-range -> None."""
        reader = self._distance_reader
        if reader is None:
            return None
        sub = self.regions["down_distance"]["subregions"].get("distance_field")
        if sub is None:
            return None
        v = self._read_1or2_digits(reader, _crop(frame, sub))
        return v if v is not None and 1 <= v <= 25 else None

    def _read_play_clock(self, frame: np.ndarray) -> str | None:
        """Read the dark-on-white play-clock (0-40) with the 2-head CNN. Returns the
        value as a string (OCRSnapshot stores play_clock as str) or None (reader
        absent, box not white/red, or the net abstains). Best-effort — the field is
        informational and smoothed downstream."""
        reader = self._play_clock_reader
        if reader is None:
            return None
        v, _conf = reader.read_value(frame)
        return None if v is None else str(v)

    def _read_1or2_digits(self, reader, patch: np.ndarray) -> int | None:
        """Read a 1- or 2-digit white-on-dark field. Isolate each digit as its own
        connected component (left-to-right) — component crops keep the narrow `1`
        undistorted, where an equal-column split would stretch it. Digits are the
        tallest blobs (chrome/noise is short). Read each with `reader`; any slot
        below tau/margin, or not 1-2 digit-sized blobs -> None (abstain)."""
        from .digit_reader import GH, GW, field_present_patch, is_corrupt_patch, vec

        if patch is None or patch.size == 0:
            return None
        if is_corrupt_patch(patch) or not field_present_patch(patch):
            return None
        g = cv2.cvtColor(patch, cv2.COLOR_BGR2GRAY)
        g = cv2.resize(g, None, fx=8, fy=8, interpolation=cv2.INTER_CUBIC)
        _, bw = cv2.threshold(g, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        bw = cv2.morphologyEx(bw, cv2.MORPH_OPEN, np.ones((3, 3), np.uint8))
        H, W = bw.shape
        bw[(bw > 0).sum(1) / W > 0.85, :] = 0
        num, lab, stats, _ = cv2.connectedComponentsWithStats((bw > 0).astype(np.uint8), 8)
        if num <= 1:
            return None
        max_h = max(int(stats[i, cv2.CC_STAT_HEIGHT]) for i in range(1, num))
        comps = sorted(
            (int(stats[i, cv2.CC_STAT_LEFT]), i)
            for i in range(1, num)
            if stats[i, cv2.CC_STAT_HEIGHT] > 0.5 * max_h
            and stats[i, cv2.CC_STAT_AREA] > 40
        )
        if not 1 <= len(comps) <= 2:
            return None
        digits = ""
        for _, i in comps:
            xs = np.where((lab == i).any(0))[0]
            ys = np.where((lab == i).any(1))[0]
            glyph = cv2.resize(
                g[ys[0] : ys[-1] + 1, xs[0] : xs[-1] + 1], (GW, GH),
                interpolation=cv2.INTER_CUBIC,
            )
            r = reader.classify(vec(glyph))
            if r.best < reader.tau or r.margin < reader.delta:
                return None
            digits += r.digit
        try:
            return int(digits)
        except ValueError:
            return None

    # --- Play-call overlay (formation name) — v2.3.0-live play_call context ---

    _SUBTITLE_KEYS = ("formation_name", "formation_name_2", "formation_name_3")

    def read_formation_name(self, frame: np.ndarray) -> FormationNameReading:
        """Read the offensive formation from the play-call overlay.

        v2.3.0-live SUBTITLE-FIRST (corrected after live testing): the play-call
        flow has TWO sub-views, and only ONE reflects the COMMITTED formation:
          * PLAY-SELECT (PRIMARY) — the play-card SUBTITLE ('<Family>
            <Sub-formation>', e.g. 'Pistol Wing Flex'), repeated under each card
            and majority-voted. This is the formation the user DRILLED INTO to
            pick a play — i.e. the one they will snap. Reads cleanly (0.7-1.0).
          * FORMATION-SELECT (fallback only) — the centered '<Formation> - N
            Plays' banner. This shows the formation the user is HOVERING while
            BROWSING, which changes as they scroll — locking it grabs a browse
            transient, not the committed formation (live bug: locked 'Gun Empty
            Trey' while the user snapped 'Pistol Wing Flex'). So the banner is a
            last resort, used only when no subtitle reads at all.
        Per-frame reads are mode-voted across the play-call screen by the
        adapter's TemporalSmoother. Returns is_play_call_screen=False (null name)
        when nothing confident reads.
        """
        pc = self.play_call_regions
        if not pc:
            return FormationNameReading(None, None, 0.0, False)

        # 1) PRIMARY: play-card subtitles (play-select = COMMITTED formation).
        #    Return on the FIRST confident card (usually card 1) — cheap (~1 OCR).
        #    Per-frame reads are mode-voted across the screen by the smoother, so
        #    a single-card read + temporal vote is robust without reading all 3.
        for key in self._SUBTITLE_KEYS:
            region = pc.get(key)
            if region is None:
                continue
            text, conf = _read_text(_crop(frame, region["bbox"]))
            name = _parse_formation_name(text)
            if name and conf > 0.5:
                # Guard: this card-subtitle line is shared with the DEFENSIVE
                # play-call screen, where it reads a defensive front ("3-4 Under",
                # "Nickel Over") — a disjoint vocabulary from offensive formations.
                # Don't lock a defensive front as an offensive formation;
                # read_defensive_front (v0.2) owns that read.
                from .defensive_playcall import canonical_front
                if canonical_front(name) is not None:
                    continue
                return FormationNameReading(
                    name, _formation_to_canonical(name), round(conf, 3), True)

        # No committed-formation subtitle -> browsing (formation-select) or not a
        # play-call screen. Do NOT read the formation-select banner for the name:
        # it shows the BROWSED (hovered) formation and locking it produced the live
        # wrong-lock ('Gun Empty Trey' while snapping 'Pistol Wing Flex'). We lock
        # ONLY the committed play-select subtitle; the lock waits for play-select.
        # Use the standalone "N Plays" counter just for the is_play_call flag.
        state_conf = 0.0
        on_screen = False
        plays_region = pc.get("plays_count")
        if plays_region is not None:
            ptext, state_conf = _read_text(_crop(frame, plays_region["bbox"]))
            on_screen = bool(_PLAYS_RE.search(ptext)) and state_conf > 0.4
        return FormationNameReading(None, None, round(state_conf, 3), on_screen)

    def read_defensive_front(self, frame: np.ndarray) -> DefensiveFrontReading:
        """Read the committed defensive FRONT off the defensive play-call screen (v0.2).

        The defensive play-call screen shows, under each coverage card, the COMMITTED
        front + alignment ("3-4 Under", "Nickel Over", "4-4 Split") on the SAME
        card-subtitle line the offensive reader uses — but a defensive front, a
        vocabulary disjoint from offensive formations. Mirrors read_formation_name's
        subtitle-first logic (the play-CARD front is the front the user drilled into,
        i.e. committed — NOT the formation-picker list highlight, which is only the
        hovered/browsed front). Returns the canonical front when a card reads one;
        is_defensive_play_call=False (null) otherwise.

        Disambiguation is by vocabulary: canonical_front matches 3-4/4-3/4-4/Nickel/
        Dime/... which no offensive formation name contains. KNOWN v0.2 edge: an
        offensive "Goal Line" formation collides with the "Goal Line" front — deferred
        (needs a possession/badge confirm) since it's rare and both screens are mutually
        exclusive per snap.
        """
        pc = self.play_call_regions
        if not pc:
            return DefensiveFrontReading(None, None, 0.0, False)
        from .defensive_playcall import canonical_front
        for key in self._SUBTITLE_KEYS:
            region = pc.get(key)
            if region is None:
                continue
            text, conf = _read_text(_crop(frame, region["bbox"]))
            front = canonical_front(text)
            if front and conf > 0.5:
                return DefensiveFrontReading(front, text.strip(), round(conf, 3), True)
        return DefensiveFrontReading(None, None, 0.0, False)

    # --- Defensive coverage from the pre-snap coach-cam play-art (v0.3) ---
    _COVERAGE_BAND = (0.12, 0.72)   # fractional y-range where the zone labels are drawn

    def _detect_blitz(self, band: np.ndarray) -> bool:
        """Red pressure lines in the play-art band => a blitz (orthogonal to coverage).
        Cover 0 and pressure variants (e.g. Cover 3 Slim Pressure) draw red rush lines."""
        if band.size == 0:
            return False
        b = band[:, :, 0].astype(np.int32)
        g = band[:, :, 1].astype(np.int32)
        r = band[:, :, 2].astype(np.int32)
        red = (r > 140) & (r - g > 60) & (r - b > 60)
        return bool(red.mean() > 0.004)

    _MANLINE_BAND = (0.35, 0.72)   # LOS->receivers band where the man/blitz lines run
    # diagonal play-art segments: man/blitz coach-cam 16-22, plain field/gameplay <=12
    # (measured over 25 real frames)
    _MANLINE_MIN_DIAG = 14

    def _detect_man_lines(self, frame: np.ndarray) -> bool:
        """Detect a coach-cam MAN look via its diagonal play-art line segments (the
        defender->receiver man lines + blitz rushes). Used ONLY for the label-less case
        (Cover 0 draws 0 zone labels) to confirm a real coach-cam view vs a plain field —
        which lacks the overlaid diagonal lines (its edges are ~horizontal yard-lines +
        short player edges). Robust: man/blitz 16-22 diagonal segments, plain <=12."""
        h = frame.shape[0]
        band = frame[int(h * self._MANLINE_BAND[0]):int(h * self._MANLINE_BAND[1])]
        if band.size == 0:
            return False
        gray = cv2.cvtColor(band, cv2.COLOR_BGR2GRAY)
        edges = cv2.Canny(gray, 60, 160)
        lines = cv2.HoughLinesP(edges, 1, np.pi / 180, threshold=40,
                                minLineLength=45, maxLineGap=8)
        if lines is None:
            return False
        diag = 0
        for x1, y1, x2, y2 in lines[:, 0]:
            ang = abs(np.degrees(np.arctan2(float(y2 - y1), float(x2 - x1))))
            ang = min(ang, 180 - ang)
            if 18 < ang < 72:               # diagonal (not axis-aligned field yard-lines)
                diag += 1
        return diag >= self._MANLINE_MIN_DIAG

    def read_coverage(self, frame: np.ndarray) -> "CoverageReading | None":
        """Read the committed defensive COVERAGE off the pre-snap coach-cam play-art (v0.3).

        With play-art ON (or the coach-cam open), Madden draws each defender's zone
        assignment as an on-field text label — a coverage FINGERPRINT (validated on 10
        captures). OCRs the play-art band, groups tokens into labels, and classifies via
        coverage_classifier (#DEEP ZONE = shell; underneath density = man/zone; QUARTER-flat
        side = Cover 6/9). Returns None when it is not a coach-cam coverage view (no zone
        labels and no blitz lines) so the caller emits only on a real read. See
        coverage_classifier for the decision tree and the documented resolution limit
        (label-identical variants fold to the canonical family, e.g. Tampa 2 -> Cover 2).
        """
        from .coverage_classifier import _ZONE_WORDS, _clean, classify_coverage

        h, w = frame.shape[:2]
        y0, y1 = int(h * self._COVERAGE_BAND[0]), int(h * self._COVERAGE_BAND[1])
        band = frame[y0:y1, :]
        if band.size == 0:
            return None
        bh = band.shape[0]
        # Upscale the band so the small, far-edge labels (SOFT SQUAT / VERT HOOK) read.
        up = cv2.resize(band, None, fx=1.6, fy=1.6, interpolation=cv2.INTER_CUBIC)
        reader = _get_reader()
        results = reader.readtext(up, paragraph=False, detail=1)
        tokens: list[tuple[float, float, str]] = []
        for _box, text, conf in results:
            if float(conf) < 0.3 or len(str(text).strip()) < 2:
                continue
            cx = (_box[0][0] + _box[2][0]) / 2 / up.shape[1]
            cy_band = (_box[0][1] + _box[2][1]) / 2 / up.shape[0]
            cy = (y0 + cy_band * bh) / h            # map back to full-frame fraction
            tokens.append((float(cx), float(cy), str(text)))

        has_zone = any(_clean(t[2]) in _ZONE_WORDS for t in tokens)
        if not has_zone:
            # Label-less frame. Recover a real Cover 0 (all-man: 0 zone labels + man
            # LINES) via the diagonal play-art lines; a plain field (no play-art) has
            # none -> None. This gates against the earlier false Cover 0, where
            # _detect_blitz alone false-fired on a red jersey.
            if not self._detect_man_lines(frame):
                return None
        blitz = self._detect_blitz(band)
        return classify_coverage(tokens, is_coach_cam=True, blitz=blitz)

    def is_play_call_screen(self, frame: np.ndarray) -> bool:
        """Cheap state check: is the pre-snap play-call overlay currently visible?"""
        return self.read_formation_name(frame).is_play_call_screen
