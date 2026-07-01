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
        "down_distance": {"cadence": "every_n", "n": 12, "phase": 3,
                          "context": LIVE_GAMEPLAY,
                          "fields": ["down", "distance", "field_position"]},
        "clock": {"cadence": "every_n", "n": 10, "phase": 0, "context": LIVE_GAMEPLAY,
                  "fields": ["clock"]},
        "score_quarter": {"cadence": "every_n", "n": 40, "phase": 25,
                          "context": LIVE_GAMEPLAY,
                          "fields": ["score_home", "score_away", "quarter"]},
        # play_clock is not in the Phase-0 payload — it returns with the M5b snap
        # detector. Omitted here to keep OCR load off the hot path.
        "formation": {"cadence": "on_play_call", "max_reads_per_screen": 5,
                      "context": PLAY_CALL, "fields": ["offensive_formation"]},
    }

    def __init__(self) -> None:
        # Lazy-loaded once per worker. EasyOCR cold-load happens on first read.
        self.ocr = OCRPipeline()
        self.formations = FormationDetector()
        self.snap = SnapDetector()
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

        # 3. cadence scheduler decides which field-groups are due this frame.
        plan = self._scheduler(session, self.ocr_cadence_schema).tick(
            context=ctx, boundary=boundary)
        fields_due = plan["fields"]
        st["_last_tier"] = plan["tier"]        # read by the tier-aware gate (7.5.3)

        # 4. read ONLY the due fields.
        updated: set[str] = set()
        offense = FormationReading(formation=None, confidence=0.0, full_name=None)
        if context == HudContext.PLAY_CALL:
            if "offensive_formation" in fields_due:
                offense = self.formations.detect_offensive(frame)   # 1 OCR pass
        elif fields_due:                                            # live + something due
            reads = self.ocr.read_fields(frame, fields_due)
            st["_ocr_conf"] = reads.pop("_confidence", 0.0)
            # A null read = "couldn't read this field this frame" (occluded / between
            # plays) -> keep the last good cached value; don't clobber it with None.
            # Only non-null reads are "fresh" (smoothed + trigger a SNAPSHOT).
            fresh = {k: v for k, v in reads.items() if v is not None}
            st.setdefault("_ocr_cache", {}).update(fresh)
            updated = set(fresh.keys())

        # 5. snap detector (cheap stub for now).
        st["snap_state"] = self.snap.update(frame, st.get("snap_state"))

        # 6. assemble from the carried-forward snapshot; smooth only fresh fields.
        return assemble(
            session=session,
            ocr=self._snapshot_from_cache(session),
            offense=offense,
            captured_at=captured_at,
            smoothing_schema=self.smoothing_schema,
            context=ctx,
            updated_fields=updated,
            play_epoch=plan["epoch"],
        )
