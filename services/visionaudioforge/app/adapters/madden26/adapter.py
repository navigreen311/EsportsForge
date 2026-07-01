"""Madden 26 adapter v0.1 — entry point implementing TitleAdapter.

Composes OCR + formation detection + snap detection + state assembly.
Phase 0: the inner pieces are stubbed; the composition is real.

Adapter version: madden26@0.0.1-phase-0
Budget: 80 ms per frame (ADR 0006 — v0.1 tier).
Cadence: football archetype, 12 fps base / 24 max (ADR 0005).
Integrity policy: per Madden's adapter spec — Tournament = no processing,
Ranked disables FORMATION_LOCKED, Broadcast redacts opponent data.
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone

from app.adapters.base import CadenceProfile, IntegrityPolicy
from app.core.session import SessionContext
from app.schemas.enums import EventType, IntegrityMode, TitleEnum
from app.schemas.events import EventEnvelope

from .formation_detector import FormationDetector
from .ocr_pipeline import OCRPipeline
from .snap_detector import SnapDetector
from .state_assembler import ADAPTER_VERSION, assemble

logger = logging.getLogger("vaf.adapters.madden26")


class Madden26Adapter:
    """Implements TitleAdapter. Singleton — instantiated once per worker."""

    title: TitleEnum = TitleEnum.MADDEN26
    version: str = ADAPTER_VERSION
    max_processing_ms: int = 80  # ADR 0006 — v0.1 tier

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

    # Temporal-smoothing schema (M5c sub-task 6). Categorical fields -> mode-vote,
    # numeric -> median, across a per-field window; windows reset on the
    # live_gameplay <-> play_call context switch. See app/core/temporal.py. The
    # engine is title-agnostic; this schema is the only Madden-specific config.
    smoothing_schema: dict = {
        # play_call context — the formation read off the play-call overlay.
        "offensive_formation": {"kind": "categorical", "window": 5, "min_window": 3},
        # live_gameplay context — the in-play HUD OCR fields.
        "field_position":      {"kind": "numeric",      "window": 7, "min_window": 4},
        "down":                {"kind": "categorical", "window": 5, "min_window": 3},
        "distance":            {"kind": "numeric",      "window": 5, "min_window": 3},
        "score_home":          {"kind": "numeric",      "window": 3, "min_window": 1},
        "score_away":          {"kind": "numeric",      "window": 3, "min_window": 1},
        "play_clock":          {"kind": "numeric",      "window": 3, "min_window": 1},
        "clock":               {"kind": "string_clock", "window": 3, "min_window": 2},
    }

    def __init__(self) -> None:
        # Lazy-loaded once per worker. Real ML model loads happen here in
        # Phase 1 M5c. Phase 0 — cheap.
        self.ocr = OCRPipeline()
        self.formations = FormationDetector()
        self.snap = SnapDetector()
        logger.info("madden26_adapter_loaded", extra={"version": self.version})

    def process_frame(
        self,
        frame,  # np.ndarray
        session: SessionContext,
    ) -> list[EventEnvelope]:
        """Single-frame pipeline.

        Phase 0: every frame produces one SNAPSHOT event with stub data.
        Phase 1 will add diffing against session.adapter_state to emit
        only changes (SCORE_CHANGE, DOWN_AND_DISTANCE, FORMATION_LOCKED).
        """

        captured_at = datetime.now(timezone.utc)

        ocr = self.ocr.read_frame(frame)
        offense = self.formations.detect_offensive(frame)

        # Snap detector update; result feeds future PLAY_STARTED/PLAY_ENDED
        # event emission. Phase 0 doesn't act on it yet.
        prior_snap = session.adapter_state.get("snap_state")
        new_snap = self.snap.update(frame, prior_snap)
        session.adapter_state["snap_state"] = new_snap

        return assemble(
            session=session,
            ocr=ocr,
            offense=offense,
            captured_at=captured_at,
            smoothing_schema=self.smoothing_schema,
        )
