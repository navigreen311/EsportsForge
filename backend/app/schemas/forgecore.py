"""Pydantic schemas for ForgeCore Orchestrator."""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------

class GameMode(str, Enum):
    """Current game/session mode that influences decision weighting."""

    RANKED = "ranked"
    TOURNAMENT = "tournament"
    TRAINING = "training"
    CASUAL = "casual"
    SCRIM = "scrim"


class PressureState(str, Enum):
    """In-game pressure level — drives information density filtering."""

    CRITICAL = "critical"  # e.g. final drive, match point
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class AgentStatus(str, Enum):
    """Health status of a registered agent."""

    ACTIVE = "active"
    DEGRADED = "degraded"
    OFFLINE = "offline"
    WARMING_UP = "warming_up"


# ---------------------------------------------------------------------------
# Decision Context
# ---------------------------------------------------------------------------

class DecisionContext(BaseModel):
    """Full context for a ForgeCore decision request."""

    mode: GameMode = GameMode.RANKED
    pressure_state: PressureState = PressureState.MEDIUM
    time_context: str | None = Field(
        default=None,
        description="Game clock or phase indicator (e.g. '2:30 Q4', 'Draft Phase 2').",
    )
    opponent_info: dict[str, Any] = Field(
        default_factory=dict,
        description="Known opponent tendencies, stats, or scouting data.",
    )
    player_state: dict[str, Any] = Field(
        default_factory=dict,
        description="Current player condition — fatigue, tilt, hot hand, etc.",
    )
    session_id: str | None = None
    extra: dict[str, Any] = Field(
        default_factory=dict,
        description="Arbitrary additional context agents may consume.",
    )


# ---------------------------------------------------------------------------
# Agent I/O
# ---------------------------------------------------------------------------

class AgentOutput(BaseModel):
    """Output produced by a single agent for a decision cycle."""

    agent_name: str
    recommendation: str
    confidence: float = Field(ge=0.0, le=1.0, description="Agent self-reported confidence 0-1.")
    reasoning: str = ""
    data: dict[str, Any] = Field(default_factory=dict)
    impact_rank_score: float = Field(
        default=0.0,
        ge=0.0,
        le=100.0,
        description="ImpactRank score — used to break priority ties.",
    )
    vetoed: bool = Field(default=False, description="True if PlayerTwin vetoed this output.")
    veto_reason: str | None = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)


# ---------------------------------------------------------------------------
# Conflict Resolution
# ---------------------------------------------------------------------------

class ConflictResolution(BaseModel):
    """Record of how a conflict between agents was resolved."""

    conflicting_agents: list[str]
    winner: str
    resolution_method: str = Field(
        description="How the conflict was resolved: priority, impact_rank, veto, confidence_threshold.",
    )
    explanation: str = ""
    discarded_recommendations: list[str] = Field(default_factory=list)


# ---------------------------------------------------------------------------
# Request / Response
# ---------------------------------------------------------------------------

class ForgeCoreRequest(BaseModel):
    """Inbound request for a ForgeCore decision."""

    user_id: str
    title: str = Field(description="Game title, e.g. 'madden26', 'cfb26'.")
    context: DecisionContext = Field(default_factory=DecisionContext)
    requested_agents: list[str] | None = Field(
        default=None,
        description="Optionally limit which agents participate. None = all available.",
    )


class ForgeCoreDecision(BaseModel):
    """The single, unified decision ForgeCore delivers to the player."""

    decision_id: str
    user_id: str
    title: str
    recommendation: str = Field(description="The ONE thing the player should do right now.")
    reasoning: str = Field(description="Concise rationale behind the recommendation.")
    confidence: float = Field(ge=0.0, le=1.0)
    context_used: DecisionContext
    contributing_agents: list[str] = Field(
        default_factory=list,
        description="Agents whose output influenced the final decision.",
    )
    conflicts_resolved: list[ConflictResolution] = Field(default_factory=list)
    filtered_count: int = Field(
        default=0,
        description="Number of agent outputs filtered out (low confidence, vetoed, density).",
    )
    information_density: str = Field(
        default="standard",
        description="Density level applied: minimal | standard | detailed.",
    )
    timestamp: datetime = Field(default_factory=datetime.utcnow)
