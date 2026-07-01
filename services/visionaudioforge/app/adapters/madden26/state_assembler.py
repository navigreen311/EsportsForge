"""Madden 26 state assembler — temporal smoothing + event emission.

Two HUD contexts drive two event paths (M5c sub-task 6, ADR 0014):

  * live_gameplay — the in-play scorebug/down-distance is visible. Smooth the
    OCR fields (categorical mode / numeric median) via the title-agnostic
    TemporalSmoother and emit a SNAPSHOT with the smoothed game state.
  * play_call — the play-call overlay is up (the formation name is readable, the
    scorebug is NOT). Mode-vote the formation across the ~3-5s the screen shows,
    and emit FORMATION_LOCKED once per screen (when the locked formation differs
    from the last emitted). No SNAPSHOT — the game HUD is not on screen.

Sampled-OCR cadence (M5c sub-task 7.5): with the cadence scheduler, most live
frames read NO OCR fields — the fields carry forward from the last sampled read.
So the assembler smooths only the fields FRESHLY read this frame (`updated_fields`)
and carries the last smoothed value forward for the rest; the smoother's window is
therefore the last K *sampled* reads, not the last K frames. A SNAPSHOT is emitted
only when something was actually read (`updated_fields` non-empty) so hot-path
frames don't spam unchanged snapshots. Live-field smoothing is tagged with the
play epoch (`live:play{N}`, from the scheduler) so a field's window RESETS at each
play boundary — a new play's down/distance is never mode-voted against the prior
play's (reuses the smoother's context-switch reset, 7.5.4).

Backward-compatible: when called without the cadence params (context/updated_fields/
play_epoch), it infers the context and smooths+emits every frame as before.
"""

from __future__ import annotations

from datetime import datetime

from app.core.envelope import make_envelope
from app.core.session import SessionContext
from app.core.temporal import TemporalSmoother
from app.schemas.enums import EventType
from app.schemas.events import EventEnvelope, Madden26Payload

from .formation_detector import FormationReading
from .ocr_pipeline import OCRSnapshot, _formation_to_canonical

ADAPTER_VERSION = "madden26@0.0.1-phase-0"

# Live-gameplay HUD fields (smoothed under the live_gameplay context).
_LIVE_FIELDS = ("score_home", "score_away", "down", "distance",
                "field_position", "play_clock", "clock")


def _get_smoother(session: SessionContext) -> TemporalSmoother:
    sm = session.adapter_state.get("_smoother")
    if sm is None:
        sm = TemporalSmoother()
        session.adapter_state["_smoother"] = sm
    return sm


def assemble(
    session: SessionContext,
    ocr: OCRSnapshot,
    offense: FormationReading,
    captured_at: datetime,
    smoothing_schema: dict | None = None,
    *,
    context: str | None = None,
    updated_fields: set[str] | None = None,
    play_epoch: int = 0,
) -> list[EventEnvelope]:
    if session.title is None:
        return []
    schema = smoothing_schema or {}
    st = session.adapter_state
    smoother = _get_smoother(session)

    # Context: explicit (from the cheap ContextDetector on the hot path) or, in
    # the legacy path, inferred from whether a formation name was read.
    if context is None:
        context = "play_call" if offense.full_name else "live_gameplay"
    prev_context = st.get("_hud_context")
    st["_hud_context"] = context
    if prev_context == "play_call" and context != "play_call":
        # left the play-call screen — reset so the next screen starts fresh.
        smoother.reset("offensive_formation")
        st["_last_locked_formation"] = None

    # ---- play_call: mode-vote formation, emit FORMATION_LOCKED once per screen.
    if context == "play_call":
        cfg = schema.get("offensive_formation",
                         {"kind": "categorical", "window": 5, "min_window": 3})
        min_w = cfg.get("min_window", 1)
        locked = smoother.smooth("offensive_formation", offense.full_name,
                                 kind=cfg["kind"], window=cfg["window"],
                                 min_window=min_w, context="play_call")
        # Only lock once the window is warm — so a first-frame misread doesn't
        # emit before the mode-vote can outvote it.
        warm = smoother.samples("offensive_formation") >= min_w
        last = st.get("_last_locked_formation")
        if warm and locked and locked != last:
            st["_last_locked_formation"] = locked
            last_live = st.get("_last_live_state", {})
            payload = Madden26Payload(
                score_home=last_live.get("score_home", 0),
                score_away=last_live.get("score_away", 0),
                quarter=last_live.get("quarter", 1),
                clock=last_live.get("clock", "0:00"),
                down=last_live.get("down"),
                distance=last_live.get("distance"),
                field_position=last_live.get("field_position"),
                possession="home",
                offensive_formation=locked,                       # full Madden name
                offensive_formation_family=_formation_to_canonical(locked),  # canonical-8
            )
            return [make_envelope(session=session, event_type=EventType.FORMATION_LOCKED,
                                  payload=payload, confidence=offense.confidence,
                                  adapter_version=ADAPTER_VERSION, captured_at=captured_at)]
        return []  # play-call screen up but formation not yet locked / unchanged.

    # ---- live_gameplay: smooth the FRESHLY-READ fields, carry the rest forward.
    epoch_ctx = f"live:play{play_epoch}"
    last_state = st.get("_last_live_state", {})
    sm: dict = {}
    for f in _LIVE_FIELDS:
        fresh = (updated_fields is None) or (f in updated_fields)
        raw = getattr(ocr, f)
        cfg = schema.get(f)
        if not fresh:
            # not sampled this frame — carry the last smoothed value forward.
            sm[f] = last_state.get(f, raw)
        elif cfg:
            sm[f] = smoother.smooth(f, raw, kind=cfg["kind"], window=cfg["window"],
                                    min_window=cfg.get("min_window", 1), context=epoch_ctx)
        else:
            sm[f] = raw

    quarter = ocr.quarter or last_state.get("quarter") or 1
    payload = Madden26Payload(
        score_home=sm["score_home"] or 0,
        score_away=sm["score_away"] or 0,
        quarter=quarter,                    # very stable; not smoothed
        clock=sm["clock"] or "0:00",
        down=sm["down"],
        distance=sm["distance"],
        field_position=sm["field_position"],
        possession="home",                  # Phase 0 placeholder
        offensive_formation=None,           # formation only comes from the play-call screen
        offensive_formation_family=None,
    )
    # Remember the smoothed live state (so a FORMATION_LOCKED can carry a coherent
    # game state while the scorebug is hidden, and so carry-forward has a source).
    st["_last_live_state"] = {f: sm[f] for f in _LIVE_FIELDS}
    st["_last_live_state"]["quarter"] = quarter

    # Emit gating: on the sampled-cadence path, a hot-path frame reads nothing —
    # don't emit an unchanged SNAPSHOT. (Legacy path: updated_fields is None -> emit.)
    if updated_fields is not None and not updated_fields:
        return []
    return [make_envelope(session=session, event_type=EventType.SNAPSHOT,
                          payload=payload, confidence=ocr.confidence_overall,
                          adapter_version=ADAPTER_VERSION, captured_at=captured_at)]
