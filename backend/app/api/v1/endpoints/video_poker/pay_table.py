"""API endpoints for PayTableIQ — RTP analysis and game comparison."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException

from app.schemas.video_poker.pay_table import (
    CompareGamesRequest,
    CompareGamesResponse,
    RTPCalculateRequest,
    RTPCalculateResponse,
    WalkAwayCheckRequest,
    WalkAwayCheckResponse,
)
from app.services.agents.video_poker.pay_table_iq import PayTableIQ

router = APIRouter(
    prefix="/titles/video-poker/pay-table",
    tags=["Video Poker — Pay Table"],
)

_pay_table_iq = PayTableIQ()


# --------------------------------------------------------------------------
# POST /titles/video-poker/pay-table/calculate-rtp
# --------------------------------------------------------------------------

@router.post("/calculate-rtp", response_model=RTPCalculateResponse)
async def calculate_rtp(request: RTPCalculateRequest) -> RTPCalculateResponse:
    """Calculate theoretical return-to-player for a pay table."""
    try:
        breakdown = _pay_table_iq.calculate_rtp(request.pay_table, request.variant)
        return RTPCalculateResponse(breakdown=breakdown)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


# --------------------------------------------------------------------------
# POST /titles/video-poker/pay-table/compare
# --------------------------------------------------------------------------

@router.post("/compare", response_model=CompareGamesResponse)
async def compare_games(request: CompareGamesRequest) -> CompareGamesResponse:
    """Compare multiple video poker games by RTP and pay table quality."""
    try:
        comparison = _pay_table_iq.compare_games(request.games)
        return CompareGamesResponse(comparison=comparison)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


# --------------------------------------------------------------------------
# POST /titles/video-poker/pay-table/walk-away-check
# --------------------------------------------------------------------------

@router.post("/walk-away-check", response_model=WalkAwayCheckResponse)
async def check_walk_away(request: WalkAwayCheckRequest) -> WalkAwayCheckResponse:
    """Check if conditions warrant walking away from the current game."""
    try:
        signal = _pay_table_iq.check_walk_away(
            request.rtp_pct, request.session_loss_pct, request.hands_played,
        )
        return WalkAwayCheckResponse(signal=signal)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
