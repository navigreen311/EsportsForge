"""Tests for production middleware — RequestId, Timing, RateLimiting."""

from __future__ import annotations

import time

import pytest
from starlette.applications import Starlette
from starlette.requests import Request
from starlette.responses import JSONResponse
from starlette.testclient import TestClient

from app.core.middleware import (
    DEFAULT_RATE_LIMITS,
    RateLimitMiddleware,
    RequestIdMiddleware,
    TimingMiddleware,
)


# ---------------------------------------------------------------------------
# Helpers — minimal Starlette app for middleware testing
# ---------------------------------------------------------------------------

def _make_app(*middleware_classes):
    """Create a test Starlette app with the given middleware stack."""

    async def homepage(request: Request) -> JSONResponse:
        body = {"ok": True}
        request_id = getattr(request.state, "request_id", None)
        if request_id:
            body["request_id"] = request_id
        return JSONResponse(body)

    app = Starlette(routes=[
        # Use a simple route
    ])

    # Add a catch-all route
    @app.route("/test")
    async def test_route(request: Request) -> JSONResponse:
        body = {"ok": True}
        request_id = getattr(request.state, "request_id", None)
        if request_id:
            body["request_id"] = request_id
        return JSONResponse(body)

    @app.route("/api/health")
    async def health(request: Request) -> JSONResponse:
        return JSONResponse({"status": "healthy"})

    for cls in reversed(middleware_classes):
        if cls == RateLimitMiddleware:
            app.add_middleware(cls, rate_limits={"_anonymous": 5})
        else:
            app.add_middleware(cls)

    return app


# ---------------------------------------------------------------------------
# RequestIdMiddleware
# ---------------------------------------------------------------------------

class TestRequestIdMiddleware:
    def test_generates_request_id(self):
        app = _make_app(RequestIdMiddleware)
        client = TestClient(app)
        response = client.get("/test")
        assert response.status_code == 200
        assert "X-Request-ID" in response.headers
        # UUID4 format: 8-4-4-4-12 hex chars
        request_id = response.headers["X-Request-ID"]
        assert len(request_id) == 36
        assert request_id.count("-") == 4

    def test_preserves_client_request_id(self):
        app = _make_app(RequestIdMiddleware)
        client = TestClient(app)
        custom_id = "my-custom-request-id-123"
        response = client.get("/test", headers={"X-Request-ID": custom_id})
        assert response.status_code == 200
        assert response.headers["X-Request-ID"] == custom_id

    def test_unique_ids_per_request(self):
        app = _make_app(RequestIdMiddleware)
        client = TestClient(app)
        ids = set()
        for _ in range(10):
            response = client.get("/test")
            ids.add(response.headers["X-Request-ID"])
        assert len(ids) == 10


# ---------------------------------------------------------------------------
# TimingMiddleware
# ---------------------------------------------------------------------------

class TestTimingMiddleware:
    def test_adds_process_time_header(self):
        app = _make_app(TimingMiddleware)
        client = TestClient(app)
        response = client.get("/test")
        assert response.status_code == 200
        assert "X-Process-Time" in response.headers
        time_val = response.headers["X-Process-Time"]
        assert time_val.endswith("ms")

    def test_process_time_is_positive(self):
        app = _make_app(TimingMiddleware)
        client = TestClient(app)
        response = client.get("/test")
        time_str = response.headers["X-Process-Time"].replace("ms", "")
        duration = float(time_str)
        assert duration >= 0


# ---------------------------------------------------------------------------
# RateLimitMiddleware
# ---------------------------------------------------------------------------

class TestRateLimitMiddleware:
    def test_allows_requests_under_limit(self):
        app = _make_app(RateLimitMiddleware)
        client = TestClient(app)
        # limit is set to 5 for anonymous
        for i in range(5):
            response = client.get("/test")
            assert response.status_code == 200

    def test_blocks_requests_over_limit(self):
        app = _make_app(RateLimitMiddleware)
        client = TestClient(app)
        # Send 6 requests (limit is 5)
        responses = [client.get("/test") for _ in range(6)]
        assert responses[-1].status_code == 429

    def test_rate_limit_response_body(self):
        app = _make_app(RateLimitMiddleware)
        client = TestClient(app)
        # Exhaust limit
        for _ in range(5):
            client.get("/test")
        response = client.get("/test")
        assert response.status_code == 429
        body = response.json()
        assert body["error"] == "rate_limit_exceeded"
        assert "retry_after_seconds" in body

    def test_rate_limit_headers(self):
        app = _make_app(RateLimitMiddleware)
        client = TestClient(app)
        response = client.get("/test")
        assert "X-RateLimit-Limit" in response.headers
        assert "X-RateLimit-Remaining" in response.headers
        assert response.headers["X-RateLimit-Limit"] == "5"

    def test_health_endpoint_bypasses_rate_limit(self):
        app = _make_app(RateLimitMiddleware)
        client = TestClient(app)
        # Exhaust limit on /test
        for _ in range(5):
            client.get("/test")
        # /api/health should still work
        response = client.get("/api/health")
        assert response.status_code == 200

    def test_default_rate_limits_defined(self):
        assert "free" in DEFAULT_RATE_LIMITS
        assert "competitive" in DEFAULT_RATE_LIMITS
        assert "elite" in DEFAULT_RATE_LIMITS
        assert "team" in DEFAULT_RATE_LIMITS
        assert "_anonymous" in DEFAULT_RATE_LIMITS


# ---------------------------------------------------------------------------
# Combined middleware stack
# ---------------------------------------------------------------------------

class TestCombinedMiddleware:
    def test_all_middleware_headers_present(self):
        app = _make_app(RequestIdMiddleware, TimingMiddleware)
        client = TestClient(app)
        response = client.get("/test")
        assert response.status_code == 200
        assert "X-Request-ID" in response.headers
        assert "X-Process-Time" in response.headers
