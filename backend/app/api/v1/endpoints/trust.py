"""API endpoints for the Trust Layer — privacy governance and audit."""

from fastapi import APIRouter, Query

from app.schemas.integrity import (
    AuditEvent,
    PrivacySettings,
    UpdatePrivacyRequest,
)
from app.services.backbone.trust_layer import TrustLayer

router = APIRouter(prefix="/trust", tags=["trust"])


@router.get("/privacy", response_model=PrivacySettings)
async def get_privacy_settings(
    user_id: str = Query(..., description="User whose privacy settings to retrieve"),
):
    """Return the current privacy/data-sharing settings for a user."""
    return TrustLayer.get_privacy_settings(user_id)


@router.put("/privacy", response_model=PrivacySettings)
async def update_privacy(
    body: UpdatePrivacyRequest,
    user_id: str = Query(..., description="User whose privacy settings to update"),
):
    """Update data-sharing permissions for a user (opt-in / opt-out)."""
    return TrustLayer.update_privacy(user_id, body.permissions)


@router.get("/audit", response_model=list[AuditEvent])
async def get_audit_trail(
    user_id: str = Query(..., description="User whose audit trail to retrieve"),
):
    """Return the full audit trail for a user."""
    return TrustLayer.get_audit_trail(user_id)


@router.post("/export")
async def export_user_data(
    user_id: str = Query(..., description="User whose data to export"),
):
    """Export all data held for a user (GDPR right-to-portability)."""
    return TrustLayer.export_user_data(user_id)


@router.delete("/data")
async def delete_user_data(
    user_id: str = Query(..., description="User whose data to delete"),
):
    """Delete all stored data for a user (GDPR right-to-erasure)."""
    return TrustLayer.handle_data_deletion(user_id)
