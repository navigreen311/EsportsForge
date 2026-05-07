"""Madden 26 OCR pipeline — score / clock / down / distance / field position.

Phase 0 stub. Real Tesseract integration lands in Phase 1 M5a, after
Tesseract is installed in the service container and per-region preprocessing
is tuned per docs/integrations/visionaudioforge/04-madden26-adapter-spec.md.

Surface is locked here so the state assembler can compose against it.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class OCRReading:
    """One read result. Confidence below 0.85 is treated as "retain prior"."""

    value: str | None
    confidence: float


@dataclass(frozen=True)
class OCRSnapshot:
    """All HUD readings for one frame."""

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


class OCRPipeline:
    """Loads HUD region map at construction; reads frames by-region.

    Phase 0: returns a fixed snapshot so the dispatcher can be exercised
    end-to-end without Tesseract installed. Real implementation replaces
    the body of `read_frame` only — interface is locked.
    """

    def __init__(self, hud_regions_path: str | None = None) -> None:
        self.hud_regions_path = hud_regions_path
        # Real path: load hud_regions.json, parse bboxes, compile region
        # crop callables. Phase 0 — no-op.

    def read_frame(self, frame) -> OCRSnapshot:  # frame: np.ndarray
        """Phase 0 stub: returns a plausible mid-game state.

        TODO(phase-1-m5a): replace with real Tesseract + region-cropping
        per the Madden adapter spec. Return shape stays identical.
        """
        return OCRSnapshot(
            score_home=14,
            score_away=10,
            quarter=3,
            clock="8:34",
            down=2,
            distance=7,
            field_position="OWN_35",
            team_home_abbr="DAL",
            team_away_abbr="PHI",
            confidence_overall=0.5,  # below 0.85 — assembler treats as low-confidence
        )
