"""Title-agnostic OCR cadence scheduler (M5c sub-task 7.5.2).

The OCR-of-overlay adapter cannot afford to OCR every HUD field every frame
(~1s/frame on CPU EasyOCR). But it doesn't need to: HUD fields change at wildly
different natural rates. This scheduler decides, per dispatched frame, which
field-GROUPS to OCR — so the hot path runs OCR only when a field is actually due.

The engine is title-agnostic (Forge Rule 5): it lives in core/ and is driven by a
per-adapter `ocr_cadence_schema`. Cadence kinds:

  once_per_session  — read once on the first applicable frame, then never (team
                      abbreviations: constant for a game).
  every_n           — read every N dispatched frames, at an optional phase offset
                      (game clock ~1 Hz, play clock). Phasing keeps two every_n
                      groups from stacking onto the same frame.
  on_play_boundary  — read only when the play-boundary trigger fires (down /
                      distance / field-position: change once per play).
  on_play_call      — read each play-call frame up to `max_reads_per_screen`,
                      enough to mode-vote the formation, then idle until the next
                      screen (offensive formation).

Each group declares the `context` it belongs to (live_gameplay vs play_call);
groups whose context != the frame's context are never due. The frame's context
comes from the cheap ContextDetector (7.5.1), not OCR.

Play epochs: on each boundary the scheduler bumps `play_epoch`. Adapters tag the
smoother's live-field context with this epoch (e.g. "live:play7") so a field's
smoothing window RESETS at each play boundary — a new play's down/distance is
never mode-voted against the previous play's (7.5.4). This reuses the smoother's
existing context-switch reset; the scheduler is the single source of the epoch.

`tick()` returns which groups/fields are due plus the frame's tier: "ocr" if any
OCR runs this frame (subject to the tier budget, 7.5.3), else "hot" (no OCR).
"""

from __future__ import annotations

from dataclasses import dataclass

ONCE_PER_SESSION = "once_per_session"
EVERY_N = "every_n"
ON_PLAY_BOUNDARY = "on_play_boundary"
ON_PLAY_CALL = "on_play_call"

PLAY_CALL = "play_call"
LIVE_GAMEPLAY = "live_gameplay"


@dataclass
class _GroupState:
    session_done: bool = False       # once_per_session: has it fired?
    reads_this_screen: int = 0       # on_play_call: reads on the current screen
    last_read_frame: int = -1


class OcrCadenceScheduler:
    """Per-session OCR cadence. One instance per session.

    Stateless w.r.t. pixels — it only tracks frame counters and per-group
    bookkeeping. The adapter calls tick() once per frame with the detected
    context and whether a play-boundary fired this frame.
    """

    def __init__(self, schema: dict) -> None:
        self.schema = schema
        self._state: dict[str, _GroupState] = {g: _GroupState() for g in schema}
        self._frame = 0
        self._epoch = 0
        self._prev_context: str | None = None

    @property
    def play_epoch(self) -> int:
        return self._epoch

    @property
    def frame_index(self) -> int:
        return self._frame

    def tick(self, *, context: str, boundary: bool) -> dict:
        """Advance one frame; return the read plan.

        Returns {"groups": [names], "fields": set[str], "epoch": int,
                 "tier": "ocr"|"hot", "context": context}.
        """
        self._frame += 1

        # Leaving the play-call screen resets per-screen read counters so the
        # next screen re-reads its formation from scratch.
        if self._prev_context == PLAY_CALL and context != PLAY_CALL:
            for g, cfg in self.schema.items():
                if cfg.get("context") == PLAY_CALL:
                    self._state[g].reads_this_screen = 0

        # A play boundary starts a new epoch (drives the smoother reset).
        if boundary:
            self._epoch += 1

        due_groups: list[str] = []
        for g, cfg in self.schema.items():
            grp_ctx = cfg.get("context")
            if grp_ctx is not None and grp_ctx != context:
                continue
            if self._is_due(g, cfg, boundary):
                due_groups.append(g)

        fields: set[str] = set()
        for g in due_groups:
            self._mark_read(g)
            fields.update(self.schema[g]["fields"])

        self._prev_context = context
        return {"groups": due_groups, "fields": fields, "epoch": self._epoch,
                "tier": "ocr" if fields else "hot", "context": context}

    def _is_due(self, g: str, cfg: dict, boundary: bool) -> bool:
        st = self._state[g]
        cad = cfg["cadence"]
        if cad == ONCE_PER_SESSION:
            return not st.session_done
        if cad == EVERY_N:
            n = cfg["n"]
            phase = cfg.get("phase", 0) % n
            return (self._frame % n) == phase
        if cad == ON_PLAY_BOUNDARY:
            return boundary
        if cad == ON_PLAY_CALL:
            return st.reads_this_screen < cfg.get("max_reads_per_screen", 5)
        return False

    def _mark_read(self, g: str) -> None:
        st = self._state[g]
        cad = self.schema[g]["cadence"]
        st.last_read_frame = self._frame
        if cad == ONCE_PER_SESSION:
            st.session_done = True
        elif cad == ON_PLAY_CALL:
            st.reads_this_screen += 1

    def reset(self) -> None:
        """Full reset (session teardown / re-open)."""
        self._state = {g: _GroupState() for g in self.schema}
        self._frame = 0
        self._epoch = 0
        self._prev_context = None
