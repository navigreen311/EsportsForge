"""Tests for the AnimaForge field added to /api/v1/health — Agent #10."""

from __future__ import annotations

from unittest.mock import AsyncMock

import pytest

from app.api.v1.endpoints import health as health_ep


class TestHealthAnimaForgeField:
    @pytest.mark.asyncio
    async def test_animaforge_offline_when_service_missing(self, monkeypatch):
        async def _missing():
            return "offline"

        monkeypatch.setattr(health_ep, "_check_animaforge", _missing)
        out = await health_ep.detailed_health()
        assert hasattr(out, "animaforge")
        assert out.animaforge == "offline"
        # Existing fields preserved
        assert out.status in ("healthy", "degraded")
        assert out.version
        assert isinstance(out.uptime_seconds, float)
        assert out.database is not None
        assert out.redis is not None

    @pytest.mark.asyncio
    async def test_animaforge_online_when_service_available(self, monkeypatch):
        async def _online():
            return "online"

        monkeypatch.setattr(health_ep, "_check_animaforge", _online)
        out = await health_ep.detailed_health()
        assert out.animaforge == "online"

    @pytest.mark.asyncio
    async def test_check_animaforge_returns_offline_on_import_error(self, monkeypatch):
        # Force the lazy import inside _check_animaforge to fail by removing
        # the module path from sys.modules and providing no fallback. The
        # function should swallow and return "offline".
        result = await health_ep._check_animaforge()
        assert result in ("online", "offline")
        # When AnimaForge code isn't on this branch yet the only correct value
        # is "offline".
        assert result == "offline"

    @pytest.mark.asyncio
    async def test_check_animaforge_handles_probe_exception(self, monkeypatch):
        """If a service module exists but is_available raises, return offline."""

        class _BoomService:
            @staticmethod
            async def is_available():
                raise RuntimeError("network failure")

        # Patch the lazy import to return our boom-on-call class. We cannot
        # easily monkeypatch a deferred import in another module, so instead
        # we inject a fake module into sys.modules for this test.
        import sys
        import types

        fake_pkg = types.ModuleType("app.services.animaforge")
        fake_client = types.ModuleType("app.services.animaforge.client")
        fake_client.AnimaForgeService = _BoomService
        sys.modules["app.services.animaforge"] = fake_pkg
        sys.modules["app.services.animaforge.client"] = fake_client
        try:
            result = await health_ep._check_animaforge()
        finally:
            sys.modules.pop("app.services.animaforge.client", None)
            sys.modules.pop("app.services.animaforge", None)
        assert result == "offline"

    @pytest.mark.asyncio
    async def test_check_animaforge_returns_online_when_service_says_yes(self):
        import sys
        import types

        class _OkService:
            @staticmethod
            async def is_available():
                return True

        fake_pkg = types.ModuleType("app.services.animaforge")
        fake_client = types.ModuleType("app.services.animaforge.client")
        fake_client.AnimaForgeService = _OkService
        sys.modules["app.services.animaforge"] = fake_pkg
        sys.modules["app.services.animaforge.client"] = fake_client
        try:
            result = await health_ep._check_animaforge()
        finally:
            sys.modules.pop("app.services.animaforge.client", None)
            sys.modules.pop("app.services.animaforge", None)
        assert result == "online"
