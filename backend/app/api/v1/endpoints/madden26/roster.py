"""API endpoints for RosterIQ — Madden 26 personnel analysis."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, Query

from app.schemas.madden26.roster import (
    AnalyzeRosterRequest,
    AnalyzeRosterResponse,
    PatchImpactRequest,
    PatchImpactResponse,
    SpeedMismatchRequest,
    SpeedMismatchResponse,
)
from app.services.agents.madden26.roster_iq import RosterIQ

router = APIRouter(prefix="/titles/madden26/roster", tags=["Madden 26 — Roster"])

_roster_iq = RosterIQ()


# --------------------------------------------------------------------------
# POST /titles/madden26/roster/analyze
# --------------------------------------------------------------------------

@router.post("/analyze", response_model=AnalyzeRosterResponse)
async def analyze_roster(request: AnalyzeRosterRequest) -> AnalyzeRosterResponse:
    """Full roster breakdown — grades, personnel packages, and hidden gems."""
    try:
        analysis = _roster_iq.analyze_roster(request.roster)
        packages = _roster_iq.get_personnel_packages(request.roster)
        gems = _roster_iq.find_hidden_gems(request.roster)
        return AnalyzeRosterResponse(
            analysis=analysis,
            personnel_packages=packages,
            hidden_gems=gems,
        )
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


# --------------------------------------------------------------------------
# POST /titles/madden26/roster/mismatches
# --------------------------------------------------------------------------

@router.post("/mismatches", response_model=SpeedMismatchResponse)
async def get_speed_mismatches(request: SpeedMismatchRequest) -> SpeedMismatchResponse:
    """Detect exploitable speed gaps between two rosters."""
    try:
        mismatches = _roster_iq.detect_speed_mismatches(
            request.offense_roster, request.defense_roster,
        )
        top = mismatches[0] if mismatches else None
        return SpeedMismatchResponse(mismatches=mismatches, top_exploit=top)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


# --------------------------------------------------------------------------
# POST /titles/madden26/roster/patch-impact
# --------------------------------------------------------------------------

@router.post("/patch-impact", response_model=PatchImpactResponse)
async def get_patch_impact(request: PatchImpactRequest) -> PatchImpactResponse:
    """Analyze a patch's impact on player ratings."""
    try:
        changes = _roster_iq.get_ratings_impact_alert(request.patch_notes)
        winners = [c.player_name for c in changes if c.delta > 0][:5]
        losers = [c.player_name for c in changes if c.delta < 0][:5]
        return PatchImpactResponse(
            patch_version=request.patch_version,
            total_changes=len(changes),
            rating_changes=changes,
            biggest_winners=winners,
            biggest_losers=losers,
        )
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
