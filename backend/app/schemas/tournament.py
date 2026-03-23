"""Pydantic schemas for TournaOps Console."""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------

class PrepStatus(str, Enum):
    """Preparation status for an opponent."""

    NOT_STARTED = "not_started"
    IN_PROGRESS = "in_progress"
    READY = "ready"
    NEEDS_REVIEW = "needs_review"


class ResetType(str, Enum):
    """Type of mental reset script."""

    QUICK = "quick"          # 30-second breathing reset
    STANDARD = "standard"    # 2-minute full reset
    DEEP = "deep"            # 5-minute deep composure reset


class HydrationLevel(str, Enum):
    """Hydration reminder urgency."""

    OK = "ok"
    DUE = "due"
    OVERDUE = "overdue"


# ---------------------------------------------------------------------------
# Memory Cards
# ---------------------------------------------------------------------------

class MemoryCard(BaseModel):
    """Quick-reference card for an opponent in a tournament."""

    opponent_id: str
    opponent_tag: str = Field(description="Opponent gamertag / handle.")
    key_tendencies: list[str] = Field(
        default_factory=list,
        description="Top 3-5 tendencies to remember mid-match.",
    )
    exploit_notes: str = Field(
        default="",
        description="One-liner on how to exploit their weakness.",
    )
    danger_plays: list[str] = Field(
        default_factory=list,
        description="Plays/setups to watch out for.",
    )
    confidence_rating: float = Field(
        default=0.5,
        ge=0.0,
        le=1.0,
        description="Your confidence level against this opponent.",
    )
    last_updated: datetime = Field(default_factory=datetime.utcnow)


# ---------------------------------------------------------------------------
# Opponent Queue
# ---------------------------------------------------------------------------

class OpponentQueue(BaseModel):
    """Single entry in the tournament opponent queue."""

    opponent_id: str
    opponent_tag: str
    seed: int | None = None
    prep_status: PrepStatus = PrepStatus.NOT_STARTED
    notes: str = ""
    estimated_round: int | None = Field(
        default=None,
        description="Estimated round number this opponent appears.",
    )


class QueueSheet(BaseModel):
    """Full queue sheet for a tournament."""

    user_id: str
    tournament_id: str
    tournament_name: str = ""
    opponents: list[OpponentQueue] = Field(default_factory=list)
    total_rounds: int = 0
    current_round: int = 0
    generated_at: datetime = Field(default_factory=datetime.utcnow)


# ---------------------------------------------------------------------------
# Warmup & Reset
# ---------------------------------------------------------------------------

class WarmupChecklist(BaseModel):
    """Pre-tournament warmup routine."""

    user_id: str
    items: list[dict[str, Any]] = Field(
        default_factory=list,
        description="Checklist items: {task, completed, duration_minutes, category}.",
    )
    estimated_total_minutes: int = 0
    notes: str = ""


class ResetScript(BaseModel):
    """Between-round mental reset script."""

    user_id: str
    reset_type: ResetType = ResetType.STANDARD
    steps: list[str] = Field(
        default_factory=list,
        description="Ordered steps for the reset routine.",
    )
    affirmation: str = Field(
        default="",
        description="Personalized affirmation or mantra.",
    )
    duration_seconds: int = 120


class HydrationReminder(BaseModel):
    """Hydration and break reminder."""

    user_id: str
    level: HydrationLevel = HydrationLevel.OK
    last_hydration: datetime | None = None
    minutes_since_last: int = 0
    message: str = "Stay hydrated!"


# ---------------------------------------------------------------------------
# Tournament Prep
# ---------------------------------------------------------------------------

class TournamentPrep(BaseModel):
    """Overall tournament preparation summary."""

    user_id: str
    tournament_id: str
    tournament_name: str = ""
    queue_sheet: QueueSheet | None = None
    memory_cards: list[MemoryCard] = Field(default_factory=list)
    warmup: WarmupChecklist | None = None
    reset_script: ResetScript | None = None
    readiness_score: float = Field(
        default=0.0,
        ge=0.0,
        le=1.0,
        description="Overall readiness score 0-1.",
    )
    quick_notes: list[str] = Field(
        default_factory=list,
        description="Fast notes logged during tournament.",
    )
    created_at: datetime = Field(default_factory=datetime.utcnow)
