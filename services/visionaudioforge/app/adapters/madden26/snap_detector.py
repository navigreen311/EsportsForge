"""Madden 26 snap detector — play-clock-freeze state machine (M5b).

The snap is signalled by the play-clock COUNTDOWN FREEZING — not by anything in
the gameplay pixels. Pre-snap the play-clock ticks down ~1/s; when the ball is
snapped it stops decrementing and holds at the snap value for the whole play,
then resets for the next play. Because it is a HUD signal it is immune to the
ball-following gameplay camera that confounds field-motion frame-diff (the same
camera that ceilinged the CNN formation classifier — ADR 0014). This was
established empirically: play-clock disappearance and field-motion were both
tried and ruled out on live capture; the freeze is what survives.

Detection (per session, per frame, no OCR):
  * tick   — a PEAK in the play-clock-zone frame-diff above a threshold (the
             digit changing); ~one per second while the clock counts down. Peak
             (not rising-edge) detection matters: a digit change smears the diff
             over a few frames, and keying on the rising edge skips ticks.
  * freeze — FREEZE_FRAMES with no tick after >=1 tick = a snap candidate.
  * gates  — a real snap's freeze is a live PLAY. Over the freeze window the
             context must be live_gameplay, the field (grass) must be on screen,
             and the play-clock must not be red. This rejects the freeze
             look-alikes: play-call screens (context), replay close-ups (no
             field), and delay-of-game (red :00 play-clock).

Validated on 8 live capture clips (61 labelled snaps, spanning field position /
tempo / red-zone / replays / delay-of-game): the real per-frame detector scores
**recall 58/61 = 95%** (meets the >=95% bar), ~18 FP across the set. Snap-time
granularity is ~1 s (the tick interval); the snap is dated to the last tick
before the freeze and confirmed ~FREEZE_FRAMES (1.5 s) later — inside the
snap+1-2 s window the coverage classifier samples.

KNOWN LIMITATION — false positives (~2 per 90 s clip). A play-clock that
briefly PAUSES/hitches mid-countdown (then resumes counting) freezes exactly
like a snap over this signal. The clean discriminator is what ENDS the freeze —
a real snap RESETS the clock to :40 (value up), a pause RESUMES it (value down) —
but that needs reading the play-clock VALUE (the deferred dark-on-white reader),
which the frame-diff signal cannot recover (measured: freeze duration and
reset-tick magnitude both fail to separate them). ~200 ms snap-time accuracy is
likewise a follow-up (needs a finer within-second cue). See
docs/phase-completions/snap-detector-m5b.md.

State machine: BETWEEN_PLAYS -> PRE_SNAP (clock ticking down) -> POST_SNAP
(frozen, play running) -> back to PRE_SNAP on the next play's reset tick.
``snapped`` is True only on the single frame a snap is confirmed.
"""

from __future__ import annotations

from collections import deque
from enum import Enum

import cv2
import numpy as np

# Zones on the 1920x1080 v2.3.0-live broadcast HUD.
_PLAY_CLOCK = (1450, 1002, 96, 44)
# Centre grass band — excludes the bottom HUD bar and the sidelines/crowd, so a
# replay close-up (a face, no field) reads near-zero grass.
_FIELD = (400, 300, 1120, 500)


class SnapState(str, Enum):
    BETWEEN_PLAYS = "BETWEEN_PLAYS"
    PRE_SNAP = "PRE_SNAP"
    POST_SNAP = "POST_SNAP"


class SnapDetector:
    """Per-session play-clock-freeze snap detector — ONE instance per session
    (state is on the instance; the adapter stores it in ``adapter_state``)."""

    TICK_TH = 4.0         # play-clock-zone mean-abs frame diff that counts as a tick
    DEBOUNCE = 15         # min frames between ticks (0.5 s @30fps)
    FREEZE_FRAMES = 45    # no tick for this long (1.5 s) after ticks = a freeze
    GREEN_MIN = 0.30      # min grass fraction during freeze (lowest real: 0.31)
    RED_MAX = 0.06        # max red fraction in the play-clock zone (delay-of-game)
    LIVE_MIN = 0.6        # min live_gameplay fraction during the freeze

    def __init__(self) -> None:
        self._prev_pc: np.ndarray | None = None
        self._since_tick = self.DEBOUNCE
        self._ticks_seen = 0
        self._d1 = 0.0  # play-clock-zone diff one frame ago (for peak detection)
        self._d2 = 0.0  # ...two frames ago
        self._state = SnapState.BETWEEN_PLAYS
        self._green: deque[float] = deque(maxlen=self.FREEZE_FRAMES)
        self._live: deque[bool] = deque(maxlen=self.FREEZE_FRAMES)
        self._red: deque[float] = deque(maxlen=self.FREEZE_FRAMES)
        self.snapped = False  # True only on the frame a snap is confirmed

    @staticmethod
    def _crop(frame: np.ndarray, box: tuple[int, int, int, int]) -> np.ndarray:
        x, y, w, h = box
        return frame[y : y + h, x : x + w]

    def _play_clock_diff(self, frame: np.ndarray) -> float:
        pc = cv2.cvtColor(self._crop(frame, _PLAY_CLOCK), cv2.COLOR_BGR2GRAY)
        if self._prev_pc is None:
            d = 0.0
        else:
            d = float(np.abs(pc.astype(int) - self._prev_pc.astype(int)).mean())
        self._prev_pc = pc
        return d

    def _field_green(self, frame: np.ndarray) -> float:
        roi = self._crop(frame, _FIELD).astype(int)
        b, g, r = roi[..., 0], roi[..., 1], roi[..., 2]
        return float(((g > r + 8) & (g > b + 8) & (g > 50) & (g < 200)).mean())

    def _red_play_clock(self, frame: np.ndarray) -> float:
        roi = self._crop(frame, _PLAY_CLOCK).astype(int)
        b, g, r = roi[..., 0], roi[..., 1], roi[..., 2]
        return float(((r > g + 40) & (r > b + 40) & (r > 90)).mean())

    def _freeze_is_a_snap(self) -> bool:
        """The buffered freeze window looks like a live play — not a play-call
        screen, a replay close-up, or a delay-of-game red clock."""
        if not self._green:
            return False
        green = sum(self._green) / len(self._green)
        live = sum(1 for x in self._live if x) / len(self._live)
        red = max(self._red) if self._red else 0.0
        return green > self.GREEN_MIN and live > self.LIVE_MIN and red < self.RED_MAX

    def update(self, frame: np.ndarray, live_gameplay: bool) -> SnapState:
        """Advance the state machine one frame. ``live_gameplay`` is the adapter's
        already-computed context read (so we don't re-run ContextDetector).
        Returns the new state; ``self.snapped`` is True on the confirmation frame.
        """
        self.snapped = False
        self._green.append(self._field_green(frame))
        self._live.append(live_gameplay)
        self._red.append(self._red_play_clock(frame))

        diff = self._play_clock_diff(frame)
        # Peak-based tick: the PREVIOUS frame's diff was a local max above the
        # threshold. A digit change smears the diff over a few frames; keying on
        # the rising edge alone skips ticks (the v0.1 recall gap). 1-frame
        # detection latency, uniform, so it does not shift relative snap timing.
        is_tick = (
            self._d1 >= self.TICK_TH
            and self._d1 >= self._d2
            and self._d1 >= diff
            and self._since_tick >= self.DEBOUNCE
        )
        self._d2, self._d1 = self._d1, diff
        if is_tick:
            # a digit changed: the clock is counting (a countdown tick or a reset)
            self._since_tick = 0
            self._ticks_seen = 1 if self._state == SnapState.POST_SNAP else self._ticks_seen + 1
            self._state = SnapState.PRE_SNAP
            return self._state

        self._since_tick += 1
        # freeze: the clock was ticking then stopped -> snap candidate. The
        # field/live/red gates below reject the freeze look-alikes (a play-clock
        # that reset to :40 and held sits during a replay -> no field / not live).
        if (
            self._state == SnapState.PRE_SNAP
            and self._ticks_seen >= 1
            and self._since_tick == self.FREEZE_FRAMES
        ):
            if self._freeze_is_a_snap():
                self.snapped = True
                self._state = SnapState.POST_SNAP
            else:
                self._state = SnapState.BETWEEN_PLAYS
                self._ticks_seen = 0
        return self._state
