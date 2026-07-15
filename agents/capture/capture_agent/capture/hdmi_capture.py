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

**Driver-recovery backoff (2026-07-15).** A generic USB dshow card can *wedge* if
you open/close it too fast when the device is gone/busy (the failure then needs a
physical re-plug). So recovery distinguishes two cases by whether the dead ffmpeg
proc ever delivered a frame:
  - **Mid-stream drop** (frames were flowing, then stopped — a cable knock, brief
    rest): recover FAST (0.5 s), because the device is fine and signal usually
    returns in seconds.
  - **Failed open** (ffmpeg died before a single frame — device busy/gone): this
    is the churn that wedges the driver, so consecutive failed opens escalate the
    backoff through tiers (0.5→1→2 s, then 5 s, then a 30 s cooldown) and, once in
    the cooldown tier, log a loud "re-plug the card" once. We never hard-exit — a
    re-plug recovers automatically and logs ``hdmi_recovered`` — but a prolonged
    absence pokes dshow at most once per 30 s instead of the old once per 5 s.
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
_BACKOFF_COOLDOWN = 30.0        # prolonged failed-open: stop churning (potentially wedging) dshow
_QUICK_RETRIES = 3             # failed opens 1..3 use fast exponential backoff (0.5→1→2 s)
_STEADY_RETRIES = 6            # 4..6 hold at _BACKOFF_MAX; 7+ escalate to the cooldown tier


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
        # Driver-recovery state.
        self._failed_spawns = 0        # consecutive spawns that delivered ZERO frames
        self._frames_since_spawn = 0   # frames the CURRENT ffmpeg proc has delivered
        self._wedge_warned = False     # "re-plug the card" logged once per outage

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
        self._frames_since_spawn = 0  # this proc has delivered nothing yet
        logger.info(
            "hdmi_ffmpeg_spawned",
            extra={"device": self.device_name, "wh": (self.width, self.height)},
        )

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

    def _recovery_backoff(self) -> float:
        """Backoff before the next respawn, escalating with consecutive failed opens.

        Mid-stream drops (``_failed_spawns == 0``) recover fast; a device that
        never opens escalates through tiers to a long cooldown so we stop
        hammering — and potentially wedging — the dshow driver.
        """
        n = self._failed_spawns
        if n <= _QUICK_RETRIES:
            # n==0 (mid-stream drop) or 1..3: 0.5, 0.5, 1, 2 s.
            return min(_BACKOFF_INITIAL * (2 ** max(n - 1, 0)), _BACKOFF_MAX)
        if n <= _STEADY_RETRIES:
            return _BACKOFF_MAX
        return _BACKOFF_COOLDOWN

    def _restart(self, backoff: float) -> None:
        logger.warning(
            "hdmi_restarting",
            extra={"backoff_s": round(backoff, 2), "failed_spawns": self._failed_spawns},
        )
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

        while not self._closed:
            buf = self._read_exact(self._frame_bytes)
            if buf is None:  # process/read failure -> recover
                if self._closed:
                    break
                if self._frames_since_spawn == 0:
                    # ffmpeg died before delivering a single frame -> a FAILED OPEN
                    # (device busy/gone). This is the churn that can wedge dshow, so
                    # escalate the backoff and, past the steady tier, ask for a re-plug.
                    self._failed_spawns += 1
                    if self._failed_spawns == _STEADY_RETRIES + 1 and not self._wedge_warned:
                        logger.error(
                            "hdmi_device_unavailable_replug",
                            extra={
                                "device": self.device_name,
                                "failed_opens": self._failed_spawns,
                                "cooldown_s": _BACKOFF_COOLDOWN,
                            },
                        )
                        self._wedge_warned = True
                else:
                    # Frames WERE flowing, then stopped -> a mid-stream drop; recover fast.
                    self._failed_spawns = 0
                self._restart(self._recovery_backoff())
                next_due = time.monotonic()
                continue

            # A full frame arrived: the device is open and delivering. If we were
            # recovering from failed opens, announce the recovery and reset.
            if self._frames_since_spawn == 0 and self._failed_spawns:
                logger.info("hdmi_recovered", extra={"after_failed_opens": self._failed_spawns})
                self._failed_spawns = 0
                self._wedge_warned = False
            self._frames_since_spawn += 1

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
