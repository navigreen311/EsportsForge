"""Cross-Title Cognitive Transfer API endpoints."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, Query

from app.schemas.cross_title import (
    CrossTitleProfile,
    TitleSwitch,
    TransferMap,
)
from app.services.backbone.cross_title_transfer import CrossTitleTransfer

router = APIRouter(prefix="/cross-title", tags=["CrossTitle"])

# ---------------------------------------------------------------------------
# Singleton (replaced by DI in production)
# ---------------------------------------------------------------------------
_engine = CrossTitleTransfer()


def get_engine() -> CrossTitleTransfer:
    """Accessor for the global CrossTitleTransfer instance (test-friendly)."""
    return _engine


# ---------------------------------------------------------------------------
# Transfer Map
# ---------------------------------------------------------------------------

@router.get("/transfer-map", response_model=list[TransferMap])
async def get_transfer_map(
    from_title: str | None = Query(default=None),
    to_title: str | None = Query(default=None),
) -> list[TransferMap]:
    """Get cognitive skill transfer mappings between titles.

    Optionally filter by source and/or destination title.
    """
    return _engine.get_transfer_map(from_title, to_title)


# ---------------------------------------------------------------------------
# Transfer Estimate
# ---------------------------------------------------------------------------

@router.get("/estimate", response_model=TransferMap)
async def estimate_transfer(
    from_title: str = Query(...),
    to_title: str = Query(...),
    skill: str = Query(...),
) -> TransferMap:
    """Estimate how well a specific skill transfers between two titles."""
    result = _engine.estimate_transfer(from_title, to_title, skill)
    if result is None:
        raise HTTPException(
            status_code=404,
            detail=f"No transfer mapping found for '{skill}' from {from_title} to {to_title}.",
        )
    return result


# ---------------------------------------------------------------------------
# Cross-Title Profile
# ---------------------------------------------------------------------------

@router.get("/profile/{user_id}", response_model=CrossTitleProfile)
async def get_cross_title_profile(user_id: str) -> CrossTitleProfile:
    """Get the player's cross-title cognitive profile."""
    return _engine.get_cross_title_profile(user_id)


# ---------------------------------------------------------------------------
# Accelerate Onboarding
# ---------------------------------------------------------------------------

@router.get("/onboarding/{user_id}/{new_title}", response_model=TitleSwitch)
async def accelerate_onboarding(user_id: str, new_title: str) -> TitleSwitch:
    """Generate an accelerated onboarding plan for a new title.

    Uses existing cognitive skills to speed up learning.
    """
    return _engine.accelerate_onboarding(user_id, new_title)
