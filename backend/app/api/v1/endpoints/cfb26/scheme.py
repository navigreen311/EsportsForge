"""API endpoints for CFB 26 SchemeDepthAI — playbook analysis and scheme mastery."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, Query

from app.schemas.cfb26.scheme import (
    CounterScheme,
    OptionReadProgression,
    PlaybookAnalysis,
    SchemeProgression,
    SchemeType,
)
from app.services.agents.cfb26.scheme_depth_ai import SchemeDepthAI

router = APIRouter(prefix="/titles/cfb26/scheme", tags=["CFB 26 — Schemes"])

_engine = SchemeDepthAI()


@router.get("/playbook/{scheme}", response_model=PlaybookAnalysis)
async def analyze_playbook(scheme: SchemeType) -> PlaybookAnalysis:
    """Analyze playbook depth for a given scheme archetype."""
    try:
        return _engine.analyze_playbook(scheme)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@router.get("/{user_id}/progression", response_model=SchemeProgression)
async def get_scheme_progression(
    user_id: str,
    scheme: SchemeType = Query(..., description="Scheme to track"),
) -> SchemeProgression:
    """Get scheme mastery progression for a player."""
    try:
        return _engine.get_progression(user_id, scheme)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@router.get("/{user_id}/option-reads", response_model=OptionReadProgression)
async def get_option_reads(
    user_id: str,
    scheme: SchemeType = Query(..., description="Scheme type"),
) -> OptionReadProgression:
    """Get option read analysis and progression."""
    try:
        return _engine.get_option_read_progression(user_id, scheme)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@router.get("/counter/{scheme}", response_model=CounterScheme)
async def get_counter_scheme(
    scheme: SchemeType,
    opponent_tendencies: str = Query("", description="Comma-separated tendencies"),
) -> CounterScheme:
    """Generate counter-strategy against an opponent's scheme."""
    tendencies = [t.strip() for t in opponent_tendencies.split(",") if t.strip()]
    try:
        return _engine.generate_counter(scheme, tendencies)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc))
