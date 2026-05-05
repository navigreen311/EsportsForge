"""Session-end hook for share-win triggers (Agent #9).

A single helper that callers (drill complete, session end) invoke at the bottom
of their handler. The helper detects triggers and fires render requests
without blocking the response.

Usage::

    from app.services.animaforge.session_end_hook import fire_share_win_hook
    await fire_share_win_hook(user_id=str(user.id), title_id=title_id, session_data=...)

Failures are logged and swallowed — share-win is a viral-growth nicety; never
let it 500 a drill-complete or session-end response.
"""

from __future__ import annotations

import asyncio
import logging
from typing import Any

from app.services.animaforge.share_spec import build_share_card_spec
from app.services.animaforge.share_triggers import (
    ShareTrigger,
    check_share_win_triggers,
)

logger = logging.getLogger(__name__)


async def _request_share_render(
    user: Any,
    user_id: str,
    title_id: str,
    trigger: ShareTrigger,
) -> None:
    """Fire-and-forget single render request for one trigger."""
    try:
        from app.services.animaforge.client import (  # type: ignore
            AnimaForgeService,
        )
    except Exception:  # noqa: BLE001
        # Agent #1's service not merged yet — nothing to do.
        return

    spec = build_share_card_spec(trigger.type, trigger.data, user)
    try:
        await AnimaForgeService.request_render(
            type="share-win",
            title_id=title_id,
            spec=spec,
            user_id=user_id,
        )
    except Exception:  # noqa: BLE001
        logger.exception("Share-win render request failed for %s", trigger.type)


async def fire_share_win_hook(
    *,
    user: Any | None = None,
    user_id: str,
    title_id: str,
    session_data: dict[str, Any],
) -> list[ShareTrigger]:
    """Detect triggers and dispatch render requests in the background.

    Returns the detected triggers (useful for tests + telemetry). Render
    requests are scheduled with ``asyncio.create_task`` so the caller never
    blocks on AnimaForge.
    """
    try:
        triggers = await check_share_win_triggers(user_id, title_id, session_data)
    except Exception:  # noqa: BLE001
        logger.exception("check_share_win_triggers failed")
        return []

    # Background-render each trigger via list comprehension over create_task.
    [
        asyncio.create_task(_request_share_render(user, user_id, title_id, t))
        for t in triggers
    ]
    return triggers


__all__ = ["fire_share_win_hook"]
