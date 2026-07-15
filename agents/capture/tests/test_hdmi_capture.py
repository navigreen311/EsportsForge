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


# ---------------------------------------------------------------------------
# Driver-recovery backoff (2026-07-15)
# ---------------------------------------------------------------------------


def _install_proc_sequence(monkeypatch, blob_lists: list[list[bytes]]) -> list:
    """Each Popen call serves the next blob-list (a spawn); an empty list => a
    proc that EOFs immediately (a FAILED OPEN). Returns the list of procs made."""
    procs: list = []
    seq = list(blob_lists)

    def _fake_popen(*_a, **_k):
        blobs = seq.pop(0) if seq else []  # extra spawns just fail (empty)
        proc = _FakeProc(_FakeStdout(list(blobs)))
        procs.append(proc)
        return proc

    monkeypatch.setattr(hdmi_capture.subprocess, "Popen", _fake_popen)
    return procs


def _record_sleeps(monkeypatch) -> list:
    sleeps: list = []
    monkeypatch.setattr(hdmi_capture.time, "sleep", lambda s, *_a, **_k: sleeps.append(s))
    return sleeps


def test_recovery_backoff_tiers():
    src = HdmiCaptureSource()
    # n==0 is a mid-stream drop (fast); 1..3 exponential; 4..6 steady; 7+ cooldown.
    expected = {
        0: 0.5, 1: 0.5, 2: 1.0, 3: 2.0,
        4: hdmi_capture._BACKOFF_MAX, 5: hdmi_capture._BACKOFF_MAX, 6: hdmi_capture._BACKOFF_MAX,
        7: hdmi_capture._BACKOFF_COOLDOWN, 12: hdmi_capture._BACKOFF_COOLDOWN,
    }
    for n, want in expected.items():
        src._failed_spawns = n
        assert src._recovery_backoff() == want, f"failed_spawns={n}"


def test_failed_opens_escalate_then_recover(_mock_ffmpeg):
    """7 consecutive failed opens escalate the backoff + warn once; the 8th
    spawn delivers a frame and clears the recovery state."""
    sleeps = _record_sleeps(_mock_ffmpeg)
    # 7 empty spawns (immediate EOF) then one good frame.
    _install_proc_sequence(_mock_ffmpeg, [[], [], [], [], [], [], [], [_frame_blob(60)]])
    src = HdmiCaptureSource(device_name="Fake Card")

    first = next(iter(src.frames()))
    src.close()

    assert int(first.image.mean()) == 60
    # Backoff tiers actually applied before each respawn: 0.5,1,2 then 5,5,5 then 30.
    assert sleeps == [0.5, 1.0, 2.0, 5.0, 5.0, 5.0, hdmi_capture._BACKOFF_COOLDOWN]
    # A frame arrived -> recovery state cleared.
    assert src._failed_spawns == 0
    assert src._wedge_warned is False


def test_wedge_warning_logged_once(_mock_ffmpeg, caplog):
    sleeps = _record_sleeps(_mock_ffmpeg)
    _install_proc_sequence(_mock_ffmpeg, [[], [], [], [], [], [], [], [_frame_blob(60)]])
    src = HdmiCaptureSource(device_name="Fake Card")

    import logging as _logging

    with caplog.at_level(_logging.ERROR, logger="capture.hdmi"):
        next(iter(src.frames()))
    src.close()

    replug = [r for r in caplog.records if r.getMessage() == "hdmi_device_unavailable_replug"]
    assert len(replug) == 1  # exactly one re-plug prompt per outage
    assert len(sleeps) == 7


def test_midstream_drop_recovers_fast_without_escalating(_mock_ffmpeg):
    """Frames flowing then a drop is NOT a failed open: fast (0.5 s) retry, no
    escalation, no wedge warning."""
    sleeps = _record_sleeps(_mock_ffmpeg)
    # spawn 1 delivers two frames then EOF; spawn 2 delivers one more.
    _install_proc_sequence(
        _mock_ffmpeg, [[_frame_blob(40), _frame_blob(50)], [_frame_blob(60)]]
    )
    src = HdmiCaptureSource(device_name="Fake Card")

    frames: list[Frame] = []
    for fr in src.frames():
        frames.append(fr)
        if len(frames) >= 3:
            break
    src.close()

    assert [int(f.image.mean()) for f in frames] == [40, 50, 60]
    assert sleeps == [0.5]  # single fast retry across the drop
    assert src._failed_spawns == 0
    assert src._wedge_warned is False
