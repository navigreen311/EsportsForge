"""Confidence endpoints — agent confidence scoring and calibration."""

from __future__ import annotations

from fastapi import APIRouter, Query

router = APIRouter(prefix="/confidence", tags=["Confidence"])


@router.get("/{agent_name}/score")
async def get_confidence_score(
    agent_name: str,
    title: str = Query(..., description="Game title"),
):
    """Get the current confidence score for an agent on a title."""
    return {
        "agent": agent_name,
        "title": title,
        "confidence": 0.0,
        "status": "stub — implementation pending",
    }


@router.get("/{agent_name}/history")
async def get_confidence_history(
    agent_name: str,
    title: str = Query(..., description="Game title"),
):
    """Get confidence score history over time."""
    return {"agent": agent_name, "title": title, "history": [], "status": "stub — implementation pending"}


@router.get("/overview")
async def get_confidence_overview(
    title: str = Query(..., description="Game title"),
):
    """Get confidence overview for all agents on a title."""
    return {"title": title, "agents": [], "status": "stub — implementation pending"}
