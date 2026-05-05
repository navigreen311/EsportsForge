"""AnimaForge integration package.

NOTE: This module is currently a STUB so Agent #4's `weapon_spec` and
`animaforge_arsenal` endpoint can import without Agent #1's canonical
service merged. Agent #1 owns this file and will replace it at merge time.
"""

# STUB — Agent #1 owns the canonical version.
# Re-exports / canonical service live in `client.py` once Agent #1 lands.

from __future__ import annotations

# Re-export the spec builder so callers can do
# `from app.services.animaforge import build_weapon_animation_spec`.
from app.services.animaforge.weapon_spec import build_weapon_animation_spec  # noqa: F401


class AnimaForgeUnavailable(Exception):
    """Raised when AnimaForge is unreachable or returns 5xx.

    STUB — Agent #1 owns the canonical version (lives in
    `app.services.animaforge.exceptions`).
    """


class AnimaForgeService:
    """Stub of the AnimaForge service wrapper.

    STUB — Agent #1 owns the canonical implementation in `client.py`.
    The real version uses httpx.AsyncClient. This stub lets Agent #4's
    endpoint module import without exploding before merge.
    """

    @staticmethod
    async def is_available() -> bool:  # pragma: no cover - stub
        # Default to False so frontend hides UI silently in dev (matches
        # contract §11 "Mocking AnimaForge in dev/tests").
        return False

    @staticmethod
    async def request_render(
        *,
        type: str,  # noqa: A002 - matches contract surface
        title_id: str,
        spec: dict,
        user_id: str,
        webhook_url: str | None = None,
    ) -> dict:  # pragma: no cover - stub
        raise NotImplementedError(
            "AnimaForgeService.request_render is a stub — "
            "Agent #1 owns the canonical implementation."
        )

    @staticmethod
    async def get_job_status(job_id: str) -> dict:  # pragma: no cover - stub
        raise NotImplementedError(
            "AnimaForgeService.get_job_status is a stub — "
            "Agent #1 owns the canonical implementation."
        )
