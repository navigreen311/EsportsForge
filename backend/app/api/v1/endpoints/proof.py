"""Proof endpoints — evidence trails and recommendation provenance."""

from __future__ import annotations

from fastapi import APIRouter, Query

router = APIRouter(prefix="/proof", tags=["Proof"])


@router.get("/{recommendation_id}")
async def get_proof_trail(recommendation_id: str):
    """Get the full evidence trail for a specific recommendation."""
    return {"recommendation_id": recommendation_id, "trail": [], "status": "stub — implementation pending"}


@router.get("/{user_id}/recent")
async def get_recent_proofs(
    user_id: str,
    title: str = Query(..., description="Game title"),
    limit: int = Query(10, ge=1, le=50),
):
    """Get recent proof trails for a player's recommendations."""
    return {"user_id": user_id, "title": title, "proofs": [], "status": "stub — implementation pending"}


@router.get("/agents/{agent_name}/accuracy-proof")
async def get_agent_accuracy_proof(
    agent_name: str,
    title: str = Query(..., description="Game title"),
):
    """Get proof of an agent's accuracy claims."""
    return {"agent": agent_name, "title": title, "proof": {}, "status": "stub — implementation pending"}
