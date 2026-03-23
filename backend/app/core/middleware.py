"""Production middleware stack for EsportsForge.

Includes request identification, timing, structured logging, and rate limiting.
"""

from __future__ import annotations

import json
import logging
import time
import uuid
from collections import defaultdict
from typing import Any

from fastapi import FastAPI
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import JSONResponse, Response

from app.models.user import UserTier

logger = logging.getLogger("esportsforge")


# ---------------------------------------------------------------------------
# RequestIdMiddleware
# ---------------------------------------------------------------------------

class RequestIdMiddleware(BaseHTTPMiddleware):
    """Attach a unique X-Request-ID to every request and response.

    If the client sends an ``X-Request-ID`` header it is re-used; otherwise a
    new UUID4 is generated.  The ID is stored on ``request.state.request_id``
    so downstream code can reference it.
    """

    async def dispatch(
        self, request: Request, call_next: RequestResponseEndpoint
    ) -> Response:
        request_id = request.headers.get("X-Request-ID") or str(uuid.uuid4())
        request.state.request_id = request_id

        response = await call_next(request)
        response.headers["X-Request-ID"] = request_id
        return response


# ---------------------------------------------------------------------------
# TimingMiddleware
# ---------------------------------------------------------------------------

class TimingMiddleware(BaseHTTPMiddleware):
    """Log request duration and attach ``X-Process-Time`` header."""

    async def dispatch(
        self, request: Request, call_next: RequestResponseEndpoint
    ) -> Response:
        start = time.perf_counter()
        response = await call_next(request)
        duration_ms = (time.perf_counter() - start) * 1000

        response.headers["X-Process-Time"] = f"{duration_ms:.2f}ms"

        # Log slow requests (>1 second)
        if duration_ms > 1000:
            request_id = getattr(request.state, "request_id", "unknown")
            logger.warning(
                "Slow request: %s %s took %.2fms (request_id=%s)",
                request.method,
                request.url.path,
                duration_ms,
                request_id,
            )

        return response


# ---------------------------------------------------------------------------
# StructuredLoggingMiddleware
# ---------------------------------------------------------------------------

class StructuredLoggingMiddleware(BaseHTTPMiddleware):
    """Emit structured JSON log lines for every request.

    Log entry includes method, path, status, duration, user tier, and
    request ID for correlation with distributed traces.
    """

    async def dispatch(
        self, request: Request, call_next: RequestResponseEndpoint
    ) -> Response:
        start = time.perf_counter()
        response = await call_next(request)
        duration_ms = (time.perf_counter() - start) * 1000

        request_id = getattr(request.state, "request_id", None)
        user_tier = getattr(request.state, "user_tier", None)

        log_entry: dict[str, Any] = {
            "event": "http_request",
            "method": request.method,
            "path": request.url.path,
            "status": response.status_code,
            "duration_ms": round(duration_ms, 2),
            "client_ip": request.client.host if request.client else None,
            "user_agent": request.headers.get("user-agent"),
        }
        if request_id:
            log_entry["request_id"] = request_id
        if user_tier:
            log_entry["user_tier"] = user_tier.value if hasattr(user_tier, "value") else str(user_tier)

        logger.info(json.dumps(log_entry))
        return response


# ---------------------------------------------------------------------------
# RateLimitMiddleware
# ---------------------------------------------------------------------------

# Default rate limits per tier (requests per minute)
DEFAULT_RATE_LIMITS: dict[str, int] = {
    UserTier.FREE.value: 20,
    UserTier.COMPETITIVE.value: 60,
    UserTier.ELITE.value: 120,
    UserTier.TEAM.value: 300,
    "_anonymous": 10,
}


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Basic in-memory rate limiter using a sliding window per client.

    In production, replace with Redis-backed rate limiting. This middleware
    is intentionally simple for MVP use.

    Rate limits are configurable per tier via ``rate_limits`` dict.
    """

    def __init__(self, app: Any, rate_limits: dict[str, int] | None = None) -> None:
        super().__init__(app)
        self.rate_limits = rate_limits or DEFAULT_RATE_LIMITS
        # Store: key -> list of timestamps
        self._requests: dict[str, list[float]] = defaultdict(list)

    def _get_client_key(self, request: Request) -> str:
        """Build a rate-limit key from user ID or client IP."""
        user = getattr(request.state, "user", None)
        if user is not None:
            return f"user:{user.id}"
        if request.client:
            return f"ip:{request.client.host}"
        return "ip:unknown"

    def _get_limit(self, request: Request) -> int:
        """Determine the rate limit for the current request."""
        user_tier = getattr(request.state, "user_tier", None)
        if user_tier is not None:
            tier_val = user_tier.value if hasattr(user_tier, "value") else str(user_tier)
            return self.rate_limits.get(tier_val, self.rate_limits.get("_anonymous", 10))
        return self.rate_limits.get("_anonymous", 10)

    async def dispatch(
        self, request: Request, call_next: RequestResponseEndpoint
    ) -> Response:
        # Skip rate limiting for health checks and docs
        path = request.url.path
        if path in {"/api/health", "/api/docs", "/api/redoc", "/openapi.json"}:
            return await call_next(request)

        client_key = self._get_client_key(request)
        limit = self._get_limit(request)
        now = time.time()
        window_start = now - 60.0  # 1-minute window

        # Clean old entries
        timestamps = self._requests[client_key]
        self._requests[client_key] = [t for t in timestamps if t > window_start]

        if len(self._requests[client_key]) >= limit:
            request_id = getattr(request.state, "request_id", None)
            retry_after = int(60 - (now - self._requests[client_key][0])) + 1
            return JSONResponse(
                status_code=429,
                content={
                    "error": "rate_limit_exceeded",
                    "message": f"Rate limit of {limit} requests/minute exceeded.",
                    "request_id": request_id,
                    "retry_after_seconds": retry_after,
                },
                headers={
                    "Retry-After": str(retry_after),
                    "X-RateLimit-Limit": str(limit),
                    "X-RateLimit-Remaining": "0",
                },
            )

        self._requests[client_key].append(now)

        response = await call_next(request)
        remaining = max(0, limit - len(self._requests[client_key]))
        response.headers["X-RateLimit-Limit"] = str(limit)
        response.headers["X-RateLimit-Remaining"] = str(remaining)
        return response


# ---------------------------------------------------------------------------
# Middleware registration helper
# ---------------------------------------------------------------------------

def register_middleware(app: FastAPI) -> None:
    """Register all production middleware on the FastAPI app.

    Order matters: middleware is executed in reverse registration order
    (last registered = outermost = runs first).
    """
    # Innermost (runs last) → outermost (runs first)
    app.add_middleware(RateLimitMiddleware)
    app.add_middleware(StructuredLoggingMiddleware)
    app.add_middleware(TimingMiddleware)
    app.add_middleware(RequestIdMiddleware)
