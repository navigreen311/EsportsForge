"""Cache service — agent output caching, session state, meta snapshots.

Provides a high-level caching API for the EsportsForge backbone.  All keys
follow the convention ``esf:<domain>:<identifier>`` so they can be
invalidated by pattern without colliding with unrelated data.
"""

from __future__ import annotations

from typing import Any

import structlog

from app.core.config import settings
from app.db.redis import RedisClient

logger = structlog.get_logger(__name__)

# ---------------------------------------------------------------------------
# Key prefixes
# ---------------------------------------------------------------------------
_PREFIX_AGENT = "esf:agent_output"
_PREFIX_PLAYER = "esf:player_state"
_PREFIX_META = "esf:meta_snapshot"
_PREFIX_OPPONENT = "esf:opponent_dossier"
_PREFIX_STATS = "esf:cache_stats"


class CacheService:
    """Typed caching layer on top of :class:`RedisClient`."""

    def __init__(self, redis: RedisClient) -> None:
        self._redis = redis

    # -- Agent output caching -----------------------------------------------

    async def cache_agent_output(
        self,
        agent_name: str,
        user_id: str,
        output: dict[str, Any],
        ttl: int | None = None,
    ) -> None:
        """Cache a ForgeCore agent decision for a user."""
        key = f"{_PREFIX_AGENT}:{agent_name}:{user_id}"
        ttl = ttl or settings.cache_ttl_agent_output
        await self._redis.set_json(key, output, ttl=ttl)
        await self._inc_stat("hits_total")  # track write as activity
        logger.debug("cache_agent_output_set", agent=agent_name, user=user_id, ttl=ttl)

    async def get_cached_output(
        self, agent_name: str, user_id: str
    ) -> dict[str, Any] | None:
        """Retrieve a cached agent decision. Returns ``None`` on miss."""
        key = f"{_PREFIX_AGENT}:{agent_name}:{user_id}"
        result = await self._redis.get_json(key)
        if result is not None:
            await self._inc_stat("hits")
            logger.debug("cache_agent_output_hit", agent=agent_name, user=user_id)
        else:
            await self._inc_stat("misses")
            logger.debug("cache_agent_output_miss", agent=agent_name, user=user_id)
        return result

    # -- Player session state -----------------------------------------------

    async def cache_player_state(
        self, user_id: str, state: dict[str, Any], ttl: int | None = None
    ) -> None:
        """Store live player state (loadout, preferences, current context)."""
        key = f"{_PREFIX_PLAYER}:{user_id}"
        ttl = ttl or settings.cache_ttl_player_state
        await self._redis.set_json(key, state, ttl=ttl)
        logger.debug("cache_player_state_set", user=user_id)

    async def get_player_state(self, user_id: str) -> dict[str, Any] | None:
        """Retrieve live player state."""
        key = f"{_PREFIX_PLAYER}:{user_id}"
        result = await self._redis.get_json(key)
        if result is not None:
            await self._inc_stat("hits")
        else:
            await self._inc_stat("misses")
        return result

    # -- Meta snapshots (MetaBot results) -----------------------------------

    async def cache_meta_snapshot(
        self, title: str, snapshot: dict[str, Any], ttl: int | None = None
    ) -> None:
        """Cache a MetaBot game-meta snapshot (default TTL: 1 hour)."""
        key = f"{_PREFIX_META}:{title}"
        ttl = ttl or settings.cache_ttl_meta_snapshot
        await self._redis.set_json(key, snapshot, ttl=ttl)
        logger.debug("cache_meta_snapshot_set", title=title, ttl=ttl)

    async def get_meta_snapshot(self, title: str) -> dict[str, Any] | None:
        """Retrieve a cached meta snapshot."""
        key = f"{_PREFIX_META}:{title}"
        result = await self._redis.get_json(key)
        if result is not None:
            await self._inc_stat("hits")
        else:
            await self._inc_stat("misses")
        return result

    # -- Opponent dossier (ScoutBot) ----------------------------------------

    async def cache_opponent_dossier(
        self,
        opponent_id: str,
        dossier: dict[str, Any],
        ttl: int | None = None,
    ) -> None:
        """Cache scouting data for an opponent."""
        key = f"{_PREFIX_OPPONENT}:{opponent_id}"
        ttl = ttl or settings.cache_ttl_opponent_dossier
        await self._redis.set_json(key, dossier, ttl=ttl)
        logger.debug("cache_opponent_dossier_set", opponent=opponent_id, ttl=ttl)

    async def get_opponent_dossier(self, opponent_id: str) -> dict[str, Any] | None:
        """Retrieve cached opponent scouting data."""
        key = f"{_PREFIX_OPPONENT}:{opponent_id}"
        return await self._redis.get_json(key)

    # -- Pattern invalidation -----------------------------------------------

    async def invalidate_pattern(self, pattern: str) -> int:
        """Delete all cache keys matching *pattern*.

        Example: ``invalidate_pattern("esf:agent_output:scout_bot:*")``
        """
        count = await self._redis.delete_pattern(pattern)
        logger.info("cache_invalidated", pattern=pattern, deleted=count)
        return count

    # -- Stats / observability ----------------------------------------------

    async def get_cache_stats(self) -> dict[str, Any]:
        """Return hit rate, miss rate, and memory usage."""
        stats_raw = await self._redis.hget_all_json(_PREFIX_STATS)
        hits = int(stats_raw.get("hits", 0)) if stats_raw else 0
        misses = int(stats_raw.get("misses", 0)) if stats_raw else 0
        total = hits + misses
        memory = await self._redis.memory_usage()
        return {
            "hits": hits,
            "misses": misses,
            "total_requests": total,
            "hit_rate": round(hits / total, 4) if total else 0.0,
            "miss_rate": round(misses / total, 4) if total else 0.0,
            "memory": memory,
            "keys": {
                "agent_outputs": await self._redis.keys_count(f"{_PREFIX_AGENT}:*"),
                "player_states": await self._redis.keys_count(f"{_PREFIX_PLAYER}:*"),
                "meta_snapshots": await self._redis.keys_count(f"{_PREFIX_META}:*"),
                "opponent_dossiers": await self._redis.keys_count(f"{_PREFIX_OPPONENT}:*"),
            },
        }

    # -- Internal helpers ---------------------------------------------------

    async def _inc_stat(self, field: str) -> None:
        """Increment a field in the stats hash."""
        try:
            await self._redis._r.hincrby(_PREFIX_STATS, field, 1)
        except Exception:
            pass  # stats are best-effort, never fail the caller
