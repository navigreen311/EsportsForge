"""Pydantic schemas for EA FC 26 squad, chemistry, card values, and player twin."""

from __future__ import annotations

import enum
from typing import Any, Optional

from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------

class ChemistryType(str, enum.Enum):
    """Types of chemistry links in EA FC 26."""
    NATION = "nation"
    LEAGUE = "league"
    CLUB = "club"
    HERO = "hero"


class CardValueTrend(str, enum.Enum):
    """Market trend direction for a card."""
    RISING = "rising"
    FALLING = "falling"
    STABLE = "stable"


class EAFCPlaystyle(str, enum.Enum):
    """Dominant playstyle classifications."""
    POSSESSION = "possession"
    COUNTER_ATTACK = "counter_attack"
    HIGH_PRESS = "high_press"
    SKILL_HEAVY = "skill_heavy"
    LONG_BALL = "long_ball"


# ---------------------------------------------------------------------------
# Card / Squad primitives
# ---------------------------------------------------------------------------

class PlayerCard(BaseModel):
    """A single player card in EA FC 26."""
    name: str = Field(..., description="Player name")
    position: str = Field(..., description="Position code, e.g. ST, CB, GK")
    overall: int = Field(..., ge=40, le=99, description="Overall rating")
    pace: int | None = Field(None, ge=0, le=99)
    shooting: int | None = Field(None, ge=0, le=99)
    passing: int | None = Field(None, ge=0, le=99)
    dribbling: int | None = Field(None, ge=0, le=99)
    defending: int | None = Field(None, ge=0, le=99)
    physical: int | None = Field(None, ge=0, le=99)
    nation: str | None = Field(None, description="Nationality")
    league: str | None = Field(None, description="League name")
    club: str | None = Field(None, description="Club name")
    tier: str = Field("gold", description="Card tier: bronze, silver, gold, rare_gold, totw, hero, icon, toty, tots")


class SquadSlot(BaseModel):
    """A position slot in a squad with an assigned card."""
    position: str = Field(..., description="Tactical position in formation")
    card: PlayerCard


# ---------------------------------------------------------------------------
# Chemistry schemas
# ---------------------------------------------------------------------------

class ChemistryLink(BaseModel):
    """A chemistry link between two players."""
    player_a: str
    player_b: str
    chemistry_type: ChemistryType
    strength: float = Field(..., ge=0, le=3.0)


class ChemistryReport(BaseModel):
    """Full chemistry analysis for a squad."""
    total_chemistry: float = Field(..., ge=0, le=33, description="Total chemistry out of 33")
    max_chemistry: int = Field(default=33)
    links: list[ChemistryLink] = Field(default_factory=list)
    weak_positions: list[str] = Field(default_factory=list)
    suggestions: list[str] = Field(default_factory=list)


# ---------------------------------------------------------------------------
# Card value schemas
# ---------------------------------------------------------------------------

class CardValue(BaseModel):
    """Market value snapshot for a player card."""
    card_name: str
    tier: str
    overall: int
    estimated_value: int = Field(..., description="Estimated coin value")
    trend: CardValueTrend = CardValueTrend.STABLE


# ---------------------------------------------------------------------------
# Budget optimization
# ---------------------------------------------------------------------------

class BudgetOptimization(BaseModel):
    """Budget-to-win-rate optimization result."""
    budget_coins: int
    formation: str
    position_allocations: dict[str, int] = Field(
        ..., description="Position -> allocated coins"
    )
    estimated_ratings: dict[str, int] = Field(
        ..., description="Position -> estimated OVR achievable"
    )
    average_overall: float
    projected_win_rate: float = Field(..., ge=0, le=1.0)
    tips: list[str] = Field(default_factory=list)


# ---------------------------------------------------------------------------
# Squad analysis
# ---------------------------------------------------------------------------

class SquadAnalysis(BaseModel):
    """Comprehensive squad analysis combining chemistry and value."""
    chemistry: ChemistryReport
    card_values: list[CardValue]
    total_estimated_value: int
    average_overall: float
    projected_win_rate: float
    value_rating: str = Field(..., description="good, over_budget, under_spent")
    improvement_suggestions: list[str] = Field(default_factory=list)


# ---------------------------------------------------------------------------
# Formation schemas
# ---------------------------------------------------------------------------

class FormationData(BaseModel):
    """A formation configuration."""
    name: str = Field(..., description="Formation name, e.g. '4-3-3 (4)'")
    positions: list[str] = Field(..., description="Position codes in formation order")
    playstyle_fit: list[str] = Field(default_factory=list)


# ---------------------------------------------------------------------------
# Player Twin schemas
# ---------------------------------------------------------------------------

class RageSubDetection(BaseModel):
    """Rage substitution detection result."""
    user_id: str
    rage_subs_detected: int
    rage_score: float = Field(..., ge=0, le=1.0)
    details: list[dict[str, Any]] = Field(default_factory=list)
    rage_frequency: float = Field(..., ge=0, le=1.0, description="Pct of matches with rage subs")
    advice: list[str] = Field(default_factory=list)


class EAFCPlaystyleProfile(BaseModel):
    """Playstyle identity profile."""
    user_id: str
    dominant_style: EAFCPlaystyle
    confidence: float = Field(..., ge=0, le=1.0)
    style_scores: dict[EAFCPlaystyle, float] = Field(default_factory=dict)
    secondary_styles: list[EAFCPlaystyle] = Field(default_factory=list)
    description: str
    recommendation: str


class TiltIndicator(BaseModel):
    """Tilt detection result."""
    user_id: str
    tilt_score: float = Field(..., ge=0, le=1.0)
    is_tilted: bool
    indicators: list[str] = Field(default_factory=list)
    recommendations: list[str] = Field(default_factory=list)


class EAFCTwinProfile(BaseModel):
    """Complete EA FC 26 player twin profile."""
    user_id: str
    playstyle: EAFCPlaystyleProfile
    tilt: TiltIndicator
    recent_rage_subs: RageSubDetection | None = None
    matches_analyzed: int = 0
