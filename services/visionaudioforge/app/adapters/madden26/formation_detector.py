"""Madden 26 formation detector — offensive only in v0.1.

Phase 0 stub. The real classifier is MobileNetV3-Small over the
formation-overlay HUD region (see hud_regions.json), classifying into
the 8 most common formations for v0.1 and expanding to 24 by v0.3.

Defensive front (v0.2) and post-snap coverage (v0.3) are not in this
file yet — separate classes will land alongside their respective
ONNX models.
"""

from __future__ import annotations

from dataclasses import dataclass


# Top-8 offensive formations for v0.1 — see Madden adapter spec.
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
    formation: str | None
    confidence: float


class FormationDetector:
    """Loads the ONNX classifier at construction.

    Phase 0: model not loaded; `detect_offensive` returns a stable
    placeholder so the dispatcher loop runs end-to-end.
    """

    def __init__(self, model_path: str | None = None) -> None:
        self.model_path = model_path
        self.model = None  # ONNX runtime session — Phase 1 M5c

    def detect_offensive(self, frame) -> FormationReading:  # frame: np.ndarray
        """Phase 0 stub.

        TODO(phase-1-m5c): crop formation_overlay_pre_snap region, resize
        to 224×224, run MobileNetV3-Small, argmax + softmax, return.
        Real model targets macro-F1 ≥ 0.85 on the v0.1 8-class subset.
        """
        return FormationReading(
            formation="shotgun_trips",
            confidence=0.5,  # below 0.85 — assembler treats as low-confidence
        )

    def detect_defensive_front(self, frame) -> FormationReading:
        """v0.2 hook — returns None until v0.2 ships."""
        return FormationReading(formation=None, confidence=0.0)

    def detect_coverage(self, frame, frames_since_snap: int) -> FormationReading:
        """v0.3 hook — returns None until v0.3 ships.

        Phase 1c cutover (Arsenal + War Room) is gated on this returning
        real values per ADR 0010.
        """
        return FormationReading(formation=None, confidence=0.0)
