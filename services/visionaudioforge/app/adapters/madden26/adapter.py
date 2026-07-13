"""Madden 26 adapter v0.1 — entry point implementing TitleAdapter.

Composes context detection + sampled OCR + formation detection + snap detection
+ state assembly.

Adapter version: madden26@0.0.1-phase-0
Budget (ADR 0006 -> ADR 0015 tiered): hot-path <=80 ms every frame; OCR-tier
sampled frames <=500 ms and exempt from the hot-path drop.
Cadence: football archetype, 12 fps base / 24 max (ADR 0005).
Integrity policy: Tournament = no processing, Ranked disables FORMATION_LOCKED,
Broadcast redacts opponent data.

Per-frame flow (M5c sub-task 7.5 — sampled-OCR cadence):
  1. ContextDetector.detect(frame)         — ~0.7ms, no OCR (7.5.1)
  2. PlayBoundaryTrigger.update(...)        — cheap frame-diff proxy (7.5.5)
  3. OcrCadenceScheduler.tick(...)          — which field-groups are due (7.5.2)
  4. read ONLY the due fields               — OCRPipeline.read_fields / detect_offensive
  5. merge with the per-session cache       — carry unread fields forward
  6. assemble(...)                          — smooth fresh fields, emit events
Most live frames read no OCR at all (tier "hot"); OCR runs only on cadence.
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone

from app.adapters.base import CadenceProfile, IntegrityPolicy
from app.core.ocr_cadence import (
    LIVE_GAMEPLAY, PLAY_CALL, OcrCadenceScheduler,
)
from app.core.session import SessionContext
from app.schemas.enums import EventType, IntegrityMode, TitleEnum
from app.schemas.events import EventEnvelope

from .context_detector import ContextDetector, HudContext
from .formation_detector import FormationDetector, FormationReading
from .ocr_pipeline import OCRPipeline, OCRSnapshot
from .play_boundary import PlayBoundaryTrigger
from .snap_detector import SnapDetector
from .state_assembler import ADAPTER_VERSION, assemble

logger = logging.getLogger("vaf.adapters.madden26")


class Madden26Adapter:
    """Implements TitleAdapter. Singleton — instantiated once per worker."""

    title: TitleEnum = TitleEnum.MADDEN26
    version: str = ADAPTER_VERSION
    max_processing_ms: int = 80          # ADR 0006 hot-path tier (ADR 0015)
    max_ocr_tier_ms: int = 500           # ADR 0015 sampled-OCR tier

    cadence: CadenceProfile = CadenceProfile(
        name="football",
        preferred_base_fps=12,
        preferred_max_fps=24,
        snap_interruption_rule="duck_only",
    )

    integrity_rules: dict = {
        IntegrityMode.OFFLINE_LAB: IntegrityPolicy.unrestricted(),
        IntegrityMode.RANKED: IntegrityPolicy(
            disable_event_types=frozenset({EventType.FORMATION_LOCKED}),
        ),
        IntegrityMode.TOURNAMENT: IntegrityPolicy(no_processing=True),
        IntegrityMode.BROADCAST: IntegrityPolicy(opponent_data_redacted=True),
    }

    # Temporal-smoothing schema (M5c sub-task 6; retuned for sampled cadence in
    # 7.5.4). Windows are over SAMPLED reads, not frames. Boundary-triggered
    # fields use a small window (trust the fresh per-play read; the play-epoch
    # context reset prevents cross-play smoothing).
    smoothing_schema: dict = {
        # play_call context — the formation read off the play-call overlay.
        "offensive_formation": {"kind": "categorical", "window": 5, "min_window": 3},
        # play_call context — the committed defensive FRONT read off the defensive
        # play-call screen's coverage-card subtitle (v0.2; OCR-of-play-call pivot).
        "defensive_formation": {"kind": "categorical", "window": 5, "min_window": 3},
        # live (pre-snap) context — the committed defensive COVERAGE read off the
        # coach-cam play-art (v0.3; OCR-of-play-call pivot).
        "defensive_coverage": {"kind": "categorical", "window": 5, "min_window": 3},
        # live_gameplay context — sampled HUD OCR fields.
        "field_position":      {"kind": "numeric",      "window": 3, "min_window": 1},
        "down":                {"kind": "categorical", "window": 3, "min_window": 1},
        "distance":            {"kind": "numeric",      "window": 3, "min_window": 1},
        "score_home":          {"kind": "numeric",      "window": 3, "min_window": 1},
        "score_away":          {"kind": "numeric",      "window": 3, "min_window": 1},
        "play_clock":          {"kind": "numeric",      "window": 3, "min_window": 1},
        "clock":               {"kind": "string_clock", "window": 3, "min_window": 1},
    }

    # OCR cadence schema (M5c sub-task 7.5.2). Each group declares its context,
    # cadence, and the fields it reads. Frame counters are DISPATCHED frames
    # (~12 fps football base), so every_n:10 ~= 0.8s.
    ocr_cadence_schema: dict = {
        "team_abbrevs": {"cadence": "once_per_session", "context": LIVE_GAMEPLAY,
                         "fields": ["team_home_abbr", "team_away_abbr"]},
        # down/distance/field-position change once per play, but read on a low-Hz
        # every_n (not on_play_boundary): the boundary PROXY is imprecise (Phase 0
        # stub) and a single boundary read often lands on a mid-transition/null
        # frame. Periodic reads catch the value whenever the HUD shows it; the
        # play-epoch reset (still driven by the boundary) keeps a new play's read
        # from smoothing against the prior play's. (7.5.5 finding.)
        # field_position parked for the live path (v2.3.0-live — no analog on the
        # broadcast bar); down+distance read from one merged region.
        "down_distance": {"cadence": "every_n", "n": 12, "phase": 3,
                          "context": LIVE_GAMEPLAY,
                          "fields": ["down", "distance"]},
        "clock": {"cadence": "every_n", "n": 10, "phase": 0, "context": LIVE_GAMEPLAY,
                  "fields": ["clock"]},
        "score_quarter": {"cadence": "every_n", "n": 40, "phase": 25,
                          "context": LIVE_GAMEPLAY,
                          "fields": ["score_home", "score_away", "quarter"]},
        # play_clock — dark-on-white 2-head CNN reader (cheap ONNX, ~ms). Read at a
        # brisk cadence: it feeds the payload AND the snap-detector reset-vs-resume
        # FP annotation, which needs the value to move soon after a snap freeze.
        "play_clock": {"cadence": "every_n", "n": 6, "phase": 6,
                       "context": LIVE_GAMEPLAY, "fields": ["play_clock"]},
        # Read the formation periodically across the WHOLE play-call screen (not a
        # capped burst): the old on_play_call cap of 5 was spent during
        # formation-select BROWSING and never reached the play-select subtitle
        # (the committed formation). every_n:9 (~0.75s @12fps) samples browse +
        # play-select; the smoother mode-votes the committed formation. (v2.3.0-live)
        "formation": {"cadence": "every_n", "n": 9, "phase": 4,
                      "context": PLAY_CALL, "fields": ["offensive_formation"]},
        # Coverage — coach-cam play-art OCR (v0.3). Pre-snap LIVE context, cadenced
        # because the band read is a full EasyOCR pass (costly); the adapter further
        # gates it to the pre-snap window (post-play-call, pre-snap) and detect_coverage
        # self-gates to None when the coach-cam play-art isn't up.
        "coverage": {"cadence": "every_n", "n": 9, "phase": 7,
                     "context": LIVE_GAMEPLAY, "fields": ["defensive_coverage"]},
    }

    def __init__(self) -> None:
        # Lazy-loaded once per worker. EasyOCR cold-load happens on first read.
        self.ocr = OCRPipeline()
        self.formations = FormationDetector()
        self.context = ContextDetector()      # stateless — shared across sessions
        logger.info("madden26_adapter_loaded", extra={"version": self.version})

    # --- per-session state helpers -----------------------------------------

    @staticmethod
    def _scheduler(session: SessionContext, schema: dict) -> OcrCadenceScheduler:
        s = session.adapter_state.get("_cadence")
        if s is None:
            s = OcrCadenceScheduler(schema)
            session.adapter_state["_cadence"] = s
        return s

    @staticmethod
    def _boundary(session: SessionContext) -> PlayBoundaryTrigger:
        b = session.adapter_state.get("_boundary")
        if b is None:
            b = PlayBoundaryTrigger()
            session.adapter_state["_boundary"] = b
        return b

    @staticmethod
    def _snap(session: SessionContext) -> SnapDetector:
        # SnapDetector holds per-session state (play-clock tick history), so it
        # lives per session in adapter_state, not as a shared adapter field.
        s = session.adapter_state.get("_snap")
        if s is None:
            s = SnapDetector()
            session.adapter_state["_snap"] = s
        return s

    @staticmethod
    def _snapshot_from_cache(session: SessionContext) -> OCRSnapshot:
        c = session.adapter_state.get("_ocr_cache", {})
        return OCRSnapshot(
            score_home=c.get("score_home"), score_away=c.get("score_away"),
            quarter=c.get("quarter"), clock=c.get("clock"),
            play_clock=c.get("play_clock"), down=c.get("down"),
            distance=c.get("distance"), field_position=c.get("field_position"),
            team_home_abbr=c.get("team_home_abbr"), team_away_abbr=c.get("team_away_abbr"),
            confidence_overall=session.adapter_state.get("_ocr_conf", 0.0),
        )

    def process_frame(
        self,
        frame,  # np.ndarray
        session: SessionContext,
    ) -> list[EventEnvelope]:
        """Single-frame sampled-OCR pipeline."""
        captured_at = datetime.now(timezone.utc)
        st = session.adapter_state

        # 1. hot-path context detection (no OCR).
        context = self.context.detect(frame)
        ctx = context.value

        # 2. play-boundary proxy (cheap frame-diff; no OCR).
        left_play_call = st.get("_prev_ctx") == PLAY_CALL and ctx != PLAY_CALL
        boundary = self._boundary(session).update(
            frame, context=ctx, left_play_call=left_play_call)
        st["_prev_ctx"] = ctx
        # Pre-snap window (post play-call, before the snap) — the only time the coach-cam
        # play-art is up, so the only time it's worth paying for a coverage read.
        if left_play_call:
            st["_presnap"] = True

        # 3. cadence scheduler decides which field-groups are due this frame.
        plan = self._scheduler(session, self.ocr_cadence_schema).tick(
            context=ctx, boundary=boundary)
        fields_due = plan["fields"]
        st["_last_tier"] = plan["tier"]        # read by the tier-aware gate (7.5.3)

        # 4. read ONLY the due fields.
        updated: set[str] = set()
        offense = FormationReading(formation=None, confidence=0.0, full_name=None)
        defense = FormationReading(formation=None, confidence=0.0, full_name=None)
        coverage = None
        if context == HudContext.PLAY_CALL:
            if "offensive_formation" in fields_due:
                # The play-call screen is offensive XOR defensive; read both and let
                # the (disjoint) vocabulary decide which one has a real reading.
                offense = self.formations.detect_offensive(frame)      # 1 OCR pass
                defense = self.formations.detect_defensive_front(frame)  # 1 OCR pass
        elif fields_due:                                            # live + something due
            hud_fields = set(fields_due)
            # v0.3 coverage — coach-cam play-art read, PRE-SNAP only (bounds the costly
            # EasyOCR band pass); detect_coverage self-gates to None off the coach-cam.
            if "defensive_coverage" in hud_fields:
                hud_fields.discard("defensive_coverage")
                if st.get("_presnap"):
                    coverage = self.formations.detect_coverage(frame)
            if hud_fields:                                          # HUD fields still due
                reads = self.ocr.read_fields(frame, hud_fields)
                st["_ocr_conf"] = reads.pop("_confidence", 0.0)
                # A null read = "couldn't read this field this frame" (occluded / between
                # plays) -> keep the last good cached value; don't clobber it with None.
                # Only non-null reads are "fresh" (smoothed + trigger a SNAPSHOT).
                fresh = {k: v for k, v in reads.items() if v is not None}
                st.setdefault("_ocr_cache", {}).update(fresh)
                updated = set(fresh.keys())

        # 5. snap detector (play-clock-freeze; cheap, no OCR). Reuses the context
        #    read from step 1. The cached play-clock value (from the CNN reader,
        #    refreshed on cadence) drives the reset-vs-resume FP annotation.
        #    snap.snapped is True on the frame a snap confirms.
        pc_cached = st.get("_ocr_cache", {}).get("play_clock")
        pc_value = int(pc_cached) if pc_cached is not None else None
        snap = self._snap(session)
        st["snap_state"] = snap.update(
            frame, context == HudContext.LIVE_GAMEPLAY, pc_value)
        if snap.snapped:
            st["_last_snap_frame"] = session.frame_count
            st["_presnap"] = False       # snap fired — coach-cam window is over
        st["_last_snap_pause"] = snap.last_snap_pause

        # 6. assemble from the carried-forward snapshot; smooth only fresh fields.
        return assemble(
            session=session,
            ocr=self._snapshot_from_cache(session),
            offense=offense,
            defense=defense,
            coverage=coverage,
            captured_at=captured_at,
            smoothing_schema=self.smoothing_schema,
            context=ctx,
            updated_fields=updated,
            play_epoch=plan["epoch"],
        )
