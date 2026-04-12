"""Learning Loop API — session processing and history endpoints.

POST /learning-loop/process            — process a completed session
GET  /learning-loop/history/{user_id}  — session analysis history
"""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Body, Query

from app.services.ai.loop_ai import LoopAIService

router = APIRouter()

# Singleton service — will be replaced by DI container
_loop_service = LoopAIService()


@router.post("/process")
async def process_session(
    session_data: dict[str, Any] = Body(
        ...,
        description="Session data including user_id, title, outcome, recommendations_followed, stats",
    ),
) -> dict[str, Any]:
    """Process a completed game session through the LoopAI pipeline.

    Evaluates win/loss against followed/ignored recommendations and
    returns PlayerTwin updates, a debrief narrative, confidence
    adjustments, and flagged patterns.

    Expected body shape::

        {
            "user_id": "abc123",
            "title": "madden26",
            "outcome": "win",  // "win" | "loss" | "draw"
            "recommendations_followed": [
                {"id": "r1", "name": "Pre-Snap Coverage ID", "followed": true, "confidence": 0.82}
            ],
            "stats": {"win_rate": 67, "games_played": 142}
        }
    """
    return _loop_service.process_session_end(session_data)


@router.get("/history/{user_id}")
async def get_learning_history(
    user_id: str,
    limit: int = Query(20, ge=1, le=100, description="Max results to return"),
) -> dict[str, Any]:
    """Retrieve the learning loop history for a player.

    Returns the most recent session analyses, ordered newest first.
    """
    entries = _loop_service.get_history(user_id, limit)
    return {
        "user_id": user_id,
        "total": len(entries),
        "results": entries,
    }
