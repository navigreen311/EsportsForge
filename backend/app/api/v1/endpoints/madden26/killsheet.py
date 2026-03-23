"""API endpoints for Kill Sheet Generator + MCS Circuit Tracker."""

from fastapi import APIRouter, HTTPException

from app.schemas.madden26.killsheet import (
    KillSheet,
    KillSheetRequest,
    ScoredKillSheet,
    SituationalKills,
)
from app.schemas.madden26.tournament import (
    Bracket,
    FormReport,
    OpponentPrep,
    TournamentBook,
)
from app.services.agents.madden26.kill_sheet import KillSheetGenerator
from app.services.agents.madden26.mcs_tracker import MCSTracker

router = APIRouter(prefix="/titles/madden26", tags=["Madden 26 — Kill Sheet & MCS"])

_kill_sheet_gen = KillSheetGenerator()
_mcs_tracker = MCSTracker()

# In-memory store for demo purposes
_kill_sheets: dict[str, KillSheet] = {}


# ---------------------------------------------------------------------------
# Kill Sheet endpoints
# ---------------------------------------------------------------------------


@router.post("/kill-sheet/generate", response_model=ScoredKillSheet)
async def generate_kill_sheet(request: KillSheetRequest) -> ScoredKillSheet:
    """Generate a kill sheet of 5 plays proven to beat this opponent."""
    try:
        sheet = _kill_sheet_gen.generate_kill_sheet(
            user_id=request.user_id,
            opponent_data=request.opponent_data,
            roster=request.roster,
        )
        scored = _kill_sheet_gen.add_confidence_scores(sheet)
        _kill_sheets[sheet.id] = sheet
        return scored
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@router.get("/kill-sheet/{sheet_id}", response_model=KillSheet)
async def get_kill_sheet(sheet_id: str) -> KillSheet:
    """Retrieve a previously generated kill sheet by ID."""
    sheet = _kill_sheets.get(sheet_id)
    if sheet is None:
        raise HTTPException(status_code=404, detail=f"Kill sheet '{sheet_id}' not found.")
    return sheet


@router.post("/kill-sheet/{sheet_id}/situational", response_model=SituationalKills)
async def get_situational_kills(sheet_id: str) -> SituationalKills:
    """Get situational kill plays (red zone, 3rd down, blitz) for an existing sheet's opponent."""
    sheet = _kill_sheets.get(sheet_id)
    if sheet is None:
        raise HTTPException(status_code=404, detail=f"Kill sheet '{sheet_id}' not found.")
    try:
        from app.schemas.madden26.killsheet import OpponentData

        opponent = OpponentData(
            opponent_id=sheet.opponent_id,
            opponent_name=sheet.opponent_name,
        )
        return _kill_sheet_gen.generate_situational_kills(opponent)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc))


# ---------------------------------------------------------------------------
# MCS Tournament endpoints
# ---------------------------------------------------------------------------


@router.get("/tournament/{tournament_id}/bracket", response_model=Bracket)
async def get_bracket(tournament_id: str) -> Bracket:
    """Get the current bracket state for a tournament."""
    try:
        return _mcs_tracker.get_tournament_bracket(tournament_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc))


@router.get("/tournament/{tournament_id}/opponents/{user_id}", response_model=list[OpponentPrep])
async def get_opponent_queue(tournament_id: str, user_id: str) -> list[OpponentPrep]:
    """Get upcoming opponents with prep for a user in a tournament."""
    try:
        return _mcs_tracker.get_opponent_queue(user_id, tournament_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc))


@router.get("/tournament/{tournament_id}/book/{user_id}", response_model=TournamentBook)
async def get_tournament_book(tournament_id: str, user_id: str) -> TournamentBook:
    """Generate a 15-play max tournament gameplan book."""
    try:
        return _mcs_tracker.generate_tournament_book(user_id, tournament_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc))


@router.get("/tournament/form/{opponent_id}", response_model=FormReport)
async def get_form_report(opponent_id: str) -> FormReport:
    """Track recent form/performance of an opponent."""
    try:
        return _mcs_tracker.track_form(opponent_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
