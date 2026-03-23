"""Pydantic schemas for Cross-Title Cognitive Transfer Engine."""

from __future__ import annotations

from datetime import datetime
from enum import Enum

from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------

class SkillCategory(str, Enum):
    """Cognitive skill categories that can transfer between titles."""

    REACTION_TIME = "reaction_time"
    PATTERN_RECOGNITION = "pattern_recognition"
    SPATIAL_AWARENESS = "spatial_awareness"
    DECISION_SPEED = "decision_speed"
    RESOURCE_MANAGEMENT = "resource_management"
    OPPONENT_READING = "opponent_reading"
    ADAPTATION = "adaptation"
    MECHANICAL = "mechanical"
    STRATEGIC = "strategic"
    COMMUNICATION = "communication"


class TransferGrade(str, Enum):
    """How well a skill transfers between two titles."""

    DIRECT = "direct"          # Near 1:1 transfer
    HIGH = "high"              # Strong transfer with minor adaptation
    MODERATE = "moderate"      # Transfers with notable differences
    LOW = "low"                # Minimal transfer, mostly re-learn
    NONE = "none"              # No meaningful transfer


# ---------------------------------------------------------------------------
# Core Models
# ---------------------------------------------------------------------------

class CognitiveSkill(BaseModel):
    """A cognitive skill that can potentially transfer between titles."""

    skill_id: str
    name: str
    category: SkillCategory
    description: str = ""
    titles: list[str] = Field(
        default_factory=list,
        description="Game titles where this skill is relevant.",
    )
    proficiency: float = Field(
        default=0.0,
        ge=0.0,
        le=1.0,
        description="Current proficiency level 0-1.",
    )


class TransferMap(BaseModel):
    """Mapping of how a cognitive skill transfers between two titles."""

    skill: str
    category: SkillCategory
    from_title: str
    to_title: str
    transfer_grade: TransferGrade
    transfer_rate: float = Field(
        ge=0.0,
        le=1.0,
        description="Expected transfer rate 0-1.",
    )
    adaptation_notes: str = Field(
        default="",
        description="What needs to change when transferring this skill.",
    )
    estimated_hours_to_adapt: float = Field(
        default=0.0,
        description="Estimated hours to fully adapt this skill to the new title.",
    )


class TitleSwitch(BaseModel):
    """Recommendation package for switching to a new title."""

    user_id: str
    from_title: str
    to_title: str
    transferable_skills: list[TransferMap] = Field(default_factory=list)
    skills_to_learn: list[str] = Field(
        default_factory=list,
        description="Skills that must be learned fresh for the new title.",
    )
    estimated_onboarding_hours: float = Field(
        default=0.0,
        description="Total estimated hours to become competitive.",
    )
    head_start_percentage: float = Field(
        default=0.0,
        ge=0.0,
        le=1.0,
        description="How much of a head start existing skills provide.",
    )
    priority_order: list[str] = Field(
        default_factory=list,
        description="Recommended skill acquisition order.",
    )
    generated_at: datetime = Field(default_factory=datetime.utcnow)


class CrossTitleProfile(BaseModel):
    """Player's cognitive profile across all titles they play."""

    user_id: str
    titles_played: list[str] = Field(default_factory=list)
    cognitive_skills: list[CognitiveSkill] = Field(default_factory=list)
    strongest_category: SkillCategory | None = None
    weakest_category: SkillCategory | None = None
    versatility_score: float = Field(
        default=0.0,
        ge=0.0,
        le=1.0,
        description="How well skills transfer across titles overall.",
    )
    recommended_titles: list[str] = Field(
        default_factory=list,
        description="Titles the player would excel at based on cognitive profile.",
    )
    last_assessed: datetime = Field(default_factory=datetime.utcnow)
