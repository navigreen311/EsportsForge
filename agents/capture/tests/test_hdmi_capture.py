"""Unit tests for the HDMI capture-card source — hardware-free.

Runs with NO capture card: `subprocess.Popen` is replaced with a fake whose
stdout yields synthetic raw bgr24 bytes for a couple of 1920x1080 frames, so the
tests exercise the source's own logic (frame assembly, contract shape, id/timestamp,
subprocess teardown, ffmpeg-absent error) without ffmpeg or a device.

Run:  cd agents/capture && python -m pytest tests/ -q
(requires: numpy, opencv-python-headless — the latter only because the capture
package __init__ imports the cv2-based file source alongside this one.)
"""

from __future__ import annotations

import numpy as np
import pytest

pytest.importorskip("cv2")  # capture package __init__ pulls in the cv2 file source
pytest.importorskip("numpy")

from capture_agent.capture import hdmi_capture  # noqa: E402
from capture_agent.capture.base import Frame  # noqa: E402
from capture_agent.capture.hdmi_capture import (  # noqa: E402
    TARGET_HEIGHT,
    TARGET_WIDTH,
    HdmiCaptureSource,
)

_FRAME_BYTES = TARGET_WIDTH * TARGET_HEIGHT * 3


def _frame_blob(fill: int) -> bytes:
    return np.full((TARGET_HEIGHT, TARGET_WIDTH, 3), fill, dtype=np.uint8).tobytes()


class _FakeStdout:
    """Serves concatenated frame blobs in arbitrary-size reads, then EOF (b'')."""

    def __init__(self, blobs: list[bytes]) -> None:
        self._buf = b"".join(blobs)
        self.closed = False

    def read(self, n: int) -> bytes:
        out, self._buf = self._buf[:n], self._buf[n:]
        return out  # b'' once exhausted => EOF, mimicking a dead pipe

    def close(self) -> None:
        self.closed = True


class _FakeProc:
    def __init__(self, stdout: _FakeStdout) -> None:
        self.stdout = stdout
        self.terminated = self.waited = self.killed = False

    def terminate(self) -> None:
        self.terminated = True

    def wait(self, timeout=None) -> int:
        self.waited = True
        return 0

    def kill(self) -> None:
        self.killed = True


@pytest.fixture
def _mock_ffmpeg(monkeypatch):
    """Present ffmpeg, a monotonic clock that never drops frames, no real sleeps."""
    monkeypatch.setattr(hdmi_capture.shutil, "which", lambda _b: "ffmpeg")
    clock = {"t": 0.0}

    def _mono():
        clock["t"] += 10.0  # big steps => pacing gate always passes (no drops)
        return clock["t"]

    monkeypatch.setattr(hdmi_capture.time, "monotonic", _mono)
    monkeypatch.setattr(hdmi_capture.time, "sleep", lambda *_a, **_k: None)
    return monkeypatch


def _install_proc(monkeypatch, blobs: list[bytes]) -> dict:
    holder: dict = {}

    def _fake_popen(*_a, **_k):
        proc = _FakeProc(_FakeStdout(list(blobs)))
        holder["proc"] = proc
        return proc

    monkeypatch.setattr(hdmi_capture.subprocess, "Popen", _fake_popen)
    return holder


def test_frames_match_contract(_mock_ffmpeg):
    _install_proc(_mock_ffmpeg, [_frame_blob(50), _frame_blob(90)])
    src = HdmiCaptureSource(device_name="Fake Card", target_fps=12)
    frames: list[Frame] = []
    for fr in src.frames():
        frames.append(fr)
        if len(frames) >= 2:
            break
    src.close()

    assert len(frames) == 2
    ids = [f.frame_id for f in frames]
    assert ids == [1, 2]  # monotonic + unique, 1-based
    for f, fill in zip(frames, (50, 90)):
        assert isinstance(f, Frame)
        assert f.image.shape == (TARGET_HEIGHT, TARGET_WIDTH, 3)
        assert f.image.dtype == np.uint8
        assert f.width == TARGET_WIDTH and f.height == TARGET_HEIGHT
        assert f.captured_at is not None and f.captured_at.tzinfo is not None
        assert int(f.image.mean()) == fill  # BGR bytes passed through intact
    assert src.device_label == "hdmi:Fake Card"


def test_close_tears_down_subprocess(_mock_ffmpeg):
    holder = _install_proc(_mock_ffmpeg, [_frame_blob(50)])
    src = HdmiCaptureSource(device_name="Fake Card")
    src.open()
    proc = holder["proc"]
    src.close()
    assert proc.terminated is True
    assert proc.stdout.closed is True
    assert src._proc is None


def test_open_raises_when_ffmpeg_absent(monkeypatch):
    monkeypatch.setattr(hdmi_capture.shutil, "which", lambda _b: None)
    src = HdmiCaptureSource()
    with pytest.raises(RuntimeError, match="ffmpeg not found"):
        src.open()
