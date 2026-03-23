"""API endpoints for MLB The Show 26 pitching — sequencing, tunneling, batter scouting."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, Query

from app.schemas.mlb26.pitching import (
    BatterTendency,
    PitchSequence,
    PitchType,
    TunnelReport,
    ZoneHeatmap,
)
from app.services.agents.mlb26.pitch_forge import PitchForge

router = APIRouter(prefix="/titles/mlb26/pitching", tags=["MLB 26 — Pitching"])

_pitch_engine = PitchForge()


@router.get("/sequence", response_model=PitchSequence, summary="Generate pitch sequence")
async def generate_sequence(
    arsenal: str = Query(..., description="Comma-separated pitch types"),
    batter_hand: str = Query("RHH", description="RHH or LHH"),
    count: str = Query("0-0"),
    outs: int = Query(0, ge=0, le=2),
    runners_on: bool = Query(False),
) -> PitchSequence:
    """Generate an optimal pitch sequence for the at-bat."""
    try:
        pitch_types = [PitchType(p.strip()) for p in arsenal.split(",")]
        return _pitch_engine.generate_sequence(pitch_types, batter_hand, count, outs, runners_on)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/tunnels", response_model=TunnelReport, summary="Find tunnel pairs")
async def find_tunnels(
    arsenal: str = Query(..., description="Comma-separated pitch types"),
) -> TunnelReport:
    """Identify the best tunneling pairs from a pitcher's arsenal."""
    try:
        pitch_types = [PitchType(p.strip()) for p in arsenal.split(",")]
        return _pitch_engine.find_tunnel_pairs(pitch_types)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/batter-tendencies/{batter_id}", response_model=BatterTendency, summary="Analyze batter")
async def analyze_batter(batter_id: str, at_bat_history: list[dict]) -> BatterTendency:
    """Analyze a batter's tendencies from pitch-by-pitch data."""
    try:
        return _pitch_engine.analyze_batter_tendencies(batter_id, at_bat_history)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/heatmap/{batter_id}", response_model=ZoneHeatmap, summary="Zone heatmap")
async def get_zone_heatmap(batter_id: str) -> ZoneHeatmap:
    """Get a 9-zone performance heatmap for a batter."""
    return _pitch_engine.get_zone_heatmap(batter_id)
