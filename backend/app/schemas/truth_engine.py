"""Pydantic schemas for the Truth Engine — platform accuracy and reliability tracking."""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from uuid import UUID, uuid4

from pydantic import BaseModel, Field


class OutcomeVerdict(str, Enum):
    """Whether a recommendation was correct, partially correct, or wrong."""

    CORRECT = "correct"
    PARTIALLY_CORRECT = "partially_correct"
    INCORRECT = "incorrect"
    INDETERMINATE = "indeterminate"


class DegradationSeverity(str, Enum):
    """How severe the detected degradation is."""

    NONE = "none"
    MILD = "mild"
    MODERATE = "moderate"
    SEVERE = "severe"
    CRITICAL = "critical"


# ---------------------------------------------------------------------------
# Prediction tracking
# ---------------------------------------------------------------------------


class PredictionContext(BaseModel):
    """Contextual metadata attached to a prediction."""

    title: str = Field(..., description="Game title (e.g. madden26, cfb26)")
    mode: str | None = Field(None, description="Game mode (e.g. h2h, franchise)")
    patch_version: str | None = Field(None, description="Game patch at time of prediction")
    situation_type: str | None = Field(None, description="Situation category (e.g. draft, play_call)")
    extra: dict | None = None


class PredictionRecord(BaseModel):
    """A single prediction made by an agent."""

    id: UUID = Field(default_factory=uuid4)
    agent_name: str
    prediction: dict = Field(..., description="Structured prediction payload")
    confidence: float = Field(..., ge=0.0, le=1.0)
    context: PredictionContext
    created_at: datetime = Field(default_factory=datetime.utcnow)
    outcome: dict | None = Field(None, description="Actual outcome once known")
    verdict: OutcomeVerdict | None = None
    resolved_at: datetime | None = None


class PredictionCreate(BaseModel):
    """Request body to record a new prediction."""

    agent_name: str
    prediction: dict
    confidence: float = Field(..., ge=0.0, le=1.0)
    context: PredictionContext


class OutcomeSubmission(BaseModel):
    """Request body to submit an actual outcome for a prediction."""

    prediction_id: UUID
    actual_outcome: dict


# ---------------------------------------------------------------------------
# Agent accuracy
# ---------------------------------------------------------------------------


class AccuracyFilters(BaseModel):
    """Filters applied when calculating accuracy."""

    title: str | None = None
    mode: str | None = None
    patch_version: str | None = None
    situation_type: str | None = None
    time_range_days: int | None = Field(None, ge=1)


class AgentAccuracy(BaseModel):
    """Accuracy summary for a single agent."""

    agent_name: str
    total_predictions: int = 0
    correct: int = 0
    partially_correct: int = 0
    incorrect: int = 0
    indeterminate: int = 0
    accuracy_rate: float = Field(0.0, description="correct / resolved predictions")
    weighted_accuracy: float = Field(0.0, description="Confidence-weighted accuracy")
    filters_applied: AccuracyFilters | None = None
    computed_at: datetime = Field(default_factory=datetime.utcnow)


class AccuracyPeriod(BaseModel):
    """Accuracy for a specific time window."""

    period_start: datetime
    period_end: datetime
    accuracy_rate: float
    total_predictions: int


class AccuracyTrend(BaseModel):
    """Accuracy over multiple time windows for trend analysis."""

    agent_name: str
    periods: list[AccuracyPeriod]
    trend_direction: str = Field("stable", description="improving | stable | declining")


# ---------------------------------------------------------------------------
# Degradation detection
# ---------------------------------------------------------------------------


class DegradationReport(BaseModel):
    """Report on whether an agent is degrading in quality."""

    agent_name: str
    title: str
    is_degrading: bool = False
    severity: DegradationSeverity = DegradationSeverity.NONE
    current_accuracy: float = 0.0
    baseline_accuracy: float = 0.0
    accuracy_delta: float = 0.0
    recent_window_days: int = 7
    baseline_window_days: int = 30
    recommendation: str = ""
    detected_at: datetime = Field(default_factory=datetime.utcnow)


# ---------------------------------------------------------------------------
# Confidence calibration
# ---------------------------------------------------------------------------


class CalibrationBucket(BaseModel):
    """One bucket in the confidence calibration curve."""

    confidence_range_low: float
    confidence_range_high: float
    predicted_accuracy: float = Field(description="Mean confidence in this bucket")
    actual_accuracy: float
    count: int


class ConfidenceCalibration(BaseModel):
    """How well an agent's confidence scores match reality."""

    agent_name: str
    buckets: list[CalibrationBucket]
    calibration_error: float = Field(0.0, description="Mean absolute calibration error")
    is_overconfident: bool = False
    is_underconfident: bool = False
    computed_at: datetime = Field(default_factory=datetime.utcnow)


# ---------------------------------------------------------------------------
# Rollback
# ---------------------------------------------------------------------------


class AgentSnapshot(BaseModel):
    """A snapshot of agent configuration at a point in time."""

    id: UUID = Field(default_factory=uuid4)
    agent_name: str
    config: dict = Field(..., description="Serialised agent configuration")
    accuracy_at_snapshot: float = 0.0
    patch_version: str | None = None
    created_at: datetime = Field(default_factory=datetime.utcnow)


class RollbackEvent(BaseModel):
    """Record of a rollback action."""

    id: UUID = Field(default_factory=uuid4)
    agent_name: str
    from_snapshot_id: UUID | None = None
    to_snapshot_id: UUID
    reason: str
    triggered_by: str = "truth_engine"
    created_at: datetime = Field(default_factory=datetime.utcnow)


class RollbackRequest(BaseModel):
    """Request body to trigger a rollback."""

    reason: str
    to_snapshot_id: UUID | None = Field(
        None,
        description="Target snapshot. If None, rolls back to most recent good snapshot.",
    )


class RollbackHistory(BaseModel):
    """List of rollback events for an agent."""

    agent_name: str
    events: list[RollbackEvent]
    current_snapshot_id: UUID | None = None


# ---------------------------------------------------------------------------
# Stale logic
# ---------------------------------------------------------------------------


class StaleLogicFlag(BaseModel):
    """Flag indicating agent logic may be stale after a patch."""

    title: str
    patch_version: str
    affected_agents: list[str]
    flagged_at: datetime = Field(default_factory=datetime.utcnow)
    acknowledged: bool = False


# ---------------------------------------------------------------------------
# Weekly truth report
# ---------------------------------------------------------------------------


class AgentReportEntry(BaseModel):
    """One agent's section in the weekly report."""

    agent_name: str
    accuracy_rate: float
    predictions_count: int
    degradation_severity: DegradationSeverity
    rollbacks_this_period: int
    confidence_calibration_error: float
    top_failure_modes: list[str] = Field(default_factory=list)


class TruthReport(BaseModel):
    """Platform-wide weekly accuracy and reliability report."""

    report_id: UUID = Field(default_factory=uuid4)
    period_start: datetime
    period_end: datetime
    overall_accuracy: float = 0.0
    total_predictions: int = 0
    total_resolved: int = 0
    agents: list[AgentReportEntry] = Field(default_factory=list)
    stale_logic_flags: list[StaleLogicFlag] = Field(default_factory=list)
    rollback_events: list[RollbackEvent] = Field(default_factory=list)
    generated_at: datetime = Field(default_factory=datetime.utcnow)


# ---------------------------------------------------------------------------
# API request / response wrappers
# ---------------------------------------------------------------------------


class AuditRequest(BaseModel):
    """Request body for the /truth/audit endpoint."""

    recommendation_id: UUID
    actual_outcome: dict


class AuditResponse(BaseModel):
    """Response from auditing a recommendation."""

    recommendation_id: UUID
    verdict: OutcomeVerdict
    agent_name: str
    accuracy_impact: str = Field(description="How this outcome affected the agent's accuracy")
