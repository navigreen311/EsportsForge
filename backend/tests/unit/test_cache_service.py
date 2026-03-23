"""Tests for CacheService — agent output, player state, meta snapshots."""

from __future__ import annotations

import pytest
import pytest_asyncio
import fakeredis.aioredis

from app.db.redis import RedisClient
from app.services.backbone.cache_service import CacheService


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest_asyncio.fixture
async def redis_client():
    """Provide a fakeredis-backed RedisClient for isolated tests."""
    fake = fakeredis.aioredis.FakeRedis(decode_responses=True)
    client = RedisClient(fake)
    yield client
    await fake.aclose()


@pytest_asyncio.fixture
async def cache(redis_client: RedisClient):
    return CacheService(redis_client)


# ---------------------------------------------------------------------------
# Agent output caching
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_cache_and_retrieve_agent_output(cache: CacheService):
    output = {"recommendation": "Run play X", "confidence": 0.92}
    await cache.cache_agent_output("scout_bot", "user-1", output, ttl=60)

    result = await cache.get_cached_output("scout_bot", "user-1")
    assert result is not None
    assert result["recommendation"] == "Run play X"
    assert result["confidence"] == 0.92


@pytest.mark.asyncio
async def test_cache_miss_returns_none(cache: CacheService):
    result = await cache.get_cached_output("nonexistent_agent", "user-999")
    assert result is None


@pytest.mark.asyncio
async def test_agent_output_different_users(cache: CacheService):
    await cache.cache_agent_output("scout_bot", "user-1", {"rec": "A"})
    await cache.cache_agent_output("scout_bot", "user-2", {"rec": "B"})

    r1 = await cache.get_cached_output("scout_bot", "user-1")
    r2 = await cache.get_cached_output("scout_bot", "user-2")
    assert r1["rec"] == "A"
    assert r2["rec"] == "B"


# ---------------------------------------------------------------------------
# Player state
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_cache_player_state(cache: CacheService):
    state = {"loadout": "aggressive", "rank": 42}
    await cache.cache_player_state("user-1", state)

    result = await cache.get_player_state("user-1")
    assert result is not None
    assert result["loadout"] == "aggressive"
    assert result["rank"] == 42


@pytest.mark.asyncio
async def test_player_state_miss(cache: CacheService):
    result = await cache.get_player_state("user-missing")
    assert result is None


# ---------------------------------------------------------------------------
# Meta snapshots
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_cache_meta_snapshot(cache: CacheService):
    snapshot = {"top_plays": ["HB Dive", "PA Crossers"], "patch": "1.2.0"}
    await cache.cache_meta_snapshot("madden26", snapshot)

    result = await cache.get_meta_snapshot("madden26")
    assert result is not None
    assert result["top_plays"] == ["HB Dive", "PA Crossers"]


@pytest.mark.asyncio
async def test_meta_snapshot_miss(cache: CacheService):
    result = await cache.get_meta_snapshot("unknown_title")
    assert result is None


# ---------------------------------------------------------------------------
# Opponent dossier
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_cache_opponent_dossier(cache: CacheService):
    dossier = {"play_style": "conservative", "win_rate": 0.61}
    await cache.cache_opponent_dossier("opp-42", dossier, ttl=120)

    result = await cache.get_opponent_dossier("opp-42")
    assert result is not None
    assert result["play_style"] == "conservative"


# ---------------------------------------------------------------------------
# Pattern invalidation
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_invalidate_pattern(cache: CacheService):
    await cache.cache_agent_output("scout_bot", "user-1", {"a": 1})
    await cache.cache_agent_output("scout_bot", "user-2", {"b": 2})
    await cache.cache_meta_snapshot("madden26", {"c": 3})

    deleted = await cache.invalidate_pattern("esf:agent_output:scout_bot:*")
    assert deleted == 2

    # Verify scout outputs are gone but meta remains
    assert await cache.get_cached_output("scout_bot", "user-1") is None
    assert await cache.get_meta_snapshot("madden26") is not None


# ---------------------------------------------------------------------------
# Stats
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_cache_stats(cache: CacheService):
    await cache.cache_agent_output("scout_bot", "user-1", {"x": 1})
    await cache.get_cached_output("scout_bot", "user-1")  # hit
    await cache.get_cached_output("scout_bot", "user-missing")  # miss

    stats = await cache.get_cache_stats()
    assert stats["hits"] >= 1
    assert stats["misses"] >= 1
    assert stats["total_requests"] >= 2
    assert 0.0 <= stats["hit_rate"] <= 1.0
    assert "memory" in stats
    assert "keys" in stats
