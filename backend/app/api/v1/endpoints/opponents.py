"""Opponent Intelligence API endpoints.

Exposes scouting dossiers, archetype classification, next-call prediction,
rival intelligence, and behavioral signal reading.
"""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

from app.schemas.opponent import (
    Archetype,
    BehavioralSignal,
    CounterPackage,
    OpponentDossier,
    Prediction,
    RivalDossier,
)
from app.services.backbone import (
    archetype_ai,
    behavioral_signal,
    opponent_prediction,
    rival_intelligence,
    scout_bot,
)

router = APIRouter(tags=["opponents"])


# ---------------------------------------------------------------------------
# Request bodies
# ---------------------------------------------------------------------------

class PredictRequest(BaseModel):
    """Body for the predict endpoint."""
    situation: str
    history: list[dict[str, Any]] | None = None


class SignalsRequest(BaseModel):
    """Query params are simpler but we expose as GET with defaults."""
    pass


# ---------------------------------------------------------------------------
# Scout / Dossier
# ---------------------------------------------------------------------------

@router.get(
    "/opponents/{opponent_id}/dossier",
    response_model=OpponentDossier,
    summary="Full scouting dossier",
)
async def get_dossier(
    opponent_id: str,
    title: str = Query(default="madden26", description="Game title"),
):
    """Build and return a full scouting dossier for an opponent."""
    dossier = scout_bot.scout_opponent(opponent_id, title)
    return dossier


# ---------------------------------------------------------------------------
# Archetype
# ---------------------------------------------------------------------------

@router.get(
    "/opponents/{opponent_id}/archetype",
    response_model=Archetype,
    summary="Classify opponent archetype",
)
async def get_archetype(
    opponent_id: str,
    title: str = Query(default="madden26", description="Game title"),
    signals: str = Query(default="", description="Comma-separated trait signals"),
):
    """Classify an opponent into an archetype based on available signals."""
    signal_list = [s.strip() for s in signals.split(",") if s.strip()] if signals else []
    data = {"signals": signal_list, "title": title, "opponent_id": opponent_id}
    archetype = archetype_ai.classify_opponent(data)
    return archetype


@router.get(
    "/opponents/{opponent_id}/archetype/counter",
    response_model=CounterPackage,
    summary="Counter package for opponent archetype",
)
async def get_archetype_counter(
    opponent_id: str,
    title: str = Query(default="madden26"),
    signals: str = Query(default=""),
):
    """Get the counter strategy package for an opponent's archetype."""
    signal_list = [s.strip() for s in signals.split(",") if s.strip()] if signals else []
    data = {"signals": signal_list, "title": title}
    archetype = archetype_ai.classify_opponent(data)
    return archetype_ai.get_counter_package(archetype)


# ---------------------------------------------------------------------------
# Prediction
# ---------------------------------------------------------------------------

@router.post(
    "/opponents/{opponent_id}/predict",
    response_model=Prediction,
    summary="Predict opponent next call",
)
async def predict_next(opponent_id: str, body: PredictRequest):
    """Predict the opponent's next action in the given situation."""
    prediction = opponent_prediction.predict_next_call(
        opponent_id=opponent_id,
        situation=body.situation,
        history=body.history,
    )
    return prediction


# ---------------------------------------------------------------------------
# Rival Intelligence
# ---------------------------------------------------------------------------

@router.get(
    "/rivals/{opponent_id}",
    response_model=RivalDossier,
    summary="Rival dossier",
)
async def get_rival(
    opponent_id: str,
    user_id: str = Query(default="current_user", description="Requesting user ID"),
):
    """Return the deep rival dossier for a repeat opponent."""
    dossier = rival_intelligence.get_rival_dossier(user_id, opponent_id)
    return dossier


# ---------------------------------------------------------------------------
# Behavioral Signals
# ---------------------------------------------------------------------------

@router.get(
    "/opponents/{opponent_id}/signals",
    response_model=list[BehavioralSignal],
    summary="Behavioral signals",
)
async def get_signals(
    opponent_id: str,
    score_differential: int = Query(default=0),
    recent_turnovers: int = Query(default=0),
):
    """Read behavioral signals from the current game state.

    Accepts lightweight query params; in a real integration the full
    game state would come from the live data feed.
    """
    game_state: dict[str, Any] = {
        "opponent_id": opponent_id,
        "score_differential": score_differential,
        "recent_turnovers": recent_turnovers,
    }
    signals = behavioral_signal.read_signals(game_state)
    return signals
