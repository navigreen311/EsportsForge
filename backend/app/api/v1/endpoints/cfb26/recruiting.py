"""API endpoints for CFB 26 RecruitingIQ — dynasty recruiting optimizer."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException

from app.schemas.cfb26.recruiting import (
    DynastyStateInput,
    RecruitData,
    RecruitEvaluation,
    RecruitingBoard,
    RosterInput,
    RosterRoadmap,
)
from app.services.agents.cfb26.recruiting_iq import RecruitingIQ

router = APIRouter(prefix="/titles/cfb26/recruiting", tags=["CFB 26 — Recruiting"])

_engine = RecruitingIQ()


@router.post("/evaluate", response_model=RecruitEvaluation)
async def evaluate_recruit(recruit: RecruitData) -> RecruitEvaluation:
    """Evaluate a recruit's scheme fit, position need, and commitment likelihood."""
    try:
        return _engine.evaluate_recruit(recruit)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@router.post("/board", response_model=RecruitingBoard)
async def build_recruiting_board(dynasty: DynastyStateInput) -> RecruitingBoard:
    """Build a prioritized recruiting board for a dynasty program."""
    try:
        return _engine.build_board(dynasty)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@router.post("/roadmap", response_model=RosterRoadmap)
async def generate_roster_roadmap(roster: RosterInput) -> RosterRoadmap:
    """Generate a multi-year roster roadmap to maximize team trajectory."""
    try:
        return _engine.generate_roadmap(roster)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc))
