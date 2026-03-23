"""Schemas for TransferAI — practice-to-competition transfer measurement."""

from __future__ import annotations

from enum import Enum

from pydantic import BaseModel, Field


class GameMode(str, Enum):
    """Game modes for transfer measurement."""

    LAB = "lab"
    PRACTICE = "practice"
    RANKED = "ranked"
    TOURNAMENT = "tournament"


class TransferRate(BaseModel):
    """Measures how well a skill transfers between game modes."""

    user_id: str
    skill: str
    from_mode: GameMode
    to_mode: GameMode
    from_mode_success_rate: float = Field(
        ..., ge=0.0, le=1.0, description="Success rate in origin mode"
    )
    to_mode_success_rate: float = Field(
        ..., ge=0.0, le=1.0, description="Success rate in destination mode"
    )
    transfer_rate: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Ratio of to_mode success to from_mode success",
    )
    sample_size_from: int = Field(..., ge=0)
    sample_size_to: int = Field(..., ge=0)
    is_reliable: bool = Field(
        ..., description="True if sample sizes meet minimum threshold"
    )
    verdict: str = Field(
        ...,
        description="Human-readable verdict: elite-transfer, solid, leaking, false-confidence",
    )


class FalseConfidence(BaseModel):
    """A skill that looks good in practice but fails under pressure."""

    skill: str
    lab_success_rate: float = Field(..., ge=0.0, le=1.0)
    ranked_success_rate: float = Field(..., ge=0.0, le=1.0)
    tournament_success_rate: float = Field(..., ge=0.0, le=1.0)
    drop_off_pct: float = Field(
        ..., description="Percentage drop from lab to worst live mode"
    )
    risk_level: str = Field(..., description="low, medium, high, critical")
    recommendation: str


class ProvenPlay(BaseModel):
    """A play that has been validated in competition."""

    skill: str
    tournament_uses: int
    tournament_success_rate: float = Field(..., ge=0.0, le=1.0)
    avg_pressure_index: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Average game-pressure when this play was used",
    )
    last_used_tournament: str | None = None


class CompetitionPackage(BaseModel):
    """Only plays that have been proven in tournament conditions."""

    user_id: str
    title: str
    proven_plays: list[ProvenPlay]
    excluded_plays: list[str] = Field(
        default_factory=list,
        description="Plays excluded because they lack tournament proof",
    )
    total_lab_plays: int
    total_proven: int
    readiness_score: float = Field(
        ..., ge=0.0, le=1.0, description="Overall competition readiness"
    )


class ModeStats(BaseModel):
    """Stats for a single game mode."""

    mode: GameMode
    total_attempts: int
    success_rate: float = Field(..., ge=0.0, le=1.0)
    avg_execution_time_ms: float | None = None
    consistency_score: float = Field(
        ..., ge=0.0, le=1.0, description="How consistent execution is"
    )


class ModeComparison(BaseModel):
    """Side-by-side comparison of performance across all modes."""

    user_id: str
    title: str
    mode_stats: list[ModeStats]
    biggest_gap: str = Field(
        ..., description="Description of the largest performance gap between modes"
    )
    false_confidence_flags: list[FalseConfidence]
    overall_transfer_grade: str = Field(
        ..., description="A+ through F grade for transfer ability"
    )
