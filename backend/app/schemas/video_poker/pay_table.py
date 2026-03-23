"""Pydantic schemas for PayTableIQ — RTP analysis and game comparison."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field

from app.schemas.video_poker.strategy import VariantType


# ---------------------------------------------------------------------------
# Core Models
# ---------------------------------------------------------------------------

class PayTableEntry(BaseModel):
    """A single row in a video poker pay table."""
    hand_name: str
    payout: int = Field(..., ge=0, description="Payout in coins per 1-coin bet")


class RTPBreakdown(BaseModel):
    """Detailed return-to-player calculation."""
    rtp_pct: float = Field(..., description="Theoretical RTP percentage")
    full_pay_rtp: float
    deviation_from_full: float
    quality_rating: str = Field(..., description="full_pay | near_full_pay | short_pay | avoid")
    hand_contributions: list[dict[str, Any]]
    house_edge_pct: float
    variant: VariantType


class PayTableRating(BaseModel):
    """Rating for a single game's pay table."""
    game_name: str
    variant: VariantType
    rtp_pct: float
    house_edge_pct: float
    quality_rating: str
    full_pay_deviation: float
    recommendation: str


class GameComparison(BaseModel):
    """Comparison of multiple video poker games."""
    ratings: list[PayTableRating]
    best_game: str | None
    best_rtp: float
    worst_game: str | None
    worst_rtp: float
    rtp_spread: float
    recommendation: str


class WalkAwayReason(BaseModel):
    """A single reason to consider walking away."""
    factor: str
    detail: str
    weight: float = Field(..., ge=0.0, le=1.0)


class WalkAwaySignal(BaseModel):
    """Walk-away recommendation based on conditions."""
    should_walk_away: bool
    severity: str = Field(..., description="ok | caution | walk_away")
    reasons: list[WalkAwayReason]
    urgency_score: float = Field(..., ge=0.0, le=1.0)
    recommendation: str


# ---------------------------------------------------------------------------
# Request / Response
# ---------------------------------------------------------------------------

class RTPCalculateRequest(BaseModel):
    """Request to calculate RTP for a pay table."""
    pay_table: list[PayTableEntry]
    variant: VariantType = VariantType.JACKS_OR_BETTER


class RTPCalculateResponse(BaseModel):
    """Response with RTP breakdown."""
    breakdown: RTPBreakdown


class CompareGamesRequest(BaseModel):
    """Request to compare multiple games."""
    games: list[dict[str, Any]] = Field(
        ..., description="List of {name, variant, pay_table} dicts"
    )


class CompareGamesResponse(BaseModel):
    """Response with game comparison."""
    comparison: GameComparison


class WalkAwayCheckRequest(BaseModel):
    """Request to check walk-away conditions."""
    rtp_pct: float
    session_loss_pct: float = 0.0
    hands_played: int = 0


class WalkAwayCheckResponse(BaseModel):
    """Response with walk-away signal."""
    signal: WalkAwaySignal
