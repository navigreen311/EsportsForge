"""API endpoints for Responsible Gambling compliance — legally required safeguards.

These endpoints enforce session time limits, self-exclusion, loss limits,
problem gambling detection, and cooling-off periods. They CANNOT be disabled.
"""

from __future__ import annotations

from fastapi import APIRouter, HTTPException

from app.schemas.video_poker.responsible_gambling import (
    CheckLossLimitsRequest,
    CheckLossLimitsResponse,
    CheckTimeLimitRequest,
    CheckTimeLimitResponse,
    ComplianceCheckRequest,
    ComplianceCheckResponse,
    CoolingOffRequest,
    CoolingOffResponse,
    ProblemDetectionRequest,
    ProblemDetectionResponse,
    SelfExclusionRequest,
    SelfExclusionResponse,
    SetLossLimitsRequest,
    SetLossLimitsResponse,
    SetTimeLimitRequest,
    SetTimeLimitResponse,
)
from app.services.agents.video_poker.responsible_gambling import (
    ResponsibleGamblingGuard,
)

router = APIRouter(
    prefix="/titles/video-poker/responsible-gambling",
    tags=["Video Poker — Responsible Gambling"],
)

_guard = ResponsibleGamblingGuard()


# --------------------------------------------------------------------------
# POST /titles/video-poker/responsible-gambling/set-time-limit
# --------------------------------------------------------------------------

@router.post("/set-time-limit", response_model=SetTimeLimitResponse)
async def set_time_limit(request: SetTimeLimitRequest) -> SetTimeLimitResponse:
    """Set session time limit. Enforces mandatory breaks."""
    try:
        limit = _guard.create_session_time_limit(
            request.user_id, request.max_minutes,
        )
        return SetTimeLimitResponse(limit=limit)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


# --------------------------------------------------------------------------
# POST /titles/video-poker/responsible-gambling/check-time-limit
# --------------------------------------------------------------------------

@router.post("/check-time-limit", response_model=CheckTimeLimitResponse)
async def check_time_limit(
    request: CheckTimeLimitRequest,
) -> CheckTimeLimitResponse:
    """Check if session time limit has been reached."""
    try:
        status = _guard.check_session_time(request.limit)
        return CheckTimeLimitResponse(status=status)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


# --------------------------------------------------------------------------
# POST /titles/video-poker/responsible-gambling/self-exclude
# --------------------------------------------------------------------------

@router.post("/self-exclude", response_model=SelfExclusionResponse)
async def self_exclude(request: SelfExclusionRequest) -> SelfExclusionResponse:
    """Activate self-exclusion. CANNOT be reversed once confirmed."""
    if not request.i_understand_this_cannot_be_reversed:
        raise HTTPException(
            status_code=400,
            detail=(
                "You must confirm you understand self-exclusion cannot be reversed "
                "by setting i_understand_this_cannot_be_reversed to true."
            ),
        )
    try:
        config = _guard.create_self_exclusion(
            request.user_id,
            request.duration_days,
            request.permanent,
            request.reason,
        )
        return SelfExclusionResponse(config=config)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


# --------------------------------------------------------------------------
# POST /titles/video-poker/responsible-gambling/set-loss-limits
# --------------------------------------------------------------------------

@router.post("/set-loss-limits", response_model=SetLossLimitsResponse)
async def set_loss_limits(
    request: SetLossLimitsRequest,
) -> SetLossLimitsResponse:
    """Configure daily, weekly, and monthly loss limits."""
    try:
        config = _guard.configure_loss_limits(
            request.user_id,
            request.daily_limit,
            request.weekly_limit,
            request.monthly_limit,
        )
        return SetLossLimitsResponse(config=config)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


# --------------------------------------------------------------------------
# POST /titles/video-poker/responsible-gambling/check-loss-limits
# --------------------------------------------------------------------------

@router.post("/check-loss-limits", response_model=CheckLossLimitsResponse)
async def check_loss_limits(
    request: CheckLossLimitsRequest,
) -> CheckLossLimitsResponse:
    """Check current losses against configured limits."""
    try:
        status = _guard.check_loss_limits(
            request.config,
            request.daily_losses,
            request.weekly_losses,
            request.monthly_losses,
        )
        return CheckLossLimitsResponse(status=status)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


# --------------------------------------------------------------------------
# POST /titles/video-poker/responsible-gambling/detect-problems
# --------------------------------------------------------------------------

@router.post("/detect-problems", response_model=ProblemDetectionResponse)
async def detect_problems(
    request: ProblemDetectionRequest,
) -> ProblemDetectionResponse:
    """Detect potential problem gambling signals from behavioral patterns.

    This is NOT a clinical diagnosis — it flags patterns for awareness.
    """
    try:
        signal = _guard.detect_problem_signals(
            request.user_id,
            request.session_history,
            request.bet_history,
            request.deposit_timestamps,
        )
        return ProblemDetectionResponse(signal=signal)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


# --------------------------------------------------------------------------
# POST /titles/video-poker/responsible-gambling/cooling-off
# --------------------------------------------------------------------------

@router.post("/cooling-off", response_model=CoolingOffResponse)
async def activate_cooling_off(
    request: CoolingOffRequest,
) -> CoolingOffResponse:
    """Activate a cooling-off period. Cannot be shortened once activated."""
    try:
        period = _guard.enforce_cooling_off(
            request.user_id, request.hours, request.reason,
        )
        return CoolingOffResponse(period=period)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


# --------------------------------------------------------------------------
# POST /titles/video-poker/responsible-gambling/compliance-check
# --------------------------------------------------------------------------

@router.post("/compliance-check", response_model=ComplianceCheckResponse)
async def full_compliance_check(
    request: ComplianceCheckRequest,
) -> ComplianceCheckResponse:
    """Run ALL compliance checks — gateway for every video poker action.

    This endpoint must be called before any video poker operation.
    """
    try:
        status = _guard.full_compliance_check(request.user_id)
        return ComplianceCheckResponse(status=status)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
