"""API endpoints for Madden 26 SchemeAI — scheme analysis, coverage matrix, hot routes."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, Query

from app.schemas.madden26.scheme import (
    CoverageMatrix,
    CoverageMatrixRequest,
    CoverageType,
    HotRoute,
    HotRouteRequest,
    SchemeAnalysis,
    SchemeName,
    Situation,
    SituationPlay,
)
from app.services.agents.madden26.scheme_ai import SchemeAI

router = APIRouter(prefix="/titles/madden26", tags=["Madden 26 — Schemes"])

_scheme_ai = SchemeAI()


@router.get("/schemes", summary="List all recognized scheme archetypes")
async def list_schemes() -> list[dict[str, str]]:
    """Return all recognized Madden 26 scheme archetypes with descriptions."""
    return _scheme_ai.list_schemes()


@router.get(
    "/schemes/{name}/analysis",
    response_model=SchemeAnalysis,
    summary="Full scheme analysis",
)
async def get_scheme_analysis(name: str) -> SchemeAnalysis:
    """
    Return a comprehensive analysis of the named scheme including strengths,
    weaknesses, core concepts, coverage answers, and situation plays.
    """
    try:
        return await _scheme_ai.analyze_scheme(name)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post(
    "/coverage-matrix",
    response_model=CoverageMatrix,
    summary="Build coverage answer matrix",
)
async def build_coverage_matrix(body: CoverageMatrixRequest) -> CoverageMatrix:
    """Generate a coverage answer matrix for the given scheme."""
    return await _scheme_ai.build_coverage_answer_matrix(
        scheme=body.scheme.value,
        formation_filter=body.formation_filter,
    )


@router.post(
    "/hot-routes",
    response_model=list[HotRoute],
    summary="Suggest hot-route adjustments",
)
async def suggest_hot_routes(body: HotRouteRequest) -> list[HotRoute]:
    """Suggest optimal hot-route adjustments for a play vs a coverage read."""
    return await _scheme_ai.suggest_hot_routes(
        play=body.play_name,
        coverage_read=body.coverage_read,
    )


@router.get(
    "/schemes/{name}/situations/{situation}",
    response_model=list[SituationPlay],
    summary="Situation-specific plays",
)
async def get_situation_plays(name: str, situation: Situation) -> list[SituationPlay]:
    """Return the best plays for a given scheme and game situation."""
    return await _scheme_ai.get_situation_plays(scheme=name, situation=situation)
