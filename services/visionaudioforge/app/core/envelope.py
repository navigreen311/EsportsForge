"""Envelope construction helper.

Lives separately from dispatcher.py to avoid circular imports — adapters
build envelopes via this module; the dispatcher calls into adapters.
"""

from __future__ import annotations

from datetime import datetime, timezone

from ulid import ULID

from app.core.session import SessionContext
from app.schemas.enums import EventType
from app.schemas.events import EventEnvelope


def make_envelope(
    session: SessionContext,
    event_type: EventType,
    payload,
    confidence: float,
    adapter_version: str,
    captured_at: datetime,
) -> EventEnvelope:
    """Build an envelope around an adapter-produced payload."""
    now = datetime.now(timezone.utc)
    return EventEnvelope(
        event_id=str(ULID()),
        session_id=session.session_id,
        user_id_hash=session.user_id_hash,
        title=session.title,  # type: ignore[arg-type]
        timestamp=now,
        captured_at=captured_at,
        confidence=confidence,
        adapter_version=adapter_version,
        event_type=event_type,
        payload=payload,
    )
