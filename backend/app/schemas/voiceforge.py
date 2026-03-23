"""Pydantic schemas for VoiceForge integration — voice briefings, commands, tilt check-ins."""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------

class VoiceToneLevel(str, Enum):
    """Detected voice tone classification."""
    CALM = "calm"
    NEUTRAL = "neutral"
    EXCITED = "excited"
    FRUSTRATED = "frustrated"
    TILTED = "tilted"
    FATIGUED = "fatigued"


class VoiceCommandType(str, Enum):
    """Supported voice command categories."""
    TOURNA_OPS = "tourna_ops"
    DRILL_BOT = "drill_bot"
    SQUAD_OPS = "squad_ops"
    GENERAL = "general"


class BriefingType(str, Enum):
    """Types of voice briefings."""
    BETWEEN_SERIES = "between_series"
    CLOCK_DRILL = "clock_drill"
    PRE_MATCH = "pre_match"
    POST_MATCH = "post_match"


class VoiceOutputFormat(str, Enum):
    """Audio output format."""
    WAV = "wav"
    MP3 = "mp3"
    OGG = "ogg"


# ---------------------------------------------------------------------------
# Voice Configuration
# ---------------------------------------------------------------------------

class VoiceConfig(BaseModel):
    """Configuration for voice synthesis."""
    voice_id: str = Field(default="default", description="VoiceForge voice profile ID")
    speed: float = Field(default=1.0, ge=0.5, le=2.0, description="Playback speed multiplier")
    pitch: float = Field(default=1.0, ge=0.5, le=2.0, description="Pitch adjustment")
    output_format: VoiceOutputFormat = Field(default=VoiceOutputFormat.MP3)
    language: str = Field(default="en-US")


# ---------------------------------------------------------------------------
# Voice Briefing
# ---------------------------------------------------------------------------

class VoiceBriefingRequest(BaseModel):
    """Request for a between-series voice briefing."""
    user_id: str = Field(..., description="Player user ID")
    briefing_type: BriefingType = Field(default=BriefingType.BETWEEN_SERIES)
    voice_config: VoiceConfig = Field(default_factory=VoiceConfig)
    context: dict[str, Any] = Field(default_factory=dict, description="Additional game context")


class VoiceBriefing(BaseModel):
    """Voice briefing output — spoken summary from AdaptAI or ClockAI."""
    briefing_id: str
    user_id: str
    briefing_type: BriefingType
    text_content: str = Field(..., description="Text version of the briefing")
    audio_url: str | None = Field(default=None, description="URL to generated audio")
    duration_seconds: float = Field(..., ge=0, le=30, description="Audio duration (max 30s)")
    generated_at: datetime = Field(default_factory=datetime.utcnow)


# ---------------------------------------------------------------------------
# Voice Commands (TournaOps)
# ---------------------------------------------------------------------------

class VoiceCommandRequest(BaseModel):
    """Incoming voice command from a player."""
    audio_base64: str = Field(..., description="Base64-encoded audio data")
    session_id: str | None = Field(default=None, description="Current session ID")


class VoiceCommand(BaseModel):
    """Parsed voice command result."""
    command_id: str
    raw_transcript: str = Field(..., description="Raw transcription of voice input")
    intent: str = Field(..., description="Detected command intent")
    command_type: VoiceCommandType = Field(default=VoiceCommandType.GENERAL)
    confidence: float = Field(..., ge=0.0, le=1.0, description="Recognition confidence")
    parameters: dict[str, Any] = Field(default_factory=dict)
    processed_at: datetime = Field(default_factory=datetime.utcnow)


class AvailableCommand(BaseModel):
    """A supported voice command definition."""
    intent: str
    phrases: list[str] = Field(..., description="Example trigger phrases")
    command_type: VoiceCommandType
    description: str


# ---------------------------------------------------------------------------
# Voice Check-In (TiltGuard)
# ---------------------------------------------------------------------------

class VoiceCheckInRequest(BaseModel):
    """Request for a voice-based mood check-in."""
    user_id: str
    audio_base64: str = Field(..., description="Base64-encoded audio of player speaking")
    session_id: str | None = None


class VoiceTone(BaseModel):
    """Voice tone analysis result."""
    tone: VoiceToneLevel
    pace_wpm: float = Field(..., ge=0, description="Words per minute")
    energy_level: float = Field(..., ge=0.0, le=1.0, description="Voice energy 0-1")
    stress_indicators: list[str] = Field(default_factory=list)
    confidence: float = Field(..., ge=0.0, le=1.0)


class VoiceCheckIn(BaseModel):
    """Complete voice check-in result for TiltGuard."""
    checkin_id: str
    user_id: str
    tone_analysis: VoiceTone
    mood_label: str = Field(..., description="Derived mood label")
    tilt_risk: float = Field(..., ge=0.0, le=1.0, description="Tilt risk score 0-1")
    recommendation: str | None = Field(default=None, description="Suggested action")
    checked_at: datetime = Field(default_factory=datetime.utcnow)


# ---------------------------------------------------------------------------
# Voice Search
# ---------------------------------------------------------------------------

class VoiceSearchQuery(BaseModel):
    """Voice-based search input."""
    audio_base64: str = Field(..., description="Base64-encoded audio query")
    scope: str = Field(default="all", description="Search scope: all, stats, opponents, drills")
    max_results: int = Field(default=5, ge=1, le=20)


class VoiceSearchResult(BaseModel):
    """Result from a voice-initiated search."""
    query_text: str = Field(..., description="Transcribed search query")
    results: list[dict[str, Any]] = Field(default_factory=list)
    result_count: int = Field(default=0)
    spoken_summary: str | None = Field(default=None, description="TTS summary of results")
    audio_url: str | None = None
