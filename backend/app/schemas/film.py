"""Pydantic schemas for FilmAI, MetaVersion Engine, and Onboarding Intelligence."""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------

class MistakeCategory(str, Enum):
    """Top-level mistake taxonomy used by FilmAI."""
    READ_ERROR = "read_error"          # misread the situation / opponent
    EXECUTION_ERROR = "execution_error"  # knew the right play, failed mechanically
    SCHEME_ERROR = "scheme_error"        # chose the wrong play / strategy


class OnboardingPhase(str, Enum):
    """Phases a new user walks through."""
    NOT_STARTED = "not_started"
    SESSION_1 = "session_1"
    SESSION_2 = "session_2"
    SESSION_3 = "session_3"
    COMPLETED = "completed"


class AdviceStatus(str, Enum):
    """Lifecycle status of a versioned recommendation."""
    ACTIVE = "active"
    STALE = "stale"
    EXPIRED = "expired"


# ---------------------------------------------------------------------------
# FilmAI — Replay Analysis
# ---------------------------------------------------------------------------

class TaggedMoment(BaseModel):
    """A single human- or AI-tagged moment in a replay."""
    replay_id: str = Field(..., description="Replay identifier")
    timestamp: float = Field(..., ge=0.0, description="Seconds into the replay")
    tag: str = Field(..., description="Label, e.g. 'turnover', 'big_play'")
    notes: str = Field("", description="Optional analyst notes")
    created_at: datetime = Field(default_factory=datetime.utcnow)


class MistakeClassification(BaseModel):
    """A classified mistake from replay analysis."""
    moment_timestamp: float = Field(..., ge=0.0)
    category: MistakeCategory
    description: str = Field("", description="Human-readable explanation")
    severity: float = Field(0.5, ge=0.0, le=1.0, description="0=minor, 1=critical")
    context: dict[str, Any] = Field(default_factory=dict)


class ReplayAnalysis(BaseModel):
    """Full analysis output for a single replay."""
    replay_id: str
    user_id: str
    title: str = Field(..., description="Game title, e.g. 'madden26'")
    tagged_moments: list[TaggedMoment] = Field(default_factory=list)
    mistakes: list[MistakeClassification] = Field(default_factory=list)
    summary: str = Field("", description="Natural-language recap")
    analyzed_at: datetime = Field(default_factory=datetime.utcnow)


class PatternDetection(BaseModel):
    """A recurring pattern detected across multiple replays."""
    user_id: str
    title: str
    pattern_name: str = Field(..., description="Short label for the pattern")
    description: str = Field("")
    frequency: float = Field(0.0, ge=0.0, le=1.0, description="How often it occurs")
    sessions_scanned: int = Field(0, ge=0)
    evidence_replay_ids: list[str] = Field(default_factory=list)
    detected_at: datetime = Field(default_factory=datetime.utcnow)


class FilmBreakdown(BaseModel):
    """Complete film breakdown combining analysis, mistakes, and patterns."""
    replay_id: str
    analysis: ReplayAnalysis
    key_moments: list[TaggedMoment] = Field(default_factory=list)
    mistake_summary: dict[MistakeCategory, int] = Field(default_factory=dict)
    recommendations: list[str] = Field(default_factory=list)


# ---------------------------------------------------------------------------
# MetaVersion Engine
# ---------------------------------------------------------------------------

class PatchVersion(BaseModel):
    """Semantic patch identifier for a game title."""
    title: str = Field(..., description="Game title")
    version: str = Field(..., description="Patch version string, e.g. '1.04'")
    released_at: datetime = Field(default_factory=datetime.utcnow)
    changelog_notes: list[str] = Field(default_factory=list)


class MetaSnapshot(BaseModel):
    """Frozen snapshot of the meta at a specific patch."""
    title: str
    patch_version: str
    top_strategies: list[str] = Field(default_factory=list)
    tier_list: dict[str, list[str]] = Field(default_factory=dict)
    meta_notes: str = Field("")
    snapshot_at: datetime = Field(default_factory=datetime.utcnow)


class MetaVersionStamp(BaseModel):
    """Version stamp attached to a recommendation."""
    recommendation_id: str
    recommendation_text: str
    patch_version: str
    title: str
    status: AdviceStatus = AdviceStatus.ACTIVE
    stamped_at: datetime = Field(default_factory=datetime.utcnow)


class StaleAdviceAlert(BaseModel):
    """Alert that a recommendation may be outdated."""
    recommendation_id: str
    recommendation_text: str
    stamped_patch: str
    current_patch: str
    title: str
    reason: str = Field("", description="Why the advice may be stale")
    detected_at: datetime = Field(default_factory=datetime.utcnow)


# ---------------------------------------------------------------------------
# Onboarding Intelligence
# ---------------------------------------------------------------------------

class OnboardingStep(BaseModel):
    """A single step in the onboarding flow."""
    step_number: int = Field(..., ge=1, le=3)
    phase: OnboardingPhase
    completed: bool = False
    insights: dict[str, Any] = Field(default_factory=dict)
    completed_at: datetime | None = None


class OnboardingProfile(BaseModel):
    """Tracks a user's onboarding journey for a title."""
    user_id: str
    title: str
    current_phase: OnboardingPhase = OnboardingPhase.NOT_STARTED
    steps: list[OnboardingStep] = Field(default_factory=list)
    preliminary_playstyle: str = Field("", description="Early guess at playstyle")
    started_at: datetime = Field(default_factory=datetime.utcnow)
    completed_at: datetime | None = None


class FirstGameplan(BaseModel):
    """Initial gameplan generated after onboarding completes."""
    user_id: str
    title: str
    recommended_strategy: str = Field("")
    focus_areas: list[str] = Field(default_factory=list)
    starter_plays: list[str] = Field(default_factory=list)
    confidence: float = Field(0.5, ge=0.0, le=1.0)
    generated_at: datetime = Field(default_factory=datetime.utcnow)
