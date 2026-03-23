"""Pydantic schemas for VarianceCoach — variance education and tilt management."""

from __future__ import annotations

from enum import Enum
from typing import Any

from pydantic import BaseModel, Field

from app.schemas.video_poker.strategy import VariantType


# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------

class TiltRisk(str, Enum):
    """Tilt risk levels."""
    NONE = "none"
    LOW = "low"
    MODERATE = "moderate"
    HIGH = "high"
    CRITICAL = "critical"


class DeviationSeverity(str, Enum):
    """Strategy deviation severity."""
    NONE = "none"
    MINOR = "minor"
    MODERATE = "moderate"
    HIGH = "high"
    CRITICAL = "critical"


class SessionMood(str, Enum):
    """Estimated player mood based on session results."""
    EUPHORIC = "euphoric"
    POSITIVE = "positive"
    NEUTRAL = "neutral"
    FRUSTRATED = "frustrated"
    TILTED = "tilted"


# ---------------------------------------------------------------------------
# Core Models
# ---------------------------------------------------------------------------

class VarianceLesson(BaseModel):
    """Educational content about variance."""
    id: str
    title: str
    content: str
    key_insight: str


class VarianceExplanation(BaseModel):
    """Contextual variance explanation for current session."""
    variant: VariantType
    hands_played: int
    current_result: float
    expected_result: float
    session_sd: float
    z_score: float
    result_assessment: str
    assessment_text: str
    relevant_lessons: list[VarianceLesson]
    encouragement: str


class TiltStatus(BaseModel):
    """Current tilt risk assessment."""
    risk_level: TiltRisk
    risk_score: float = Field(..., ge=0.0, le=1.0)
    triggers: list[str]
    recommendation: str
    should_take_break: bool
    mandatory_stop: bool


class DeviationAlert(BaseModel):
    """Strategy deviation detection result."""
    is_deviating: bool
    severity: DeviationSeverity
    recent_accuracy: float
    baseline_accuracy: float
    accuracy_drop: float
    pattern: str | None
    recommendation: str


class StreakAnalysis(BaseModel):
    """Analysis of winning/losing streaks."""
    total_hands: int
    winning_hands: int
    losing_hands: int
    longest_win_streak: int
    longest_loss_streak: int
    current_streak: int
    current_streak_type: str
    streak_is_normal: bool
    explanation: str
    mood: SessionMood


# ---------------------------------------------------------------------------
# Request / Response
# ---------------------------------------------------------------------------

class VarianceExplainRequest(BaseModel):
    """Request for variance explanation."""
    variant: VariantType = VariantType.JACKS_OR_BETTER
    hands_played: int = Field(0, ge=0)
    current_result: float = 0.0
    bet_size: float = Field(1.25, gt=0)


class VarianceExplainResponse(BaseModel):
    """Response with variance explanation."""
    explanation: VarianceExplanation


class TiltAssessRequest(BaseModel):
    """Request for tilt assessment."""
    consecutive_losses: int = Field(0, ge=0)
    session_loss_pct: float = Field(0.0, ge=0.0)
    hands_played: int = Field(0, ge=0)
    missed_big_hands: int = Field(0, ge=0)
    time_playing_minutes: int = Field(0, ge=0)


class TiltAssessResponse(BaseModel):
    """Response with tilt status."""
    status: TiltStatus


class DeviationCheckRequest(BaseModel):
    """Request for strategy deviation check."""
    recent_decisions: list[dict[str, Any]]
    baseline_accuracy: float = Field(98.0, ge=0.0, le=100.0)


class DeviationCheckResponse(BaseModel):
    """Response with deviation alert."""
    alert: DeviationAlert


class StreakAnalysisRequest(BaseModel):
    """Request for streak analysis."""
    results: list[float] = Field(..., description="List of per-hand results (positive=win, negative/zero=loss)")
    bet_size: float = Field(1.25, gt=0)


class StreakAnalysisResponse(BaseModel):
    """Response with streak analysis."""
    analysis: StreakAnalysis
