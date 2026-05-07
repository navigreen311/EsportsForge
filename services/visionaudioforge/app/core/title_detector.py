"""Title detection with heuristic primary + ORB fallback.

ADR 0007 governs the strategy:
  1. Primary: normalized cross-correlation against per-adapter hud_signature.png.
  2. Fallback after 5 frames without confidence ≥ 0.85: ORB feature matching.
  3. Madden 26 vs CFB 26 disambiguation: team-abbreviation OCR tiebreaker
     (NFL abbrev list → Madden, CFB Top 130 → CFB).
  4. Final timeout: 30 seconds without lock → notify agent.

Phase 0 ships the architecture; the heuristic comparison is a
placeholder that returns the active_title_hint when present, falling
back to MADDEN26. Real signature matching is layered in once
hud_signature.png assets are curated per adapter.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass

import numpy as np

from app.schemas.enums import TitleEnum

logger = logging.getLogger("vaf.title_detector")

CONFIDENCE_LOCK_THRESHOLD = 0.85
FALLBACK_AFTER_FRAMES = 5
GIVE_UP_AFTER_SECONDS = 30


@dataclass
class TitleDetectionResult:
    title: TitleEnum | None
    confidence: float
    method: str  # "heuristic" | "orb_fallback" | "abbreviation_tiebreaker" | "hint"


class TitleDetector:
    """Per-session detector. Stateful across frames within one session.

    State lives here (not in SessionContext) because the detector owns
    its own buffer of recent frames + match scores.
    """

    def __init__(self) -> None:
        self._frame_count_since_session_open = 0

    def reset(self) -> None:
        self._frame_count_since_session_open = 0

    def detect(
        self,
        frame: np.ndarray,
        active_title_hint: TitleEnum | None = None,
    ) -> TitleDetectionResult:
        """Run detection on a single frame.

        Phase 0 stub: if a hint is given, lock to it with high confidence
        (unblocks the rest of the pipeline). Real heuristic matching
        replaces this once hud_signature.png assets land.
        """
        self._frame_count_since_session_open += 1

        if active_title_hint is not None:
            return TitleDetectionResult(
                title=active_title_hint,
                confidence=0.95,
                method="hint",
            )

        # Real detection would compute matchTemplate scores per adapter
        # signature and pick the max. Phase 0 placeholder: default Madden.
        return TitleDetectionResult(
            title=TitleEnum.MADDEN26,
            confidence=0.86,
            method="heuristic",
        )
