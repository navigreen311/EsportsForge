"""Pydantic schemas for CoachPortal — dashboard, drills, playbook sharing, war room."""

from __future__ import annotations

from typing import Any, Optional

from pydantic import BaseModel, Field


class CoachDashboard(BaseModel):
    """Coach dashboard overview."""
    coach_id: str
    team_name: str
    player_count: int
    active_drills: int
    pending_reviews: int
    overall_improvement_pct: float
    top_performers: list[dict[str, Any]] = Field(default_factory=list)
    struggling_players: list[dict[str, Any]] = Field(default_factory=list)
    recent_activity: list[dict[str, Any]] = Field(default_factory=list)


class DrillAssignment(BaseModel):
    """A drill assigned by a coach to a player."""
    drill_id: str
    coach_id: str
    player_id: str
    title: str
    description: str
    drill_type: str = Field(..., description="timing, positioning, decision, execution")
    target_metric: str
    target_value: float
    current_value: float = 0.0
    status: str = Field("assigned", description="assigned, in_progress, completed, expired")
    due_date: str | None = None


class DrillResult(BaseModel):
    """Result of assigning a drill."""
    success: bool
    drill_id: str
    message: str


class SharedPlaybook(BaseModel):
    """A playbook shared between coach and players."""
    playbook_id: str
    coach_id: str
    title: str
    game_title: str
    strategies: list[dict[str, Any]] = Field(default_factory=list)
    player_ids: list[str] = Field(default_factory=list)
    version: int = 1
    last_updated: str = ""
    notes: str = ""


class WarRoom(BaseModel):
    """War room — real-time coaching session with live data."""
    room_id: str
    coach_id: str
    game_title: str
    active_players: list[str] = Field(default_factory=list)
    live_recommendations: list[dict[str, Any]] = Field(default_factory=list)
    opponent_tendencies: dict[str, Any] = Field(default_factory=dict)
    adjustments_made: list[str] = Field(default_factory=list)
    status: str = Field("active", description="active, paused, ended")


class SeatManagement(BaseModel):
    """Coach subscription seat management."""
    coach_id: str
    plan: str = Field(..., description="solo, team, organization")
    total_seats: int
    used_seats: int
    available_seats: int
    players: list[dict[str, str]] = Field(default_factory=list)
