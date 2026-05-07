"""Per-frame dispatch loop.

For each frame received from an agent:
  1. Validate session.
  2. Frame-level integrity gate.
  3. Title detection (once per session).
  4. Adapter dispatch (with per-frame budget enforcement).
  5. Event-level integrity policy applied.
  6. Publish events to subscribers.

Phase 0 wires steps 1–5; step 6 (webhook delivery to EsportsForge
backend) is stubbed until M3 lands.
"""

from __future__ import annotations

import logging
import time
from datetime import datetime, timezone

import numpy as np

from app.core.integrity_gate import evaluate_frame
from app.core.session import SessionContext
from app.core.title_detector import TitleDetector
from app.schemas.events import EventEnvelope

logger = logging.getLogger("vaf.dispatcher")


class Dispatcher:
    """One Dispatcher per session.

    Owns the title detector for the session; the adapter is fetched
    fresh per frame from the registry (cheap — registry caches singletons).
    """

    def __init__(self, session: SessionContext) -> None:
        self.session = session
        self.title_detector = TitleDetector()

    def process_frame(self, frame: np.ndarray) -> list[EventEnvelope]:
        """Run the full dispatch loop for one frame.

        Returns the list of events to publish. Empty list = nothing to do
        (frame dropped at gate, no adapter for title, etc.). Never raises;
        any adapter error is logged and turned into an empty list.
        """
        self.session.frame_count += 1

        # 1. Frame-level integrity gate (uses last-known title for ranked
        #    title-blocking; unknown title gets the OFFLINE_LAB / RANKED
        #    default treatment).
        gate = evaluate_frame(self.session.integrity_mode, self.session.title)
        if not gate.process:
            self._log_integrity_drop(gate.reason)
            return []

        # 2. Title detection (locks once confident).
        if self.session.title is None:
            hint = self.session.adapter_state.get("_active_title_hint")
            result = self.title_detector.detect(frame, active_title_hint=hint)
            if result.title is not None and result.confidence >= 0.85:
                self.session.title = result.title
                self.session.title_confidence = result.confidence
                self.session.title_locked_at = datetime.now(timezone.utc)
                logger.info(
                    "title_locked",
                    extra={
                        "session_id": self.session.session_id,
                        "title": result.title.value,
                        "confidence": result.confidence,
                        "method": result.method,
                    },
                )
            else:
                # Not yet confident — wait for more frames.
                return []

        # 3. Adapter dispatch. Lazy import to avoid circular at module-load.
        from app.adapters.registry import get_adapter

        adapter = get_adapter(self.session.title)
        if adapter is None:
            logger.warning(
                "no_adapter_for_title",
                extra={"title": self.session.title.value},
            )
            return []

        # 4. Per-frame budget enforcement (ADR 0006).
        start = time.monotonic()
        try:
            events = adapter.process_frame(frame, self.session)
        except Exception as exc:  # noqa: BLE001
            logger.exception(
                "adapter_raised",
                extra={
                    "title": self.session.title.value,
                    "version": adapter.version,
                    "exc_type": type(exc).__name__,
                },
            )
            return []
        elapsed_ms = (time.monotonic() - start) * 1000.0

        if elapsed_ms > adapter.max_processing_ms:
            logger.warning(
                "adapter_budget_breach",
                extra={
                    "title": self.session.title.value,
                    "elapsed_ms": elapsed_ms,
                    "budget_ms": adapter.max_processing_ms,
                },
            )
            # Per spec: budget breaches drop the frame. We've already
            # paid the cost, but we don't publish the events to keep
            # the sentinel "we're behind real time" signal honest.
            return []

        # 5. Event-level integrity policy.
        policy = adapter.integrity_rules.get(self.session.integrity_mode)
        if policy is not None:
            if policy.no_processing:
                return []
            if policy.disable_event_types:
                events = [e for e in events if e.event_type not in policy.disable_event_types]

        return events

    def _log_integrity_drop(self, reason: str) -> None:
        # Audit-trail entry per ADR 0007 / spec §6 audit trail.
        logger.info(
            "integrity_drop",
            extra={
                "session_id": self.session.session_id,
                "user_id_hash": self.session.user_id_hash,
                "mode": self.session.integrity_mode.value,
                "reason": reason,
            },
        )


