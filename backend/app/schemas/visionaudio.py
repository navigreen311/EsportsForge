"""Pydantic schemas for VisionAudioForge integration services."""

from __future__ import annotations

import enum
from typing import Any, Optional

from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------

class MomentType(str, enum.Enum):
    SCORING_PLAY = "scoring_play"
    TURNOVER = "turnover"
    BIG_PLAY = "big_play"
    MOMENTUM_SHIFT = "momentum_shift"
    FORMATION_CHANGE = "formation_change"
    SUBSTITUTION = "substitution"


class OverlayType(str, enum.Enum):
    FORMATION_LABEL = "formation_label"
    COVERAGE_INDICATOR = "coverage_indicator"
    PLAY_RESULT = "play_result"
    ARROW = "arrow"
    HIGHLIGHT_BOX = "highlight_box"
    TELESTRATOR = "telestrator"


class LootTier(str, enum.Enum):
    COMMON = "common"
    UNCOMMON = "uncommon"
    RARE = "rare"
    EPIC = "epic"
    LEGENDARY = "legendary"
    MYTHIC = "mythic"


# ---------------------------------------------------------------------------
# VisionClient schemas
# ---------------------------------------------------------------------------

class ConnectionStatus(BaseModel):
    connected: bool
    session_id: str | None = None
    endpoint: str | None = None
    error: str | None = None
    features: list[str] = Field(default_factory=list)
    title: str | None = None


class ScreenCaptureResult(BaseModel):
    success: bool
    error: str | None = None
    session_id: str | None = None
    resolution: str | None = None
    processing_time_ms: int = 0
    objects: list[dict[str, Any]] = Field(default_factory=list)
    game_state: dict[str, Any] = Field(default_factory=dict)
    analysis_type: str | None = None


class VideoReplayResult(BaseModel):
    success: bool
    error: str | None = None
    session_id: str | None = None
    duration_sec: float = 0
    frames_analyzed: int = 0
    processing_time_ms: int = 0
    events: list[dict[str, Any]] = Field(default_factory=list)
    highlights: list[dict[str, Any]] = Field(default_factory=list)


class AntiCheatResult(BaseModel):
    title: str
    anti_cheat_system: str
    capture_method: str
    is_compliant: bool
    risk_level: str
    warnings: list[str] = Field(default_factory=list)
    recommendations: list[str] = Field(default_factory=list)


# ---------------------------------------------------------------------------
# FilmVisualAI schemas
# ---------------------------------------------------------------------------

class PlayData(BaseModel):
    play_number: int
    play_type: str
    sub_type: str = "unknown"
    formation: str | None = None
    result: str = "incomplete"
    yards: int = 0
    start_time_sec: float = 0.0
    end_time_sec: float = 0.0
    confidence: float = Field(0.75, ge=0, le=1.0)
    raw_events: list[dict[str, Any]] = Field(default_factory=list)


class KeyMoment(BaseModel):
    moment_type: MomentType
    play_number: int
    timestamp_sec: float
    importance: float = Field(..., ge=0, le=1.0)
    description: str


class ReplayAnalysis(BaseModel):
    plays: list[PlayData] = Field(default_factory=list)
    key_moments: list[KeyMoment] = Field(default_factory=list)
    patterns: list[dict[str, Any]] = Field(default_factory=list)
    summary: str
    total_plays: int = 0


# ---------------------------------------------------------------------------
# FormationRecognition schemas
# ---------------------------------------------------------------------------

class FormationDetection(BaseModel):
    formation: str
    confidence: float = Field(..., ge=0, le=1.0)
    indicators: list[str] = Field(default_factory=list)
    strengths: list[str] = Field(default_factory=list)
    weaknesses: list[str] = Field(default_factory=list)
    personnel: str | None = None


class CoverageShell(BaseModel):
    coverage: str
    confidence: float = Field(..., ge=0, le=1.0)
    description: str
    vulnerable_zones: list[str] = Field(default_factory=list)
    recommended_attacks: list[str] = Field(default_factory=list)


class FormationCounter(BaseModel):
    formation: str
    counter_defense: str
    adjustments: list[str] = Field(default_factory=list)
    key: str


# ---------------------------------------------------------------------------
# VisualTelemetry schemas
# ---------------------------------------------------------------------------

class StickMovementAnalysis(BaseModel):
    total_samples: int
    avg_stick_magnitude: float
    direction_changes: int
    smoothness_score: float = Field(..., ge=0, le=1.0)
    panic_windows: int = 0
    dead_zone_pct: float = 0.0
    context: str = "general"
    notes: list[str] = Field(default_factory=list)


class HesitationWindow(BaseModel):
    start_ms: float
    end_ms: float
    duration_ms: float
    context: str = "unknown"
    severity: str = Field(..., description="minor, moderate, critical")
    recommendation: str | None = None


class TelemetryReport(BaseModel):
    stick_analysis: StickMovementAnalysis
    hesitations: list[HesitationWindow] = Field(default_factory=list)
    hesitation_count: int = 0
    avg_reaction_time_ms: float = 0.0
    reaction_grade: str = "no_data"
    context: str = "general"


# ---------------------------------------------------------------------------
# SceneReader schemas
# ---------------------------------------------------------------------------

class ZonePositionRead(BaseModel):
    title: str
    zone: str
    available_zones: list[str] = Field(default_factory=list)
    details: dict[str, Any] = Field(default_factory=dict)
    advice: list[str] = Field(default_factory=list)


class SquadLocation(BaseModel):
    title: str
    alive_count: int
    downed_count: int = 0
    centroid_x: float
    centroid_y: float
    max_spread: float
    spread_rating: str
    members: list[dict[str, Any]] = Field(default_factory=list)
    advice: list[str] = Field(default_factory=list)


class LootTierDetection(BaseModel):
    title: str
    detected_color: str
    tier: str
    rarity: int = Field(..., ge=0, le=6)
    value_score: float = Field(..., ge=0, le=1.0)
    item_name: str | None = None
    advice: list[str] = Field(default_factory=list)


# ---------------------------------------------------------------------------
# ClipExport schemas
# ---------------------------------------------------------------------------

class OverlayConfig(BaseModel):
    overlay_type: OverlayType
    content: str
    timestamp_sec: float
    duration_sec: float = 3.0
    position: dict[str, float] = Field(default_factory=dict)
    style: dict[str, Any] = Field(default_factory=dict)


class ClipData(BaseModel):
    clip_id: str
    replay_id: str
    start_sec: float
    end_sec: float
    duration_sec: float
    title: str = "Clip"
    tags: list[str] = Field(default_factory=list)
    overlays: list[OverlayConfig] = Field(default_factory=list)
    created_at: str = ""
    resolution: str = "1080p"


class ExportPackage(BaseModel):
    clip_id: str
    format: str
    quality: str
    resolution: str
    duration_sec: float
    include_overlays: bool
    overlay_count: int
    include_audio: bool
    estimated_size_mb: float
    processing_time_sec: float
    export_url: str
    status: str = "ready"
