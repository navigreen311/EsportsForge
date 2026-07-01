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

Post-PR-#62 review additions:
  - Per-session latency tracking (rolling deque of last 1000 frames'
    adapter elapsed_ms) for D3 + D4 measurement.
  - title_detector receives an OCR-text extractor so the Madden/CFB
    abbreviation tiebreaker (ADR 0007) is exercised in production.
"""

from __future__ import annotations

import logging
import time
from collections import deque
from datetime import datetime, timezone

import numpy as np

from app.core.integrity_gate import evaluate_frame
from app.core.session import SessionContext
from app.core.title_detector import TitleDetector
from app.schemas.events import EventEnvelope

logger = logging.getLogger("vaf.dispatcher")

LATENCY_WINDOW_FRAMES = 1000


def _ocr_text_for_tiebreaker(frame: np.ndarray, bbox: list[int]) -> str:
    """Read a single bbox via the Madden OCR pipeline's text reader.

    Imported lazily so unit tests that don't exercise the tiebreaker
    don't pay the EasyOCR cold-start cost.
    """
    from app.adapters.madden26 import ocr_pipeline

    cropped = ocr_pipeline._crop(frame, bbox)
    text, _conf = ocr_pipeline._read_text(cropped, "ABCDEFGHIJKLMNOPQRSTUVWXYZ")
    return text


class Dispatcher:
    """One Dispatcher per session.

    Owns the title detector for the session; the adapter is fetched
    fresh per frame from the registry (cheap — registry caches singletons).
    """

    def __init__(self, session: SessionContext) -> None:
        self.session = session
        self.title_detector = TitleDetector(
            ocr_text_extractor=_ocr_text_for_tiebreaker,
        )
        # Adapter-elapsed-ms ring for the last 1000 frames. Used by
        # GET /sessions/{id}/latency and the real-footage harness.
        self.latency_ms: deque[float] = deque(maxlen=LATENCY_WINDOW_FRAMES)
        # Per-tier rings (ADR 0015): the hot path (no OCR) and the sampled OCR
        # tier have different budgets, so they're reported separately.
        self.latency_by_tier: dict[str, deque[float]] = {
            "hot": deque(maxlen=LATENCY_WINDOW_FRAMES),
            "ocr": deque(maxlen=LATENCY_WINDOW_FRAMES),
        }

    @staticmethod
    def _pctiles(values) -> dict[str, float | int]:
        if not values:
            return {"count": 0, "p50_ms": 0.0, "p95_ms": 0.0, "p99_ms": 0.0}
        ordered = sorted(values)
        n = len(ordered)
        def pct(p: float) -> float:
            return round(ordered[min(n - 1, int(p * n))], 3)
        return {"count": n, "p50_ms": pct(0.50), "p95_ms": pct(0.95), "p99_ms": pct(0.99)}

    def latency_percentiles(self) -> dict[str, float | int | dict]:
        """p50/p95/p99 over all frames, plus a per-tier breakdown (ADR 0015)."""
        out = self._pctiles(self.latency_ms)
        out["by_tier"] = {t: self._pctiles(v) for t, v in self.latency_by_tier.items()}
        return out

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
        self.latency_ms.append(elapsed_ms)

        # Tier-aware budget (ADR 0015). The adapter signals which tier this frame
        # ran: "hot" (no OCR, 80ms budget) vs "ocr" (a sampled OCR read, its own
        # ~500ms budget). A hot-path frame over 80ms is a real "behind real time"
        # signal and drops; a scheduled OCR-tier frame is expected to be slower and
        # is NOT dropped for exceeding the hot-path budget — dropping it would throw
        # away the only frames that produce events (the Phase 0 zero-events failure).
        tier = self.session.adapter_state.get("_last_tier", "hot")
        self.latency_by_tier.get(tier, self.latency_by_tier["hot"]).append(elapsed_ms)
        budget = (getattr(adapter, "max_ocr_tier_ms", adapter.max_processing_ms)
                  if tier == "ocr" else adapter.max_processing_ms)

        if elapsed_ms > budget:
            logger.warning(
                "adapter_budget_breach",
                extra={
                    "title": self.session.title.value,
                    "elapsed_ms": elapsed_ms,
                    "budget_ms": budget,
                    "tier": tier,
                },
            )
            # Budget breach drops the frame (honest "behind real time" sentinel),
            # now evaluated against the frame's own tier budget.
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


