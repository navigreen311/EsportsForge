"""API endpoints for MatchupAI + ReadAI — Madden 26 matchup analysis."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, Path

from app.schemas.madden26.matchup import (
    FindAdvantagesRequest,
    FindAdvantagesResponse,
    MatchupHistoryResponse,
    ReadCoverageRequest,
    ReadCoverageResponse,
)
from app.services.agents.madden26.matchup_ai import MatchupAI
from app.services.agents.madden26.read_ai import ReadAI

router = APIRouter(prefix="/titles/madden26/matchup", tags=["Madden 26 — Matchup"])

_matchup_ai = MatchupAI()
_read_ai = ReadAI()


# --------------------------------------------------------------------------
# POST /titles/madden26/matchup/advantages
# --------------------------------------------------------------------------

@router.post("/advantages", response_model=FindAdvantagesResponse)
async def find_advantages(request: FindAdvantagesRequest) -> FindAdvantagesResponse:
    """Find all pre-snap personnel advantages."""
    try:
        advantages = _matchup_ai.find_matchup_advantages(
            request.offense, request.defense,
        )

        leverage = None
        motion = None
        if request.formation and request.offense.players:
            leverage = _matchup_ai.isolate_leverage_matchup(
                request.offense.players, request.formation,
            )
            motion = _matchup_ai.suggest_motion_to_create(leverage)

        best_personnel = None
        if advantages:
            best_personnel = "11"  # Default recommendation

        return FindAdvantagesResponse(
            advantages=advantages,
            best_personnel=best_personnel,
            leverage_matchup=leverage,
            motion_suggestion=motion,
        )
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


# --------------------------------------------------------------------------
# POST /titles/madden26/matchup/read
# --------------------------------------------------------------------------

@router.post("/read", response_model=ReadCoverageResponse)
async def read_coverage(request: ReadCoverageRequest) -> ReadCoverageResponse:
    """Read pre-snap coverage and blitz, with optional audible suggestion."""
    try:
        coverage = _read_ai.identify_coverage(request.pre_snap_info)
        blitz = _read_ai.identify_blitz(request.pre_snap_info)

        audible = None
        if request.current_play:
            audible = _read_ai.suggest_audible(coverage, request.current_play)

        patterns = []
        if request.opponent_history:
            patterns = _read_ai.get_pattern_recognition(request.opponent_history)

        return ReadCoverageResponse(
            coverage_read=coverage,
            blitz_read=blitz,
            audible=audible,
            tendency_patterns=patterns,
        )
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


# --------------------------------------------------------------------------
# GET /titles/madden26/matchup/history/{opponent_id}
# --------------------------------------------------------------------------

@router.get("/history/{opponent_id}", response_model=MatchupHistoryResponse)
async def get_matchup_history(
    opponent_id: str = Path(..., description="Opponent user ID"),
) -> MatchupHistoryResponse:
    """Retrieve historical matchup results against an opponent.

    NOTE: In production this queries the database. Currently returns
    an empty history stub until the data layer is wired up.
    """
    results = _matchup_ai.get_matchup_history(
        user_id="current_user",  # TODO: wire up auth
        opponent_id=opponent_id,
    )
    wins = sum(1 for r in results if r.result == "win")
    losses = sum(1 for r in results if r.result == "loss")
    draws = sum(1 for r in results if r.result == "draw")
    total = len(results)

    return MatchupHistoryResponse(
        opponent_id=opponent_id,
        total_games=total,
        wins=wins,
        losses=losses,
        draws=draws,
        win_rate=wins / total if total else 0.0,
        results=results,
    )
