"""AnimaForge service client — STUB.

Agent #8 placed this so the gameplan slice can import. Agent #1 owns the
real implementation. The stub matches the public surface defined in the
contract: `AnimaForgeService.is_available`, `request_render`,
`get_job_status`. All methods raise/return placeholder values that the
real client overrides.
"""

from __future__ import annotations


class AnimaForgeUnavailable(Exception):
    """Raised when AnimaForge is unreachable or returns 5xx."""


class AnimaForgeService:
    """Stub. Agent #1 replaces with httpx-based async client."""

    @staticmethod
    async def is_available() -> bool:
        return False

    @staticmethod
    async def request_render(
        *,
        type: str,
        title_id: str,
        spec: dict,
        user_id: str,
        webhook_url: str | None = None,
    ) -> dict:
        raise AnimaForgeUnavailable("AnimaForge client stub — not configured.")

    @staticmethod
    async def get_job_status(job_id: str) -> dict:
        raise AnimaForgeUnavailable("AnimaForge client stub — not configured.")
