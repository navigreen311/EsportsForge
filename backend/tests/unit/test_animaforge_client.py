"""Unit tests for ``AnimaForgeService`` (Agent #1).

All HTTP traffic is mocked via ``unittest.mock`` patching ``httpx.AsyncClient``.
"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest

from app.services.animaforge import AnimaForgeService, AnimaForgeUnavailable


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

class _FakeResponse:
    def __init__(self, status_code: int, json_data: dict | None = None,
                 text: str = ""):
        self.status_code = status_code
        self._json = json_data
        self.text = text

    def json(self):
        if self._json is None:
            raise ValueError("no json body")
        return self._json


def _make_async_client_mock(*, get=None, post=None):
    """Build a mock that stands in for ``httpx.AsyncClient(...)``.

    The mock is async-context-manager-aware so the service code's
    ``async with httpx.AsyncClient(...)`` block works.
    """
    inner = MagicMock()
    if get is not None:
        inner.get = AsyncMock(side_effect=get) if callable(get) and not isinstance(
            get, AsyncMock
        ) else AsyncMock(return_value=get)
    if post is not None:
        inner.post = AsyncMock(side_effect=post) if callable(post) and not isinstance(
            post, AsyncMock
        ) else AsyncMock(return_value=post)

    cm = MagicMock()
    cm.__aenter__ = AsyncMock(return_value=inner)
    cm.__aexit__ = AsyncMock(return_value=None)

    factory = MagicMock(return_value=cm)
    return factory, inner


@pytest.fixture(autouse=True)
def _ensure_url(monkeypatch):
    """Default to a known API URL so tests don't short-circuit on empty config."""
    from app.core import config as cfg
    monkeypatch.setattr(cfg.settings, "animaforge_api_url", "http://anima.test")
    monkeypatch.setattr(cfg.settings, "animaforge_api_key", "test-key")
    monkeypatch.setattr(
        cfg.settings, "animaforge_webhook_base_url", "http://esf.test"
    )
    yield


# ---------------------------------------------------------------------------
# is_available()
# ---------------------------------------------------------------------------

class TestIsAvailable:
    @pytest.mark.asyncio
    async def test_returns_true_on_2xx(self):
        factory, inner = _make_async_client_mock(get=_FakeResponse(200))
        with patch("app.services.animaforge.client.httpx.AsyncClient", factory):
            assert await AnimaForgeService.is_available() is True
        inner.get.assert_awaited_once_with("http://anima.test/health")

    @pytest.mark.asyncio
    async def test_returns_false_on_4xx(self):
        factory, _ = _make_async_client_mock(get=_FakeResponse(503))
        with patch("app.services.animaforge.client.httpx.AsyncClient", factory):
            assert await AnimaForgeService.is_available() is False

    @pytest.mark.asyncio
    async def test_returns_false_on_connection_error(self):
        async def boom(*_a, **_kw):
            raise httpx.ConnectError("nope")

        factory, _ = _make_async_client_mock(get=boom)
        with patch("app.services.animaforge.client.httpx.AsyncClient", factory):
            assert await AnimaForgeService.is_available() is False

    @pytest.mark.asyncio
    async def test_returns_false_when_url_blank(self, monkeypatch):
        from app.core import config as cfg
        monkeypatch.setattr(cfg.settings, "animaforge_api_url", "")
        # Should never even construct an httpx client.
        with patch("app.services.animaforge.client.httpx.AsyncClient") as factory:
            assert await AnimaForgeService.is_available() is False
            factory.assert_not_called()


# ---------------------------------------------------------------------------
# request_render()
# ---------------------------------------------------------------------------

class TestRequestRender:
    @pytest.mark.asyncio
    async def test_returns_shaped_dict_on_200(self):
        body = {"job_id": "af_123", "estimated_seconds": 45, "status": "pending"}
        factory, inner = _make_async_client_mock(post=_FakeResponse(200, body))
        with patch("app.services.animaforge.client.httpx.AsyncClient", factory):
            result = await AnimaForgeService.request_render(
                type="weapon-diagram",
                title_id="madden-26",
                spec={"foo": "bar"},
                user_id="u1",
            )
        assert result == body
        # webhook URL defaulted from settings
        kwargs = inner.post.await_args.kwargs
        assert kwargs["json"]["webhook_url"] == "http://esf.test/api/v1/animaforge/webhook"
        assert kwargs["json"]["type"] == "weapon-diagram"
        assert kwargs["json"]["data"] == {"foo": "bar"}
        assert kwargs["headers"]["Authorization"] == "Bearer test-key"

    @pytest.mark.asyncio
    async def test_raises_on_5xx(self):
        factory, _ = _make_async_client_mock(
            post=_FakeResponse(500, text="boom")
        )
        with patch("app.services.animaforge.client.httpx.AsyncClient", factory):
            with pytest.raises(AnimaForgeUnavailable):
                await AnimaForgeService.request_render(
                    type="weapon-diagram",
                    title_id="madden-26",
                    spec={},
                    user_id="u1",
                )

    @pytest.mark.asyncio
    async def test_raises_on_network_error(self):
        async def boom(*_a, **_kw):
            raise httpx.ConnectError("nope")

        factory, _ = _make_async_client_mock(post=boom)
        with patch("app.services.animaforge.client.httpx.AsyncClient", factory):
            with pytest.raises(AnimaForgeUnavailable):
                await AnimaForgeService.request_render(
                    type="weapon-diagram",
                    title_id="madden-26",
                    spec={},
                    user_id="u1",
                )

    @pytest.mark.asyncio
    async def test_uses_explicit_webhook_url(self):
        body = {"job_id": "af_456", "estimated_seconds": 10, "status": "pending"}
        factory, inner = _make_async_client_mock(post=_FakeResponse(200, body))
        with patch("app.services.animaforge.client.httpx.AsyncClient", factory):
            await AnimaForgeService.request_render(
                type="drill-demo",
                title_id="nba-2k26",
                spec={},
                user_id="system",
                webhook_url="https://override.example/hook",
            )
        kwargs = inner.post.await_args.kwargs
        assert kwargs["json"]["webhook_url"] == "https://override.example/hook"


# ---------------------------------------------------------------------------
# get_job_status()
# ---------------------------------------------------------------------------

class TestGetJobStatus:
    @pytest.mark.asyncio
    async def test_returns_body_on_200(self):
        body = {"status": "complete", "video_url": "https://v/x.mp4", "progress": 100}
        factory, _ = _make_async_client_mock(get=_FakeResponse(200, body))
        with patch("app.services.animaforge.client.httpx.AsyncClient", factory):
            result = await AnimaForgeService.get_job_status("af_123")
        assert result == body

    @pytest.mark.asyncio
    async def test_raises_on_5xx(self):
        factory, _ = _make_async_client_mock(get=_FakeResponse(502))
        with patch("app.services.animaforge.client.httpx.AsyncClient", factory):
            with pytest.raises(AnimaForgeUnavailable):
                await AnimaForgeService.get_job_status("af_123")

    @pytest.mark.asyncio
    async def test_raises_on_404(self):
        factory, _ = _make_async_client_mock(get=_FakeResponse(404))
        with patch("app.services.animaforge.client.httpx.AsyncClient", factory):
            with pytest.raises(AnimaForgeUnavailable):
                await AnimaForgeService.get_job_status("missing")
