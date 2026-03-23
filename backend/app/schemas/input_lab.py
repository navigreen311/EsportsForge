"""Schemas for InputLab — controller telemetry and mechanical diagnostics."""

from __future__ import annotations

from enum import Enum

from pydantic import BaseModel, Field


class InputType(str, Enum):
    """Supported input device types."""

    CONTROLLER = "controller"
    KBM = "kbm"
    FIGHT_STICK = "fight_stick"


class TelemetryData(BaseModel):
    """Raw telemetry payload from a gameplay session."""

    user_id: str
    input_type: InputType
    session_id: str
    inputs: list[InputEvent]
    session_duration_ms: int = Field(..., ge=0)
    title: str


class InputEvent(BaseModel):
    """A single input event from telemetry."""

    timestamp_ms: int = Field(..., ge=0)
    input_name: str = Field(..., description="e.g. 'left_stick', 'mouse_move', 'qcf'")
    action: str = Field(..., description="press, release, move, combo")
    value: float | None = Field(
        None, description="Analog value, movement delta, etc."
    )
    duration_ms: int | None = Field(
        None, description="Duration held for press/release events"
    )


# Re-order so TelemetryData can reference InputEvent
TelemetryData.model_rebuild()


class MechanicalLeak(BaseModel):
    """A detected inefficiency in the player's mechanical inputs."""

    leak_type: str = Field(
        ...,
        description="wasted_input, hesitation_window, ghost_input, over_travel, mis_chain",
    )
    description: str
    frequency_per_minute: float = Field(..., ge=0.0)
    impact_rating: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="How much this leak hurts performance (0=negligible, 1=critical)",
    )
    affected_inputs: list[str]
    example_timestamps_ms: list[int] = Field(
        default_factory=list, description="Sample timestamps where the leak occurred"
    )


class DrillSpec(BaseModel):
    """A corrective drill to fix a mechanical leak."""

    drill_name: str
    target_leak: str
    input_type: InputType
    description: str
    duration_minutes: int = Field(..., ge=1)
    difficulty: str = Field(..., description="beginner, intermediate, advanced, elite")
    success_criteria: str
    repetitions: int = Field(..., ge=1)
    rest_between_reps_seconds: int = Field(default=5, ge=0)


class EliteBenchmark(BaseModel):
    """Comparison of a player's input metrics against elite players."""

    user_id: str
    input_type: InputType
    skill: str
    user_metric: float
    elite_avg: float
    elite_top_10_pct: float
    percentile: float = Field(
        ..., ge=0.0, le=100.0, description="Player's percentile rank"
    )
    gap_to_elite: float = Field(
        ..., description="Absolute gap between user and elite average"
    )
    verdict: str = Field(
        ..., description="elite, above-average, average, below-average, needs-work"
    )


class InputDiagnosis(BaseModel):
    """Full mechanical diagnosis for a telemetry session."""

    user_id: str
    input_type: InputType
    session_id: str
    overall_efficiency: float = Field(
        ..., ge=0.0, le=1.0, description="Ratio of effective inputs to total inputs"
    )
    leaks: list[MechanicalLeak]
    total_inputs: int
    wasted_inputs: int
    avg_reaction_time_ms: float
    correction_drills: list[DrillSpec]
    summary: str


class InputProfile(BaseModel):
    """Full input profile for a player across sessions."""

    user_id: str
    primary_input_type: InputType
    total_sessions_analyzed: int
    avg_efficiency: float = Field(..., ge=0.0, le=1.0)
    avg_reaction_time_ms: float
    common_leaks: list[MechanicalLeak]
    strengths: list[str]
    weaknesses: list[str]
    recommended_drills: list[DrillSpec]
    elite_comparison: list[EliteBenchmark]
