"""API endpoints for LoadoutForge — Warzone weapon meta and loadout optimization."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, Query

from app.schemas.warzone.combat import (
    AttachmentTradeOff,
    LoadoutOptimizeRequest,
    LoadoutOptimizeResponse,
    WeaponClass,
    WeaponMeta,
)
from app.services.agents.warzone.loadout_forge import LoadoutForge

router = APIRouter(prefix="/titles/warzone/loadout", tags=["Warzone — Loadout"])

_loadout_forge = LoadoutForge()


# --------------------------------------------------------------------------
# GET /titles/warzone/loadout/meta
# --------------------------------------------------------------------------

@router.get("/meta", response_model=list[WeaponMeta])
async def get_meta_tier_list() -> list[WeaponMeta]:
    """Current weapon meta tier list sorted by tier and win rate."""
    try:
        return _loadout_forge.get_meta_tier_list()
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


# --------------------------------------------------------------------------
# POST /titles/warzone/loadout/optimize
# --------------------------------------------------------------------------

@router.post("/optimize", response_model=LoadoutOptimizeResponse)
async def optimize_loadout(request: LoadoutOptimizeRequest) -> LoadoutOptimizeResponse:
    """Build an optimized loadout based on playstyle and engagement preferences."""
    try:
        return _loadout_forge.optimize_loadout(request)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


# --------------------------------------------------------------------------
# GET /titles/warzone/loadout/attachments
# --------------------------------------------------------------------------

@router.get("/attachments", response_model=list[AttachmentTradeOff])
async def get_attachment_tradeoffs(
    weapon_class: WeaponClass = Query(..., description="Weapon class to analyze"),
) -> list[AttachmentTradeOff]:
    """Attachment trade-off analysis for a weapon class."""
    try:
        return _loadout_forge.get_attachment_tradeoffs(weapon_class)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


# --------------------------------------------------------------------------
# GET /titles/warzone/loadout/compare
# --------------------------------------------------------------------------

@router.get("/compare")
async def compare_weapons(
    weapon_a: str = Query(..., description="First weapon name"),
    weapon_b: str = Query(..., description="Second weapon name"),
) -> dict:
    """Head-to-head weapon comparison."""
    try:
        result = _loadout_forge.compare_weapons(weapon_a, weapon_b)
        if "error" in result:
            raise HTTPException(status_code=404, detail=result["error"])
        return result
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
