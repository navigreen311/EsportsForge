"""HDMI capture-card source via an ffmpeg subprocess.

Discovery (2026-07-07) proved the on-hand generic ``USB3.0 Video`` card
(MacroSilicon-style, vid_345f&pid_2130) is native **1920x1080 MJPEG** and that
**OpenCV's ``VideoCapture`` cannot grab it** — DSHOW *and* MSMF, every forced
format, returned black stuck at a 720p fallback — while **ffmpeg captures it
perfectly** at 1080p. So this source shells out to ffmpeg (dshow input) and
reads raw ``bgr24`` frames off stdout, rather than the ``cv2.CAP_DSHOW`` path
the ``base`` module originally sketched (that path is ruled out for this
hardware). See docs/adr / the distance-to-done recon for the discovery trail.

It implements the same ``CaptureSource`` protocol as ``FilePlaybackSource`` so
it is a drop-in — nothing downstream changes. Native 1080p means no resize is
needed (the Madden HUD regions are calibrated at 1080p, ADR 0013).

Key difference from the file source: this is a **live, unbounded** feed that can
drop (PS5 rest mode, channel change, cable knock). On ffmpeg process death or a
short/failed read it **restarts the subprocess with backoff** instead of
treating it as EOF. A black-but-alive stream (no-signal while ffmpeg keeps
delivering black frames) is *logged* rather than restart-churned — real frames
resume automatically when signal returns, so restarting ffmpeg would be futile
churn (see ``_note_black``). Restart is reserved for actual process/read failure.
"""

from __future__ import annotations

import logging
import shutil
import subprocess
import time
from datetime import datetime, timezone
from typing import Iterator

import numpy as np

from .base import Frame

logger = logging.getLogger("capture.hdmi")

DEFAULT_DEVICE_NAME = "USB3.0 Video"
TARGET_WIDTH = 1920
TARGET_HEIGHT = 1080
_CHANNELS = 3
_BLACK_MEAN_THRESH = 3.0        # mean pixel < this ≈ no-signal black (probe: black~1.4, signal~38)
_BLACK_WARN_AFTER = 60          # consecutive black reads before logging "signal appears lost"
_BACKOFF_INITIAL = 0.5
_BACKOFF_MAX = 5.0


class HdmiCaptureSource:
    """Live HDMI capture via ffmpeg (dshow) → raw bgr24 frames → ``Frame``s."""

    def __init__(
        self,
        device_name: str = DEFAULT_DEVICE_NAME,
        target_fps: int = 12,
        width: int = TARGET_WIDTH,
        height: int = TARGET_HEIGHT,
        ffmpeg_bin: str = "ffmpeg",
    ) -> None:
        self.device_name = device_name
        self.target_fps = max(int(target_fps), 1)
        self.width = int(width)
        self.height = int(height)
        self.ffmpeg_bin = ffmpeg_bin

        self._frame_bytes = self.width * self.height * _CHANNELS
        self._proc: subprocess.Popen[bytes] | None = None
        self._frame_id = 0
        self._closed = False
        self._black_run = 0
        self._black_warned = False

    @property
    def device_label(self) -> str:
        return f"hdmi:{self.device_name}"

    def _command(self) -> list[str]:
        # dshow addresses devices by NAME (there is no cv2-style numeric index
        # in the ffmpeg/dshow path); -video_size pins 1080p so we never fall
        # back to the black 720p mode OpenCV got stuck on.
        return [
            self.ffmpeg_bin, "-hide_banner", "-loglevel", "error",
            "-f", "dshow",
            "-rtbufsize", "100M",
            "-video_size", f"{self.width}x{self.height}",
            "-i", f"video={self.device_name}",
            "-pix_fmt", "bgr24", "-f", "rawvideo", "pipe:1",
        ]

    def _spawn(self) -> None:
        self._proc = subprocess.Popen(
            self._command(),
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
        )
        logger.info("hdmi_ffmpeg_spawned", extra={"device": self.device_name,
                                                   "wh": (self.width, self.height)})

    def open(self) -> None:
        if shutil.which(self.ffmpeg_bin) is None:
            raise RuntimeError(
                f"ffmpeg not found on PATH ({self.ffmpeg_bin!r}); the HDMI source "
                "requires ffmpeg (this card is not grabbable via OpenCV)."
            )
        self._closed = False
        self._spawn()

    def close(self) -> None:
        self._closed = True
        self._teardown_proc()

    def _teardown_proc(self) -> None:
        proc, self._proc = self._proc, None
        if proc is None:
            return
        try:
            if proc.stdout is not None:
                proc.stdout.close()
        except Exception:
            pass
        proc.terminate()
        try:
            proc.wait(timeout=3)
        except Exception:
            proc.kill()

    def _read_exact(self, n: int) -> bytes | None:
        """Read exactly n bytes from ffmpeg stdout; None on EOF/proc death."""
        assert self._proc is not None and self._proc.stdout is not None
        buf = bytearray()
        stdout = self._proc.stdout
        while len(buf) < n:
            chunk = stdout.read(n - len(buf))
            if not chunk:  # EOF — ffmpeg exited (device gone/busy/error)
                return None
            buf.extend(chunk)
        return bytes(buf)

    def _restart(self, backoff: float) -> None:
        logger.warning("hdmi_signal_lost_restarting", extra={"backoff_s": round(backoff, 2)})
        self._teardown_proc()
        time.sleep(backoff)
        self._black_run = 0
        self._black_warned = False
        self._spawn()

    def _note_black(self, mean: float) -> None:
        self._black_run += 1
        if self._black_run == _BLACK_WARN_AFTER and not self._black_warned:
            logger.warning("hdmi_signal_appears_black", extra={"mean_brightness": round(mean, 2)})
            self._black_warned = True

    def frames(self) -> Iterator[Frame]:
        """Yield live Frames at ~target_fps, restarting ffmpeg on failure."""
        if self._proc is None:
            self.open()
        period = 1.0 / self.target_fps
        next_due = time.monotonic()
        backoff = _BACKOFF_INITIAL

        while not self._closed:
            buf = self._read_exact(self._frame_bytes)
            if buf is None:  # process/read failure -> recover
                if self._closed:
                    break
                self._restart(backoff)
                backoff = min(backoff * 2, _BACKOFF_MAX)
                next_due = time.monotonic()
                continue
            backoff = _BACKOFF_INITIAL  # a full frame arrived; reset recovery backoff

            image = np.frombuffer(buf, dtype=np.uint8).reshape(
                self.height, self.width, _CHANNELS
            )
            mean = float(image.mean())
            if mean < _BLACK_MEAN_THRESH:
                self._note_black(mean)
            else:
                self._black_run = 0
                self._black_warned = False

            # Drain-and-pace: we read every frame off the pipe (keeps latency
            # low), but only *emit* at target_fps; drop the rest.
            now = time.monotonic()
            if now < next_due:
                continue
            next_due = max(next_due + period, now)

            self._frame_id += 1
            yield Frame(
                frame_id=self._frame_id,
                captured_at=datetime.now(timezone.utc),
                image=image.copy(),  # own the buffer (downstream batches/holds it)
                width=self.width,
                height=self.height,
            )
