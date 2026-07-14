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
from typing import TYPE_CHECKING

from app.core.envelope import make_envelope
from app.core.session import SessionContext
from app.core.temporal import TemporalSmoother
from app.schemas.enums import EventType
from app.schemas.events import EventEnvelope, Madden26Payload

from .formation_detector import FormationReading
from .ocr_pipeline import OCRSnapshot, _formation_to_canonical

if TYPE_CHECKING:
    from .coverage_classifier import CoverageReading

ADAPTER_VERSION = "madden26@0.0.1-phase-0"

# Live-gameplay HUD fields (smoothed under the live_gameplay context).
_LIVE_FIELDS = ("score_home", "score_away", "down", "distance",
                "field_position", "play_clock", "clock")


def _as_int(v: object) -> int | None:
    """Coerce a smoothed play-clock value (a digit-string like "40", an int, or
    None) to int for the payload. Never raises — a non-numeric/absent value emits
    null (null-HUD philosophy: degrade, don't fabricate or crash)."""
    if isinstance(v, bool):        # bool is an int subclass — exclude explicitly
        return None
    if isinstance(v, int):
        return v
    if isinstance(v, str) and v.isdigit():
        return int(v)
    return None


def _get_smoother(session: SessionContext) -> TemporalSmoother:
    sm = session.adapter_state.get("_smoother")
    if sm is None:
        sm = TemporalSmoother()
        session.adapter_state["_smoother"] = sm
    return sm


def _coverage_lock(
    session: SessionContext, smoother: TemporalSmoother, schema: dict,
    coverage: "CoverageReading | None", play_epoch: int, captured_at: datetime,
    st: dict,
) -> list[EventEnvelope]:
    """Mode-vote the pre-snap coach-cam coverage read and emit COVERAGE_LOCKED once per
    play when it locks (v0.3, OCR-of-play-call). Per-play reset: the smoother clears its
    window on the `cov:play<epoch>` context switch, and _last_locked_coverage is cleared
    when the play epoch advances so the same call re-locks on the next play. Carries the
    last-live game state (like FORMATION_LOCKED) so the event is coherent while the
    scorebug is hidden pre-snap."""
    if st.get("_cov_epoch") != play_epoch:            # new play -> allow a fresh lock
        st["_cov_epoch"] = play_epoch
        st["_last_locked_coverage"] = None
    if coverage is None or coverage.coverage is None:
        return []
    cfg = schema.get("defensive_coverage",
                     {"kind": "categorical", "window": 5, "min_window": 3})
    min_w = cfg.get("min_window", 1)
    locked = smoother.smooth("defensive_coverage", coverage.coverage, kind=cfg["kind"],
                             window=cfg["window"], min_window=min_w,
                             context=f"cov:play{play_epoch}")
    warm = smoother.samples("defensive_coverage") >= min_w
    if not (warm and locked and locked != st.get("_last_locked_coverage")):
        return []
    st["_last_locked_coverage"] = locked
    last_live = st.get("_last_live_state", {})
    payload = Madden26Payload(
        score_home=last_live.get("score_home"), score_away=last_live.get("score_away"),
        quarter=last_live.get("quarter"), clock=last_live.get("clock"),
        play_clock=_as_int(last_live.get("play_clock")), down=last_live.get("down"),
        distance=last_live.get("distance"), field_position=last_live.get("field_position"),
        possession="home",
        defensive_coverage=locked,                    # canonical, e.g. "Cover 3" / "Cover 2-Man"
    )
    return [make_envelope(session=session, event_type=EventType.COVERAGE_LOCKED,
                          payload=payload, confidence=coverage.confidence,
                          adapter_version=ADAPTER_VERSION, captured_at=captured_at)]


# Snap-boundary event confidence. The play-clock-freeze detector scores ~95% recall
# with ~2 FP / 90s clip (docs/phase-completions/snap-detector-m5b.md); PLAY_STARTED
# fires at the freeze-confirm frame. A fixed sub-1.0 confidence reflects that FP floor
# (the reset-vs-resume annotation that could refine it isn't known at snap time).
_SNAP_CONFIDENCE = 0.9


def _play_boundary_events(
    session: SessionContext, st: dict, snap_started: bool, snap_ended: bool,
    captured_at: datetime,
) -> list[EventEnvelope]:
    """Emit PLAY_STARTED / PLAY_ENDED from the snap-detector edges (M5b).

    PLAY_STARTED = the snap confirm (PRE_SNAP -> POST_SNAP); PLAY_ENDED = the prior
    play's post-snap freeze ending on the next play's reset tick (POST_SNAP -> PRE_SNAP).
    Both carry the last-live game state (like FORMATION_LOCKED / COVERAGE_LOCKED) so the
    down/distance/clock of the play travel with the event; the scorebug may be mid-
    transition on the boundary frame. Emitted UNGATED by the SNAPSHOT OCR-cadence gate
    (a snap on a hot, no-OCR frame must still fire). The two never co-occur on one frame
    (a reset tick and a freeze-confirm are distinct frames), but order deterministically:
    PLAY_ENDED (prior play) before PLAY_STARTED (new play)."""
    if not (snap_started or snap_ended):
        return []
    last_live = st.get("_last_live_state", {})

    def _payload() -> Madden26Payload:
        return Madden26Payload(
            score_home=last_live.get("score_home"), score_away=last_live.get("score_away"),
            quarter=last_live.get("quarter"), clock=last_live.get("clock"),
            play_clock=_as_int(last_live.get("play_clock")), down=last_live.get("down"),
            distance=last_live.get("distance"), field_position=last_live.get("field_position"),
            possession="home",
        )

    events: list[EventEnvelope] = []
    if snap_ended:
        events.append(make_envelope(
            session=session, event_type=EventType.PLAY_ENDED, payload=_payload(),
            confidence=_SNAP_CONFIDENCE, adapter_version=ADAPTER_VERSION,
            captured_at=captured_at))
    if snap_started:
        events.append(make_envelope(
            session=session, event_type=EventType.PLAY_STARTED, payload=_payload(),
            confidence=_SNAP_CONFIDENCE, adapter_version=ADAPTER_VERSION,
            captured_at=captured_at))
    return events


def assemble(
    session: SessionContext,
    ocr: OCRSnapshot,
    offense: FormationReading,
    captured_at: datetime,
    defense: FormationReading | None = None,
    coverage: "CoverageReading | None" = None,
    smoothing_schema: dict | None = None,
    *,
    context: str | None = None,
    updated_fields: set[str] | None = None,
    play_epoch: int = 0,
    snap_started: bool = False,
    snap_ended: bool = False,
) -> list[EventEnvelope]:
    if session.title is None:
        return []
    schema = smoothing_schema or {}
    st = session.adapter_state
    smoother = _get_smoother(session)

    # Context: explicit (from the cheap ContextDetector on the hot path) or, in
    # the legacy path, inferred from whether a formation name was read.
    if context is None:
        on_play_call = bool(offense.full_name or (defense and defense.full_name))
        context = "play_call" if on_play_call else "live_gameplay"
    prev_context = st.get("_hud_context")
    st["_hud_context"] = context
    if prev_context == "play_call" and context != "play_call":
        # left the play-call screen — reset so the next screen starts fresh.
        smoother.reset("offensive_formation")
        st["_last_locked_formation"] = None
        smoother.reset("defensive_formation")
        st["_last_locked_def_front"] = None

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
                # Carry the real last-live game state (may be null before the HUD
                # has ever read) rather than fabricating 0-0/0:00.
                score_home=last_live.get("score_home"),
                score_away=last_live.get("score_away"),
                quarter=last_live.get("quarter"),
                clock=last_live.get("clock"),
                play_clock=_as_int(last_live.get("play_clock")),
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

        # ---- defensive front (v0.2): the DEFENSIVE play-call screen carries the
        # committed front on the same card-subtitle line (disjoint vocab). Mode-vote
        # it across the screen and emit FORMATION_LOCKED once per screen, mirroring
        # the offensive path. Offense XOR defense reads on any one screen, so at most
        # one of these two blocks emits.
        if defense is not None and defense.formation:
            dcfg = schema.get("defensive_formation",
                              {"kind": "categorical", "window": 5, "min_window": 3})
            dmin_w = dcfg.get("min_window", 1)
            dlocked = smoother.smooth("defensive_formation", defense.formation,
                                      kind=dcfg["kind"], window=dcfg["window"],
                                      min_window=dmin_w, context="play_call")
            dwarm = smoother.samples("defensive_formation") >= dmin_w
            dlast = st.get("_last_locked_def_front")
            if dwarm and dlocked and dlocked != dlast:
                st["_last_locked_def_front"] = dlocked
                last_live = st.get("_last_live_state", {})
                payload = Madden26Payload(
                    score_home=last_live.get("score_home"),
                    score_away=last_live.get("score_away"),
                    quarter=last_live.get("quarter"),
                    clock=last_live.get("clock"),
                    play_clock=_as_int(last_live.get("play_clock")),
                    down=last_live.get("down"),
                    distance=last_live.get("distance"),
                    field_position=last_live.get("field_position"),
                    possession="home",
                    defensive_formation=dlocked,                   # canonical front, e.g. "3-4"
                )
                return [make_envelope(session=session, event_type=EventType.FORMATION_LOCKED,
                                      payload=payload, confidence=defense.confidence,
                                      adapter_version=ADAPTER_VERSION, captured_at=captured_at)]
        return []  # play-call screen up but formation not yet locked / unchanged.

    # ---- live_gameplay: smooth the FRESHLY-READ fields, carry the rest forward.
    # v0.3 coverage: the pre-snap coach-cam read (self-gated, cadenced) mode-votes into a
    # COVERAGE_LOCKED, emitted alongside whatever SNAPSHOT this frame produces.
    cov_events = _coverage_lock(session, smoother, schema, coverage, play_epoch,
                                captured_at, st)
    # Snap-boundary events (M5b): read the last-live state BEFORE this frame updates it,
    # so PLAY_STARTED carries the snapped play's pre-snap down/distance. These lead the
    # frame's events and are exempt from the SNAPSHOT OCR-cadence gate below.
    lead = _play_boundary_events(session, st, snap_started, snap_ended, captured_at) \
        + cov_events
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

    quarter = ocr.quarter or last_state.get("quarter")   # may be None (unreadable)
    # Graceful degrade: if NOTHING core was readable this cycle (menu / replay /
    # mis-region), skip the SNAPSHOT instead of emitting an all-null/fabricated one.
    # A PARTIAL read still emits, degrading field-by-field (null where unreadable).
    core = (sm["score_home"], sm["score_away"], sm["clock"], sm["down"], sm["distance"])
    if updated_fields is not None and not any(v is not None for v in core):
        st["_last_live_state"] = {f: sm[f] for f in _LIVE_FIELDS}
        st["_last_live_state"]["quarter"] = quarter
        return lead
    payload = Madden26Payload(
        score_home=sm["score_home"],        # nullable — no fabricated 0 on unreadable
        score_away=sm["score_away"],
        quarter=quarter,                    # very stable; not smoothed
        clock=sm["clock"],                  # nullable — no fabricated "0:00"
        play_clock=_as_int(sm["play_clock"]),  # smoothed CNN read; nullable
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
        return lead
    return lead + [make_envelope(session=session, event_type=EventType.SNAPSHOT,
                   payload=payload, confidence=ocr.confidence_overall,
                   adapter_version=ADAPTER_VERSION, captured_at=captured_at)]
