"""Integration tests for FORMATION_LOCKED emission + temporal smoothing in the
Madden 26 state assembler (M5c sub-task 6)."""

from datetime import datetime, timezone

from app.adapters.madden26.adapter import Madden26Adapter
from app.adapters.madden26.formation_detector import FormationReading
from app.adapters.madden26.ocr_pipeline import OCRSnapshot
from app.adapters.madden26.state_assembler import assemble
from app.core.session import SessionContext
from app.schemas.enums import EventType, IntegrityMode, TitleEnum

SCHEMA = Madden26Adapter.smoothing_schema
NOW = datetime(2026, 6, 30, tzinfo=timezone.utc)


def _session():
    s = SessionContext.open("s1", "u1", IntegrityMode.OFFLINE_LAB)
    s.title = TitleEnum.MADDEN26
    return s


def _ocr(**kw):
    d = dict(score_home=0, score_away=0, quarter=1, clock="3:00", play_clock="20",
             down=1, distance=10, field_position="+40", team_home_abbr="BAL",
             team_away_abbr="CIN", confidence_overall=0.9)
    d.update(kw)
    return OCRSnapshot(**d)


def _pc(full_name):  # a play-call frame (overlay up, formation readable)
    return FormationReading(formation=None, confidence=0.9, full_name=full_name)


def _live():  # a live-gameplay frame (no overlay)
    return FormationReading(formation=None, confidence=0.0, full_name=None)


def _run(session, offense):
    return assemble(session=session, ocr=_ocr(), offense=offense,
                    captured_at=NOW, smoothing_schema=SCHEMA)


def _locks(frames):
    return [e for fr in frames for e in fr if e.event_type == EventType.FORMATION_LOCKED]


def test_formation_locked_fires_once_per_screen_after_warm():
    s = _session()
    frames = [_run(s, _pc("Trips TE Offset")) for _ in range(5)]
    locks = _locks(frames)
    assert len(locks) == 1                                   # once, not per-frame
    assert locks[0].payload.offensive_formation == "Trips TE Offset"
    assert locks[0].payload.offensive_formation_family == "shotgun_trips"
    # no SNAPSHOT while the play-call overlay is up
    assert all(e.event_type == EventType.FORMATION_LOCKED for fr in frames for e in fr)


def test_mode_vote_outvotes_a_single_misread():
    s = _session()
    seq = ["Trips TE Offset", "Doubies XX", "Trips TE Offset",
           "Trips TE Offset", "Trips TE Offset"]
    locks = _locks([_run(s, _pc(n)) for n in seq])
    assert locks and all(l.payload.offensive_formation == "Trips TE Offset" for l in locks)


def test_context_reset_lets_the_next_screen_reemit():
    s = _session()
    first = _locks([_run(s, _pc("Trips TE Offset")) for _ in range(4)])
    # live gameplay between the two play-call screens -> SNAPSHOTs, formation reset
    snaps = [e for _ in range(3) for e in _run(s, _live()) if e.event_type == EventType.SNAPSHOT]
    second = _locks([_run(s, _pc("Bunch Base")) for _ in range(4)])
    assert [l.payload.offensive_formation_family for l in first] == ["shotgun_trips"]
    assert len(snaps) == 3
    assert [l.payload.offensive_formation_family for l in second] == ["shotgun_bunch"]


def test_live_snapshot_has_no_formation():
    s = _session()
    events = [e for e in _run(s, _live())]
    assert len(events) == 1
    assert events[0].event_type == EventType.SNAPSHOT
    assert events[0].payload.offensive_formation is None
