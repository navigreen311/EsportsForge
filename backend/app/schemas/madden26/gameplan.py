"""Pydantic schemas for GameplanAI — gameplan generation, kill sheets, meta analysis."""

from __future__ import annotations

import enum
import uuid
from typing import Any, Optional

from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------

class MetaRatingValue(str, enum.Enum):
    """How a strategy rates against the current meta."""

    EXPLOIT = "exploit"
    STRONG = "strong"
    NEUTRAL = "neutral"
    COUNTERED = "countered"
    EXPIRED = "expired"


class PlayType(str, enum.Enum):
    """High-level play classification."""

    RUN = "run"
    PASS_SHORT = "pass_short"
    PASS_MEDIUM = "pass_medium"
    PASS_DEEP = "pass_deep"
    RPO = "rpo"
    SCREEN = "screen"
    PLAY_ACTION = "play_action"
    QB_RUN = "qb_run"


# ---------------------------------------------------------------------------
# Core play schema
# ---------------------------------------------------------------------------

class Play(BaseModel):
    """A single play in a gameplan."""

    name: str = Field(..., description="Play name from playbook")
    formation: str
    play_type: PlayType
    concept: str = Field(..., description="Offensive concept, e.g. 'Flood', 'Mesh'")
    primary_read: str = Field(..., description="First progression read")
    hot_route_adjustments: Optional[dict[str, str]] = Field(
        None, description="Position -> route adjustment map"
    )
    beats: list[str] = Field(
        default_factory=list, description="Coverages/fronts this play beats"
    )
    situation_tags: list[str] = Field(
        default_factory=list, description="Situations this play is ideal for"
    )
    notes: Optional[str] = Field(None, description="AI coaching notes")


# ---------------------------------------------------------------------------
# Gameplan
# ---------------------------------------------------------------------------

class GameplanGenerateRequest(BaseModel):
    """Request body for generating a full gameplan."""

    user_id: uuid.UUID = Field(..., description="Player requesting the gameplan")
    opponent_id: Optional[uuid.UUID] = Field(
        None, description="Opponent to game-plan against"
    )
    scheme: Optional[str] = Field(None, description="Preferred scheme archetype")
    roster_context: Optional[dict[str, Any]] = Field(
        None, description="Roster strengths/weaknesses"
    )
    meta_aware: bool = Field(True, description="Adjust for current meta")


class Gameplan(BaseModel):
    """A complete 10-play gameplan with supporting data."""

    id: uuid.UUID = Field(default_factory=uuid.uuid4)
    user_id: uuid.UUID
    opponent_id: Optional[uuid.UUID] = None
    scheme: str = Field(..., description="Scheme archetype used")
    plays: list[Play] = Field(
        ..., min_length=1, max_length=15, description="Core play sheet (target 10)"
    )
    opening_script: list[str] = Field(
        default_factory=list,
        description="First 5 play calls in order",
    )
    audible_tree: Optional[AudibleTree] = None
    red_zone_package: list[Play] = Field(default_factory=list)
    anti_blitz_package: list[Play] = Field(default_factory=list)
    meta_snapshot: Optional[str] = Field(
        None, description="Meta state when gameplan was generated"
    )
    confidence: float = Field(
        ..., ge=0.0, le=1.0, description="Overall gameplan confidence"
    )
    generated_at: str = Field(..., description="ISO timestamp")
    notes: Optional[str] = None


class ValidatedGameplan(BaseModel):
    """Gameplan filtered through the player's execution ceiling."""

    gameplan: Gameplan
    removed_plays: list[dict[str, str]] = Field(
        default_factory=list,
        description="Plays removed and the reason (execution too hard)",
    )
    replacement_plays: list[Play] = Field(
        default_factory=list,
        description="Simpler alternatives that replaced removed plays",
    )
    execution_score: float = Field(
        ..., ge=0.0, le=1.0,
        description="How well this gameplan matches the player's skill",
    )
    warnings: list[str] = Field(default_factory=list)


# ---------------------------------------------------------------------------
# Kill Sheet
# ---------------------------------------------------------------------------

class KillSheetRequest(BaseModel):
    """Request body for generating a kill sheet."""

    opponent_id: uuid.UUID
    opponent_data: Optional[dict[str, Any]] = Field(
        None, description="Scouting data on the opponent"
    )


class KillSheet(BaseModel):
    """5 specific plays designed to exploit a specific opponent."""

    opponent_id: uuid.UUID
    opponent_summary: str = Field(..., description="AI summary of opponent tendencies")
    kill_plays: list[Play] = Field(
        ..., min_length=1, max_length=7,
        description="Plays that exploit opponent weaknesses (target 5)",
    )
    exploit_notes: list[str] = Field(
        default_factory=list, description="Specific tendencies to attack"
    )
    counter_warnings: list[str] = Field(
        default_factory=list, description="What to watch for if they adjust"
    )
    generated_at: str


# ---------------------------------------------------------------------------
# Audible Tree
# ---------------------------------------------------------------------------

class AudibleBranch(BaseModel):
    """A single branch in the audible decision tree."""

    condition: str = Field(..., description="Pre-snap read, e.g. 'Safety rotates down'")
    audible_to: str = Field(..., description="Play name to audible into")
    reason: str


class AudibleTree(BaseModel):
    """If-then decision tree for audibles at the line of scrimmage."""

    base_play: str = Field(..., description="Play called in the huddle")
    branches: list[AudibleBranch] = Field(
        ..., description="Decision branches based on defensive reads"
    )
    stay_conditions: list[str] = Field(
        default_factory=list,
        description="Conditions where you keep the original play",
    )


# ---------------------------------------------------------------------------
# Meta
# ---------------------------------------------------------------------------

class MetaExploit(BaseModel):
    """A currently exploitable strategy in the meta."""

    name: str
    description: str
    counter: Optional[str] = Field(None, description="Known counter if any")
    time_remaining: Optional[str] = Field(
        None, description="Estimated time before patched/countered"
    )
    risk_level: str = Field("medium", description="low / medium / high")


class MetaRating(BaseModel):
    """How a specific strategy rates against the current meta."""

    strategy: str
    rating: MetaRatingValue
    explanation: str
    confidence: float = Field(..., ge=0.0, le=1.0)
    suggested_adjustments: list[str] = Field(default_factory=list)


class MetaReport(BaseModel):
    """Weekly meta snapshot for Madden 26."""

    title: str = Field(default="madden26")
    patch_version: str
    report_date: str = Field(..., description="ISO date")
    top_strategies: list[str] = Field(
        ..., description="Dominant strategies this week"
    )
    rising_strategies: list[str] = Field(default_factory=list)
    declining_strategies: list[str] = Field(default_factory=list)
    exploits: list[MetaExploit] = Field(default_factory=list)
    meta_summary: str = Field(..., description="AI narrative summary")


# ---------------------------------------------------------------------------
# Forward reference resolution
# ---------------------------------------------------------------------------

Gameplan.model_rebuild()
