"""v0.3 COVERAGE_LOCKED emit wiring (OCR-of-play-call coverage leg).

Covers the assembler's coverage-lock: mode-voted across the pre-snap coach-cam reads,
emitted once per play, resetting per play-epoch. CI-safe: the coverage reading is a
plain CoverageReading (no EasyOCR / no frame).
"""

from datetime import datetime, timezone

from app.adapters.madden26.adapter import Madden26Adapter
from app.adapters.madden26.coverage_classifier import CoverageReading
from app.adapters.madden26.formation_detector import FormationReading
from app.adapters.madden26.ocr_pipeline import OCRSnapshot
from app.adapters.madden26.state_assembler import assemble
from app.core.session import SessionContext
from app.schemas.enums import EventType, IntegrityMode, TitleEnum

SCHEMA = Madden26Adapter.smoothing_schema
NOW = datetime(2026, 6, 30, tzinfo=timezone.utc)


def _session() -> SessionContext:
    s = SessionContext.open("s1", "u1", IntegrityMode.OFFLINE_LAB)
    s.title = TitleEnum.MADDEN26
    return s


def _ocr(**kw) -> OCRSnapshot:
    d = dict(score_home=7, score_away=3, quarter=1, clock="3:00", play_clock="20",
             down=1, distance=10, field_position="+40", team_home_abbr="BAL",
             team_away_abbr="CIN", confidence_overall=0.9)
    d.update(kw)
    return OCRSnapshot(**d)


def _null() -> FormationReading:
    return FormationReading(formation=None, confidence=0.0, full_name=None)


def _cov(name: str, mz: str = "zone", deep: int = 3) -> CoverageReading:
    return CoverageReading(coverage=name, man_zone=mz, deep_count=deep,
                           n_labels=7, confidence=0.9)


def _run(session, coverage, epoch=0):
    # live-gameplay frame with no fresh HUD fields -> only a COVERAGE_LOCKED may emit.
    return assemble(session=session, ocr=_ocr(), offense=_null(), coverage=coverage,
                    captured_at=NOW, smoothing_schema=SCHEMA, context="live_gameplay",
                    updated_fields=set(), play_epoch=epoch)


def _locks(frames):
    return [e for fr in frames for e in fr if e.event_type == EventType.COVERAGE_LOCKED]


def test_coverage_locked_once_per_play_after_warm():
    s = _session()
    locks = _locks([_run(s, _cov("Cover 3")) for _ in range(5)])
    assert len(locks) == 1                                    # once, not per-frame
    assert locks[0].payload.defensive_coverage == "Cover 3"


def test_coverage_mode_vote_outvotes_a_misread():
    s = _session()
    seq = ["Cover 3", "Cover 2", "Cover 3", "Cover 3", "Cover 3"]
    locks = _locks([_run(s, _cov(n)) for n in seq])
    assert locks and all(e.payload.defensive_coverage == "Cover 3" for e in locks)


def test_new_play_epoch_reemits():
    s = _session()
    first = _locks([_run(s, _cov("Cover 3"), epoch=0) for _ in range(4)])
    second = _locks([_run(s, _cov("Cover 2-Man", "man", 2), epoch=1) for _ in range(4)])
    assert [e.payload.defensive_coverage for e in first] == ["Cover 3"]
    assert [e.payload.defensive_coverage for e in second] == ["Cover 2-Man"]


def test_null_coverage_emits_no_lock():
    s = _session()
    events = _run(s, None)
    assert not [e for e in events if e.event_type == EventType.COVERAGE_LOCKED]
