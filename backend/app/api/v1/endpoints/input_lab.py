"""API endpoints for InputLab — controller telemetry diagnostics."""

from fastapi import APIRouter, Query

from app.schemas.input_lab import (
    EliteBenchmark,
    InputDiagnosis,
    InputProfile,
    InputType,
    TelemetryData,
)
from app.services.backbone.input_lab import InputLab

router = APIRouter(prefix="/input-lab", tags=["InputLab"])

_engine = InputLab()


@router.post("/diagnose", response_model=InputDiagnosis)
async def diagnose_input(payload: TelemetryData) -> InputDiagnosis:
    """Submit controller/KBM/fight-stick telemetry for full mechanical diagnosis."""
    return await _engine.diagnose_input(
        user_id=payload.user_id,
        input_type=payload.input_type,
        telemetry_data=payload.inputs,
        session_id=payload.session_id,
    )


@router.get("/{user_id}/profile", response_model=InputProfile)
async def get_input_profile(
    user_id: str,
    input_type: InputType = Query(..., description="Input device type"),
) -> InputProfile:
    """Get full input profile for a player."""
    return await _engine.get_input_profile(user_id, input_type)


@router.get("/{user_id}/benchmarks", response_model=EliteBenchmark)
async def get_elite_benchmark(
    user_id: str,
    input_type: InputType = Query(..., description="Input device type"),
    skill: str = Query(..., description="Skill to benchmark"),
) -> EliteBenchmark:
    """Compare a player's input metrics against elite players."""
    return await _engine.compare_to_elite(user_id, input_type, skill)
