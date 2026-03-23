"""API endpoints for NBA 2K26 BuildForge — build analysis, badge optimization, meta tracking."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, Query

from app.schemas.nba2k26.builds import (
    Archetype,
    Build,
    BuildAnalysisResult,
    BuildCompareResult,
    MetaBuild,
    MetaTier,
    Position,
)
from app.services.agents.nba2k26.build_forge import BuildForge

router = APIRouter(prefix="/titles/nba2k26/builds", tags=["NBA 2K26 — Builds"])

_engine = BuildForge()


@router.post("/analyze", response_model=BuildAnalysisResult)
async def analyze_build(build: Build) -> BuildAnalysisResult:
    """Analyze a player build — meta tier, badge optimization, attribute thresholds."""
    try:
        return _engine.analyze_build(build)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@router.post("/compare", response_model=BuildCompareResult)
async def compare_builds(build_a: Build, build_b: Build) -> BuildCompareResult:
    """Head-to-head comparison of two builds."""
    try:
        return _engine.compare_builds(build_a, build_b)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@router.get("/meta", response_model=list[MetaBuild])
async def get_meta_builds(
    position: Position | None = Query(None, description="Filter by position"),
    tier: MetaTier | None = Query(None, description="Filter by meta tier"),
) -> list[MetaBuild]:
    """Get current meta builds, optionally filtered by position or tier."""
    try:
        return _engine.get_meta_builds(position=position, tier=tier)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@router.get("/meta/counters/{archetype}", response_model=list[MetaBuild])
async def get_counter_builds(archetype: Archetype) -> list[MetaBuild]:
    """Find meta builds that counter a given archetype."""
    try:
        return _engine.get_counter_builds(archetype)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc))
