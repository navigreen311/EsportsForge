"""API endpoints for IntegrityMode — compliance governance."""

from fastapi import APIRouter, HTTPException, Query

from app.schemas.integrity import (
    ComplianceMatrixResponse,
    ComplianceResult,
    IntegritySettings,
    SetModeRequest,
)
from app.services.backbone.integrity_mode import IntegrityMode

router = APIRouter(prefix="/integrity", tags=["integrity"])


@router.get("/mode", response_model=IntegritySettings)
async def get_current_mode(
    user_id: str = Query(..., description="User whose compliance mode to retrieve"),
):
    """Return the active compliance mode for the given user."""
    return IntegrityMode.get_active_mode(user_id)


@router.put("/mode", response_model=IntegritySettings)
async def set_mode(
    body: SetModeRequest,
    user_id: str = Query(..., description="User whose compliance mode to set"),
):
    """Set the active compliance mode (environment + timing) for a user."""
    return IntegrityMode.set_mode(user_id, body.environment, body.timing)


@router.get("/matrix", response_model=ComplianceMatrixResponse)
async def get_compliance_matrix():
    """Return the full four-axis compliance matrix for all registered features."""
    matrix = IntegrityMode.get_compliance_matrix()
    return ComplianceMatrixResponse(features=list(matrix.values()))


@router.get("/check/{feature}", response_model=ComplianceResult)
async def check_feature_compliance(
    feature: str,
    user_id: str = Query(..., description="User whose mode to check against"),
):
    """Check whether a specific feature is compliant under the user's current mode."""
    mode = IntegrityMode.get_active_mode(user_id)
    result = IntegrityMode.check_feature_compliance(feature, mode)
    return result
