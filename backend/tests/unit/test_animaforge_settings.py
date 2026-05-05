"""Unit tests for AnimaForge settings, test-connection, and admin stats — Agent #10.

These tests exercise the route handlers directly (no live HTTP). The endpoint
module is defensive: it tolerates Agent #1's surfaces being missing on this
branch by lazy-importing them with try/except. The tests cover both paths.
"""

from __future__ import annotations

import asyncio
import uuid
from datetime import datetime, timedelta, timezone
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock

import pytest

from app.api.v1.endpoints import animaforge_settings as ep
from app.models.user import User, UserRole
from app.schemas.animaforge import (
    AdminStatsResponse,
    AnimaForgeSettingsResponse,
    AnimaForgeSettingsUpdate,
    TestConnectionResponse,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_user(role: UserRole = UserRole.FREE) -> MagicMock:
    user = MagicMock(spec=User)
    user.id = uuid.uuid4()
    user.email = "u@example.com"
    user.username = "u"
    user.role = role
    return user


def _run(coro):
    return asyncio.get_event_loop().run_until_complete(coro)


@pytest.fixture(autouse=True)
def _reset_cache():
    """Make sure the in-memory settings cache is empty between tests."""
    ep._SETTINGS_CACHE.clear()
    yield
    ep._SETTINGS_CACHE.clear()


# ===========================================================================
# GET /settings
# ===========================================================================

class TestGetSettings:
    @pytest.mark.asyncio
    async def test_returns_defaults_for_new_user(self):
        user = _make_user()
        out = await ep.get_settings(current_user=user)
        assert isinstance(out, AnimaForgeSettingsResponse)
        assert out.auto_arsenal is True
        assert out.auto_drill is True
        assert out.auto_share is True
        assert out.quality in ("standard", "high", "low")

    @pytest.mark.asyncio
    async def test_returns_persisted_values_after_update(self):
        user = _make_user()
        ep._SETTINGS_CACHE[str(user.id)] = {
            "auto_arsenal": False,
            "auto_drill": True,
            "auto_share": False,
            "quality": "high",
        }
        out = await ep.get_settings(current_user=user)
        assert out.auto_arsenal is False
        assert out.auto_drill is True
        assert out.auto_share is False
        assert out.quality == "high"


# ===========================================================================
# POST /settings
# ===========================================================================

class TestUpdateSettings:
    @pytest.mark.asyncio
    async def test_persists_payload_to_cache(self):
        user = _make_user()
        payload = AnimaForgeSettingsUpdate(
            auto_arsenal=False,
            auto_drill=False,
            auto_share=True,
            quality="low",
        )
        out = await ep.update_settings(payload=payload, current_user=user)
        assert out.auto_arsenal is False
        assert out.auto_drill is False
        assert out.auto_share is True
        assert out.quality == "low"
        # Cache should reflect the write
        assert ep._SETTINGS_CACHE[str(user.id)]["quality"] == "low"

    @pytest.mark.asyncio
    async def test_round_trip(self):
        user = _make_user()
        payload = AnimaForgeSettingsUpdate(
            auto_arsenal=True, auto_drill=False, auto_share=True, quality="high",
        )
        await ep.update_settings(payload=payload, current_user=user)
        got = await ep.get_settings(current_user=user)
        assert got.auto_drill is False
        assert got.quality == "high"


# ===========================================================================
# POST /test-connection
# ===========================================================================

class TestTestConnection:
    @pytest.mark.asyncio
    async def test_returns_offline_when_service_missing(self, monkeypatch):
        monkeypatch.setattr(ep, "_try_import_service", lambda: None)
        out = await ep.test_connection(current_user=_make_user())
        assert isinstance(out, TestConnectionResponse)
        assert out.available is False
        assert out.latency_ms == 0
        assert "not yet" in out.message.lower() or "offline" in out.message.lower()

    @pytest.mark.asyncio
    async def test_returns_available_when_service_responds(self, monkeypatch):
        fake_service = SimpleNamespace(is_available=AsyncMock(return_value=True))
        monkeypatch.setattr(ep, "_try_import_service", lambda: fake_service)
        out = await ep.test_connection(current_user=_make_user())
        assert out.available is True
        assert out.latency_ms >= 0
        assert "connected" in out.message.lower()

    @pytest.mark.asyncio
    async def test_returns_offline_when_probe_returns_false(self, monkeypatch):
        fake_service = SimpleNamespace(is_available=AsyncMock(return_value=False))
        monkeypatch.setattr(ep, "_try_import_service", lambda: fake_service)
        out = await ep.test_connection(current_user=_make_user())
        assert out.available is False
        assert "offline" in out.message.lower()

    @pytest.mark.asyncio
    async def test_swallows_exceptions(self, monkeypatch):
        async def _boom():
            raise RuntimeError("network down")

        fake_service = SimpleNamespace(is_available=_boom)
        monkeypatch.setattr(ep, "_try_import_service", lambda: fake_service)
        out = await ep.test_connection(current_user=_make_user())
        assert out.available is False


# ===========================================================================
# GET /admin/stats
# ===========================================================================

class TestAdminStats:
    @pytest.mark.asyncio
    async def test_rejects_non_admin(self):
        from fastapi import HTTPException

        user = _make_user(role=UserRole.FREE)
        db = AsyncMock()
        with pytest.raises(HTTPException) as exc:
            await ep.admin_stats(current_user=user, db=db)
        assert exc.value.status_code == 403

    @pytest.mark.asyncio
    async def test_returns_zeros_when_job_model_missing(self, monkeypatch):
        monkeypatch.setattr(ep, "_try_import_job_model", lambda: None)
        monkeypatch.setattr(ep, "_try_import_service", lambda: None)
        user = _make_user(role=UserRole.TEAM)
        out = await ep.admin_stats(current_user=user, db=AsyncMock())
        assert isinstance(out, AdminStatsResponse)
        assert out.jobs_today == 0
        assert out.avg_render_seconds == 0.0
        assert out.storage_mb == 0.0
        assert out.queue_depth == 0

    @pytest.mark.asyncio
    async def test_uses_job_model_helpers_when_available(self, monkeypatch):
        sentinel = object()
        monkeypatch.setattr(ep, "_try_import_job_model", lambda: sentinel)

        async def _fake_count(db, job_model, since):
            assert job_model is sentinel
            return 7

        async def _fake_avg(db, job_model, since):
            return 42.5

        async def _fake_storage(db, job_model):
            return 128.25

        monkeypatch.setattr(ep, "_count_jobs_since", _fake_count)
        monkeypatch.setattr(ep, "_avg_render_seconds", _fake_avg)
        monkeypatch.setattr(ep, "_storage_estimate_mb", _fake_storage)

        # Service exposes a queue_depth callable.
        fake_service = SimpleNamespace(queue_depth=AsyncMock(return_value=4))
        monkeypatch.setattr(ep, "_try_import_service", lambda: fake_service)

        user = _make_user(role=UserRole.TEAM)
        out = await ep.admin_stats(current_user=user, db=AsyncMock())
        assert out.jobs_today == 7
        assert out.avg_render_seconds == 42.5
        assert out.storage_mb == 128.25
        assert out.queue_depth == 4

    @pytest.mark.asyncio
    async def test_degrades_when_db_helpers_raise(self, monkeypatch):
        sentinel = object()
        monkeypatch.setattr(ep, "_try_import_job_model", lambda: sentinel)

        async def _boom(*a, **k):
            raise RuntimeError("db down")

        monkeypatch.setattr(ep, "_count_jobs_since", _boom)
        monkeypatch.setattr(ep, "_avg_render_seconds", _boom)
        monkeypatch.setattr(ep, "_storage_estimate_mb", _boom)
        monkeypatch.setattr(ep, "_try_import_service", lambda: None)

        user = _make_user(role=UserRole.TEAM)
        out = await ep.admin_stats(current_user=user, db=AsyncMock())
        # Failure → zeros, no exception bubbled
        assert out.jobs_today == 0
        assert out.avg_render_seconds == 0.0
        assert out.storage_mb == 0.0


# ===========================================================================
# _queue_depth helper
# ===========================================================================

class TestQueueDepth:
    @pytest.mark.asyncio
    async def test_zero_when_no_service(self, monkeypatch):
        monkeypatch.setattr(ep, "_try_import_service", lambda: None)
        assert await ep._queue_depth() == 0

    @pytest.mark.asyncio
    async def test_zero_when_service_lacks_method(self, monkeypatch):
        monkeypatch.setattr(ep, "_try_import_service", lambda: SimpleNamespace())
        assert await ep._queue_depth() == 0

    @pytest.mark.asyncio
    async def test_returns_value_from_async_method(self, monkeypatch):
        svc = SimpleNamespace(queue_depth=AsyncMock(return_value=11))
        monkeypatch.setattr(ep, "_try_import_service", lambda: svc)
        assert await ep._queue_depth() == 11

    @pytest.mark.asyncio
    async def test_returns_value_from_sync_method(self, monkeypatch):
        svc = SimpleNamespace(queue_depth=lambda: 3)
        monkeypatch.setattr(ep, "_try_import_service", lambda: svc)
        assert await ep._queue_depth() == 3

    @pytest.mark.asyncio
    async def test_clamps_negative(self, monkeypatch):
        svc = SimpleNamespace(queue_depth=lambda: -5)
        monkeypatch.setattr(ep, "_try_import_service", lambda: svc)
        assert await ep._queue_depth() == 0
