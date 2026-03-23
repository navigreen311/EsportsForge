"""Pydantic schemas for Responsible Gambling compliance."""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------

class AlertSeverity(str, Enum):
    """Alert severity levels."""
    INFO = "info"
    WARNING = "warning"
    HIGH = "high"
    CRITICAL = "critical"


class ProblemGamblingRiskLevel(str, Enum):
    """Problem gambling risk classification."""
    NONE = "none"
    LOW = "low"
    MODERATE = "moderate"
    HIGH = "high"


# ---------------------------------------------------------------------------
# Core Models
# ---------------------------------------------------------------------------

class SessionTimeLimit(BaseModel):
    """Session time limit configuration."""
    user_id: str
    start_time: datetime
    max_minutes: int = Field(..., ge=15)
    warning_at_minutes: int
    expires_at: datetime
    mandatory_break_minutes: int


class SessionTimeLimitStatus(BaseModel):
    """Current status of session time limit."""
    action: str = Field(..., description="continue | warn | force_stop")
    elapsed_minutes: float
    remaining_minutes: float
    message: str
    must_break: bool
    break_until: datetime | None = None


class SelfExclusionConfig(BaseModel):
    """Self-exclusion configuration."""
    user_id: str
    is_permanent: bool
    start_date: datetime
    end_date: datetime | None = None
    duration_days: int
    reason: str
    can_be_reversed: bool = False
    helpline_numbers: list[dict[str, str]]
    confirmation_required: bool = True
    message: str


class SelfExclusionStatus(BaseModel):
    """Current self-exclusion status."""
    is_excluded: bool
    message: str
    can_play: bool
    remaining_days: int | None = None


class LossLimitConfig(BaseModel):
    """Loss limit configuration."""
    user_id: str
    daily_limit: float = Field(..., gt=0)
    weekly_limit: float = Field(..., gt=0)
    monthly_limit: float = Field(..., gt=0)
    cooling_off_for_increase_hours: int = 24
    message: str


class GamblingAlert(BaseModel):
    """A compliance or problem gambling alert."""
    severity: AlertSeverity
    category: str
    message: str


class LossLimitStatus(BaseModel):
    """Current loss limit status."""
    can_continue: bool
    daily_losses: float
    daily_limit: float
    daily_pct: float
    weekly_losses: float
    weekly_limit: float
    weekly_pct: float
    monthly_losses: float
    monthly_limit: float
    monthly_pct: float
    alerts: list[GamblingAlert]


class ProblemGamblingSignal(BaseModel):
    """Problem gambling detection result."""
    user_id: str
    risk_level: ProblemGamblingRiskLevel
    risk_score: float = Field(..., ge=0.0, le=1.0)
    signals: list[GamblingAlert]
    recommendation: str
    helpline_numbers: list[dict[str, str]]
    disclaimer: str


class CoolingOffPeriod(BaseModel):
    """Cooling-off period configuration."""
    user_id: str
    start_time: datetime
    end_time: datetime
    duration_hours: int
    reason: str
    is_active: bool
    can_be_shortened: bool = False
    message: str


class ComplianceStatus(BaseModel):
    """Unified compliance check result."""
    user_id: str
    can_play: bool
    blocks: list[str]
    warnings: list[str]
    checked_at: datetime
    message: str


class ResponsibleGamblingProfile(BaseModel):
    """Complete responsible gambling profile for a user."""
    user_id: str
    session_time_limit_minutes: int = Field(240, ge=15)
    daily_loss_limit: float = Field(200.0, gt=0)
    weekly_loss_limit: float = Field(500.0, gt=0)
    monthly_loss_limit: float = Field(1500.0, gt=0)
    self_excluded: bool = False
    cooling_off_active: bool = False


# ---------------------------------------------------------------------------
# Request / Response
# ---------------------------------------------------------------------------

class SetTimeLimitRequest(BaseModel):
    """Request to set session time limit."""
    user_id: str
    max_minutes: int = Field(240, ge=15, le=480)


class SetTimeLimitResponse(BaseModel):
    """Response with session time limit."""
    limit: SessionTimeLimit


class CheckTimeLimitRequest(BaseModel):
    """Request to check time limit status."""
    limit: SessionTimeLimit


class CheckTimeLimitResponse(BaseModel):
    """Response with time limit status."""
    status: SessionTimeLimitStatus


class SelfExclusionRequest(BaseModel):
    """Request for self-exclusion."""
    user_id: str
    duration_days: int | None = Field(None, ge=30)
    permanent: bool = False
    reason: str = ""
    i_understand_this_cannot_be_reversed: bool = Field(
        ..., description="Must be True to activate self-exclusion"
    )


class SelfExclusionResponse(BaseModel):
    """Response with self-exclusion config."""
    config: SelfExclusionConfig


class SetLossLimitsRequest(BaseModel):
    """Request to configure loss limits."""
    user_id: str
    daily_limit: float = Field(200.0, gt=0)
    weekly_limit: float = Field(500.0, gt=0)
    monthly_limit: float = Field(1500.0, gt=0)


class SetLossLimitsResponse(BaseModel):
    """Response with loss limit config."""
    config: LossLimitConfig


class CheckLossLimitsRequest(BaseModel):
    """Request to check loss limits."""
    config: LossLimitConfig
    daily_losses: float = 0.0
    weekly_losses: float = 0.0
    monthly_losses: float = 0.0


class CheckLossLimitsResponse(BaseModel):
    """Response with loss limit status."""
    status: LossLimitStatus


class ProblemDetectionRequest(BaseModel):
    """Request for problem gambling detection."""
    user_id: str
    session_history: list[dict[str, Any]]
    bet_history: list[float] | None = None
    deposit_timestamps: list[datetime] | None = None


class ProblemDetectionResponse(BaseModel):
    """Response with problem gambling signals."""
    signal: ProblemGamblingSignal


class CoolingOffRequest(BaseModel):
    """Request to activate cooling-off period."""
    user_id: str
    hours: int = Field(24, ge=24)
    reason: str = "user_requested"


class CoolingOffResponse(BaseModel):
    """Response with cooling-off period."""
    period: CoolingOffPeriod


class ComplianceCheckRequest(BaseModel):
    """Request for full compliance check."""
    user_id: str


class ComplianceCheckResponse(BaseModel):
    """Response with compliance status."""
    status: ComplianceStatus
