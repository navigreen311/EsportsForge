"""Integration test configuration.

Mounts backbone routers that are not yet included in the main app
so integration tests can exercise them end-to-end.
"""

import pytest
from app.main import app

# Backbone routers that exist but are not mounted in main.py / router.py yet.
from app.api.v1.endpoints.forgecore import router as forgecore_router
from app.api.v1.endpoints.player_twin import router as player_twin_router
from app.api.v1.endpoints.opponents import router as opponents_router
from app.api.v1.endpoints.integrity import router as integrity_router
from app.api.v1.endpoints.mental import router as mental_router

_BACKBONE_PREFIXES = [
    "/api/v1/forgecore",
    "/api/v1/player-twin",
    "/api/v1/opponents",
    "/api/v1/integrity",
    "/api/v1/mental",
]


def _router_already_mounted(prefix: str) -> bool:
    """Check whether a prefix is already registered on the app."""
    for route in app.routes:
        path = getattr(route, "path", "")
        if path.startswith(prefix):
            return True
    return False


# Mount backbone routers under /api/v1 if they are not already present.
if not _router_already_mounted("/api/v1/forgecore"):
    app.include_router(forgecore_router, prefix="/api/v1")
if not _router_already_mounted("/api/v1/player-twin"):
    app.include_router(player_twin_router, prefix="/api/v1")
if not _router_already_mounted("/api/v1/opponents"):
    app.include_router(opponents_router, prefix="/api/v1")
if not _router_already_mounted("/api/v1/integrity"):
    app.include_router(integrity_router, prefix="/api/v1")
if not _router_already_mounted("/api/v1/mental"):
    app.include_router(mental_router, prefix="/api/v1")

# Also ensure the v1 router (auth, etc.) is mounted.
from app.api.v1.router import api_v1_router  # noqa: E402

if not _router_already_mounted("/api/v1/auth"):
    app.include_router(api_v1_router)


# Integration tests reference a `test_client` fixture, but the shared
# parent conftest defines it as `client`. Alias the parent fixture so
# the existing test files don't all need to be touched.
import pytest_asyncio  # noqa: E402


@pytest_asyncio.fixture
async def test_client(client):
    yield client


# The auth-flow integration suite hits register/login in rapid
# succession; production rate-limit middleware caps those at 5 per
# 15-minute window which trips after a handful of tests and produces
# 429s instead of the expected 422 / 200 responses. Disable the
# throttle for the test process — the suite still exercises the
# normal validation paths.
from app.middleware.rate_limit import RateLimitMiddleware  # noqa: E402

RateLimitMiddleware._clean_and_count = lambda self, key: 0  # type: ignore[method-assign]
