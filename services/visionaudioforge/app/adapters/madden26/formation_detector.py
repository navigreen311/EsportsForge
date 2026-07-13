"""Madden 26 offensive formation detector — OCR-of-play-call-overlay (v0.1).

M5c sub-task 4 pivot (ADR 0014). Reads the offensive formation from the game's
own play-call overlay TEXT rather than inferring it from the gameplay-camera
pixels. The single-frame CNN approach ceilinged at ~0.22 macro-F1 across 12
training runs — the elevated ball-following gameplay camera does not expose
enough player detail for fine-grained formation discrimination. Reading the
explicit on-screen formation name is far more reliable (feasibility: 100% on the
8 canonical practice clips, production-confirmed on the human exhibition clip).

Output: the full Madden formation name (e.g. "Trips TE Offset") as the primary
label plus a canonical-8 family tag (e.g. "shotgun_trips"). Returns a null
reading when the play-call overlay is not on screen — mid-play, or CPU-vs-CPU,
which never shows a play-call screen. The FORMATION_LOCKED event is emitted by
the adapter (Madden26Adapter.process_frame) from a non-null reading; the value
is stable within a play-call screen, so the title-agnostic TemporalSmoother
(sub-task 6, categorical field) mode-votes away single-frame OCR misreads.

Defensive front (v0.2) and post-snap coverage (v0.3) remain hooks until their
signals ship.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:  # avoid importing EasyOCR-heavy pipeline at module load
    import numpy as np

    from .coverage_classifier import CoverageReading
    from .ocr_pipeline import OCRPipeline


# Top-8 offensive formations for v0.1 (canonical family tags). v0.3 expands to 24
# and adds left-panel family disambiguation for ambiguous names ("Pro","Strong").
TOP_8_FORMATIONS = (
    "shotgun_trips",
    "shotgun_bunch",
    "shotgun_empty",
    "i_form_pro",
    "singleback_ace",
    "pistol_strong",
    "shotgun_doubles",
    "singleback_wing",
)


@dataclass(frozen=True)
class FormationReading:
    formation: str | None          # canonical-8 family tag, or None
    confidence: float
    full_name: str | None = None   # full Madden play-call name (primary label)


class FormationDetector:
    """OCR-of-overlay offensive-formation reader.

    Reads the play-call banner via the shared OCRPipeline (which loads the
    v2.2.0 hud_regions play_call context). The pipeline is lazily constructed so
    unit tests and non-formation code paths don't pay the EasyOCR cost.
    """

    def __init__(self, ocr_pipeline: "OCRPipeline | None" = None) -> None:
        self._ocr = ocr_pipeline

    @property
    def ocr(self) -> "OCRPipeline":
        if self._ocr is None:
            from .ocr_pipeline import OCRPipeline
            self._ocr = OCRPipeline()
        return self._ocr

    def detect_offensive(self, frame: "np.ndarray") -> FormationReading:
        """Read the offensive formation if the play-call overlay is visible.

        Returns a null reading (formation=None, confidence=0.0) when the overlay
        is not on screen, so downstream logic emits FORMATION_LOCKED only on a
        real read.
        """
        reading = self.ocr.read_formation_name(frame)
        if not reading.is_play_call_screen:
            return FormationReading(formation=None, confidence=0.0, full_name=None)
        return FormationReading(
            formation=reading.canonical,
            confidence=reading.confidence,
            full_name=reading.full_name,
        )

    def detect_play_call(
        self, frame: "np.ndarray"
    ) -> "tuple[FormationReading, FormationReading]":
        """One OCR pass -> (offensive formation, defensive front). Unifies detect_offensive
        + detect_defensive_front (which read the SAME card-subtitle regions) onto a single
        read_play_call pass — the play-call hot path. Same per-side semantics as the
        individual detectors (null reading when that side isn't on screen)."""
        off, front = self.ocr.read_play_call(frame)
        offense = (FormationReading(off.canonical, off.confidence, off.full_name)
                   if off.is_play_call_screen
                   else FormationReading(None, 0.0, None))
        defense = (FormationReading(front.front, front.confidence, front.full_name)
                   if front.is_defensive_play_call
                   else FormationReading(None, 0.0, None))
        return offense, defense

    def detect_defensive_front(self, frame: "np.ndarray") -> FormationReading:
        """Read the committed defensive FRONT off the defensive play-call screen (v0.2).

        Reads the coverage-card subtitle ("3-4 Under", "Nickel Over") via the shared
        OCRPipeline and maps it to a canonical front (OCR-of-play-call pivot, mirrors
        detect_offensive). Returns a null reading (formation=None, confidence=0.0) when
        the defensive play-call screen is not up, so the adapter emits
        defensive_formation only on a real read.
        """
        reading = self.ocr.read_defensive_front(frame)
        if not reading.is_defensive_play_call:
            return FormationReading(formation=None, confidence=0.0, full_name=None)
        return FormationReading(
            formation=reading.front,          # canonical front, e.g. "3-4"
            confidence=reading.confidence,
            full_name=reading.full_name,      # raw card subtitle, e.g. "3-4 Under"
        )

    def detect_coverage(
        self, frame: "np.ndarray", frames_since_snap: int = 0
    ) -> "CoverageReading | None":
        """Read the committed defensive COVERAGE off the pre-snap coach-cam play-art (v0.3).

        OCR-of-play-call pivot, coverage leg. Reads the on-field zone-assignment labels via
        the shared OCRPipeline and classifies the constellation into a canonical coverage +
        man/zone (see coverage_classifier). Returns None when the coach-cam play-art is not
        on screen (self-gating: no zone labels -> not a coverage view), so the adapter emits
        COVERAGE_LOCKED only on a real read.

        Note: this is a PRE-snap read (the coach-cam is a pre-snap view), so frames_since_snap
        is unused — kept for signature compatibility with the ADR-0010 hook. The failed
        post-snap-vision arc is superseded by this approach.
        """
        return self.ocr.read_coverage(frame)
