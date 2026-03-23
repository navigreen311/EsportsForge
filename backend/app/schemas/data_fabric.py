"""Pydantic schemas for the ForgeData Fabric — ingestion, entity resolution, and player data."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field

from backend.app.schemas.common import DataQualityReport


# ---------------------------------------------------------------------------
# Ingestion inputs
# ---------------------------------------------------------------------------
class SessionIngest(BaseModel):
    """Payload for ingesting a game session into the data fabric."""

    user_id: str = Field(..., description="Authenticated user ID")
    title: str = Field(..., description="Game title slug (e.g. 'madden26', 'eafc26')")
    mode: str = Field(..., description="Game mode (ranked, casual, tournament, practice)")
    stats: dict[str, Any] = Field(..., description="Title-specific stat block for this session")
    opponent: dict[str, Any] | None = Field(default=None, description="Opponent identifiers and metadata")
    plays: list[dict[str, Any]] = Field(default_factory=list, description="Per-play or per-round breakdown")


class ReplayIngest(BaseModel):
    """Payload for ingesting a replay file or clip."""

    user_id: str = Field(..., description="Authenticated user ID")
    title: str = Field(..., description="Game title slug")
    replay_data: str = Field(..., description="Base64-encoded replay blob or presigned URL")
    format: str = Field(..., description="Replay format identifier (e.g. 'native', 'mp4', 'json')")


# ---------------------------------------------------------------------------
# Entity resolution
# ---------------------------------------------------------------------------
class EntityResolution(BaseModel):
    """Result of resolving an ambiguous player/opponent reference to a canonical ID."""

    matched_id: str = Field(..., description="Canonical entity ID in the data fabric")
    confidence: float = Field(..., ge=0, le=1, description="Match confidence 0-1")
    method: str = Field(
        ...,
        description="Resolution method used (e.g. 'exact_gamertag', 'fuzzy_name', 'play_style_fingerprint')",
    )


# ---------------------------------------------------------------------------
# Clean data responses
# ---------------------------------------------------------------------------
class PlayerDataResponse(BaseModel):
    """Cleaned and enriched player data returned by the fabric."""

    profile: dict[str, Any] = Field(..., description="Canonical player profile")
    sessions: list[dict[str, Any]] = Field(default_factory=list, description="Recent session summaries")
    trends: dict[str, Any] = Field(default_factory=dict, description="Computed trend vectors and deltas")
    quality_score: DataQualityReport


class OpponentDataResponse(BaseModel):
    """Cleaned opponent data and scouting dossier."""

    dossier: dict[str, Any] = Field(..., description="Opponent profile and scouting summary")
    encounters: list[dict[str, Any]] = Field(default_factory=list, description="Past head-to-head sessions")
    tendencies: dict[str, Any] = Field(default_factory=dict, description="Identified opponent tendencies")


# ---------------------------------------------------------------------------
# Ingestion result
# ---------------------------------------------------------------------------
class IngestResult(BaseModel):
    """Acknowledgement returned after successful data ingestion."""

    success: bool = Field(..., description="Whether ingestion completed without critical errors")
    quality_score: float = Field(..., ge=0, le=1, description="Quality assessment of the ingested data")
    warnings: list[str] = Field(default_factory=list, description="Non-fatal issues encountered")
    stored_id: str = Field(..., description="ID of the stored record in the data fabric")
