"""Unit tests for the Phase 1a file-mode capture source.

Runs without a real video file or codec: `cv2.VideoCapture` is replaced with
a fake that yields synthetic numpy frames, so the tests exercise the source's
own logic (play-once, EOF, stride sampling, 1080p normalization) rather than
OpenCV's decoder.

Run:  cd agents/capture && python -m pytest tests/ -q
(requires the capture-agent deps: opencv-python-headless, numpy)
"""

from __future__ import annotations

import numpy as np
import pytest

cv2 = pytest.importorskip("cv2")  # skips the module if cv2 isn't installed

from capture_agent.capture.file_playback import (  # noqa: E402
    TARGET_HEIGHT,
    TARGET_WIDTH,
    FilePlaybackSource,
)


class _FakeCap:
    """Stand-in for cv2.VideoCapture yielding `n` frames of size (w, h) then EOF."""

    def __init__(self, n: int, fps: float, w: int, h: int) -> None:
        self._frames = [
            np.full((h, w, 3), (i % 256), dtype=np.uint8) for i in range(n)
        ]
        self._i = 0
        self._props = {
            cv2.CAP_PROP_FPS: fps,
            cv2.CAP_PROP_FRAME_COUNT: float(n),
            cv2.CAP_PROP_FRAME_WIDTH: float(w),
            cv2.CAP_PROP_FRAME_HEIGHT: float(h),
        }

    def isOpened(self) -> bool:
        return True

    def get(self, prop):
        return self._props.get(prop, 0.0)

    def read(self):
        if self._i >= len(self._frames):
            return False, None
        f = self._frames[self._i]
        self._i += 1
        return True, f

    def set(self, *_args):
        return True

    def release(self):
        pass


def _patch_cap(monkeypatch, cap, exists=True):
    monkeypatch.setattr(cv2, "VideoCapture", lambda *_a, **_k: cap)
    monkeypatch.setattr(
        "capture_agent.capture.file_playback.Path.exists", lambda self: exists
    )


def test_plays_once_and_signals_completion(monkeypatch):
    # 24 fps source, target 12 fps -> stride 2 -> 20 frames yields 10.
    _patch_cap(monkeypatch, _FakeCap(n=20, fps=24.0, w=1920, h=1080))
    src = FilePlaybackSource("clip.mp4", target_fps=12, playback_mode="max")

    frames = list(src.frames())

    assert len(frames) == 10
    assert src.frames_emitted == 10
    assert src.completed is True
    # Frame ids are monotonic from 1.
    assert [f.frame_id for f in frames] == list(range(1, 11))


def test_does_not_loop_forever(monkeypatch):
    # A bounded fake would hang the test if the source looped like TestVideoSource.
    _patch_cap(monkeypatch, _FakeCap(n=6, fps=12.0, w=1920, h=1080))
    src = FilePlaybackSource("clip.mp4", target_fps=12, playback_mode="max")
    assert len(list(src.frames())) == 6  # stride 1, single pass


def test_normalizes_non_1080p_to_1080p(monkeypatch):
    # 720p source must be upscaled to 1920x1080 for HUD alignment.
    _patch_cap(monkeypatch, _FakeCap(n=4, fps=12.0, w=1280, h=720))
    src = FilePlaybackSource("clip.mp4", target_fps=12, playback_mode="max")

    frames = list(src.frames())

    assert frames, "expected emitted frames"
    for f in frames:
        assert (f.width, f.height) == (TARGET_WIDTH, TARGET_HEIGHT)
        assert f.image.shape == (TARGET_HEIGHT, TARGET_WIDTH, 3)


def test_normalization_can_be_disabled(monkeypatch):
    _patch_cap(monkeypatch, _FakeCap(n=4, fps=12.0, w=1280, h=720))
    src = FilePlaybackSource(
        "clip.mp4", target_fps=12, playback_mode="max", normalize_1080p=False
    )
    f = next(src.frames())
    assert (f.width, f.height) == (1280, 720)


def test_missing_file_raises(monkeypatch):
    _patch_cap(monkeypatch, _FakeCap(n=1, fps=12.0, w=1920, h=1080), exists=False)
    src = FilePlaybackSource("nope.mp4")
    with pytest.raises(FileNotFoundError):
        src.open()


def test_invalid_playback_mode_rejected():
    with pytest.raises(ValueError):
        FilePlaybackSource("clip.mp4", playback_mode="turbo")


def test_device_label():
    assert FilePlaybackSource("a/b/madden26_yt_x.mp4").device_label == (
        "file:madden26_yt_x.mp4"
    )
