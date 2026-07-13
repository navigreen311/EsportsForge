"""Unified play-call read (detect_play_call) — one OCR pass -> (offense, defense).

The play-call screen is offensive XOR defensive; read_play_call reads the shared
card-subtitle regions once and classifies by vocabulary. This checks FormationDetector
maps its (FormationNameReading, DefensiveFrontReading) to the per-side FormationReadings
with the same null-when-absent semantics as the old detect_offensive/detect_defensive_front.
CI-safe: OCR is faked.
"""

from __future__ import annotations

from app.adapters.madden26.formation_detector import FormationDetector
from app.adapters.madden26.ocr_pipeline import DefensiveFrontReading, FormationNameReading


class _FakeOCR:
    def __init__(self, off: FormationNameReading, dfr: DefensiveFrontReading) -> None:
        self._r = (off, dfr)

    def read_play_call(self, frame):
        return self._r


def test_defensive_play_call():
    off = FormationNameReading(None, None, 0.9, True)          # play-call screen, no off name
    dfr = DefensiveFrontReading("3-4", "3-4 Under", 0.9, True)
    o, d = FormationDetector(_FakeOCR(off, dfr)).detect_play_call(None)  # type: ignore[arg-type]
    assert o.formation is None and o.full_name is None
    assert d.formation == "3-4" and d.full_name == "3-4 Under"


def test_offensive_play_call():
    off = FormationNameReading("Trips TE Offset", "shotgun_trips", 0.9, True)
    dfr = DefensiveFrontReading(None, None, 0.0, False)
    o, d = FormationDetector(_FakeOCR(off, dfr)).detect_play_call(None)  # type: ignore[arg-type]
    assert o.full_name == "Trips TE Offset" and o.formation == "shotgun_trips"
    assert d.formation is None


def test_not_a_play_call_screen():
    off = FormationNameReading(None, None, 0.0, False)
    dfr = DefensiveFrontReading(None, None, 0.0, False)
    o, d = FormationDetector(_FakeOCR(off, dfr)).detect_play_call(None)  # type: ignore[arg-type]
    assert o.formation is None and o.confidence == 0.0
    assert d.formation is None and d.confidence == 0.0
