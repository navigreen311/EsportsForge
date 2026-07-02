"""Unit tests for the title-agnostic TemporalSmoother (M5c sub-task 6)."""

from app.core.temporal import TemporalSmoother, apply_schema, CATEGORICAL, NUMERIC


def _cat(sm, values, window=5, min_window=3, context="c"):
    out = None
    for v in values:
        out = sm.smooth("f", v, kind=CATEGORICAL, window=window,
                        min_window=min_window, context=context)
    return out


def test_categorical_mode_vote_outvotes_single_misread():
    sm = TemporalSmoother()
    # 4 "trips" + 1 stray "bunch" -> mode is "trips"
    assert _cat(sm, ["trips", "trips", "bunch", "trips", "trips"]) == "trips"


def test_min_window_passes_through_until_warm():
    sm = TemporalSmoother()
    # min_window=3: first two return the raw value, not a vote
    assert sm.smooth("f", "a", kind=CATEGORICAL, window=5, min_window=3) == "a"
    assert sm.smooth("f", "b", kind=CATEGORICAL, window=5, min_window=3) == "b"
    # third warms up -> mode of [a, b, a] once we add another a
    assert sm.smooth("f", "a", kind=CATEGORICAL, window=5, min_window=3) == "a"


def test_numeric_median_ignores_outlier_and_keeps_format():
    sm = TemporalSmoother()
    # field_position "+41" x3, one misread "+47" -> median picks the "+41" string
    for v in ["+41", "+41", "+47", "+41"]:
        out = sm.smooth("fp", v, kind=NUMERIC, window=7, min_window=4, context="live")
    assert out == "+41"


def test_none_not_buffered_but_returns_estimate():
    sm = TemporalSmoother()
    for v in ["trips", "trips", "trips"]:
        sm.smooth("f", v, kind=CATEGORICAL, window=5, min_window=3)
    # a frame that failed to read (None) should still return the smoothed estimate
    assert sm.smooth("f", None, kind=CATEGORICAL, window=5, min_window=3) == "trips"


def test_context_switch_resets_window():
    sm = TemporalSmoother()
    for v in ["trips", "trips", "trips"]:
        sm.smooth("f", v, kind=CATEGORICAL, window=5, min_window=3, context="play_call")
    assert sm.current_context("f") == "play_call"
    # switching context clears the window: a single "bunch" in the new context
    # is returned as-is (window not yet warm), NOT mode-voted against old trips.
    out = sm.smooth("f", "bunch", kind=CATEGORICAL, window=5, min_window=3, context="live")
    assert out == "bunch"
    assert sm.current_context("f") == "live"


def test_explicit_reset():
    sm = TemporalSmoother()
    for v in ["a", "a", "a"]:
        sm.smooth("f", v, kind=CATEGORICAL, window=5, min_window=3)
    sm.reset("f")
    assert sm.current_context("f") is None
    assert sm.smooth("f", "b", kind=CATEGORICAL, window=5, min_window=3) == "b"


def test_apply_schema_only_touches_schema_fields():
    sm = TemporalSmoother()
    schema = {"down": {"kind": "categorical", "window": 3, "min_window": 1}}
    out = apply_schema(sm, {"down": 2, "clock": "3:00"}, schema, context="live")
    assert out["down"] == 2
    assert out["clock"] == "3:00"  # not in schema -> untouched
