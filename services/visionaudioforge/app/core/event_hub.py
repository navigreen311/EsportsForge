"""In-memory per-session event fan-out hub (Phase 1a Day 1).

The dispatcher's events are delivered to the EsportsForge webhook AND,
per the Phase 1a state report (§8 P8) and the Drill Lab kickoff brief,
fanned out in-process to any frontend subscribers connected on the
events WebSocket surface (`/ws/events/{session_id}`). This hub is that
fan-out.

In-memory only for Phase 1a (state report Q3 decision — durable event
storage is a later, deliberate decision; no Postgres). A subscriber is a
plain `asyncio.Queue`; `publish` is fire-and-forward to every live
subscriber of a session. Subscriber queues are bounded and drop the
oldest event under backpressure, so a slow browser tab can never stall
the dispatch loop — event-display is latest-wins tolerant.
"""

from __future__ import annotations

import asyncio
import logging
from typing import Any

logger = logging.getLogger("vaf.event_hub")

# Bound per-subscriber backlog so a stalled client cannot grow memory
# without limit. Under backpressure the oldest queued event is dropped.
SUBSCRIBER_MAX_QUEUE = 256


class EventHub:
    """Session-scoped in-memory pub/sub for event-envelope dicts."""

    def __init__(self) -> None:
        self._subscribers: dict[str, set[asyncio.Queue]] = {}

    def subscribe(self, session_id: str) -> asyncio.Queue:
        """Register a new subscriber queue for a session."""
        q: asyncio.Queue = asyncio.Queue(maxsize=SUBSCRIBER_MAX_QUEUE)
        self._subscribers.setdefault(session_id, set()).add(q)
        logger.debug(
            "subscribe",
            extra={"session_id": session_id, "subscribers": len(self._subscribers[session_id])},
        )
        return q

    def unsubscribe(self, session_id: str, q: asyncio.Queue) -> None:
        """Remove a subscriber; drop the session bucket when it empties."""
        subs = self._subscribers.get(session_id)
        if not subs:
            return
        subs.discard(q)
        if not subs:
            self._subscribers.pop(session_id, None)

    async def publish(self, session_id: str, event: dict[str, Any]) -> int:
        """Deliver one event to every subscriber of a session.

        Non-blocking: a full subscriber queue drops its oldest event to
        make room (bounded backpressure) and never stalls the caller.
        Returns the number of subscribers the event was delivered to.
        """
        subs = self._subscribers.get(session_id)
        if not subs:
            return 0
        delivered = 0
        for q in tuple(subs):
            try:
                q.put_nowait(event)
            except asyncio.QueueFull:
                try:
                    q.get_nowait()  # drop oldest
                except asyncio.QueueEmpty:
                    pass
                try:
                    q.put_nowait(event)
                except asyncio.QueueFull:
                    pass
            delivered += 1
        return delivered

    def subscriber_count(self, session_id: str) -> int:
        return len(self._subscribers.get(session_id, ()))


# Module-level singleton, mirroring app.core.webhook.publisher.
hub = EventHub()
