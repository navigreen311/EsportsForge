"""Pydantic schemas for subscription tier management."""

from __future__ import annotations

from pydantic import BaseModel, Field


class SubscriptionTier(BaseModel):
    """Represents a subscription tier with its metadata."""

    name: str = Field(..., description="Tier name (free, competitive, elite, team)")
    display_name: str = Field(..., description="Human-readable tier name")
    price_monthly: float = Field(..., description="Monthly price in USD")
    price_yearly: float = Field(..., description="Yearly price in USD")
    description: str = Field(..., description="Tier description")
    is_current: bool = Field(default=False, description="Whether this is the user's current tier")


class TierFeatures(BaseModel):
    """Features available for a given tier."""

    tier: str = Field(..., description="Tier name")
    features: list[str] = Field(default_factory=list, description="List of feature keys")
    title_limit: int | None = Field(
        default=None,
        description="Max number of game titles (null = unlimited)",
    )
    seat_limit: int | None = Field(
        default=None,
        description="Max number of team seats (null = single user)",
    )
    ai_agents: list[str] = Field(
        default_factory=list,
        description="AI agent names available at this tier",
    )


class TierLimits(BaseModel):
    """Rate and usage limits per tier."""

    tier: str
    api_requests_per_minute: int = Field(..., description="API rate limit per minute")
    api_requests_per_day: int = Field(..., description="API rate limit per day")
    ai_queries_per_day: int = Field(..., description="AI agent queries per day")
    max_gameplans: int = Field(..., description="Max stored gameplans")
    max_kill_sheets: int = Field(..., description="Max stored kill sheets")
    max_opponent_dossiers: int = Field(..., description="Max stored opponent dossiers")
    storage_gb: float = Field(..., description="Cloud storage allocation in GB")


class UpgradePrompt(BaseModel):
    """Prompt returned when a user hits a tier gate."""

    current_tier: str = Field(..., description="User's current subscription tier")
    required_tier: str = Field(..., description="Minimum tier required for this feature")
    feature: str | None = Field(default=None, description="Feature that triggered the gate")
    message: str = Field(..., description="Human-readable upgrade prompt")
    upgrade_url: str = Field(
        default="/api/v1/subscription/upgrade",
        description="URL to upgrade subscription",
    )
    available_tiers: list[SubscriptionTier] = Field(
        default_factory=list,
        description="Tiers available for upgrade",
    )


# ---------------------------------------------------------------------------
# Predefined tier configurations
# ---------------------------------------------------------------------------

FREE_FEATURES = TierFeatures(
    tier="free",
    features=["basic_gameplan", "meta_alerts"],
    title_limit=1,
    seat_limit=None,
    ai_agents=["ForgeCore (basic)"],
)

COMPETITIVE_FEATURES = TierFeatures(
    tier="competitive",
    features=[
        "basic_gameplan",
        "meta_alerts",
        "full_ai_agents",
        "player_twin",
        "film_ai",
        "tilt_guard",
        "benchmark_ai",
        "install_ai",
    ],
    title_limit=3,
    seat_limit=None,
    ai_agents=[
        "ForgeCore",
        "PlayerTwin",
        "FilmAI",
        "TiltGuard",
        "BenchmarkAI",
        "InstallAI",
    ],
)

ELITE_FEATURES = TierFeatures(
    tier="elite",
    features=[
        "basic_gameplan",
        "meta_alerts",
        "full_ai_agents",
        "player_twin",
        "film_ai",
        "tilt_guard",
        "benchmark_ai",
        "install_ai",
        "full_platform",
        "tourna_ops",
        "voice_forge",
        "forge_vault",
        "impact_rank_priority",
    ],
    title_limit=None,
    seat_limit=None,
    ai_agents=[
        "ForgeCore",
        "PlayerTwin",
        "FilmAI",
        "TiltGuard",
        "BenchmarkAI",
        "InstallAI",
        "TournaOps",
        "VoiceForge",
        "ForgeVault",
        "ImpactRank (priority)",
    ],
)

TEAM_FEATURES = TierFeatures(
    tier="team",
    features=[
        "basic_gameplan",
        "meta_alerts",
        "full_ai_agents",
        "player_twin",
        "film_ai",
        "tilt_guard",
        "benchmark_ai",
        "install_ai",
        "full_platform",
        "tourna_ops",
        "voice_forge",
        "forge_vault",
        "impact_rank_priority",
        "coach_portal",
        "war_room",
        "squad_ops",
        "shared_playbooks",
    ],
    title_limit=None,
    seat_limit=6,
    ai_agents=[
        "ForgeCore",
        "PlayerTwin",
        "FilmAI",
        "TiltGuard",
        "BenchmarkAI",
        "InstallAI",
        "TournaOps",
        "VoiceForge",
        "ForgeVault",
        "ImpactRank (priority)",
        "Coach Portal",
        "War Room",
        "SquadOps",
    ],
)

FREE_LIMITS = TierLimits(
    tier="free",
    api_requests_per_minute=20,
    api_requests_per_day=500,
    ai_queries_per_day=10,
    max_gameplans=3,
    max_kill_sheets=1,
    max_opponent_dossiers=2,
    storage_gb=0.5,
)

COMPETITIVE_LIMITS = TierLimits(
    tier="competitive",
    api_requests_per_minute=60,
    api_requests_per_day=5000,
    ai_queries_per_day=100,
    max_gameplans=25,
    max_kill_sheets=10,
    max_opponent_dossiers=20,
    storage_gb=5.0,
)

ELITE_LIMITS = TierLimits(
    tier="elite",
    api_requests_per_minute=120,
    api_requests_per_day=20000,
    ai_queries_per_day=500,
    max_gameplans=100,
    max_kill_sheets=50,
    max_opponent_dossiers=100,
    storage_gb=25.0,
)

TEAM_LIMITS = TierLimits(
    tier="team",
    api_requests_per_minute=300,
    api_requests_per_day=100000,
    ai_queries_per_day=2000,
    max_gameplans=500,
    max_kill_sheets=200,
    max_opponent_dossiers=500,
    storage_gb=100.0,
)
