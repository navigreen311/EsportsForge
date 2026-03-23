"""Schemas for IntegrityMode, Trust Layer, and compliance governance."""

from __future__ import annotations

import enum
from datetime import datetime

from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# Enumerations — the four compliance axes
# ---------------------------------------------------------------------------

class Environment(str, enum.Enum):
    """Where a feature is allowed to operate."""
    OFFLINE_LAB = "offline_lab"
    RANKED_ONLINE = "ranked_online"
    TOURNAMENT = "tournament"
    BROADCAST = "broadcast"


class Timing(str, enum.Enum):
    """When a feature may be used relative to a match."""
    PRE_GAME = "pre_game"
    BETWEEN_SERIES = "between_series"
    POST_GAME = "post_game"
    NEVER = "never"


class RiskLevel(str, enum.Enum):
    """How risky a feature is from a competitive-integrity standpoint."""
    SAFE = "safe"
    USE_WITH_CAUTION = "use_with_caution"
    TOURNAMENT_RESTRICTED = "tournament_restricted"
    DISABLED = "disabled"


class AntiCheatStatus(str, enum.Enum):
    """Anti-cheat verification status for the feature."""
    VERIFIED_SAFE = "verified_safe"
    UNDER_REVIEW = "under_review"
    BLOCKED = "blocked"


# ---------------------------------------------------------------------------
# Feature compliance (one entry in the 4-axis matrix)
# ---------------------------------------------------------------------------

class FeatureCompliance(BaseModel):
    """Four-axis compliance tag for a single feature."""
    feature_name: str
    environments: list[Environment] = Field(
        description="Environments where this feature is permitted.",
    )
    timings: list[Timing] = Field(
        description="Match-timing windows where this feature is permitted.",
    )
    risk_level: RiskLevel
    anti_cheat_status: AntiCheatStatus


# ---------------------------------------------------------------------------
# Integrity settings / results
# ---------------------------------------------------------------------------

class IntegritySettings(BaseModel):
    """Current compliance mode for a user session."""
    user_id: str
    environment: Environment
    timing: Timing
    enforced: bool = True
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class ComplianceResult(BaseModel):
    """Result of checking whether a feature may run."""
    feature_name: str
    allowed: bool
    reason: str = ""
    environment: Environment
    timing: Timing
    risk_level: RiskLevel
    anti_cheat_status: AntiCheatStatus


class FilteredOutput(BaseModel):
    """Agent output after compliance filtering."""
    original_keys: list[str] = Field(
        description="Keys present in the original agent output.",
    )
    output: dict
    redacted_keys: list[str] = Field(
        default_factory=list,
        description="Keys removed or masked by the compliance filter.",
    )
    mode: IntegritySettings


# ---------------------------------------------------------------------------
# Privacy / Trust
# ---------------------------------------------------------------------------

class DataPermission(str, enum.Enum):
    """Granular data-sharing permission flags."""
    SHARE_STATS = "share_stats"
    SHARE_REPLAYS = "share_replays"
    SHARE_GAMEPLANS = "share_gameplans"
    SHARE_TENDENCIES = "share_tendencies"
    ALLOW_ANALYTICS = "allow_analytics"
    ALLOW_BROADCAST = "allow_broadcast"


class PrivacySettings(BaseModel):
    """A user's data-sharing and privacy preferences."""
    user_id: str
    permissions: dict[DataPermission, bool] = Field(
        default_factory=lambda: {p: False for p in DataPermission},
        description="Explicit opt-in / opt-out for each data category.",
    )
    opted_in_at: datetime | None = None
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class AuditEvent(BaseModel):
    """Single entry in the audit trail."""
    event_id: str
    action: str
    user_id: str
    details: str = ""
    timestamp: datetime = Field(default_factory=datetime.utcnow)


# ---------------------------------------------------------------------------
# Request / Response helpers for the API layer
# ---------------------------------------------------------------------------

class SetModeRequest(BaseModel):
    """Body for PUT /integrity/mode."""
    environment: Environment
    timing: Timing


class UpdatePrivacyRequest(BaseModel):
    """Body for PUT /trust/privacy."""
    permissions: dict[DataPermission, bool]


class ComplianceMatrixResponse(BaseModel):
    """Full compliance matrix returned by GET /integrity/matrix."""
    features: list[FeatureCompliance]
