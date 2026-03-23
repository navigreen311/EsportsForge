"""API endpoints for EA FC 26 SquadForge — chemistry, budget optimization, card values."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, Query

from app.schemas.eafc26.squad import (
    BudgetOptimization,
    CardValue,
    ChemistryReport,
    EAFCPlaystyleProfile,
    EAFCTwinProfile,
    PlayerCard,
    RageSubDetection,
    SquadAnalysis,
    SquadSlot,
    TiltIndicator,
)
from app.services.agents.eafc26.squad_forge import SquadForge
from app.services.agents.eafc26.eafc_player_twin import EAFCPlayerTwin

router = APIRouter(prefix="/titles/eafc26/squad", tags=["EA FC 26 — Squad"])

_squad_engine = SquadForge()
_twin_engine = EAFCPlayerTwin()


# ---------------------------------------------------------------------------
# Chemistry endpoints
# ---------------------------------------------------------------------------

@router.post("/chemistry", response_model=ChemistryReport, summary="Optimize squad chemistry")
async def optimize_chemistry(squad_slots: list[SquadSlot]) -> ChemistryReport:
    """Analyze and optimize chemistry links across the squad."""
    try:
        return _squad_engine.optimize_chemistry(squad_slots)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/analyze", response_model=SquadAnalysis, summary="Full squad analysis")
async def analyze_squad(
    squad_slots: list[SquadSlot],
    budget_coins: int | None = Query(None, ge=0),
) -> SquadAnalysis:
    """Run comprehensive squad analysis including chemistry and card values."""
    try:
        return _squad_engine.analyze_squad(squad_slots, budget_coins)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


# ---------------------------------------------------------------------------
# Budget endpoints
# ---------------------------------------------------------------------------

@router.get("/budget", response_model=BudgetOptimization, summary="Budget optimizer")
async def optimize_budget(
    budget_coins: int = Query(..., ge=0),
    formation: str = Query("4-3-3", description="Preferred formation"),
    league: str | None = Query(None, description="Preferred league"),
) -> BudgetOptimization:
    """Optimize squad building within a coin budget."""
    try:
        return _squad_engine.optimize_budget(budget_coins, formation, league)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


# ---------------------------------------------------------------------------
# Card value endpoints
# ---------------------------------------------------------------------------

@router.post("/card-value", response_model=CardValue, summary="Track card value")
async def track_card_value(card: PlayerCard) -> CardValue:
    """Get the estimated market value and trend for a card."""
    try:
        return _squad_engine.track_card_value(card)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/card-history/{card_name}", response_model=list[CardValue], summary="Card price history")
async def get_card_history(card_name: str) -> list[CardValue]:
    """Get price history for a tracked card."""
    return _squad_engine.get_card_history(card_name)


# ---------------------------------------------------------------------------
# Player Twin endpoints
# ---------------------------------------------------------------------------

@router.post("/twin/rage-subs/{user_id}", response_model=RageSubDetection, summary="Detect rage subs")
async def detect_rage_subs(user_id: str, match_data: dict) -> RageSubDetection:
    """Analyze substitution patterns for rage sub detection."""
    try:
        return _twin_engine.detect_rage_subs(user_id, match_data)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/twin/playstyle/{user_id}", response_model=EAFCPlaystyleProfile, summary="Identify playstyle")
async def identify_playstyle(user_id: str, stats: dict) -> EAFCPlaystyleProfile:
    """Identify the player's dominant playstyle from match stats."""
    try:
        return _twin_engine.identify_playstyle(user_id, stats)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/twin/tilt/{user_id}", response_model=TiltIndicator, summary="Detect tilt")
async def detect_tilt(user_id: str, recent_results: list[dict]) -> TiltIndicator:
    """Detect if the player is on tilt based on recent results."""
    try:
        return _twin_engine.detect_tilt(user_id, recent_results)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
