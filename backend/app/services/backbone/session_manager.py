"""Session manager — real-time session lifecycle backed by Redis.

Active gaming sessions are kept in Redis for sub-millisecond reads.
When a session ends, metrics are persisted to PostgreSQL for long-term
analytics.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

import structlog

from app.core.config import settings
from app.db.redis import RedisClient

logger = structlog.get_logger(__name__)

# ---------------------------------------------------------------------------
# Key conventions
# ---------------------------------------------------------------------------
_PREFIX_SESSION = "esf:session"
_ACTIVE_SET = "esf:sessions:active"


class SessionManager:
    """Manage real-time gaming sessions stored in Redis."""

    def __init__(self, redis: RedisClient, *, persist_callback=None) -> None:
        """
        Parameters
        ----------
        redis:
            Typed Redis wrapper.
        persist_callback:
            Optional async callable ``(session_data) -> None`` invoked when a
            session ends, used to persist the completed session to PostgreSQL.
        """
        self._redis = redis
        self._persist = persist_callback

    # -- Lifecycle ----------------------------------------------------------

    async def start_session(
        self, user_id: str, title: str, mode: str
    ) -> dict[str, Any]:
        """Create an active session for *user_id*.

        Returns the full session dict including a generated ``session_id``.
        """
        session_id = str(uuid.uuid4())
        now = datetime.now(timezone.utc).isoformat()

        session = {
            "session_id": session_id,
            "user_id": user_id,
            "title": title,
            "mode": mode,
            "started_at": now,
            "updated_at": now,
            "status": "active",
            "metrics": {},
        }

        key = f"{_PREFIX_SESSION}:{user_id}"
        await self._redis.set_json(key, session, ttl=settings.cache_ttl_session)

        # Track in the active-sessions set
        await self._redis._r.sadd(_ACTIVE_SET, user_id)

        logger.info(
            "session_started",
            session_id=session_id,
            user=user_id,
            title=title,
            mode=mode,
        )
        return session

    async def update_session(
        self, user_id: str, metrics: dict[str, Any]
    ) -> dict[str, Any] | None:
        """Merge *metrics* into the active session for *user_id*.

        Returns the updated session or ``None`` if no active session exists.
        """
        key = f"{_PREFIX_SESSION}:{user_id}"
        session = await self._redis.get_json(key)
        if session is None:
            logger.warning("session_update_miss", user=user_id)
            return None

        session["metrics"].update(metrics)
        session["updated_at"] = datetime.now(timezone.utc).isoformat()
        await self._redis.set_json(key, session, ttl=settings.cache_ttl_session)

        logger.debug("session_updated", user=user_id, metric_keys=list(metrics.keys()))
        return session

    async def end_session(self, user_id: str) -> dict[str, Any] | None:
        """End the active session, persist to PostgreSQL, and clean up Redis.

        Returns the final session snapshot or ``None`` if there was no session.
        """
        key = f"{_PREFIX_SESSION}:{user_id}"
        session = await self._redis.get_json(key)
        if session is None:
            logger.warning("session_end_miss", user=user_id)
            return None

        session["status"] = "completed"
        session["ended_at"] = datetime.now(timezone.utc).isoformat()

        # Persist to PostgreSQL via callback
        if self._persist is not None:
            try:
                await self._persist(session)
                logger.info("session_persisted", session_id=session["session_id"])
            except Exception:
                logger.exception("session_persist_failed", session_id=session["session_id"])

        # Cleanup Redis
        await self._redis.delete(key)
        await self._redis._r.srem(_ACTIVE_SET, user_id)

        logger.info("session_ended", session_id=session["session_id"], user=user_id)
        return session

    # -- Queries ------------------------------------------------------------

    async def get_active_session(self, user_id: str) -> dict[str, Any] | None:
        """Return the current active session for *user_id* or ``None``."""
        key = f"{_PREFIX_SESSION}:{user_id}"
        return await self._redis.get_json(key)

    async def get_active_sessions_count(self) -> int:
        """Return the number of currently active sessions platform-wide."""
        return await self._redis._r.scard(_ACTIVE_SET)
