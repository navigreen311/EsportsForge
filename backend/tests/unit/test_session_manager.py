"""Tests for SessionManager — real-time session lifecycle."""

from __future__ import annotations

import pytest
import pytest_asyncio
import fakeredis.aioredis

from app.db.redis import RedisClient
from app.services.backbone.session_manager import SessionManager


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest_asyncio.fixture
async def redis_client():
    fake = fakeredis.aioredis.FakeRedis(decode_responses=True)
    client = RedisClient(fake)
    yield client
    await fake.aclose()


@pytest_asyncio.fixture
async def manager(redis_client: RedisClient):
    return SessionManager(redis_client)


# ---------------------------------------------------------------------------
# Start session
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_start_session(manager: SessionManager):
    session = await manager.start_session("user-1", "madden26", "ranked")

    assert session["user_id"] == "user-1"
    assert session["title"] == "madden26"
    assert session["mode"] == "ranked"
    assert session["status"] == "active"
    assert "session_id" in session
    assert "started_at" in session
    assert session["metrics"] == {}


@pytest.mark.asyncio
async def test_start_session_retrievable(manager: SessionManager):
    await manager.start_session("user-1", "madden26", "ranked")

    active = await manager.get_active_session("user-1")
    assert active is not None
    assert active["user_id"] == "user-1"


# ---------------------------------------------------------------------------
# Update session
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_update_session_metrics(manager: SessionManager):
    await manager.start_session("user-1", "madden26", "ranked")

    updated = await manager.update_session("user-1", {"score": 21, "quarter": 3})
    assert updated is not None
    assert updated["metrics"]["score"] == 21
    assert updated["metrics"]["quarter"] == 3


@pytest.mark.asyncio
async def test_update_session_merges_metrics(manager: SessionManager):
    await manager.start_session("user-1", "madden26", "ranked")
    await manager.update_session("user-1", {"score": 7})
    updated = await manager.update_session("user-1", {"quarter": 2})

    assert updated["metrics"]["score"] == 7
    assert updated["metrics"]["quarter"] == 2


@pytest.mark.asyncio
async def test_update_nonexistent_session(manager: SessionManager):
    result = await manager.update_session("ghost-user", {"score": 0})
    assert result is None


# ---------------------------------------------------------------------------
# End session
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_end_session(manager: SessionManager):
    await manager.start_session("user-1", "madden26", "ranked")
    session = await manager.end_session("user-1")

    assert session is not None
    assert session["status"] == "completed"
    assert "ended_at" in session

    # Should be gone from Redis
    assert await manager.get_active_session("user-1") is None


@pytest.mark.asyncio
async def test_end_session_calls_persist_callback(redis_client: RedisClient):
    persisted = []

    async def fake_persist(data):
        persisted.append(data)

    mgr = SessionManager(redis_client, persist_callback=fake_persist)
    await mgr.start_session("user-1", "cfb26", "dynasty")
    await mgr.end_session("user-1")

    assert len(persisted) == 1
    assert persisted[0]["title"] == "cfb26"
    assert persisted[0]["status"] == "completed"


@pytest.mark.asyncio
async def test_end_nonexistent_session(manager: SessionManager):
    result = await manager.end_session("ghost-user")
    assert result is None


# ---------------------------------------------------------------------------
# Active session count
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_active_sessions_count(manager: SessionManager):
    assert await manager.get_active_sessions_count() == 0

    await manager.start_session("user-1", "madden26", "ranked")
    await manager.start_session("user-2", "cfb26", "dynasty")
    assert await manager.get_active_sessions_count() == 2

    await manager.end_session("user-1")
    assert await manager.get_active_sessions_count() == 1


# ---------------------------------------------------------------------------
# Edge cases
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_start_session_overwrites_existing(manager: SessionManager):
    """Starting a new session for the same user replaces the old one."""
    s1 = await manager.start_session("user-1", "madden26", "ranked")
    s2 = await manager.start_session("user-1", "cfb26", "dynasty")

    active = await manager.get_active_session("user-1")
    assert active["session_id"] == s2["session_id"]
    assert active["title"] == "cfb26"
