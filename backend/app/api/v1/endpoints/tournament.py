"""TournaOps Console API endpoints — tournament day operations."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, Query

from app.schemas.tournament import (
    HydrationReminder,
    MemoryCard,
    QueueSheet,
    ResetScript,
    ResetType,
    TournamentPrep,
    WarmupChecklist,
)
from app.services.backbone.tourna_ops import TournaOps

router = APIRouter(prefix="/tournament", tags=["TournaOps"])

# ---------------------------------------------------------------------------
# Singleton (replaced by DI in production)
# ---------------------------------------------------------------------------
_tourna_ops = TournaOps()


def get_tourna_ops() -> TournaOps:
    """Accessor for the global TournaOps instance (test-friendly)."""
    return _tourna_ops


# ---------------------------------------------------------------------------
# Opponent Queue
# ---------------------------------------------------------------------------

@router.get("/queue/{user_id}/{tournament_id}", response_model=QueueSheet)
async def get_opponent_queue(user_id: str, tournament_id: str) -> QueueSheet:
    """Get the opponent queue sheet for a tournament."""
    return _tourna_ops.get_opponent_queue(user_id, tournament_id)


@router.post("/queue/{user_id}/{tournament_id}/add", response_model=QueueSheet)
async def add_opponent(
    user_id: str,
    tournament_id: str,
    opponent_id: str = Query(...),
    opponent_tag: str = Query(...),
    seed: int | None = Query(default=None),
    estimated_round: int | None = Query(default=None),
) -> QueueSheet:
    """Add an opponent to the queue sheet."""
    return _tourna_ops.add_opponent_to_queue(
        user_id, tournament_id, opponent_id, opponent_tag, seed, estimated_round
    )


# ---------------------------------------------------------------------------
# Matchup Notes
# ---------------------------------------------------------------------------

@router.get("/matchup/{user_id}/{opponent_id}")
async def get_matchup_notes(user_id: str, opponent_id: str) -> dict:
    """Get quick matchup notes for an opponent."""
    return _tourna_ops.get_matchup_notes(user_id, opponent_id)


# ---------------------------------------------------------------------------
# Warmup
# ---------------------------------------------------------------------------

@router.get("/warmup/{user_id}", response_model=WarmupChecklist)
async def get_warmup_checklist(user_id: str) -> WarmupChecklist:
    """Get the pre-tournament warmup checklist."""
    return _tourna_ops.get_warmup_checklist(user_id)


# ---------------------------------------------------------------------------
# Reset Script
# ---------------------------------------------------------------------------

@router.get("/reset/{user_id}", response_model=ResetScript)
async def get_reset_script(
    user_id: str,
    reset_type: ResetType = Query(default=ResetType.STANDARD),
) -> ResetScript:
    """Get a between-round mental reset script."""
    return _tourna_ops.get_reset_script(user_id, reset_type)


# ---------------------------------------------------------------------------
# Memory Cards
# ---------------------------------------------------------------------------

@router.get("/memory-cards/{user_id}/{tournament_id}", response_model=list[MemoryCard])
async def get_memory_cards(user_id: str, tournament_id: str) -> list[MemoryCard]:
    """Get memory cards for a tournament."""
    return _tourna_ops.get_memory_cards(user_id, tournament_id)


@router.post("/memory-cards/{user_id}/{tournament_id}", response_model=MemoryCard)
async def add_memory_card(
    user_id: str,
    tournament_id: str,
    opponent_id: str = Query(...),
    opponent_tag: str = Query(...),
    exploit_notes: str = Query(default=""),
    confidence_rating: float = Query(default=0.5, ge=0.0, le=1.0),
) -> MemoryCard:
    """Create or update a memory card for an opponent."""
    return _tourna_ops.add_memory_card(
        user_id, tournament_id, opponent_id, opponent_tag,
        exploit_notes=exploit_notes,
        confidence_rating=confidence_rating,
    )


# ---------------------------------------------------------------------------
# Quick Notes
# ---------------------------------------------------------------------------

@router.post("/notes/{user_id}")
async def log_quick_note(user_id: str, note: str = Query(...)) -> dict:
    """Log a fast note during a tournament."""
    return _tourna_ops.log_quick_note(user_id, note)


@router.get("/notes/{user_id}")
async def get_quick_notes(user_id: str) -> list[str]:
    """Get all quick notes for a user."""
    return _tourna_ops.get_quick_notes(user_id)


# ---------------------------------------------------------------------------
# Hydration
# ---------------------------------------------------------------------------

@router.get("/hydration/{user_id}", response_model=HydrationReminder)
async def get_hydration_reminder(user_id: str) -> HydrationReminder:
    """Check hydration status."""
    return _tourna_ops.get_hydration_reminder(user_id)


@router.post("/hydration/{user_id}", response_model=HydrationReminder)
async def log_hydration(user_id: str) -> HydrationReminder:
    """Log a hydration event."""
    return _tourna_ops.log_hydration(user_id)
