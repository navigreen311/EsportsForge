"""Shared FastAPI dependencies for EsportsForge.

Central location for commonly injected dependencies so that endpoint
modules don't need to re-import from scattered locations.
"""

from __future__ import annotations

import logging
from typing import Any, AsyncGenerator

from fastapi import Depends, HTTPException, Query, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.db.base import get_db as _get_db
from app.models.user import User, UserTier

logger = logging.getLogger("esportsforge.deps")


# ---------------------------------------------------------------------------
# Database session
# ---------------------------------------------------------------------------

async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Provide an async database session.

    Re-exports from ``app.db.base`` for convenience so endpoint modules
    only need to import from ``app.core.deps``.
    """
    async for session in _get_db():
        yield session


# ---------------------------------------------------------------------------
# Redis client
# ---------------------------------------------------------------------------

_redis_client: Any | None = None


async def get_redis() -> Any | None:
    """Provide a Redis client connection.

    Returns ``None`` if Redis is not configured or unavailable.
    In production this is initialized during app startup.
    """
    return _redis_client


def set_redis_client(client: Any) -> None:
    """Set the global Redis client (called during app startup)."""
    global _redis_client
    _redis_client = client


# ---------------------------------------------------------------------------
# Current user
# ---------------------------------------------------------------------------

async def get_current_user(
    *,
    _db: AsyncSession = Depends(get_db),
    _request: Request,
) -> User:
    """Get the currently authenticated user.

    Delegates to ``app.core.security.get_current_user`` to avoid circular
    imports while providing a single import point from deps.
    """
    from app.core.security import get_current_user as _get_user, oauth2_scheme

    token = await oauth2_scheme(_request)
    return await _get_user(token=token, db=_db)


# ---------------------------------------------------------------------------
# Role / tier enforcement
# ---------------------------------------------------------------------------

def require_role(allowed_roles: list[UserTier]):
    """Dependency factory: require the user to have one of the listed roles.

    Usage::

        @router.get("/admin-only", dependencies=[Depends(require_role([UserTier.TEAM]))])
        async def admin_only(): ...
    """
    from app.core.security import get_current_user as _get_user

    async def _check_role(current_user: User = Depends(_get_user)) -> User:
        if current_user.tier not in allowed_roles:
            allowed_names = ", ".join(r.value for r in allowed_roles)
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={
                    "error": "role_denied",
                    "message": f"Requires one of: {allowed_names}. Your tier: {current_user.tier.value}.",
                    "allowed_roles": [r.value for r in allowed_roles],
                    "current_tier": current_user.tier.value,
                },
            )
        return current_user

    return _check_role


# ---------------------------------------------------------------------------
# Title context
# ---------------------------------------------------------------------------

async def get_title_context(
    title: str = Query(
        ...,
        description="Game title slug (e.g. 'madden26', 'cfb26')",
        pattern=r"^[a-z0-9_]+$",
    ),
) -> str:
    """Extract and validate the game title from query parameters.

    This dependency standardizes how endpoints receive the active title
    and can later include title-specific config loading.
    """
    supported = {
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
    }
    if title not in supported:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "error": "unsupported_title",
                "message": f"Title '{title}' is not supported.",
                "supported_titles": sorted(supported),
            },
        )
    return title


# ---------------------------------------------------------------------------
# Claude / Anthropic client
# ---------------------------------------------------------------------------

_claude_client: Any | None = None


async def get_claude_client() -> Any | None:
    """Return the Anthropic Claude client, or None if no API key is configured.

    The client is lazily initialized on first call and cached globally.
    """
    global _claude_client

    if _claude_client is not None:
        return _claude_client

    api_key = settings.anthropic_api_key
    if not api_key or api_key == "YOUR_ANTHROPIC_API_KEY_HERE":
        logger.info("Anthropic API key not configured; Claude client unavailable.")
        return None

    try:
        from anthropic import AsyncAnthropic

        _claude_client = AsyncAnthropic(api_key=api_key)
        logger.info("Claude client initialized (model: %s).", settings.claude_model)
        return _claude_client
    except ImportError:
        logger.warning("anthropic package not installed; Claude client unavailable.")
        return None
    except Exception as exc:
        logger.error("Failed to initialize Claude client: %s", exc)
        return None
