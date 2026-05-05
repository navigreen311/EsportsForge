# STUB — replace at merge.
#
# Agent #1 owns the canonical contents of this package
# (`client.py`, `exceptions.py`, full re-exports).  This stub exists ONLY
# so Agent #6's drill endpoint can import `AnimaForgeService` and
# `AnimaForgeUnavailable` without needing Agent #1's branch merged first.
#
# At merge time, replace this file with Agent #1's version. The public
# surface (`AnimaForgeService.is_available`, `.request_render`,
# `.get_job_status`, `AnimaForgeUnavailable`) matches the contract in
# `docs/integrations/animaforge_contract.md` Section 3.
from __future__ import annotations

from typing import Any


class AnimaForgeUnavailable(Exception):
    """Raised when AnimaForge is unreachable or returns 5xx."""


class AnimaForgeService:
    """Stub of the AnimaForge service wrapper (Agent #1 owns the real one).

    All methods are async and match the canonical signatures in the
    integration contract. Tests monkeypatch these — production code on
    main will replace this stub with the real httpx-backed client.
    """

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
    ) -> dict[str, Any]:
        raise AnimaForgeUnavailable(
            "AnimaForgeService stub — replace with Agent #1 client at merge"
        )

    @staticmethod
    async def get_job_status(job_id: str) -> dict[str, Any]:
        raise AnimaForgeUnavailable(
            "AnimaForgeService stub — replace with Agent #1 client at merge"
        )


__all__ = ["AnimaForgeService", "AnimaForgeUnavailable"]
