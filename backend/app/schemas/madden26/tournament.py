"""Schemas for MCS Circuit Tracker — tournament bracket intelligence."""

from __future__ import annotations

from enum import Enum
from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------

class TournamentStatus(str, Enum):
    """Overall tournament lifecycle."""
    UPCOMING = "upcoming"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class MatchStatus(str, Enum):
    """Status of a single bracket match."""
    PENDING = "pending"
    LIVE = "live"
    COMPLETED = "completed"
    BYE = "bye"


class FormTrend(str, Enum):
    """Recent performance trend."""
    HOT = "hot"
    WARM = "warm"
    NEUTRAL = "neutral"
    COLD = "cold"
    SLUMPING = "slumping"


# ---------------------------------------------------------------------------
# Sub-models
# ---------------------------------------------------------------------------

class BracketMatch(BaseModel):
    """A single match within a tournament bracket."""
    match_id: str
    round_number: int = Field(..., ge=1)
    player_a_id: str | None = None
    player_a_name: str | None = None
    player_b_id: str | None = None
    player_b_name: str | None = None
    winner_id: str | None = None
    score_a: int | None = None
    score_b: int | None = None
    status: MatchStatus = MatchStatus.PENDING
    scheduled_time: str | None = None


class BracketRound(BaseModel):
    """A round within the bracket (e.g. Quarterfinals)."""
    round_number: int = Field(..., ge=1)
    round_name: str = Field(..., description="e.g. 'Quarterfinals'")
    matches: list[BracketMatch]


# ---------------------------------------------------------------------------
# Response schemas
# ---------------------------------------------------------------------------

class Bracket(BaseModel):
    """Full tournament bracket state."""
    tournament_id: str
    tournament_name: str
    status: TournamentStatus
    total_rounds: int = Field(..., ge=1)
    current_round: int = Field(..., ge=1)
    rounds: list[BracketRound]
    participants_count: int = Field(..., ge=2)
    last_synced_at: str = Field(..., description="ISO-8601 timestamp")


class OpponentPrep(BaseModel):
    """Scouting prep for an upcoming opponent in a tournament."""
    opponent_id: str
    opponent_name: str
    round_number: int
    seed: int | None = None
    record: str = Field("0-0", description="e.g. '5-2'")
    form_trend: FormTrend = FormTrend.NEUTRAL
    top_plays: list[str] = Field(default_factory=list, description="Known go-to plays")
    defensive_tendencies: str = ""
    offensive_tendencies: str = ""
    key_weakness: str = ""
    head_to_head_record: str = Field("0-0", description="User vs this opponent")
    prep_notes: str = ""


class TournamentPlay(BaseModel):
    """A single play in the tournament gameplan book."""
    play_name: str
    formation: str
    situation: str = Field(..., description="When to call this play")
    priority: int = Field(..., ge=1, le=15)
    target_opponent_weakness: str = ""
    notes: str = ""


class TournamentBook(BaseModel):
    """15-play max tournament gameplan."""
    tournament_id: str
    tournament_name: str
    user_id: str
    plays: list[TournamentPlay] = Field(..., max_length=15)
    total_plays: int = Field(..., ge=1, le=15)
    opponents_scouted: int = Field(0, ge=0)
    strategy_summary: str = ""
    generated_at: str = Field(..., description="ISO-8601 timestamp")


class RecentMatch(BaseModel):
    """A recent match result for form tracking."""
    opponent_name: str
    result: str = Field(..., description="'W' or 'L'")
    score: str = Field(..., description="e.g. '28-14'")
    date: str
    tournament_name: str | None = None


class FormReport(BaseModel):
    """Recent performance report for an opponent."""
    opponent_id: str
    opponent_name: str
    trend: FormTrend
    last_5_record: str = Field(..., description="e.g. '4-1'")
    last_10_record: str = Field(..., description="e.g. '7-3'")
    win_streak: int = Field(0, ge=0)
    loss_streak: int = Field(0, ge=0)
    recent_matches: list[RecentMatch] = Field(default_factory=list)
    avg_score_for: float = Field(0.0, ge=0.0)
    avg_score_against: float = Field(0.0, ge=0.0)
    analysis: str = ""
