"""Opponent intelligence schemas — dossiers, archetypes, predictions, signals."""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------

class TendencyType(str, Enum):
    """Categories of opponent tendencies."""
    OFFENSIVE = "offensive"
    DEFENSIVE = "defensive"
    SITUATIONAL = "situational"
    MOMENTUM = "momentum"
    LATE_GAME = "late_game"
    EARLY_GAME = "early_game"


class ArchetypeLabel(str, Enum):
    """High-level opponent archetype labels (title-agnostic)."""
    AGGRESSOR = "aggressor"
    TURTLE = "turtle"
    COUNTER_PUNCHER = "counter_puncher"
    CHAOS_AGENT = "chaos_agent"
    META_SLAVE = "meta_slave"
    ADAPTIVE = "adaptive"
    ONE_TRICK = "one_trick"
    UNKNOWN = "unknown"


class SignalType(str, Enum):
    """Types of behavioral signals."""
    TIMEOUT = "timeout"
    PACE_CHANGE = "pace_change"
    FORMATION_SHIFT = "formation_shift"
    SUBSTITUTION = "substitution"
    AGGRESSION_SHIFT = "aggression_shift"
    TILT = "tilt"


# ---------------------------------------------------------------------------
# Scout Bot schemas
# ---------------------------------------------------------------------------

class GameSummary(BaseModel):
    """Summary of a single game."""
    game_id: str
    opponent_id: str
    title: str
    result: str = Field(description="win / loss / draw")
    score: str = Field(default="", description="e.g. '24-17'")
    key_plays: list[str] = Field(default_factory=list)
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class Tendency(BaseModel):
    """A situational tendency detected for an opponent."""
    tendency_type: TendencyType
    situation: str = Field(description="When this tendency fires, e.g. '3rd & long'")
    action: str = Field(description="What they tend to do")
    frequency: float = Field(ge=0.0, le=1.0, description="0-1 probability")
    sample_size: int = Field(ge=0)
    confidence: float = Field(ge=0.0, le=1.0)


class ExploitableWeakness(BaseModel):
    """An exploitable weakness in an opponent's game."""
    area: str = Field(description="e.g. 'red zone defense'")
    description: str
    severity: float = Field(ge=0.0, le=1.0, description="0=minor, 1=critical")
    suggested_exploit: str


class PlayFrequencyReport(BaseModel):
    """Breakdown of how often an opponent runs each play/action."""
    opponent_id: str
    total_plays: int = 0
    top_plays: list[dict[str, Any]] = Field(
        default_factory=list,
        description="Ordered list of {play, count, frequency}",
    )
    formation_distribution: dict[str, float] = Field(default_factory=dict)
    situation_breakdown: dict[str, list[dict[str, Any]]] = Field(default_factory=dict)


class OpponentDossier(BaseModel):
    """Full scouting dossier for an opponent."""
    opponent_id: str
    title: str
    generated_at: datetime = Field(default_factory=datetime.utcnow)
    recent_games: list[GameSummary] = Field(default_factory=list)
    record: dict[str, int] = Field(
        default_factory=lambda: {"wins": 0, "losses": 0, "draws": 0},
    )
    play_frequency: PlayFrequencyReport | None = None
    tendencies: list[Tendency] = Field(default_factory=list)
    weaknesses: list[ExploitableWeakness] = Field(default_factory=list)
    overall_threat_level: float = Field(
        default=0.5, ge=0.0, le=1.0, description="0=easy, 1=elite",
    )


# ---------------------------------------------------------------------------
# Archetype AI schemas
# ---------------------------------------------------------------------------

class Archetype(BaseModel):
    """Opponent archetype classification."""
    label: ArchetypeLabel = ArchetypeLabel.UNKNOWN
    confidence: float = Field(default=0.0, ge=0.0, le=1.0)
    traits: list[str] = Field(default_factory=list)
    description: str = ""
    title: str = ""
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class CounterPackage(BaseModel):
    """Counter strategy package for an archetype."""
    target_archetype: ArchetypeLabel
    strategies: list[str] = Field(default_factory=list)
    key_adjustments: list[str] = Field(default_factory=list)
    plays_to_exploit: list[str] = Field(default_factory=list)
    mental_notes: list[str] = Field(default_factory=list)
    confidence: float = Field(default=0.0, ge=0.0, le=1.0)


# ---------------------------------------------------------------------------
# Prediction Engine schemas
# ---------------------------------------------------------------------------

class Prediction(BaseModel):
    """Prediction for an opponent's next action."""
    opponent_id: str
    situation: str
    predicted_action: str
    confidence: float = Field(ge=0.0, le=1.0)
    alternatives: list[dict[str, Any]] = Field(
        default_factory=list,
        description="Other likely actions with probabilities",
    )
    reasoning: str = ""
    timestamp: datetime = Field(default_factory=datetime.utcnow)


# ---------------------------------------------------------------------------
# Rival Intelligence schemas
# ---------------------------------------------------------------------------

class EncounterRecord(BaseModel):
    """Record of a single encounter with a rival."""
    game_id: str
    result: str
    score: str = ""
    key_moments: list[str] = Field(default_factory=list)
    opponent_adjustments: list[str] = Field(default_factory=list)
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class KillSheet(BaseModel):
    """Kill sheet — what works against this rival."""
    effective_strategies: list[str] = Field(default_factory=list)
    ineffective_strategies: list[str] = Field(default_factory=list)
    exploits: list[str] = Field(default_factory=list)
    notes: list[str] = Field(default_factory=list)
    last_updated: datetime = Field(default_factory=datetime.utcnow)


class RivalDossier(BaseModel):
    """Deep dossier for a repeat opponent (rival)."""
    user_id: str
    opponent_id: str
    is_rival: bool = False
    encounter_count: int = 0
    encounters: list[EncounterRecord] = Field(default_factory=list)
    head_to_head: dict[str, int] = Field(
        default_factory=lambda: {"wins": 0, "losses": 0, "draws": 0},
    )
    archetype: Archetype | None = None
    kill_sheet: KillSheet = Field(default_factory=KillSheet)
    tendencies_vs_user: list[Tendency] = Field(default_factory=list)
    threat_trend: str = Field(
        default="stable", description="rising / falling / stable",
    )
    last_encountered: datetime | None = None


# ---------------------------------------------------------------------------
# Behavioral Signal schemas
# ---------------------------------------------------------------------------

class TimeoutPattern(BaseModel):
    """Detected timeout usage pattern."""
    total_timeouts: int = 0
    avg_game_time_when_called: float = Field(
        default=0.0, description="Average game clock % when timeout called",
    )
    panic_timeout_ratio: float = Field(
        default=0.0, ge=0.0, le=1.0,
        description="Fraction called under pressure vs. strategic",
    )
    pattern_description: str = ""


class PaceChange(BaseModel):
    """Detected pace change signal."""
    detected: bool = False
    direction: str = Field(default="none", description="faster / slower / none")
    magnitude: float = Field(default=0.0, ge=0.0, le=1.0)
    likely_reason: str = ""
    game_phase: str = ""


class SubPattern(BaseModel):
    """Formation / substitution pattern detection."""
    detected: bool = False
    pattern_type: str = Field(default="none", description="formation / substitution")
    description: str = ""
    frequency: float = Field(default=0.0, ge=0.0, le=1.0)
    trigger_situation: str = ""


class BehavioralSignal(BaseModel):
    """A single behavioral signal read from a game state."""
    signal_type: SignalType
    intensity: float = Field(ge=0.0, le=1.0)
    description: str
    actionable: bool = False
    suggested_response: str = ""
    timestamp: datetime = Field(default_factory=datetime.utcnow)
