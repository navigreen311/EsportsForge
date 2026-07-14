"""PLAY_STARTED / PLAY_ENDED emit wiring (snap-boundary events, M5b).

Covers the assembler's play-boundary emit: PLAY_STARTED on the snap-confirm edge,
PLAY_ENDED on the post-snap reset-tick edge (the adapter derives both from the
SnapDetector state machine and passes them as snap_started / snap_ended). The events
carry the last-live game state and are exempt from the SNAPSHOT OCR-cadence gate (a
snap on a hot, no-OCR frame must still fire). CI-safe: assemble is driven with plain
values (no frames / no EasyOCR).
"""

from datetime import datetime, timezone

from app.adapters.madden26.adapter import Madden26Adapter
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
             down=2, distance=7, field_position="+40", team_home_abbr="BAL",
             team_away_abbr="CIN", confidence_overall=0.9)
    d.update(kw)
    return OCRSnapshot(**d)


def _null() -> FormationReading:
    return FormationReading(formation=None, confidence=0.0, full_name=None)


def _run(session, *, snap_started=False, snap_ended=False, updated=None, epoch=0):
    return assemble(
        session=session, ocr=_ocr(), offense=_null(), captured_at=NOW,
        smoothing_schema=SCHEMA, context="live_gameplay",
        updated_fields=set() if updated is None else updated, play_epoch=epoch,
        snap_started=snap_started, snap_ended=snap_ended,
    )


def _of(events, et):
    return [e for e in events if e.event_type == et]


def test_play_started_emitted_on_snap():
    s = _session()
    events = _run(s, snap_started=True)
    assert len(_of(events, EventType.PLAY_STARTED)) == 1
    assert not _of(events, EventType.PLAY_ENDED)


def test_play_ended_emitted_on_reset():
    s = _session()
    events = _run(s, snap_ended=True)
    assert len(_of(events, EventType.PLAY_ENDED)) == 1
    assert not _of(events, EventType.PLAY_STARTED)


def test_no_boundary_events_without_an_edge():
    s = _session()
    events = _run(s)                                  # a plain hot frame, no edge
    assert not _of(events, EventType.PLAY_STARTED)
    assert not _of(events, EventType.PLAY_ENDED)


def test_play_started_fires_ungated_on_a_hot_no_ocr_frame():
    # updated_fields empty (hot frame, no OCR sampled) normally suppresses SNAPSHOT;
    # the boundary event must still fire.
    s = _session()
    events = _run(s, snap_started=True, updated=set())
    assert _of(events, EventType.PLAY_STARTED)
    assert not _of(events, EventType.SNAPSHOT)        # gate still suppresses the snapshot


def test_boundary_event_carries_last_live_state():
    s = _session()
    # Prime the last-live state with a real SNAPSHOT (down=2 & distance=7 from _ocr).
    snap_frame = _run(s, updated={"down", "distance"})
    assert _of(snap_frame, EventType.SNAPSHOT)
    # A subsequent snap frame's PLAY_STARTED carries that down/distance.
    started = _of(_run(s, snap_started=True), EventType.PLAY_STARTED)[0]
    assert started.payload.down == 2 and started.payload.distance == 7


def test_play_ended_orders_before_play_started_when_both_set():
    # The two edges never co-occur on a real frame, but if both are passed the order
    # is deterministic: the prior play ends before the new one starts.
    s = _session()
    types = [e.event_type for e in _run(s, snap_started=True, snap_ended=True)]
    assert types.index(EventType.PLAY_ENDED) < types.index(EventType.PLAY_STARTED)
