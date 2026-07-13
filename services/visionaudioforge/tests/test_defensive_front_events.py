"""v0.2 defensive-front reader wiring (OCR-of-play-call pivot).

Covers the detector mapping (DefensiveFrontReading -> FormationReading) and the
FORMATION_LOCKED emit path in the state assembler — mode-voted, once per screen,
setting `defensive_formation` (not `offensive_formation`). CI-safe: the OCR pass
is faked, so these run without EasyOCR / a real frame.
"""

from datetime import datetime, timezone

from app.adapters.madden26.adapter import Madden26Adapter
from app.adapters.madden26.formation_detector import FormationDetector, FormationReading
from app.adapters.madden26.ocr_pipeline import DefensiveFrontReading, OCRSnapshot
from app.adapters.madden26.state_assembler import assemble
from app.core.session import SessionContext
from app.schemas.enums import EventType, IntegrityMode, TitleEnum

SCHEMA = Madden26Adapter.smoothing_schema
NOW = datetime(2026, 6, 30, tzinfo=timezone.utc)


class _FakeOCR:
    """Stand-in OCRPipeline that returns a canned defensive-front reading."""

    def __init__(self, reading: DefensiveFrontReading) -> None:
        self._reading = reading

    def read_defensive_front(self, frame) -> DefensiveFrontReading:
        return self._reading


def test_detect_defensive_front_maps_reading() -> None:
    ocr = _FakeOCR(DefensiveFrontReading("3-4", "3-4 Under", 0.9, True))
    r = FormationDetector(ocr).detect_defensive_front(None)  # type: ignore[arg-type]
    assert r.formation == "3-4"
    assert r.full_name == "3-4 Under"
    assert r.confidence == 0.9


def test_detect_defensive_front_abstains_off_screen() -> None:
    # Not the defensive play-call screen (e.g. formation-picker browse list) -> null.
    ocr = _FakeOCR(DefensiveFrontReading(None, None, 0.0, False))
    r = FormationDetector(ocr).detect_defensive_front(None)  # type: ignore[arg-type]
    assert r.formation is None
    assert r.confidence == 0.0


def _session() -> SessionContext:
    s = SessionContext.open("s1", "u1", IntegrityMode.OFFLINE_LAB)
    s.title = TitleEnum.MADDEN26
    return s


def _ocr(**kw) -> OCRSnapshot:
    d = dict(score_home=0, score_away=0, quarter=1, clock="3:00", play_clock="20",
             down=1, distance=10, field_position="+40", team_home_abbr="BAL",
             team_away_abbr="CIN", confidence_overall=0.9)
    d.update(kw)
    return OCRSnapshot(**d)


def _null() -> FormationReading:
    return FormationReading(formation=None, confidence=0.0, full_name=None)


def _def(front: str) -> FormationReading:  # a defensive play-call frame
    return FormationReading(formation=front, confidence=0.9, full_name=f"{front} Under")


def _run_def(session: SessionContext, defense: FormationReading):
    return assemble(session=session, ocr=_ocr(), offense=_null(), defense=defense,
                    captured_at=NOW, smoothing_schema=SCHEMA)


def _locks(frames):
    return [e for fr in frames for e in fr if e.event_type == EventType.FORMATION_LOCKED]


def test_defensive_front_locked_once_per_screen() -> None:
    s = _session()
    locks = _locks([_run_def(s, _def("3-4")) for _ in range(5)])
    assert len(locks) == 1                                   # once, not per-frame
    assert locks[0].payload.defensive_formation == "3-4"
    assert locks[0].payload.offensive_formation is None      # front doesn't leak to offense


def test_defensive_front_mode_vote_outvotes_a_misread() -> None:
    s = _session()
    seq = ["3-4", "4-4", "3-4", "3-4", "3-4"]
    locks = _locks([_run_def(s, _def(n)) for n in seq])
    assert locks and all(l.payload.defensive_formation == "3-4" for l in locks)
