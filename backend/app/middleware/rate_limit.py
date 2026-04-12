"""Simple in-memory rate limiter middleware for FastAPI.

Production deployments should replace this with a Redis-backed solution.
"""

import time
from collections import defaultdict

from fastapi import status
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse, Response


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Rate-limit specific paths by client IP address.

    Parameters
    ----------
    paths : list[str]
        URL paths to apply the rate limit to.
    max_requests : int
        Maximum number of requests allowed within the window.
    window_seconds : int
        Sliding window duration in seconds.
    """

    def __init__(
        self,
        app,
        paths: list[str] | None = None,
        max_requests: int = 5,
        window_seconds: int = 900,
    ):
        super().__init__(app)
        self.paths = set(paths or [])
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        # {ip: [timestamp, ...]}
        self._hits: dict[str, list[float]] = defaultdict(list)

    def _clean_and_count(self, key: str) -> int:
        """Remove expired timestamps and return current count."""
        now = time.time()
        cutoff = now - self.window_seconds
        self._hits[key] = [t for t in self._hits[key] if t > cutoff]
        return len(self._hits[key])

    async def dispatch(self, request: Request, call_next) -> Response:
        if request.url.path not in self.paths:
            return await call_next(request)

        client_ip = request.client.host if request.client else "unknown"
        key = f"{client_ip}:{request.url.path}"

        count = self._clean_and_count(key)
        if count >= self.max_requests:
            return JSONResponse(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                content={
                    "detail": "Too many requests. Please try again later.",
                },
            )

        self._hits[key].append(time.time())
        return await call_next(request)
