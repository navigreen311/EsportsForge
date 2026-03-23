"""Pydantic schemas for CommunityIntel — meta contributions, rankings, opponent seeding."""

from __future__ import annotations

from typing import Any, Optional

from pydantic import BaseModel, Field


class CommunityMeta(BaseModel):
    """Community-sourced meta snapshot for a title."""
    title: str
    patch_version: str
    top_strategies: list[dict[str, Any]] = Field(default_factory=list)
    trending_up: list[str] = Field(default_factory=list)
    trending_down: list[str] = Field(default_factory=list)
    sample_size: int = 0
    last_updated: str = ""


class CommunityContribution(BaseModel):
    """A single data contribution from a community member."""
    user_id: str
    title: str
    data_type: str = Field(..., description="strategy, match_result, opponent_data")
    payload: dict[str, Any] = Field(default_factory=dict)
    timestamp: str = ""
    reputation_score: float = Field(0.0, ge=0, le=1.0)


class ContributionResult(BaseModel):
    """Result of a community data contribution."""
    accepted: bool
    contribution_id: str | None = None
    reputation_delta: float = 0.0
    message: str


class CommunityRanking(BaseModel):
    """Community ranking entry."""
    user_id: str
    title: str
    rank: int
    elo: float
    wins: int
    losses: int
    win_rate: float
    tier: str = Field(..., description="bronze, silver, gold, platinum, diamond, champion")


class CommunityRankingsResponse(BaseModel):
    """Community rankings response."""
    title: str
    rankings: list[CommunityRanking] = Field(default_factory=list)
    total_players: int = 0
    your_rank: int | None = None


class OpponentSeed(BaseModel):
    """Seeded opponent data from community contributions."""
    opponent_id: str
    title: str
    archetype: str
    tendencies: dict[str, Any] = Field(default_factory=dict)
    sample_size: int = 0
    confidence: float = Field(0.0, ge=0, le=1.0)
    last_seen: str = ""
