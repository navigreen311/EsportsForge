"""Unit tests for the play-clock-freeze snap detector (M5b).

Synthetic frames: a play-clock zone whose grey level we flip to fake a digit
"tick", over a controllable field band (grass vs not). Exercises the state
machine — countdown ticks then a freeze fires a snap when the freeze is a live
grass play, and does not when it is a replay-style non-field freeze.
"""

from __future__ import annotations

import numpy as np

from app.adapters.madden26.snap_detector import SnapDetector, SnapState

_PC = (1450, 1002, 96, 44)
_FIELD = (400, 300, 1120, 500)


def _frame(pc_level: int, *, grass: bool) -> np.ndarray:
    f = np.zeros((1080, 1920, 3), dtype=np.uint8)
    fx, fy, fw, fh = _FIELD
    f[fy : fy + fh, fx : fx + fw] = (30, 180, 40) if grass else (40, 40, 40)  # BGR
    x, y, w, h = _PC
    f[y : y + h, x : x + w] = pc_level
    return f


def _run(det: SnapDetector, level: int, n: int, *, grass: bool,
         pc: int | None = None) -> int:
    """Feed n identical frames; return how many fired a snap."""
    fired = 0
    for _ in range(n):
        det.update(_frame(level, grass=grass), grass, pc)
        fired += int(det.snapped)
    return fired


def _drive_to_snap(det: SnapDetector, pc: int) -> None:
    """Countdown ticks then a grass freeze -> one confirmed snap, capturing ``pc``
    as the plateau play-clock value at confirmation."""
    _run(det, 100, 20, grass=True, pc=pc)
    _run(det, 150, 25, grass=True, pc=pc)                       # tick 1
    _run(det, 100, 25, grass=True, pc=pc)                       # tick 2
    _run(det, 100, det.FREEZE_FRAMES + 1, grass=True, pc=pc)    # hold -> freeze -> snap
    assert det._state == SnapState.POST_SNAP


def test_countdown_then_freeze_on_grass_fires_one_snap():
    det = SnapDetector()
    # two countdown ticks (grey flips), spaced past the debounce, on grass
    _run(det, 100, 20, grass=True)
    _run(det, 150, 25, grass=True)          # tick 1
    _run(det, 100, 25, grass=True)          # tick 2, then it starts to freeze
    assert det._state == SnapState.PRE_SNAP
    fired = _run(det, 100, det.FREEZE_FRAMES + 5, grass=True)  # hold -> freeze
    assert fired == 1
    assert det._state == SnapState.POST_SNAP


def test_freeze_off_grass_is_not_a_snap():
    det = SnapDetector()
    _run(det, 100, 20, grass=False)
    _run(det, 150, 25, grass=False)         # tick 1
    _run(det, 100, 25, grass=False)         # tick 2
    fired = _run(det, 100, det.FREEZE_FRAMES + 5, grass=False)  # replay-style hold
    assert fired == 0                        # no field -> gate rejects


def test_static_feed_never_snaps():
    det = SnapDetector()
    fired = _run(det, 100, 200, grass=True)  # no ticks at all
    assert fired == 0
    assert det._state == SnapState.BETWEEN_PLAYS


def test_play_clock_resume_flags_snap_as_pause():
    # A snap confirms with the play-clock plateaued at :25. If the clock then
    # RESUMES counting DOWN (24, 23, ...) it was a pause, not a snap.
    det = SnapDetector()
    _drive_to_snap(det, pc=25)
    assert det.last_snap_pause is None                     # undetermined at confirm
    for v in (24, 23, 22):                                 # clock resumes DOWN
        det.update(_frame(100, grass=True), True, v)
    assert det.last_snap_pause is True


def test_play_clock_frozen_then_reset_is_a_real_snap():
    # A real snap holds the clock at the plateau for the whole play, then the next
    # play resets it UP to :40 — never resumes down, so it is NOT flagged a pause.
    det = SnapDetector()
    _drive_to_snap(det, pc=25)
    for v in (25, 25, 25, 40, 40):                         # frozen then reset up
        det.update(_frame(100, grass=True), True, v)
    assert det.last_snap_pause is None


def test_reset_vs_resume_is_inert_without_pc_value():
    # Without a play-clock value the detector runs exactly as before (OCR-free):
    # no pause annotation is ever raised.
    det = SnapDetector()
    _drive_to_snap(det, pc=None)
    for _ in range(10):
        det.update(_frame(100, grass=True), True, None)
    assert det.last_snap_pause is None
