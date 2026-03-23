"""Pydantic schemas for user profile and management."""

import uuid
from datetime import datetime

from pydantic import BaseModel, EmailStr, Field


class UserUpdate(BaseModel):
    """Schema for updating user profile."""
    display_name: str | None = Field(default=None, max_length=100)
    username: str | None = Field(default=None, min_length=3, max_length=50, pattern=r"^[a-zA-Z0-9_-]+$")
    email: EmailStr | None = None


class UserProfile(BaseModel):
    """Full user profile (visible to the user themselves)."""
    id: uuid.UUID
    email: str
    username: str
    display_name: str | None
    tier: str
    title_limit: int | None
    is_active: bool
    is_verified: bool
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class UserPublic(BaseModel):
    """Public user info (visible to other users)."""
    id: uuid.UUID
    username: str
    display_name: str | None
    tier: str
    created_at: datetime

    model_config = {"from_attributes": True}
