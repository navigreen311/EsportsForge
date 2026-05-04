"""Pydantic schemas for the Secret Weapon Arsenal."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field

Difficulty = Literal["easy", "medium", "hard"]
SourceType = Literal["platform", "user-upload", "web-discovery"]
WeaponSide = Literal["offense", "defense"]


class WeaponBase(BaseModel):
    title_id: str
    side: WeaponSide = "offense"
    name: str
    category: str
    sub_category: str | None = None
    formation: str | None = None
    play_name: str | None = None
    description: str
    instructions: list[str] = Field(default_factory=list)
    setup_steps: list[str] = Field(default_factory=list)
    when_to_use: str
    trigger_conditions: dict[str, Any] = Field(default_factory=dict)
    difficulty: Difficulty = "medium"
    title_specific_data: dict[str, Any] = Field(default_factory=dict)
    patch_version: str | None = None
    source_type: SourceType = "platform"
    source_url: str | None = None
    video_url: str | None = None
    thumbnail_url: str | None = None
    tags: list[str] = Field(default_factory=list)
    verified: bool = False


class WeaponCreate(WeaponBase):
    """Body for POST /weapons (user-created upload)."""


class WeaponUpdate(BaseModel):
    side: WeaponSide | None = None
    name: str | None = None
    category: str | None = None
    sub_category: str | None = None
    formation: str | None = None
    play_name: str | None = None
    description: str | None = None
    instructions: list[str] | None = None
    setup_steps: list[str] | None = None
    when_to_use: str | None = None
    trigger_conditions: dict[str, Any] | None = None
    difficulty: Difficulty | None = None
    tags: list[str] | None = None
    verified: bool | None = None


class WeaponResponse(WeaponBase):
    model_config = ConfigDict(from_attributes=True)

    id: str
    user_id: str | None = None
    success_rate: float
    times_used: int
    community_rating: float
    community_votes: int
    saved: bool = False
    created_at: datetime
    updated_at: datetime


class UsageLogCreate(BaseModel):
    weapon_id: str
    session_id: str | None = None
    title_id: str
    game_state: dict[str, Any] | None = None
    deployed: bool = False
    worked: bool | None = None
    outcome: Literal["yes", "no", "not-used"] | None = None
    opponent_adjusted: bool = False
    notes: str | None = None


class UsageLogResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    weapon_id: str
    deployed: bool
    worked: bool | None
    created_at: datetime


class WeaponRateBody(BaseModel):
    stars: int = Field(ge=1, le=5)
