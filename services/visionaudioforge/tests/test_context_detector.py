"""ContextDetector rule tests (v2.4.0-ps5 recalibration).

The detector separates the pre-snap play-call overlay from live gameplay with two
cheap features: dark_frac (frame dimming) and green_low (green field in the lower card
band). Rule: play_call <=> 0.30 <= dark_frac <= 0.78 AND green_low < 0.30. These synthetic
frames reproduce the feature signatures measured on the PS5 feed (play-call: dark UI over
a covered field; live: green grass; menu/pause: near-black) — see the class docstring.
"""

from __future__ import annotations

import numpy as np

from app.adapters.madden26.context_detector import ContextDetector, HudContext

H, W = 1080, 1920
_CARD = slice(int(H * 0.55), int(H * 0.86))   # the lower-middle "card band"


def _frame(dark_top: float, card_bgr: tuple[int, int, int]) -> np.ndarray:
    """A frame with `dark_top` fraction of rows near-black (drives dark_frac) and the
    card band painted `card_bgr` (drives green_low). Non-dark rows are mid-grey."""
    f = np.full((H, W, 3), 110, np.uint8)
    f[: int(H * dark_top)] = 18
    f[_CARD] = card_bgr
    return f


def test_play_call_dark_ui_over_covered_field():
    # ~50% dimmed + card band is grey UI (no green) -> play_call.
    f = _frame(0.50, (90, 90, 90))
    assert ContextDetector().detect(f) == HudContext.PLAY_CALL


def test_live_gameplay_green_field():
    # Bright green field everywhere -> low dark_frac, high green_low -> live.
    f = np.full((H, W, 3), (0, 150, 0), np.uint8)
    assert ContextDetector().detect(f) == HudContext.LIVE_GAMEPLAY


def test_menu_or_pause_near_black_is_not_play_call():
    # Near-black menu/pause: dark_frac > 0.78 -> live (adapter degrades gracefully).
    f = np.full((H, W, 3), 12, np.uint8)
    assert ContextDetector().detect(f) == HudContext.LIVE_GAMEPLAY


def test_dark_frame_with_green_field_stays_live():
    # Defensive: a dim frame whose dark_frac lands in the band but whose field still
    # reads green (coach-cam / night gameplay) must NOT be misread as play_call.
    f = _frame(0.50, (0, 150, 0))
    d = ContextDetector().features(f)
    assert 0.30 <= d["dark_frac"] <= 0.78 and d["green_low"] >= 0.30
    assert ContextDetector().detect(f) == HudContext.LIVE_GAMEPLAY


def test_features_expose_both_keys():
    d = ContextDetector().features(_frame(0.5, (90, 90, 90)))
    assert set(d) == {"dark_frac", "green_low"}
