"""Pydantic schemas for Streamer/Analyst Mode."""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------

class OverlayLayout(str, Enum):
    """Available overlay layout presets."""
    COMPACT = "compact"
    FULL = "full"
    MINIMAL = "minimal"


class OverlayTheme(str, Enum):
    """Overlay color themes."""
    DARK = "dark"
    LIGHT = "light"
    CUSTOM = "custom"


class ClipFormat(str, Enum):
    """Supported clip export formats."""
    MP4 = "mp4"
    GIF = "gif"
    WEBM = "webm"
    PNG = "png"


class ExportStatus(str, Enum):
    """Status of an export job."""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


# ---------------------------------------------------------------------------
# Overlay Config
# ---------------------------------------------------------------------------

class OverlayConfig(BaseModel):
    """Broadcast overlay configuration for a streamer."""
    user_id: str = Field(..., description="Streamer/analyst user ID")
    enabled: bool = Field(False, description="Whether overlay is active")
    layout: str = Field("compact", description="Layout preset")
    theme: str = Field("dark", description="Color theme")
    position: str = Field("top-right", description="Screen position")
    opacity: float = Field(0.85, ge=0.0, le=1.0, description="Overlay opacity")
    show_stats: list[str] = Field(
        default_factory=list,
        description="Which stats to display on overlay",
    )
    show_confidence: bool = Field(True, description="Show AI confidence scores")
    show_meta_tier: bool = Field(True, description="Show meta tier info")
    auto_hide_timeout_seconds: int = Field(10, ge=0, description="Auto-hide delay")
    created_at: str = Field("", description="Creation timestamp")
    updated_at: str = Field("", description="Last update timestamp")


# ---------------------------------------------------------------------------
# Post-Game Export
# ---------------------------------------------------------------------------

class SessionSummary(BaseModel):
    """Summary stats for a game session."""
    result: str = Field("pending", description="Win/loss/draw")
    total_plays: int = Field(0, ge=0)
    key_decisions: int = Field(0, ge=0)
    ai_accuracy: float = Field(0.0, ge=0.0, le=1.0)


class PostGameExport(BaseModel):
    """Exportable post-game breakdown."""
    export_id: str = Field(..., description="Unique export identifier")
    session_id: str = Field(..., description="Source session ID")
    status: str = Field("generated")
    summary: SessionSummary = Field(default_factory=SessionSummary)
    key_moments: list[dict[str, Any]] = Field(default_factory=list)
    stat_lines: dict[str, Any] = Field(default_factory=dict)
    recommendations_used: list[str] = Field(default_factory=list)
    export_formats_available: list[str] = Field(default_factory=list)
    generated_at: str = Field("", description="Generation timestamp")


# ---------------------------------------------------------------------------
# Clips
# ---------------------------------------------------------------------------

class Clip(BaseModel):
    """A single clip in the queue."""
    clip_id: str = Field(..., description="Clip identifier")
    title: str = Field("", description="Clip title")
    timestamp: float = Field(0.0, ge=0.0, description="Timestamp in session")
    duration_seconds: float = Field(0.0, ge=0.0)
    tags: list[str] = Field(default_factory=list)


class ClipQueue(BaseModel):
    """User's clip queue."""
    user_id: str
    clips: list[dict[str, Any]] = Field(default_factory=list)
    total_clips: int = Field(0, ge=0)
    retrieved_at: str = Field("")


class ClipExport(BaseModel):
    """Result of a clip export operation."""
    clip_id: str
    format: str
    status: str = Field("processing")
    download_url: str = Field("")
    estimated_size_mb: float = Field(0.0, ge=0.0)
    exported_at: str = Field("")
