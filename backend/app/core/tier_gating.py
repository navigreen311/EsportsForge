"""Subscription tier enforcement for EsportsForge.

Provides dependency injectors, decorators, and middleware for gating
API features and game-title access based on the user's subscription tier.
"""

from __future__ import annotations

import functools
from typing import Any, Callable

from fastapi import Depends, HTTPException, Request, status
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.responses import JSONResponse, Response

from app.models.user import TIER_TITLE_LIMITS, User, UserTier

# ---------------------------------------------------------------------------
# Tier ordering (used for comparison)
# ---------------------------------------------------------------------------

TIER_ORDER: list[UserTier] = [
    UserTier.FREE,
    UserTier.COMPETITIVE,
    UserTier.ELITE,
    UserTier.TEAM,
]


def _tier_level(tier: UserTier) -> int:
    """Return the numeric level for a tier (0-based)."""
    try:
        return TIER_ORDER.index(tier)
    except ValueError:
        return 0


# ---------------------------------------------------------------------------
# Feature → minimum tier mapping
# ---------------------------------------------------------------------------

# Features available per tier (cumulative — higher tiers include lower)
TIER_FEATURES: dict[UserTier, set[str]] = {
    UserTier.FREE: {
        "basic_gameplan",
        "meta_alerts",
    },
    UserTier.COMPETITIVE: {
        # All Free features plus:
        "basic_gameplan",
        "meta_alerts",
        "full_ai_agents",
        "player_twin",
        "film_ai",
        "tilt_guard",
        "benchmark_ai",
        "install_ai",
    },
    UserTier.ELITE: {
        # All Competitive features plus:
        "basic_gameplan",
        "meta_alerts",
        "full_ai_agents",
        "player_twin",
        "film_ai",
        "tilt_guard",
        "benchmark_ai",
        "install_ai",
        "full_platform",
        "tourna_ops",
        "voice_forge",
        "forge_vault",
        "impact_rank_priority",
    },
    UserTier.TEAM: {
        # All Elite features plus:
        "basic_gameplan",
        "meta_alerts",
        "full_ai_agents",
        "player_twin",
        "film_ai",
        "tilt_guard",
        "benchmark_ai",
        "install_ai",
        "full_platform",
        "tourna_ops",
        "voice_forge",
        "forge_vault",
        "impact_rank_priority",
        "coach_portal",
        "war_room",
        "squad_ops",
        "shared_playbooks",
    },
}

# Total supported game titles
ALL_TITLES: list[str] = [
    "madden26",
    "cfb26",
    "fc26",
    "nba2k26",
    "nhl26",
    "mlb26",
    "cod26",
    "fortnite",
    "apex",
    "valorant",
    "rocket_league",
]


# ---------------------------------------------------------------------------
# Dependency: require_tier
# ---------------------------------------------------------------------------

def require_tier(minimum_tier: UserTier):
    """FastAPI dependency factory that enforces a minimum subscription tier.

    Usage::

        @router.get("/premium", dependencies=[Depends(require_tier(UserTier.COMPETITIVE))])
        async def premium_endpoint(): ...

    Or inject the user directly::

        @router.get("/premium")
        async def premium_endpoint(user: User = Depends(require_tier(UserTier.COMPETITIVE))): ...
    """
    from app.core.security import get_current_user  # avoid circular import

    async def _check_tier(current_user: User = Depends(get_current_user)) -> User:
        user_level = _tier_level(current_user.tier)
        required_level = _tier_level(minimum_tier)
        if user_level < required_level:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={
                    "error": "tier_access_denied",
                    "message": (
                        f"This feature requires '{minimum_tier.value}' tier or above. "
                        f"Current tier: '{current_user.tier.value}'."
                    ),
                    "required_tier": minimum_tier.value,
                    "current_tier": current_user.tier.value,
                    "upgrade_url": "/api/v1/subscription/upgrade",
                },
            )
        return current_user

    return _check_tier


# ---------------------------------------------------------------------------
# Title access check
# ---------------------------------------------------------------------------

def check_title_access(user: User, title: str) -> bool:
    """Check whether a user's tier allows access to a specific game title.

    Returns True if access is allowed.

    Free = 1 title, Competitive = 3, Elite/Team = all 11.
    """
    limit = TIER_TITLE_LIMITS.get(user.tier)
    if limit is None:
        return True  # unlimited

    # For limited tiers, the user's active_title is checked.
    # In a real system this would check against their selected titles list.
    if user.active_title and user.active_title == title:
        return True

    # If no active title is set, allow the first title they access.
    if user.active_title is None:
        return True

    return False


def require_title_access(title_param: str = "title"):
    """FastAPI dependency that checks title access based on the user's tier.

    Reads the title from query/path params identified by ``title_param``.
    """
    from app.core.security import get_current_user

    async def _check(
        request: Request,
        current_user: User = Depends(get_current_user),
    ) -> User:
        # Try query params, then path params
        title = request.query_params.get(title_param) or request.path_params.get(
            title_param
        )
        if title and not check_title_access(current_user, title):
            limit = TIER_TITLE_LIMITS.get(current_user.tier, 1)
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={
                    "error": "title_access_denied",
                    "message": (
                        f"Your '{current_user.tier.value}' tier allows access to "
                        f"{limit} title(s). Upgrade to access '{title}'."
                    ),
                    "current_tier": current_user.tier.value,
                    "title_limit": limit,
                    "requested_title": title,
                    "upgrade_url": "/api/v1/subscription/upgrade",
                },
            )
        return current_user

    return _check


# ---------------------------------------------------------------------------
# Feature access check
# ---------------------------------------------------------------------------

def check_feature_access(user: User, feature: str) -> bool:
    """Return True if the user's tier includes the named feature."""
    allowed = TIER_FEATURES.get(user.tier, set())
    return feature in allowed


def require_feature(feature: str):
    """FastAPI dependency that checks whether the user's tier includes a feature."""
    from app.core.security import get_current_user

    async def _check(current_user: User = Depends(get_current_user)) -> User:
        if not check_feature_access(current_user, feature):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={
                    "error": "feature_access_denied",
                    "message": (
                        f"The '{feature}' feature is not available on your "
                        f"'{current_user.tier.value}' tier."
                    ),
                    "feature": feature,
                    "current_tier": current_user.tier.value,
                    "upgrade_url": "/api/v1/subscription/upgrade",
                },
            )
        return current_user

    return _check


# ---------------------------------------------------------------------------
# Decorator: @requires_tier
# ---------------------------------------------------------------------------

def requires_tier(minimum_tier: UserTier):
    """Decorator for endpoint-level tier gating.

    Usage::

        @router.get("/premium")
        @requires_tier(UserTier.COMPETITIVE)
        async def premium_endpoint(request: Request): ...

    Note: For most cases, prefer the ``require_tier`` dependency which
    integrates better with FastAPI's DI system. This decorator is useful
    when you want a simple decorator pattern.
    """

    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        async def wrapper(*args: Any, **kwargs: Any) -> Any:
            request: Request | None = kwargs.get("request")
            if request is None:
                for arg in args:
                    if isinstance(arg, Request):
                        request = arg
                        break

            if request is not None:
                user = getattr(request.state, "user", None)
                if user is not None:
                    user_level = _tier_level(user.tier)
                    required_level = _tier_level(minimum_tier)
                    if user_level < required_level:
                        raise HTTPException(
                            status_code=status.HTTP_403_FORBIDDEN,
                            detail={
                                "error": "tier_access_denied",
                                "message": (
                                    f"This feature requires '{minimum_tier.value}' tier or above. "
                                    f"Current tier: '{user.tier.value}'."
                                ),
                                "required_tier": minimum_tier.value,
                                "current_tier": user.tier.value,
                            },
                        )
            return await func(*args, **kwargs)

        return wrapper

    return decorator


# ---------------------------------------------------------------------------
# Middleware: TierGateMiddleware
# ---------------------------------------------------------------------------

# Routes that are exempt from tier checking (public routes)
TIER_EXEMPT_PATHS: set[str] = {
    "/api/health",
    "/api/v1/status",
    "/api/v1/auth/login",
    "/api/v1/auth/register",
    "/api/v1/auth/refresh",
    "/api/docs",
    "/api/redoc",
    "/openapi.json",
}


class TierGateMiddleware(BaseHTTPMiddleware):
    """Middleware that checks tier on every request.

    This middleware attaches tier information to the request state and
    can enforce route-level tier requirements based on path prefix mapping.
    It works alongside the more granular ``require_tier`` dependency.
    """

    # Path prefix -> minimum tier mapping
    ROUTE_TIER_MAP: dict[str, UserTier] = {
        "/api/v1/forgecore": UserTier.FREE,
        "/api/v1/player-twin": UserTier.COMPETITIVE,
        "/api/v1/film": UserTier.COMPETITIVE,
        "/api/v1/mental": UserTier.COMPETITIVE,
        "/api/v1/drills": UserTier.FREE,
        "/api/v1/install": UserTier.COMPETITIVE,
        "/api/v1/sim": UserTier.COMPETITIVE,
        "/api/v1/calibration": UserTier.COMPETITIVE,
        "/api/v1/adapt": UserTier.COMPETITIVE,
        "/api/v1/confidence": UserTier.COMPETITIVE,
        "/api/v1/proof": UserTier.COMPETITIVE,
    }

    async def dispatch(
        self, request: Request, call_next: RequestResponseEndpoint
    ) -> Response:
        """Process each request through tier gate logic."""
        path = request.url.path

        # Skip exempt paths
        if path in TIER_EXEMPT_PATHS or path.startswith("/api/docs") or path.startswith("/api/redoc"):
            return await call_next(request)

        # Attach tier info to request state if user is available
        user = getattr(request.state, "user", None)
        if user is not None:
            request.state.user_tier = user.tier
            request.state.tier_features = TIER_FEATURES.get(user.tier, set())

            # Check route-level tier requirements
            for prefix, min_tier in self.ROUTE_TIER_MAP.items():
                if path.startswith(prefix):
                    user_level = _tier_level(user.tier)
                    required_level = _tier_level(min_tier)
                    if user_level < required_level:
                        return JSONResponse(
                            status_code=403,
                            content={
                                "detail": {
                                    "error": "tier_access_denied",
                                    "message": (
                                        f"This route requires '{min_tier.value}' "
                                        f"tier or above."
                                    ),
                                    "required_tier": min_tier.value,
                                    "current_tier": user.tier.value,
                                }
                            },
                        )
                    break

        return await call_next(request)
