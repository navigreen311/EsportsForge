"""Unit tests for the title-agnostic OCR cadence scheduler (M5c sub-task 7.5.2)."""

from app.core.ocr_cadence import (
    LIVE_GAMEPLAY, PLAY_CALL, OcrCadenceScheduler,
)

SCHEMA = {
    "team_abbrevs": {"cadence": "once_per_session", "context": LIVE_GAMEPLAY,
                     "fields": ["team_home_abbr", "team_away_abbr"]},
    "down_distance": {"cadence": "on_play_boundary", "context": LIVE_GAMEPLAY,
                      "fields": ["down", "distance", "field_position"]},
    "clock": {"cadence": "every_n", "n": 10, "phase": 0, "context": LIVE_GAMEPLAY,
              "fields": ["clock"]},
    "play_clock": {"cadence": "every_n", "n": 10, "phase": 5, "context": LIVE_GAMEPLAY,
                   "fields": ["play_clock"]},
    "formation": {"cadence": "on_play_call", "max_reads_per_screen": 5,
                  "context": PLAY_CALL, "fields": ["offensive_formation"]},
}


def _sched():
    return OcrCadenceScheduler(SCHEMA)


def test_once_per_session_fires_once():
    s = _sched()
    first = s.tick(context=LIVE_GAMEPLAY, boundary=False)
    assert "team_abbrevs" in first["groups"]
    for _ in range(20):
        r = s.tick(context=LIVE_GAMEPLAY, boundary=False)
        assert "team_abbrevs" not in r["groups"]


def test_every_n_phase_offset_no_stacking():
    s = _sched()
    clock_frames, pc_frames = [], []
    for _ in range(30):
        r = s.tick(context=LIVE_GAMEPLAY, boundary=False)
        if "clock" in r["groups"]:
            clock_frames.append(s.frame_index)
        if "play_clock" in r["groups"]:
            pc_frames.append(s.frame_index)
    # clock on frame 10,20,30 (frame%10==0); play_clock on 5,15,25 (phase 5)
    assert clock_frames == [10, 20, 30]
    assert pc_frames == [5, 15, 25]
    assert not set(clock_frames) & set(pc_frames)   # never the same frame


def test_on_play_boundary_only_fires_on_boundary_and_bumps_epoch():
    s = _sched()
    r = s.tick(context=LIVE_GAMEPLAY, boundary=False)
    assert "down_distance" not in r["groups"] and r["epoch"] == 0
    r = s.tick(context=LIVE_GAMEPLAY, boundary=True)
    assert "down_distance" in r["groups"] and r["epoch"] == 1
    assert {"down", "distance", "field_position"} <= r["fields"]
    r = s.tick(context=LIVE_GAMEPLAY, boundary=True)
    assert r["epoch"] == 2                              # each boundary = new epoch


def test_context_gating_live_vs_play_call():
    s = _sched()
    live = s.tick(context=LIVE_GAMEPLAY, boundary=False)
    assert "formation" not in live["groups"]           # play_call group idle on live
    pc = s.tick(context=PLAY_CALL, boundary=False)
    assert "formation" in pc["groups"]                 # live groups idle on play_call
    assert "clock" not in pc["groups"] and "down_distance" not in pc["groups"]


def test_on_play_call_caps_reads_then_resets_next_screen():
    s = _sched()
    fired = 0
    for _ in range(8):                                  # more than max_reads_per_screen=5
        if "formation" in s.tick(context=PLAY_CALL, boundary=False)["groups"]:
            fired += 1
    assert fired == 5                                   # capped at 5 reads/screen
    # leave to live, then a new play-call screen re-reads from scratch
    s.tick(context=LIVE_GAMEPLAY, boundary=False)
    fired2 = sum(1 for _ in range(8)
                 if "formation" in s.tick(context=PLAY_CALL, boundary=False)["groups"])
    assert fired2 == 5


def test_tier_is_hot_when_nothing_due():
    s = _sched()
    tiers = [s.tick(context=LIVE_GAMEPLAY, boundary=False)["tier"] for _ in range(10)]
    # frame 1: team_abbrevs (once) -> ocr; frame 5: play_clock (phase 5) -> ocr;
    # frame 10: clock (frame%10==0) -> ocr; all other frames: hot (no OCR).
    assert tiers == ["ocr", "hot", "hot", "hot", "ocr", "hot", "hot", "hot", "hot", "ocr"]
    # most live frames do no OCR at all -> the hot path stays cheap.
    assert tiers.count("hot") == 7
