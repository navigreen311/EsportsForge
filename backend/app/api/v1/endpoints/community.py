"""API endpoints for CommunityIntel — meta, contributions, rankings, opponent seeding."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, Query

from app.schemas.community import (
    CommunityContribution,
    CommunityMeta,
    CommunityRankingsResponse,
    ContributionResult,
    OpponentSeed,
)
from app.services.backbone import community_intel

router = APIRouter(prefix="/community", tags=["Community Intel"])


@router.get("/meta/{title}", response_model=CommunityMeta, summary="Community meta")
async def get_meta(title: str, patch: str = Query("latest")) -> CommunityMeta:
    """Get community-sourced meta snapshot for a title."""
    return community_intel.get_community_meta(title, patch)


@router.post("/contribute", response_model=ContributionResult, summary="Contribute data")
async def contribute(contribution: CommunityContribution) -> ContributionResult:
    """Submit a data contribution to the community."""
    return community_intel.contribute_data(contribution)


@router.get("/rankings/{title}", response_model=CommunityRankingsResponse, summary="Rankings")
async def get_rankings(
    title: str,
    user_id: str | None = Query(None),
    limit: int = Query(50, ge=1, le=200),
) -> CommunityRankingsResponse:
    """Get community rankings for a title."""
    return community_intel.get_community_rankings(title, user_id, limit)


@router.post("/opponent-seed", response_model=OpponentSeed, summary="Seed opponent data")
async def seed_opponent(
    title: str = Query(...),
    opponent_id: str = Query(...),
    tendencies: dict = ...,
    archetype: str = Query("unknown"),
) -> OpponentSeed:
    """Seed opponent scouting data from community contributions."""
    try:
        return community_intel.seed_opponent_data(title, opponent_id, tendencies, archetype)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
