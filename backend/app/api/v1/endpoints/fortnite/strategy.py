"""API endpoints for Fortnite ZoneForge, FortniteMeta, and FortniteTwin."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, Query

from app.schemas.fortnite.gameplay import (
    AugmentPriority,
    FortniteTwinProfile,
    MaterialType,
    MetaSnapshot,
    MobilityItem,
    PlayerPosition,
    RotationPlan,
    StormState,
    WeaponMeta,
    ZonePhase,
)
from app.services.agents.fortnite.fortnite_meta import FortniteMetaAI
from app.services.agents.fortnite.fortnite_twin import FortniteTwin
from app.services.agents.fortnite.zone_forge_fn import ZoneForgeFN

router = APIRouter(prefix="/titles/fortnite/strategy", tags=["Fortnite — Strategy & Meta"])

_zone_engine = ZoneForgeFN()
_meta_engine = FortniteMetaAI()
_twin_engine = FortniteTwin()


# ---------------------------------------------------------------------------
# ZoneForge FN endpoints
# ---------------------------------------------------------------------------


@router.post("/{user_id}/rotation", response_model=RotationPlan)
async def generate_rotation_plan(
    user_id: str,
    zone_phase: ZonePhase = Query(..., description="Current zone phase"),
    seconds_until_close: int = Query(60, ge=0),
    safe_zone_x: float = Query(0.0),
    safe_zone_y: float = Query(0.0),
    safe_zone_radius: float = Query(500.0, ge=0),
    player_x: float = Query(0.0),
    player_y: float = Query(0.0),
    health: int = Query(100, ge=0, le=100),
    shield: int = Query(100, ge=0, le=100),
    wood: int = Query(500, ge=0),
    brick: int = Query(300, ge=0),
    metal: int = Query(200, ge=0),
    has_mobility: bool = Query(False),
    alive_players: int = Query(50, ge=1),
) -> RotationPlan:
    """Generate optimal rotation plan with zone tax calculation."""
    storm = StormState(
        zone_phase=zone_phase,
        seconds_until_close=seconds_until_close,
        storm_damage_per_tick=_get_storm_damage(zone_phase),
        safe_zone_center=(safe_zone_x, safe_zone_y),
        safe_zone_radius=safe_zone_radius,
    )
    player = PlayerPosition(
        x=player_x,
        y=player_y,
        health=health,
        shield=shield,
        materials={
            MaterialType.WOOD: wood,
            MaterialType.BRICK: brick,
            MaterialType.METAL: metal,
        },
        has_mobility_item=has_mobility,
        alive_players=alive_players,
    )
    try:
        return _zone_engine.generate_rotation_plan(user_id, storm, player)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc))


def _get_storm_damage(phase: ZonePhase) -> float:
    """Get storm damage per tick for a zone phase."""
    damage_table = {
        ZonePhase.EARLY_GAME: 1.0,
        ZonePhase.FIRST_ZONE: 1.0,
        ZonePhase.SECOND_ZONE: 2.0,
        ZonePhase.THIRD_ZONE: 5.0,
        ZonePhase.FOURTH_ZONE: 8.0,
        ZonePhase.MOVING_ZONE: 10.0,
        ZonePhase.HALF_HALF: 10.0,
        ZonePhase.ENDGAME: 10.0,
    }
    return damage_table.get(phase, 1.0)


# ---------------------------------------------------------------------------
# FortniteMeta AI endpoints
# ---------------------------------------------------------------------------


@router.get("/meta/weapons", response_model=list[WeaponMeta])
async def get_weapon_tier_list(
    weapon_class: str | None = Query(None, description="Filter by weapon class"),
) -> list[WeaponMeta]:
    """Get current weapon tier list, optionally filtered by class."""
    try:
        return _meta_engine.get_weapon_tier_list(weapon_class)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@router.get("/meta/augments", response_model=list[AugmentPriority])
async def get_augment_priorities(
    playstyle: str | None = Query(None, description="aggressive, passive, or balanced"),
    top_n: int = Query(5, ge=1, le=20),
) -> list[AugmentPriority]:
    """Get augment priority rankings for current meta."""
    try:
        return _meta_engine.get_augment_priorities(playstyle, top_n)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@router.get("/meta/augments/select", response_model=AugmentPriority | None)
async def select_augment(
    options: str = Query(..., description="Comma-separated augment names offered"),
    playstyle: str = Query("balanced"),
) -> AugmentPriority | None:
    """Select the best augment from offered options."""
    option_list = [o.strip() for o in options.split(",") if o.strip()]
    try:
        return _meta_engine.select_augment(option_list, playstyle)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@router.get("/meta/mobility", response_model=list[MobilityItem])
async def get_mobility_items(
    zone_phase: ZonePhase | None = Query(None),
) -> list[MobilityItem]:
    """Get mobility item optimization for current meta."""
    try:
        return _meta_engine.get_mobility_items(zone_phase)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@router.get("/meta/snapshot", response_model=MetaSnapshot)
async def get_meta_snapshot(
    patch_version: str = Query("32.10"),
    season: str = Query("Chapter 6 Season 2"),
) -> MetaSnapshot:
    """Get full meta snapshot for current patch/season."""
    try:
        return _meta_engine.get_meta_snapshot(patch_version, season)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@router.get("/meta/mobility/should-carry")
async def should_carry_mobility(
    zone_phase: ZonePhase = Query(...),
    has_heals: bool = Query(True),
    slots_free: int = Query(1, ge=0),
) -> dict:
    """Get advice on whether to carry a mobility item."""
    try:
        return _meta_engine.should_carry_mobility(zone_phase, has_heals, slots_free)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc))


# ---------------------------------------------------------------------------
# FortniteTwin endpoints
# ---------------------------------------------------------------------------


@router.get("/{user_id}/twin", response_model=FortniteTwinProfile)
async def get_player_twin(user_id: str) -> FortniteTwinProfile:
    """Get the Fortnite digital twin profile for a player.

    In production, this aggregates stored BuildForge, EditForge, and
    ZoneForge data. Returns a baseline demo profile here.
    """
    try:
        return _twin_engine.build_twin(user_id)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc))
