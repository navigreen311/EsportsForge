"""Pydantic schemas for MobileAPI — kill sheets, tournament ops, quick view, push notifications."""

from __future__ import annotations

from typing import Any, Optional

from pydantic import BaseModel, Field


class MobileKillSheet(BaseModel):
    """Simplified kill sheet optimized for mobile display."""
    user_id: str
    opponent_id: str | None = None
    title: str
    plays: list[dict[str, Any]] = Field(default_factory=list, description="Condensed play list for mobile")
    quick_tips: list[str] = Field(default_factory=list)
    last_updated: str = ""


class TournamentOps(BaseModel):
    """Mobile tournament operations view."""
    user_id: str
    tournament_id: str
    tournament_name: str
    current_round: int
    total_rounds: int
    next_opponent: dict[str, Any] | None = None
    bracket_position: str = ""
    schedule: list[dict[str, Any]] = Field(default_factory=list)
    quick_prep: list[str] = Field(default_factory=list)
    status: str = Field("active", description="active, eliminated, champion, pending")


class QuickView(BaseModel):
    """Quick view dashboard for mobile — essential info at a glance."""
    user_id: str
    title: str
    current_rating: float = 0.0
    rank_tier: str = "unranked"
    recent_record: str = "0-0"
    win_streak: int = 0
    loss_streak: int = 0
    top_recommendation: str = ""
    active_drills: int = 0
    notifications: int = 0
    last_session: str = ""


class PushNotification(BaseModel):
    """Push notification to be sent to a mobile device."""
    notification_id: str
    user_id: str
    title: str
    body: str
    notification_type: str = Field(..., description="meta_alert, drill_reminder, tournament, achievement, coach")
    priority: str = Field("normal", description="low, normal, high, urgent")
    data: dict[str, Any] = Field(default_factory=dict)
    sent: bool = False
    sent_at: str | None = None


class PushResult(BaseModel):
    """Result of sending a push notification."""
    success: bool
    notification_id: str
    message: str
