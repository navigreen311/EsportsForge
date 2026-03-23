"""API endpoints for UFC 5 OnlineCareer Forge — fighter builds, perk rankings, style paths."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, Query

from app.schemas.ufc5.combat import (
    ArchetypeStyle,
    FighterBuild,
    FighterStylePath,
    PerkRanking,
)
from app.services.agents.ufc5.online_career import OnlineCareerForge

router = APIRouter(prefix="/titles/ufc5/career", tags=["UFC 5 — Online Career"])

_career_forge = OnlineCareerForge()


@router.get("/perks", summary="Get perk rankings")
async def get_perk_rankings(
    style: str | None = Query(None, description="Filter by synergy style"),
) -> list[PerkRanking]:
    """Return all perks ranked by effectiveness, optionally filtered by style."""
    style_enum = None
    if style:
        try:
            style_enum = ArchetypeStyle(style)
        except ValueError as exc:
            raise HTTPException(
                status_code=400, detail=f"Invalid style: {exc}"
            ) from exc
    return _career_forge.get_perk_rankings(style=style_enum)


@router.get("/style-paths", summary="Get style paths by win rate")
async def get_style_paths(
    weight_class: str | None = Query(None, description="Filter by weight class"),
) -> list[FighterStylePath]:
    """Return style paths ranked by win rate across weight classes."""
    return _career_forge.get_style_paths(weight_class=weight_class)


@router.get(
    "/build/{style}/{weight_class}",
    response_model=FighterBuild,
    summary="Generate optimized fighter build",
)
async def build_fighter(
    style: str,
    weight_class: str,
    name: str = Query("Custom Fighter", description="Fighter name"),
) -> FighterBuild:
    """Generate an optimized fighter build for the given style and weight class."""
    try:
        style_enum = ArchetypeStyle(style)
    except ValueError as exc:
        raise HTTPException(
            status_code=400, detail=f"Invalid style: {exc}"
        ) from exc
    return _career_forge.build_fighter(
        name=name,
        weight_class=weight_class,
        style=style_enum,
    )


@router.get("/weight-classes", summary="List weight classes with best styles")
async def get_weight_class_recommendations() -> dict[str, list[dict]]:
    """Return the best style paths for each weight class."""
    all_paths = _career_forge.get_style_paths()
    by_wc: dict[str, list[dict]] = {}
    for path in all_paths:
        wc = path.weight_class
        if wc not in by_wc:
            by_wc[wc] = []
        by_wc[wc].append({
            "style": path.style.value,
            "win_rate": path.win_rate,
        })
    # Sort each weight class by win rate
    for wc in by_wc:
        by_wc[wc].sort(key=lambda x: -x["win_rate"])
    return by_wc
