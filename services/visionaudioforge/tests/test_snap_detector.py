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


def _run(det: SnapDetector, level: int, n: int, *, grass: bool) -> int:
    """Feed n identical frames; return how many fired a snap."""
    fired = 0
    for _ in range(n):
        det.update(_frame(level, grass=grass), grass)
        fired += int(det.snapped)
    return fired


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
