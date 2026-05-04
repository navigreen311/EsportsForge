"""Adapt endpoints — in-game adaptation and real-time adjustments.

The /play POST is what the gameplan page's "Simulate" button calls — it
asks Claude (or a deterministic fallback) for the right adjustment when a
specific play meets a specific opponent tendency or coverage shell.
"""

from __future__ import annotations

import json
import logging
from typing import Any

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel, Field

from app.core.security import get_current_user
from app.models.user import User
from app.services.ai.claude_client import ClaudeClient

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/adapt", tags=["Adaptation"])

_claude = ClaudeClient()


class AdaptPlayRequest(BaseModel):
    play: dict[str, Any] = Field(description="The play under consideration.")
    opponent_tendency: str = Field(description="Coverage / scheme being faced.")
    title_id: str
    opponent_archetype: str | None = None


class AdaptPlayResponse(BaseModel):
    adjustment: str
    audible_to: str | None = None
    confidence: int
    reasoning: str
    source: str = "claude"


_ADAPT_SYSTEM = (
    "You are AdaptAI for EsportsForge. Given a play and the live coverage / "
    "tendency the player is seeing, recommend the immediate in-game adjustment. "
    "Respond with strict JSON only — no markdown."
)


def _formula_adapt(req: AdaptPlayRequest) -> AdaptPlayResponse:
    name = req.play.get("name", "the play")
    tendency = req.opponent_tendency or "their look"
    return AdaptPlayResponse(
        adjustment=f"If {tendency} shows pre-snap, audible to a complementary call against the same shell.",
        audible_to=None,
        confidence=60,
        reasoning=f"Heuristic only — {name} typically benefits from a counter-tag against {tendency}. Set ANTHROPIC_API_KEY for a live read.",
        source="mock",
    )


@router.post("/play", response_model=AdaptPlayResponse)
async def adapt_play(
    payload: AdaptPlayRequest,
    _user: User = Depends(get_current_user),
) -> AdaptPlayResponse:
    """Real-time adjustment recommendation for a single play vs a specific look."""
    if not _claude.is_available:
        return _formula_adapt(payload)

    prompt = json.dumps({
        "play": payload.play,
        "opponent_tendency": payload.opponent_tendency,
        "opponent_archetype": payload.opponent_archetype,
        "title_id": payload.title_id,
        "schema": {
            "adjustment": "one short sentence",
            "audible_to": "name of audible play, or null",
            "confidence": "integer 0-100",
            "reasoning": "one short paragraph",
        },
    })
    try:
        data = await _claude.generate_json(
            prompt,
            system=_ADAPT_SYSTEM,
            max_tokens=350,
            temperature=0.3,
        )
    except Exception as exc:  # noqa: BLE001
        logger.info("AdaptAI fell back to formula: %s", exc)
        return _formula_adapt(payload)
    return AdaptPlayResponse(
        adjustment=str(data.get("adjustment") or "")[:400] or "Hold the call.",
        audible_to=str(data.get("audible_to")) if data.get("audible_to") else None,
        confidence=max(0, min(100, int(data.get("confidence", 60) or 60))),
        reasoning=str(data.get("reasoning") or "")[:600],
        source="claude",
    )


# Legacy compatibility — keep stub paths so existing callers don't 404.

@router.post("/{user_id}/suggest")
async def get_adaptation(user_id: str, title: str = Query(...)):
    return {"user_id": user_id, "title": title, "adaptations": [], "status": "use POST /adapt/play"}


@router.get("/{user_id}/history")
async def get_adaptation_history(user_id: str, title: str = Query(...)):
    return {"user_id": user_id, "title": title, "history": []}


@router.post("/{user_id}/feedback")
async def submit_adaptation_feedback(user_id: str):
    return {"user_id": user_id, "status": "ok"}
