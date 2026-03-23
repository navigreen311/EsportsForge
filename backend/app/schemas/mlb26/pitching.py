"""Pydantic schemas for PitchForge — pitch sequencing, tunneling, batter tendencies."""

from __future__ import annotations

import enum
from typing import Any, Optional

from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------

class PitchType(str, enum.Enum):
    FOUR_SEAM = "four_seam"
    TWO_SEAM = "two_seam"
    CUTTER = "cutter"
    SLIDER = "slider"
    CURVEBALL = "curveball"
    CHANGEUP = "changeup"
    SINKER = "sinker"
    SPLITTER = "splitter"
    KNUCKLE_CURVE = "knuckle_curve"


class SequenceStrategy(str, enum.Enum):
    TUNNEL = "tunnel"
    PUTAWAY = "putaway"
    GROUNDBALL = "groundball"
    STRIKEOUT = "strikeout"
    SETUP = "setup"


# ---------------------------------------------------------------------------
# Pitch location
# ---------------------------------------------------------------------------

class PitchLocation(BaseModel):
    """A pitch location in the strike zone grid."""
    zone: int = Field(..., ge=1, le=14, description="Zone 1-9 strike zone, 10-13 chase, 14 waste")
    x: float | None = Field(None, description="Normalized x position")
    y: float | None = Field(None, description="Normalized y position")


# ---------------------------------------------------------------------------
# Pitch sequence
# ---------------------------------------------------------------------------

class PitchSequence(BaseModel):
    """An AI-generated pitch sequence for an at-bat."""
    pitches: list[dict[str, Any]] = Field(..., description="Ordered pitch calls with type, zone, intent")
    strategy: SequenceStrategy
    strikeout_probability: float = Field(..., ge=0, le=1.0)
    batter_hand: str = Field(..., description="RHH or LHH")
    count: str
    notes: str


# ---------------------------------------------------------------------------
# Tunnel pair
# ---------------------------------------------------------------------------

class TunnelPair(BaseModel):
    """A pair of pitches that create deceptive tunneling."""
    pitch_a: PitchType
    pitch_b: PitchType
    tunnel_score: float = Field(..., ge=0, le=1.0)
    velo_diff: float
    movement_diff_h: float
    movement_diff_v: float
    deception_rating: str = Field(..., description="elite, strong, average")
    description: str


class TunnelReport(BaseModel):
    """Complete tunnel analysis for a pitcher's arsenal."""
    arsenal: list[PitchType]
    pairs: list[TunnelPair]
    best_pair: TunnelPair | None = None
    recommendation: str


# ---------------------------------------------------------------------------
# Batter tendency
# ---------------------------------------------------------------------------

class BatterTendency(BaseModel):
    """Batter tendency scouting report."""
    batter_id: str
    sample_size: int
    hot_zones: list[int] = Field(default_factory=list, description="Zones where batter hits well")
    cold_zones: list[int] = Field(default_factory=list, description="Zones where batter struggles")
    chase_rate: float = Field(..., ge=0, le=1.0)
    whiff_pitches: list[str] = Field(default_factory=list)
    tendency_notes: list[str] = Field(default_factory=list)


# ---------------------------------------------------------------------------
# Zone heatmap
# ---------------------------------------------------------------------------

class ZoneHeatmap(BaseModel):
    """9-zone performance heatmap for a batter."""
    batter_id: str
    zones: dict[int, dict[str, float]] = Field(
        ..., description="Zone -> {avg, swing_rate, contact_rate}"
    )
    sample_size: int
