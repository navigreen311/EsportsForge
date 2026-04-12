"""Leaderboard endpoints — player rankings by title and skill dimension."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel

from app.core.security import get_current_user
from app.models.user import User

router = APIRouter(tags=["Leaderboard"])


# ---------------------------------------------------------------------------
# Schemas
# ---------------------------------------------------------------------------

class LeaderboardEntry(BaseModel):
    rank: int
    gamertag: str
    title: str
    win_rate: float
    percentile: int


class LeaderboardResponse(BaseModel):
    entries: list[LeaderboardEntry]
    total_players: int
    timeframe: str


class MyPositionResponse(BaseModel):
    rank: int
    total_players: int
    percentile: int
    message: str


# ---------------------------------------------------------------------------
# Mock Data
# ---------------------------------------------------------------------------

_MOCK_ENTRIES = [
    LeaderboardEntry(rank=1,  gamertag="xShadowKing",    title="Madden 26", win_rate=92.3, percentile=99),
    LeaderboardEntry(rank=2,  gamertag="ProGrinder99",   title="Madden 26", win_rate=89.7, percentile=98),
    LeaderboardEntry(rank=3,  gamertag="ClutchMaster",   title="Madden 26", win_rate=87.1, percentile=97),
    LeaderboardEntry(rank=4,  gamertag="GridironAce",    title="Madden 26", win_rate=85.4, percentile=96),
    LeaderboardEntry(rank=5,  gamertag="BlitzKingX",     title="Madden 26", win_rate=83.9, percentile=95),
    LeaderboardEntry(rank=6,  gamertag="TDmachine22",    title="Madden 26", win_rate=81.2, percentile=93),
    LeaderboardEntry(rank=7,  gamertag="PocketSniper",   title="Madden 26", win_rate=79.8, percentile=91),
    LeaderboardEntry(rank=8,  gamertag="ZoneBuster",     title="Madden 26", win_rate=78.3, percentile=89),
    LeaderboardEntry(rank=9,  gamertag="EndZoneElite",   title="Madden 26", win_rate=76.5, percentile=87),
    LeaderboardEntry(rank=10, gamertag="ForgeLegend",    title="Madden 26", win_rate=74.9, percentile=85),
]


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@router.get("", response_model=LeaderboardResponse)
async def get_leaderboard(
    title_id: str = Query(default="madden26", description="Game title filter"),
    skill_dimension: str = Query(default="overall", description="Skill dimension filter"),
    timeframe: str = Query(default="monthly", description="Timeframe: weekly, monthly, all"),
    current_user: User = Depends(get_current_user),
):
    """Return top players for a given title, skill dimension, and timeframe."""
    return LeaderboardResponse(
        entries=_MOCK_ENTRIES,
        total_players=3672,
        timeframe=timeframe,
    )


@router.get("/me", response_model=MyPositionResponse)
async def get_my_position(
    current_user: User = Depends(get_current_user),
):
    """Return the current user's leaderboard position."""
    return MyPositionResponse(
        rank=1247,
        total_players=3672,
        percentile=66,
        message="You are #1247, top 34%",
    )
