"""API endpoints for Warzone combat intelligence — zone, gunfight, squad, twin."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, Query

from app.schemas.warzone.combat import (
    EngagementRange,
    GunfightAnalysis,
    SquadAnalysis,
    SquadOpsRequest,
    WarzoneTwinProfile,
    WarzoneTwinRequest,
    ZoneRequest,
    ZoneResponse,
)
from app.services.agents.warzone.gunfight_ai import GunfightAI
from app.services.agents.warzone.squad_ops import SquadOps
from app.services.agents.warzone.warzone_twin import WarzoneTwin
from app.services.agents.warzone.zone_forge import ZoneForge

router = APIRouter(prefix="/titles/warzone/combat", tags=["Warzone — Combat"])

_zone_forge = ZoneForge()
_gunfight_ai = GunfightAI()
_squad_ops = SquadOps()
_warzone_twin = WarzoneTwin()


# --------------------------------------------------------------------------
# POST /titles/warzone/combat/zone
# --------------------------------------------------------------------------

@router.post("/zone", response_model=ZoneResponse)
async def analyze_zone(request: ZoneRequest) -> ZoneResponse:
    """Full zone intelligence — circle prediction, rotation plan, third-party risk."""
    try:
        return _zone_forge.analyze_zone(request)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


# --------------------------------------------------------------------------
# GET /titles/warzone/combat/gunfight
# --------------------------------------------------------------------------

@router.get("/gunfight", response_model=GunfightAnalysis)
async def gunfight_analysis(
    your_weapon: str | None = Query(None, description="Your weapon name"),
    enemy_weapon: str | None = Query(None, description="Enemy weapon name"),
    engagement_range: EngagementRange = Query(
        EngagementRange.MEDIUM, description="Engagement distance band"
    ),
    skill_level: str = Query("intermediate", description="beginner/intermediate/advanced"),
) -> GunfightAnalysis:
    """Gunfight intelligence — recoil patterns, drills, engagement decision."""
    try:
        weapons = None
        if your_weapon:
            weapons = [your_weapon]
            if enemy_weapon:
                weapons.append(enemy_weapon)
        return _gunfight_ai.full_gunfight_analysis(
            weapon_names=weapons,
            your_weapon=your_weapon,
            enemy_weapon=enemy_weapon,
            engagement_range=engagement_range,
            skill_level=skill_level,
        )
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


# --------------------------------------------------------------------------
# POST /titles/warzone/combat/squad
# --------------------------------------------------------------------------

@router.post("/squad", response_model=SquadAnalysis)
async def analyze_squad(request: SquadOpsRequest) -> SquadAnalysis:
    """Full squad operations analysis — roles, comms, revive priority, synergy."""
    try:
        return _squad_ops.analyze_squad(request)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


# --------------------------------------------------------------------------
# POST /titles/warzone/combat/twin
# --------------------------------------------------------------------------

@router.post("/twin", response_model=WarzoneTwinProfile)
async def build_twin(request: WarzoneTwinRequest) -> WarzoneTwinProfile:
    """Build a digital twin profile from match history."""
    try:
        return _warzone_twin.build_profile(request)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
