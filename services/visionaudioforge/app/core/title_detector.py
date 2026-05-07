"""Title detection per ADR 0007.

Strategy:
  1. Primary: normalized cross-correlation against per-adapter hud_signature.png.
  2. Fallback after 5 frames without confidence ≥ 0.85: ORB feature matching.
  3. Madden 26 vs CFB 26 disambiguation: when both score ≥ 0.7 with delta < 0.10,
     team-abbreviation OCR tiebreaker (NFL list → Madden, CFB Top 130 → CFB).
  4. Final timeout: 30 seconds without lock → notify agent.

Phase 0 + post-review additions: real heuristic match against signatures
when present; ORB fallback wired and exercised by tests; abbrev-OCR
tiebreaker wired and tested.
"""

from __future__ import annotations

import logging
import time
from dataclasses import dataclass
from pathlib import Path

import cv2
import numpy as np

from app.schemas.enums import TitleEnum

logger = logging.getLogger("vaf.title_detector")

CONFIDENCE_LOCK_THRESHOLD = 0.85
FALLBACK_AFTER_FRAMES = 5
GIVE_UP_AFTER_SECONDS = 30
TIEBREAK_BAND = 0.7   # both ≥ 0.7 and within 0.10 of each other → tiebreaker
TIEBREAK_DELTA = 0.10

# Football-archetype titles that share a HUD shape and may need tiebreaking.
_FOOTBALL_TITLES: set[TitleEnum] = {TitleEnum.MADDEN26, TitleEnum.CFB26}

# NFL team abbreviations (32). Real-world spelling of how Madden's HUD
# presents team codes. Used by the team-abbrev tiebreaker.
NFL_ABBREVS: frozenset[str] = frozenset({
    "ARI", "ATL", "BAL", "BUF", "CAR", "CHI", "CIN", "CLE",
    "DAL", "DEN", "DET", "GB",  "HOU", "IND", "JAX", "KC",
    "LV",  "LAC", "LAR", "MIA", "MIN", "NE",  "NO",  "NYG",
    "NYJ", "PHI", "PIT", "SF",  "SEA", "TB",  "TEN", "WAS",
})

# Sample of CFB program abbreviations (top tier). Not exhaustive — false-
# negative behaviour is "no tiebreaker" which falls back to template-match
# winner. The list is updated when CFB 26 adapter ships.
CFB_ABBREVS: frozenset[str] = frozenset({
    "BAMA", "OSU", "MICH", "GA", "UGA", "TEX", "OU", "OKLA",
    "ND", "LSU", "USC", "FSU", "ORE", "PSU", "MIA", "WIS",
    "TENN", "AUB", "MSU", "CLEM", "FLA", "ARK", "ALA",
})


@dataclass
class TitleDetectionResult:
    title: TitleEnum | None
    confidence: float
    method: str  # "heuristic" | "orb_fallback" | "abbreviation_tiebreaker" | "hint" | "unknown"


class _SignatureCache:
    """Lazy-loaded per-title hud_signature.png templates.

    Adapters ship signatures under
    services/visionaudioforge/app/adapters/<title>/hud_signature.png. The
    detector loads them on first use; missing files are skipped silently
    (an adapter that hasn't curated its signature yet just doesn't
    contribute to detection).
    """

    def __init__(self) -> None:
        self._templates: dict[TitleEnum, np.ndarray] = {}
        self._loaded = False

    def get(self, title: TitleEnum) -> np.ndarray | None:
        if not self._loaded:
            self._load_all()
        return self._templates.get(title)

    def _load_all(self) -> None:
        # Walk app/adapters/<title>/hud_signature.png.
        adapters_root = Path(__file__).resolve().parent.parent / "adapters"
        if adapters_root.exists():
            for title in TitleEnum:
                path = adapters_root / title.value / "hud_signature.png"
                if path.exists():
                    img = cv2.imread(str(path), cv2.IMREAD_GRAYSCALE)
                    if img is not None:
                        self._templates[title] = img
                        logger.info(
                            "signature_loaded",
                            extra={"title": title.value, "shape": img.shape},
                        )
        self._loaded = True

    def all_templates(self) -> dict[TitleEnum, np.ndarray]:
        if not self._loaded:
            self._load_all()
        return dict(self._templates)


_signature_cache = _SignatureCache()


def _heuristic_score(frame: np.ndarray, template: np.ndarray) -> float:
    """Normalized cross-correlation. Returns max match score in [0, 1]."""
    if frame is None or template is None:
        return 0.0
    if frame.ndim == 3:
        frame_gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    else:
        frame_gray = frame
    fh, fw = frame_gray.shape[:2]
    th, tw = template.shape[:2]
    if th > fh or tw > fw:
        return 0.0
    res = cv2.matchTemplate(frame_gray, template, cv2.TM_CCOEFF_NORMED)
    return float(res.max())


def _orb_score(frame: np.ndarray, template: np.ndarray) -> float:
    """ORB feature-matching score. Returns ratio of good matches in [0, 1].

    Robust to scaling / lighting variation; slower than template matching.
    Used as the fallback per ADR 0007.
    """
    if frame is None or template is None:
        return 0.0
    if frame.ndim == 3:
        frame_gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    else:
        frame_gray = frame
    orb = cv2.ORB_create(nfeatures=500)
    kp1, des1 = orb.detectAndCompute(template, None)
    kp2, des2 = orb.detectAndCompute(frame_gray, None)
    if des1 is None or des2 is None or len(kp1) == 0:
        return 0.0
    matcher = cv2.BFMatcher(cv2.NORM_HAMMING, crossCheck=True)
    matches = matcher.match(des1, des2)
    if not matches:
        return 0.0
    # Good-match ratio: fraction with distance below the 25th percentile.
    distances = sorted(m.distance for m in matches)
    threshold = distances[len(distances) // 4] if distances else 0
    good = sum(1 for m in matches if m.distance <= threshold)
    return good / max(len(kp1), 1)


def _disambiguate_football(
    frame: np.ndarray, ocr_text_extractor
) -> TitleDetectionResult | None:
    """Madden 26 vs CFB 26 tiebreaker via team-abbreviation OCR.

    `ocr_text_extractor` is a callable(frame, region_bbox) -> str. Injected
    so unit tests can stub the OCR without instantiating EasyOCR.
    """
    # The relevant region is the home + away team-abbreviation bands. We
    # use Madden's hud_regions.json scoreboard.subregions as the canonical
    # band layout — CFB's HUD will mirror this when its adapter ships.
    home_bbox = [60, 50, 55, 30]
    away_bbox = [205, 50, 55, 30]

    try:
        home_text = ocr_text_extractor(frame, home_bbox).strip().upper()
        away_text = ocr_text_extractor(frame, away_bbox).strip().upper()
    except Exception as exc:  # noqa: BLE001
        logger.warning("tiebreaker_ocr_failed", extra={"exc_type": type(exc).__name__})
        return None

    nfl_hits = sum(1 for abbr in (home_text, away_text) if abbr in NFL_ABBREVS)
    cfb_hits = sum(1 for abbr in (home_text, away_text) if abbr in CFB_ABBREVS)

    if nfl_hits > cfb_hits:
        return TitleDetectionResult(
            title=TitleEnum.MADDEN26,
            confidence=0.5 + 0.25 * nfl_hits,  # 0.75 with one hit, 1.0 with two
            method="abbreviation_tiebreaker",
        )
    if cfb_hits > nfl_hits:
        return TitleDetectionResult(
            title=TitleEnum.CFB26,
            confidence=0.5 + 0.25 * cfb_hits,
            method="abbreviation_tiebreaker",
        )

    # Tiebreaker inconclusive — return None, caller falls back to template-match winner.
    return None


class TitleDetector:
    """Per-session detector. State lives here; SessionContext owns nothing detector-specific."""

    def __init__(
        self,
        ocr_text_extractor=None,  # callable(frame, bbox) -> str; for tiebreaker
    ) -> None:
        self._frames_seen = 0
        self._opened_at = time.monotonic()
        self._ocr_text_extractor = ocr_text_extractor

    @property
    def frames_seen(self) -> int:
        return self._frames_seen

    @property
    def elapsed_sec(self) -> float:
        return time.monotonic() - self._opened_at

    def reset(self) -> None:
        self._frames_seen = 0
        self._opened_at = time.monotonic()

    def detect(
        self,
        frame: np.ndarray,
        active_title_hint: TitleEnum | None = None,
    ) -> TitleDetectionResult:
        """Run detection on a single frame.

        Per ADR 0007:
          1. If hint is supplied AND we're in the first 3 frames AND no template
             contradicts it strongly, accept the hint.
          2. Score each registered template via normalized cross-correlation.
          3. If best score < 0.85 AND we've seen ≥5 frames, ORB-fallback.
          4. If two football titles both score ≥ 0.7 within 0.10 of each other,
             team-abbreviation OCR tiebreaker.
          5. If still no lock and >30s elapsed, return TitleDetectionResult(None, 0.0).
        """
        self._frames_seen += 1

        templates = _signature_cache.all_templates()

        # Step 1: hint path. Hints are supplied by the EsportsForge backend
        # at session-open time (player's active_title setting). We trust the
        # hint for the first 3 frames unless a template contradicts it
        # strongly (>= 0.5 difference in favor of another title).
        if active_title_hint is not None and self._frames_seen <= 3 and templates:
            scores = {t: _heuristic_score(frame, tpl) for t, tpl in templates.items()}
            best_other_title, best_other_score = max(
                ((t, s) for t, s in scores.items() if t != active_title_hint),
                default=(None, 0.0),
            )
            hint_score = scores.get(active_title_hint, 0.0)
            if best_other_score - hint_score < 0.5:
                return TitleDetectionResult(
                    title=active_title_hint,
                    confidence=max(hint_score, 0.95),  # hint trust floor
                    method="hint",
                )

        # If no templates registered (e.g., Phase 0 before signatures curated),
        # fall back to hint when present, else unknown.
        if not templates:
            if active_title_hint is not None:
                return TitleDetectionResult(
                    title=active_title_hint, confidence=0.9, method="hint"
                )
            return TitleDetectionResult(title=None, confidence=0.0, method="unknown")

        # Step 2: heuristic template-match scoring.
        scores = {t: _heuristic_score(frame, tpl) for t, tpl in templates.items()}
        best_title, best_score = max(scores.items(), key=lambda kv: kv[1])

        # Step 4 (run before locking): football tiebreaker if applicable.
        football_scores = {t: scores[t] for t in _FOOTBALL_TITLES if t in scores}
        if len(football_scores) >= 2:
            top_two = sorted(football_scores.values(), reverse=True)[:2]
            if (
                top_two[0] >= TIEBREAK_BAND
                and (top_two[0] - top_two[1]) < TIEBREAK_DELTA
                and self._ocr_text_extractor is not None
            ):
                tied = _disambiguate_football(frame, self._ocr_text_extractor)
                if tied is not None:
                    return tied

        # Step 2 cont: lock if confident.
        if best_score >= CONFIDENCE_LOCK_THRESHOLD:
            return TitleDetectionResult(
                title=best_title, confidence=best_score, method="heuristic"
            )

        # Step 3: ORB fallback after 5 frames.
        if self._frames_seen >= FALLBACK_AFTER_FRAMES:
            orb_scores = {t: _orb_score(frame, tpl) for t, tpl in templates.items()}
            best_title_orb, best_score_orb = max(orb_scores.items(), key=lambda kv: kv[1])
            # ORB confidence interpretation: >= 0.30 of keypoints matching is
            # a strong signal (the template is small; absolute counts are low).
            if best_score_orb >= 0.30:
                return TitleDetectionResult(
                    title=best_title_orb,
                    confidence=min(0.85, 0.5 + best_score_orb),  # ceiling at 0.85
                    method="orb_fallback",
                )

        # Step 5: still no lock.
        return TitleDetectionResult(title=None, confidence=best_score, method="heuristic")
