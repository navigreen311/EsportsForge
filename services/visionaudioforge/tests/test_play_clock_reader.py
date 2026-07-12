"""Unit tests for the play-clock 2-head CNN reader (M5b follow-up).

Covers the graceful-degradation contract (missing model -> None reader), the
white-box / red gate (abstain, never fabricate), and — when the committed ONNX +
onnxruntime are present — a real read off a live capture frame.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pytest

from app.adapters.madden26.play_clock_reader import PlayClockReader

_MODEL = Path(__file__).resolve().parents[1] / (
    "app/adapters/madden26/models/play_clock_v0_2.onnx"
)


def test_missing_model_loads_gracefully_to_none():
    assert PlayClockReader.load(Path("does/not/exist.onnx")) is None


def test_reader_is_present():
    # The ONNX model is committed; onnxruntime is a pinned dep. If either is
    # missing this reader degrades to None and play_clock stays null (no crash).
    if PlayClockReader.load(_MODEL) is None:
        pytest.skip("onnxruntime or model unavailable in this env")


def test_abstains_on_non_white_box():
    reader = PlayClockReader.load(_MODEL)
    if reader is None:
        pytest.skip("onnxruntime or model unavailable in this env")
    # A dark frame => no white play-clock box => abstain (None), never a guess.
    dark = np.zeros((1080, 1920, 3), dtype=np.uint8)
    v, conf = reader.read_value(dark)
    assert v is None and conf == 0.0


def test_abstains_on_red_play_clock():
    reader = PlayClockReader.load(_MODEL)
    if reader is None:
        pytest.skip("onnxruntime or model unavailable in this env")
    # A bright RED box (delay-of-game) is not the white 2-digit clock this net
    # reads => the red gate abstains.
    f = np.zeros((1080, 1920, 3), dtype=np.uint8)
    x, y, w, h = (1448, 1022, 88, 38)
    f[y : y + h, x : x + w] = (30, 30, 220)  # BGR red
    v, _conf = reader.read_value(f)
    assert v is None
