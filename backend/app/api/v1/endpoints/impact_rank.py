"""ImpactRank API — ruthless prioritization endpoints."""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, HTTPException, Query

from app.schemas.impact_rank import (
    ImpactRankResponse,
    ImpactRanking,
    OutcomeReport,
    PriorityRecommendation,
    RecalculateRequest,
)
from app.services.backbone.impact_rank import impact_rank_engine

router = APIRouter(prefix="/impact-rank", tags=["ImpactRank"])


@router.get(
    "/{user_id}",
    response_model=ImpactRankResponse,
    summary="All rankings for a player",
)
async def get_rankings(
    user_id: str,
    title: str = Query(..., description="Game title (e.g. 'madden26')."),
    include_suppressed: bool = Query(
        False,
        description="Include suppressed low-ROI items.",
    ),
) -> ImpactRankResponse:
    """Return all ImpactRank rankings for a player in a given title.

    Rankings are ordered by composite score (highest priority first).
    Suppressed items are excluded unless ``include_suppressed=True``.
    """
    key = (user_id, title)
    rankings = impact_rank_engine._store.get(key, [])

    if not include_suppressed:
        visible = [r for r in rankings if not r.suppressed]
    else:
        visible = list(rankings)

    suppressed_count = sum(1 for r in rankings if r.suppressed)

    return ImpactRankResponse(
        user_id=user_id,
        title=title,
        rankings=visible,
        suppressed_count=suppressed_count,
    )


@router.get(
    "/{user_id}/top",
    response_model=PriorityRecommendation,
    summary="THE one thing to fix next",
)
async def get_top_priority(
    user_id: str,
    title: str = Query(..., description="Game title (e.g. 'madden26')."),
) -> PriorityRecommendation:
    """Return the single highest-leverage fix for a player.

    This is the core ImpactRank output: one clear, actionable directive.
    """
    result = impact_rank_engine.get_top_priority(user_id, title)
    if result is None:
        raise HTTPException(
            status_code=404,
            detail=f"No rankings found for user={user_id} title={title}. "
            "Run POST /recalculate first.",
        )
    return result


@router.post(
    "/{user_id}/recalculate",
    response_model=ImpactRankResponse,
    summary="Force full recalculation",
)
async def recalculate(
    user_id: str,
    body: RecalculateRequest,
    player_data: dict | None = None,
) -> ImpactRankResponse:
    """Trigger a full recalculation of rankings for a player + title.

    In production, ``player_data`` is fetched from ForgeDataFabric and
    PlayerTwin automatically.  For now, pass mock data or rely on
    stored state.
    """
    rankings = impact_rank_engine.recalculate(
        user_id=user_id,
        title=body.title,
        player_data=player_data,
    )

    suppressed_count = sum(1 for r in rankings if r.suppressed)

    return ImpactRankResponse(
        user_id=user_id,
        title=body.title,
        rankings=[r for r in rankings if not r.suppressed],
        suppressed_count=suppressed_count,
    )


@router.post(
    "/{user_id}/{ranking_id}/outcome",
    response_model=ImpactRanking,
    summary="Report outcome for a ranking",
)
async def report_outcome(
    user_id: str,
    ranking_id: UUID,
    body: OutcomeReport,
) -> ImpactRanking:
    """Report the outcome after a player attempted the recommended fix.

    This feeds into LoopAI learning — ImpactRank adjusts its confidence
    and scores based on observed results.
    """
    outcome = {
        "verdict": body.verdict.value,
        "observed_lift": body.observed_lift,
        "games_played": body.games_played,
        "notes": body.notes,
    }

    result = impact_rank_engine.update_from_outcome(user_id, ranking_id, outcome)
    if result is None:
        raise HTTPException(
            status_code=404,
            detail=f"Ranking {ranking_id} not found.",
        )
    return result
