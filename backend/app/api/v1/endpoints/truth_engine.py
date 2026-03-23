"""Truth Engine API — endpoints for auditing, accuracy, and rollback."""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, HTTPException, Query

from app.schemas.truth_engine import (
    AccuracyFilters,
    AgentAccuracy,
    AuditRequest,
    AuditResponse,
    ConfidenceCalibration,
    DegradationReport,
    OutcomeVerdict,
    RollbackHistory,
    RollbackRequest,
    StaleLogicFlag,
    TruthReport,
)
from app.services.backbone.truth_engine import TruthEngine

router = APIRouter(prefix="/truth", tags=["truth-engine"])

# ---------------------------------------------------------------------------
# Singleton engine — in production, wire via dependency injection / lifespan.
# ---------------------------------------------------------------------------
_engine = TruthEngine()


def get_engine() -> TruthEngine:
    """Return the shared TruthEngine instance."""
    return _engine


# ---------------------------------------------------------------------------
# Agent accuracy
# ---------------------------------------------------------------------------


@router.get("/agents", response_model=list[AgentAccuracy])
async def list_agent_accuracy(
    title: str | None = Query(None, description="Filter by game title"),
    time_range_days: int | None = Query(None, ge=1, description="Limit to recent N days"),
):
    """Return accuracy stats for every tracked agent."""
    engine = get_engine()
    agents = engine.get_all_agent_names()
    results = []
    for name in agents:
        acc = engine.get_agent_accuracy(name, title=title, time_range_days=time_range_days)
        results.append(acc)
    return results


@router.get("/agents/{name}/accuracy", response_model=AgentAccuracy)
async def get_agent_accuracy(
    name: str,
    title: str | None = Query(None),
    time_range_days: int | None = Query(None, ge=1),
):
    """Return accuracy stats for a single agent."""
    engine = get_engine()
    return engine.get_agent_accuracy(name, title=title, time_range_days=time_range_days)


@router.get("/agents/{name}/degradation", response_model=DegradationReport)
async def get_agent_degradation(
    name: str,
    title: str = Query(..., description="Game title to check"),
    recent_days: int = Query(7, ge=1),
    baseline_days: int = Query(30, ge=1),
):
    """Check whether an agent is degrading for a specific title."""
    engine = get_engine()
    return engine.detect_degradation(
        name,
        title=title,
        recent_days=recent_days,
        baseline_days=baseline_days,
    )


@router.get("/agents/{name}/calibration", response_model=ConfidenceCalibration)
async def get_agent_calibration(name: str):
    """Return confidence calibration analysis for an agent."""
    engine = get_engine()
    return engine.get_confidence_calibration(name)


# ---------------------------------------------------------------------------
# Audit
# ---------------------------------------------------------------------------


@router.post("/audit", response_model=AuditResponse)
async def audit_recommendation(body: AuditRequest):
    """Audit a recommendation by comparing expected vs actual outcome."""
    engine = get_engine()
    try:
        return engine.audit_recommendation(body.recommendation_id, body.actual_outcome)
    except KeyError:
        raise HTTPException(
            status_code=404,
            detail=f"Recommendation {body.recommendation_id} not found",
        )


# ---------------------------------------------------------------------------
# Rollback
# ---------------------------------------------------------------------------


@router.post("/rollback/{agent_name}", response_model=dict)
async def trigger_rollback(agent_name: str, body: RollbackRequest):
    """Trigger a rollback for an agent to a previous logic version."""
    engine = get_engine()
    try:
        event = engine.trigger_rollback(
            agent_name,
            reason=body.reason,
            to_snapshot_id=body.to_snapshot_id,
        )
        return {
            "status": "rolled_back",
            "event_id": str(event.id),
            "agent": agent_name,
            "to_snapshot": str(event.to_snapshot_id),
            "reason": event.reason,
        }
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@router.get("/rollback/{agent_name}/history", response_model=RollbackHistory)
async def get_rollback_history(agent_name: str):
    """Return rollback history for an agent."""
    engine = get_engine()
    return engine.rollback.get_rollback_history(agent_name)


# ---------------------------------------------------------------------------
# Stale logic
# ---------------------------------------------------------------------------


@router.post("/stale", response_model=StaleLogicFlag)
async def flag_stale_logic(
    title: str = Query(...),
    patch_version: str = Query(...),
):
    """Flag agent logic as potentially stale after a game patch."""
    engine = get_engine()
    return engine.flag_stale_logic(title, patch_version)


# ---------------------------------------------------------------------------
# Report
# ---------------------------------------------------------------------------


@router.get("/report", response_model=TruthReport)
async def get_weekly_report(period_days: int = Query(7, ge=1)):
    """Generate the weekly truth report for the entire platform."""
    engine = get_engine()
    return engine.generate_weekly_report(period_days=period_days)
