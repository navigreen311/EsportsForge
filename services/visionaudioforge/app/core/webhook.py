"""Webhook publisher to EsportsForge backend.

Per ADR 0003: in-process v1 with fire-and-forget + 5 retries
(250 ms → 4 s exponential). Per-session delivery-failure rate is logged
and published to CloudWatch (see app/core/metrics.py); the alarm at
>0.1% sustained over 60 minutes triggers the Redis Streams upgrade
before Phase 1c.

Post-PR-#62 review (L2): the metrics-emit hook fires every 60 s while
the publisher is alive. Without it, the alarm would have no signal.
"""

from __future__ import annotations

import asyncio
import logging
import os

import httpx

from app.core.metrics import MetricsClient

logger = logging.getLogger("vaf.webhook")

# Default updated to :8002 per ADR 0011.
DEFAULT_BACKEND = os.environ.get("ESF_BACKEND_URL", "http://127.0.0.1:8002")
WEBHOOK_PATH = "/api/v1/visionaudio/events"
RETRY_DELAYS_SEC = [0.25, 0.5, 1.0, 2.0, 4.0]
BATCH_FLUSH_INTERVAL_SEC = 0.25
BATCH_MAX_EVENTS = 32
METRICS_EMIT_INTERVAL_SEC = 60.0


class WebhookPublisher:
    """Per-session batching publisher.

    Phase 0 implementation. Publishes EventEnvelope batches to the
    EsportsForge backend's webhook receiver. Tracks per-session
    delivery-failure rate for the ADR 0003 alarm.
    """

    def __init__(
        self,
        backend_url: str | None = None,
        session_id: str = "_unscoped",
        title: str = "_unknown",
    ) -> None:
        self._backend_url = backend_url or DEFAULT_BACKEND
        self._session_id = session_id
        self._title = title
        self._buffer: list[dict] = []
        self._lock = asyncio.Lock()
        self._flush_task: asyncio.Task | None = None
        self._metrics_task: asyncio.Task | None = None

        # Per-session metrics for the alarm threshold.
        self._delivered = 0
        self._failed = 0
        self._delivered_window = 0
        self._failed_window = 0
        self._metrics = MetricsClient.get()

    async def enqueue(self, envelope_json: dict) -> None:
        """Enqueue an event for the next batch flush."""
        async with self._lock:
            self._buffer.append(envelope_json)
            if len(self._buffer) >= BATCH_MAX_EVENTS:
                await self._flush_locked()

    async def flush_periodic(self) -> None:
        """Loop forever: flush every BATCH_FLUSH_INTERVAL_SEC.

        Started by the FastAPI lifespan handler; cancelled at shutdown.
        """
        try:
            while True:
                await asyncio.sleep(BATCH_FLUSH_INTERVAL_SEC)
                async with self._lock:
                    await self._flush_locked()
        except asyncio.CancelledError:
            # One last flush on shutdown.
            async with self._lock:
                await self._flush_locked()
            raise

    async def _flush_locked(self) -> None:
        if not self._buffer:
            return
        batch = self._buffer
        self._buffer = []
        # Release lock before the network call.
        await self._send_with_retry(batch)

    async def _send_with_retry(self, batch: list[dict]) -> None:
        url = f"{self._backend_url}{WEBHOOK_PATH}"
        for attempt, delay in enumerate([0.0] + RETRY_DELAYS_SEC):
            if delay > 0:
                await asyncio.sleep(delay)
            try:
                async with httpx.AsyncClient(timeout=5.0) as client:
                    res = await client.post(url, json={"events": batch})
                if res.status_code < 300:
                    self._delivered += len(batch)
                    self._delivered_window += len(batch)
                    return
                logger.warning(
                    "webhook_non_2xx",
                    extra={"status": res.status_code, "attempt": attempt},
                )
            except Exception as exc:  # noqa: BLE001
                logger.warning(
                    "webhook_request_failed",
                    extra={"exc_type": type(exc).__name__, "attempt": attempt},
                )

        self._failed += len(batch)
        self._failed_window += len(batch)
        logger.error(
            "webhook_dlq",
            extra={
                "events_dropped": len(batch),
                "delivered_total": self._delivered,
                "failed_total": self._failed,
            },
        )

    async def emit_metrics_periodic(self) -> None:
        """Emit per-session failure rate to CloudWatch every 60 s.

        Started by the FastAPI lifespan handler alongside flush_periodic.
        Each emit window is independent (rolling rate, not cumulative)
        so the alarm sees recent state, not lifetime state.
        """
        try:
            while True:
                await asyncio.sleep(METRICS_EMIT_INTERVAL_SEC)
                window_total = self._delivered_window + self._failed_window
                rate = (self._failed_window / window_total) if window_total else 0.0
                self._metrics.publish_failure_rate(
                    session_id=self._session_id,
                    title=self._title,
                    rate=rate,
                    delivered=self._delivered_window,
                    failed=self._failed_window,
                )
                self._delivered_window = 0
                self._failed_window = 0
        except asyncio.CancelledError:
            raise

    @property
    def failure_rate(self) -> float:
        total = self._delivered + self._failed
        return self._failed / total if total else 0.0


# Module-level singleton — wired into FastAPI lifespan.
publisher = WebhookPublisher()
