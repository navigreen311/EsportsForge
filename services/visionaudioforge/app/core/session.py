"""Session lifecycle and per-session context.

A SessionContext is constructed when the EsportsForge backend POSTs
/api/v1/sessions/open and lives until the agent disconnects (5-min TTL
on stale sessions).

Per docs/specs/02-visionaudioforge-core.md §"State per session" —
in-memory only in v1.
"""

from __future__ import annotations

import asyncio
import hashlib
from collections import deque
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any

from app.schemas.enums import IntegrityMode, TitleEnum


def _hash_user_id(user_id: str) -> str:
    """One-way hash so adapters and downstream subscribers don't
    receive raw user_id. SHA-256 truncated to 16 hex chars."""
    return hashlib.sha256(user_id.encode("utf-8")).hexdigest()[:16]


@dataclass
class SessionContext:
    """Per-session state owned by the core, mutated by the dispatcher."""

    session_id: str
    user_id: str
    user_id_hash: str
    integrity_mode: IntegrityMode
    title: TitleEnum | None = None
    title_confidence: float = 0.0
    title_locked_at: datetime | None = None

    opened_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    last_heartbeat_at: datetime | None = None
    frame_count: int = 0
    last_event_id: str | None = None

    # Adapter-owned mutable state. Adapters read/write freely.
    adapter_state: dict[str, Any] = field(default_factory=dict)

    # Frame history for adapters that need temporal features.
    # Stores small refs (frame_id + captured_at), not the bytes.
    frame_history: deque = field(default_factory=lambda: deque(maxlen=30))

    @classmethod
    def open(
        cls,
        session_id: str,
        user_id: str,
        integrity_mode: IntegrityMode,
        active_title_hint: TitleEnum | None = None,
    ) -> "SessionContext":
        ctx = cls(
            session_id=session_id,
            user_id=user_id,
            user_id_hash=_hash_user_id(user_id),
            integrity_mode=integrity_mode,
        )
        if active_title_hint is not None:
            # Hint, not authoritative — title detection still runs.
            ctx.adapter_state["_active_title_hint"] = active_title_hint
        return ctx


class SessionRegistry:
    """In-memory registry. Phase 0 — single-instance only.

    When we cross the 1000-concurrent-sessions threshold or move to
    multi-instance deployment, this gets replaced by a Redis-backed
    registry per the open-question resolution path.
    """

    def __init__(self) -> None:
        self._sessions: dict[str, SessionContext] = {}
        self._lock = asyncio.Lock()

    async def open(
        self,
        session_id: str,
        user_id: str,
        integrity_mode: IntegrityMode,
        active_title_hint: TitleEnum | None = None,
    ) -> SessionContext:
        async with self._lock:
            ctx = SessionContext.open(
                session_id=session_id,
                user_id=user_id,
                integrity_mode=integrity_mode,
                active_title_hint=active_title_hint,
            )
            self._sessions[session_id] = ctx
            return ctx

    async def get(self, session_id: str) -> SessionContext | None:
        return self._sessions.get(session_id)

    async def close(self, session_id: str) -> None:
        async with self._lock:
            self._sessions.pop(session_id, None)

    async def update_integrity_mode(
        self, session_id: str, mode: IntegrityMode
    ) -> SessionContext | None:
        async with self._lock:
            ctx = self._sessions.get(session_id)
            if ctx is not None:
                ctx.integrity_mode = mode
            return ctx

    def active_count(self) -> int:
        return len(self._sessions)


# Module-level singleton — wired into FastAPI app state in main.py.
registry = SessionRegistry()
