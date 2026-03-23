"""Redis connection pool and typed client wrapper."""

from __future__ import annotations

import json
from contextlib import asynccontextmanager
from typing import Any

import redis.asyncio as redis
import structlog

from app.core.config import settings

logger = structlog.get_logger(__name__)

# ---------------------------------------------------------------------------
# Connection pool (module-level singleton)
# ---------------------------------------------------------------------------
_pool: redis.ConnectionPool | None = None
_client: redis.Redis | None = None


async def init_redis() -> redis.Redis:
    """Initialise the Redis connection pool and return a client."""
    global _pool, _client
    _pool = redis.ConnectionPool.from_url(
        settings.redis_url,
        max_connections=settings.redis_max_connections,
        decode_responses=True,
        socket_connect_timeout=settings.redis_socket_timeout,
        socket_timeout=settings.redis_socket_timeout,
    )
    _client = redis.Redis(connection_pool=_pool)
    # Verify connectivity
    await _client.ping()
    logger.info("redis_connected", url=settings.redis_url)
    return _client


async def close_redis() -> None:
    """Gracefully close the Redis connection pool."""
    global _pool, _client
    if _client is not None:
        await _client.aclose()
        _client = None
    if _pool is not None:
        await _pool.aclose()
        _pool = None
    logger.info("redis_disconnected")


async def get_redis() -> redis.Redis:
    """FastAPI dependency — returns the shared Redis client."""
    if _client is None:
        raise RuntimeError("Redis is not initialised. Call init_redis() first.")
    return _client


# ---------------------------------------------------------------------------
# Typed wrapper
# ---------------------------------------------------------------------------

class RedisClient:
    """Convenience wrapper with typed helpers around the raw Redis client."""

    def __init__(self, client: redis.Redis) -> None:
        self._r = client

    # -- Primitives ---------------------------------------------------------

    async def set_json(self, key: str, value: Any, ttl: int | None = None) -> None:
        """Serialise *value* as JSON and store under *key*."""
        payload = json.dumps(value, default=str)
        if ttl:
            await self._r.setex(key, ttl, payload)
        else:
            await self._r.set(key, payload)

    async def get_json(self, key: str) -> Any | None:
        """Return deserialised JSON stored at *key*, or ``None``."""
        raw = await self._r.get(key)
        if raw is None:
            return None
        return json.loads(raw)

    async def delete(self, key: str) -> int:
        """Delete a single key. Returns number of keys removed."""
        return await self._r.delete(key)

    async def delete_pattern(self, pattern: str) -> int:
        """Delete all keys matching *pattern* (SCAN-based, safe for prod)."""
        count = 0
        async for key in self._r.scan_iter(match=pattern, count=200):
            await self._r.delete(key)
            count += 1
        return count

    async def exists(self, key: str) -> bool:
        return bool(await self._r.exists(key))

    async def ttl(self, key: str) -> int:
        return await self._r.ttl(key)

    async def keys_count(self, pattern: str = "*") -> int:
        """Count keys matching *pattern* via SCAN (non-blocking)."""
        count = 0
        async for _ in self._r.scan_iter(match=pattern, count=200):
            count += 1
        return count

    # -- Hash helpers -------------------------------------------------------

    async def hset_json(self, key: str, mapping: dict[str, Any], ttl: int | None = None) -> None:
        """Store a dict as a Redis hash with JSON-encoded values."""
        encoded = {k: json.dumps(v, default=str) for k, v in mapping.items()}
        await self._r.hset(key, mapping=encoded)
        if ttl:
            await self._r.expire(key, ttl)

    async def hget_all_json(self, key: str) -> dict[str, Any] | None:
        """Retrieve a full Redis hash, JSON-decoding each value."""
        raw = await self._r.hgetall(key)
        if not raw:
            return None
        return {k: json.loads(v) for k, v in raw.items()}

    # -- Info ---------------------------------------------------------------

    async def memory_usage(self) -> dict[str, Any]:
        """Return memory-related stats from INFO."""
        info = await self._r.info("memory")
        return {
            "used_memory_human": info.get("used_memory_human", "N/A"),
            "used_memory_peak_human": info.get("used_memory_peak_human", "N/A"),
            "maxmemory_human": info.get("maxmemory_human", "N/A"),
        }

    async def ping(self) -> bool:
        return await self._r.ping()
