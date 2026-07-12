"""Sampled-OCR cadence behaviors in the assembler + adapter (M5c sub-task 7.5.4):
per-field carry-forward, SNAPSHOT emit-gating, play-epoch smoothing reset, and
null-read carry-forward (a failed read must not clobber the last good value)."""

from datetime import datetime, timezone

import numpy as np

from app.adapters.madden26.adapter import Madden26Adapter
from app.adapters.madden26.context_detector import HudContext
from app.adapters.madden26.formation_detector import FormationReading
from app.adapters.madden26.ocr_pipeline import OCRSnapshot
from app.adapters.madden26.state_assembler import assemble
from app.core.session import SessionContext
from app.schemas.enums import EventType, IntegrityMode, TitleEnum

SCHEMA = Madden26Adapter.smoothing_schema
NOW = datetime(2026, 6, 30, tzinfo=timezone.utc)
NULL_OFFENSE = FormationReading(formation=None, confidence=0.0, full_name=None)


def _session():
    s = SessionContext.open("s", "u", IntegrityMode.OFFLINE_LAB)
    s.title = TitleEnum.MADDEN26
    return s


def _snap(**kw):
    d = dict(score_home=0, score_away=0, quarter=1, clock="5:00", play_clock=None,
             down=None, distance=None, field_position=None,
             team_home_abbr="BAL", team_away_abbr="CIN", confidence_overall=0.9)
    d.update(kw)
    return OCRSnapshot(**d)


def _live(session, snap, updated, epoch=0):
    return assemble(session=session, ocr=snap, offense=NULL_OFFENSE, captured_at=NOW,
                    smoothing_schema=SCHEMA, context="live_gameplay",
                    updated_fields=updated, play_epoch=epoch)


def test_snapshot_emitted_only_when_a_field_is_fresh():
    s = _session()
    # a fresh clock read -> SNAPSHOT
    evs = _live(s, _snap(clock="5:00"), {"clock"})
    assert len(evs) == 1 and evs[0].event_type == EventType.SNAPSHOT
    # a hot-path frame (nothing read this frame) -> no SNAPSHOT spam
    assert _live(s, _snap(clock="5:00"), set()) == []


def test_unread_fields_carry_forward():
    s = _session()
    _live(s, _snap(down=2, distance=7), {"down", "distance"})
    # next frame reads only the clock; down/distance carry forward, not None.
    evs = _live(s, _snap(clock="4:58", down=None, distance=None), {"clock"})
    p = evs[0].payload
    assert p.down == 2 and p.distance == 7 and p.clock == "4:58"


def test_play_clock_read_reaches_payload_as_int():
    # The CNN play-clock reader emits a digit-string ("40"); it is smoothed
    # (numeric) and must surface in the payload as an int (was silently dropped —
    # play_clock had no payload field before the reader landed).
    s = _session()
    evs = _live(s, _snap(play_clock="40"), {"play_clock"})
    assert evs[0].payload.play_clock == 40


def test_unreadable_play_clock_emits_null_not_fabricated():
    s = _session()
    evs = _live(s, _snap(clock="5:00", play_clock=None), {"clock"})
    assert evs[0].payload.play_clock is None


def test_null_hud_read_is_skipped_not_raised():
    # A fully-unreadable frame (menu / replay / broadcast / null-HUD): the sampled
    # path skips the SNAPSHOT rather than emitting an all-null payload or raising a
    # Madden26Payload ValidationError. Regression for the drill-lab null-HUD finding
    # (resolved by the v2.3.0-live nullable schema + this skip guard).
    s = _session()
    evs = _live(s, _snap(score_home=None, score_away=None, quarter=None, clock=None,
                         down=None, distance=None, play_clock=None),
                {"clock", "score_home"})
    assert evs == []


def test_play_epoch_reset_prevents_cross_play_smoothing():
    s = _session()
    for _ in range(3):
        _live(s, _snap(down=1, distance=10), {"down", "distance"}, epoch=5)
    # a new play (epoch bumps): the first read of the new play must win outright,
    # not be out-voted by the previous play's buffered reads.
    evs = _live(s, _snap(down=3, distance=2), {"down", "distance"}, epoch=6)
    p = evs[0].payload
    assert p.down == 3 and p.distance == 2


def test_adapter_null_read_does_not_clobber_cache():
    ad = Madden26Adapter()                       # cheap: EasyOCR is lazy
    ad.context.detect = lambda frame: HudContext.LIVE_GAMEPLAY
    ad.ocr_cadence_schema = {                     # make `down` due every frame
        "dd": {"cadence": "every_n", "n": 1, "context": "live_gameplay",
               "fields": ["down"]},
    }
    queue = [{"down": 5}, {"down": None}, {"down": 7}]

    class _StubOCR:
        def read_fields(self, frame, fields):
            d = dict(queue.pop(0))
            d["_confidence"] = 0.9
            return d
    ad.ocr = _StubOCR()

    s = _session()
    frame = np.zeros((1080, 1920, 3), dtype=np.uint8)
    ad.process_frame(frame, s)                    # reads 5
    assert s.adapter_state["_ocr_cache"]["down"] == 5
    ad.process_frame(frame, s)                    # reads None -> keep 5
    assert s.adapter_state["_ocr_cache"]["down"] == 5
    ad.process_frame(frame, s)                    # reads 7
    assert s.adapter_state["_ocr_cache"]["down"] == 7
