"""Four-axis compliance matrix — the source of truth for feature permissions.

Every feature in EsportsForge carries a compliance tag with four axes:
  1. Environment   (where)
  2. Timing        (when)
  3. Risk Level    (how risky)
  4. Anti-Cheat    (verification status)

The COMPLIANCE_REGISTRY is pre-populated for all Phase 1 backbone agents and
Madden 26 modules.  New features MUST register here before they can operate.
"""

from __future__ import annotations

from app.schemas.integrity import (
    AntiCheatStatus,
    ComplianceResult,
    Environment,
    FeatureCompliance,
    RiskLevel,
    Timing,
)

# ---------------------------------------------------------------------------
# Phase 1 feature registry
# ---------------------------------------------------------------------------

COMPLIANCE_REGISTRY: dict[str, FeatureCompliance] = {
    # ── Backbone agents ────────────────────────────────────────────────
    "forge_data_fabric": FeatureCompliance(
        feature_name="forge_data_fabric",
        environments=[Environment.OFFLINE_LAB, Environment.RANKED_ONLINE, Environment.TOURNAMENT, Environment.BROADCAST],
        timings=[Timing.PRE_GAME, Timing.BETWEEN_SERIES, Timing.POST_GAME],
        risk_level=RiskLevel.SAFE,
        anti_cheat_status=AntiCheatStatus.VERIFIED_SAFE,
    ),
    "forge_core": FeatureCompliance(
        feature_name="forge_core",
        environments=[Environment.OFFLINE_LAB, Environment.RANKED_ONLINE, Environment.TOURNAMENT, Environment.BROADCAST],
        timings=[Timing.PRE_GAME, Timing.BETWEEN_SERIES, Timing.POST_GAME],
        risk_level=RiskLevel.SAFE,
        anti_cheat_status=AntiCheatStatus.VERIFIED_SAFE,
    ),
    "player_twin": FeatureCompliance(
        feature_name="player_twin",
        environments=[Environment.OFFLINE_LAB, Environment.RANKED_ONLINE],
        timings=[Timing.PRE_GAME, Timing.POST_GAME],
        risk_level=RiskLevel.USE_WITH_CAUTION,
        anti_cheat_status=AntiCheatStatus.VERIFIED_SAFE,
    ),
    "impact_rank": FeatureCompliance(
        feature_name="impact_rank",
        environments=[Environment.OFFLINE_LAB, Environment.RANKED_ONLINE, Environment.TOURNAMENT],
        timings=[Timing.PRE_GAME, Timing.BETWEEN_SERIES, Timing.POST_GAME],
        risk_level=RiskLevel.SAFE,
        anti_cheat_status=AntiCheatStatus.VERIFIED_SAFE,
    ),
    "truth_engine": FeatureCompliance(
        feature_name="truth_engine",
        environments=[Environment.OFFLINE_LAB, Environment.RANKED_ONLINE],
        timings=[Timing.POST_GAME],
        risk_level=RiskLevel.SAFE,
        anti_cheat_status=AntiCheatStatus.VERIFIED_SAFE,
    ),
    "loop_ai": FeatureCompliance(
        feature_name="loop_ai",
        environments=[Environment.OFFLINE_LAB],
        timings=[Timing.PRE_GAME, Timing.POST_GAME],
        risk_level=RiskLevel.USE_WITH_CAUTION,
        anti_cheat_status=AntiCheatStatus.UNDER_REVIEW,
    ),
    # ── Madden 26 modules ──────────────────────────────────────────────
    "madden26_gameplan": FeatureCompliance(
        feature_name="madden26_gameplan",
        environments=[Environment.OFFLINE_LAB, Environment.RANKED_ONLINE, Environment.TOURNAMENT],
        timings=[Timing.PRE_GAME, Timing.BETWEEN_SERIES],
        risk_level=RiskLevel.SAFE,
        anti_cheat_status=AntiCheatStatus.VERIFIED_SAFE,
    ),
    "madden26_tendencies": FeatureCompliance(
        feature_name="madden26_tendencies",
        environments=[Environment.OFFLINE_LAB, Environment.RANKED_ONLINE],
        timings=[Timing.PRE_GAME, Timing.POST_GAME],
        risk_level=RiskLevel.USE_WITH_CAUTION,
        anti_cheat_status=AntiCheatStatus.VERIFIED_SAFE,
    ),
    "madden26_adjustments": FeatureCompliance(
        feature_name="madden26_adjustments",
        environments=[Environment.OFFLINE_LAB, Environment.RANKED_ONLINE],
        timings=[Timing.PRE_GAME, Timing.BETWEEN_SERIES],
        risk_level=RiskLevel.TOURNAMENT_RESTRICTED,
        anti_cheat_status=AntiCheatStatus.UNDER_REVIEW,
    ),
    "madden26_film_room": FeatureCompliance(
        feature_name="madden26_film_room",
        environments=[Environment.OFFLINE_LAB, Environment.RANKED_ONLINE, Environment.TOURNAMENT, Environment.BROADCAST],
        timings=[Timing.PRE_GAME, Timing.BETWEEN_SERIES, Timing.POST_GAME],
        risk_level=RiskLevel.SAFE,
        anti_cheat_status=AntiCheatStatus.VERIFIED_SAFE,
    ),
    "madden26_roster_intel": FeatureCompliance(
        feature_name="madden26_roster_intel",
        environments=[Environment.OFFLINE_LAB, Environment.RANKED_ONLINE, Environment.TOURNAMENT],
        timings=[Timing.PRE_GAME, Timing.BETWEEN_SERIES, Timing.POST_GAME],
        risk_level=RiskLevel.SAFE,
        anti_cheat_status=AntiCheatStatus.VERIFIED_SAFE,
    ),
    # ── CFB 26 modules ─────────────────────────────────────────────────
    "cfb26_gameplan": FeatureCompliance(
        feature_name="cfb26_gameplan",
        environments=[Environment.OFFLINE_LAB, Environment.RANKED_ONLINE, Environment.TOURNAMENT],
        timings=[Timing.PRE_GAME, Timing.BETWEEN_SERIES],
        risk_level=RiskLevel.SAFE,
        anti_cheat_status=AntiCheatStatus.VERIFIED_SAFE,
    ),
    "cfb26_tendencies": FeatureCompliance(
        feature_name="cfb26_tendencies",
        environments=[Environment.OFFLINE_LAB, Environment.RANKED_ONLINE],
        timings=[Timing.PRE_GAME, Timing.POST_GAME],
        risk_level=RiskLevel.USE_WITH_CAUTION,
        anti_cheat_status=AntiCheatStatus.VERIFIED_SAFE,
    ),
}


# ---------------------------------------------------------------------------
# Public helpers
# ---------------------------------------------------------------------------

def get_feature(feature_name: str) -> FeatureCompliance | None:
    """Return the compliance entry for *feature_name*, or ``None``."""
    return COMPLIANCE_REGISTRY.get(feature_name)


def validate_feature(
    feature_name: str,
    environment: Environment,
    timing: Timing,
) -> ComplianceResult:
    """Check all four axes for *feature_name* in a given context.

    Returns a ``ComplianceResult`` indicating whether the feature is allowed
    and, if not, the reason it was blocked.
    """
    entry = COMPLIANCE_REGISTRY.get(feature_name)

    if entry is None:
        return ComplianceResult(
            feature_name=feature_name,
            allowed=False,
            reason=f"Feature '{feature_name}' is not registered in the compliance matrix.",
            environment=environment,
            timing=timing,
            risk_level=RiskLevel.DISABLED,
            anti_cheat_status=AntiCheatStatus.BLOCKED,
        )

    # Axis 1 — Environment
    if environment not in entry.environments:
        return ComplianceResult(
            feature_name=feature_name,
            allowed=False,
            reason=f"Feature '{feature_name}' is not permitted in environment '{environment.value}'.",
            environment=environment,
            timing=timing,
            risk_level=entry.risk_level,
            anti_cheat_status=entry.anti_cheat_status,
        )

    # Axis 2 — Timing
    if timing not in entry.timings:
        return ComplianceResult(
            feature_name=feature_name,
            allowed=False,
            reason=f"Feature '{feature_name}' is not permitted during timing '{timing.value}'.",
            environment=environment,
            timing=timing,
            risk_level=entry.risk_level,
            anti_cheat_status=entry.anti_cheat_status,
        )

    # Axis 3 — Risk level
    if entry.risk_level == RiskLevel.DISABLED:
        return ComplianceResult(
            feature_name=feature_name,
            allowed=False,
            reason=f"Feature '{feature_name}' is currently disabled.",
            environment=environment,
            timing=timing,
            risk_level=entry.risk_level,
            anti_cheat_status=entry.anti_cheat_status,
        )

    if entry.risk_level == RiskLevel.TOURNAMENT_RESTRICTED and environment == Environment.TOURNAMENT:
        return ComplianceResult(
            feature_name=feature_name,
            allowed=False,
            reason=f"Feature '{feature_name}' is tournament-restricted.",
            environment=environment,
            timing=timing,
            risk_level=entry.risk_level,
            anti_cheat_status=entry.anti_cheat_status,
        )

    # Axis 4 — Anti-cheat
    if entry.anti_cheat_status == AntiCheatStatus.BLOCKED:
        return ComplianceResult(
            feature_name=feature_name,
            allowed=False,
            reason=f"Feature '{feature_name}' is blocked by anti-cheat.",
            environment=environment,
            timing=timing,
            risk_level=entry.risk_level,
            anti_cheat_status=entry.anti_cheat_status,
        )

    # All axes pass
    return ComplianceResult(
        feature_name=feature_name,
        allowed=True,
        reason="Compliant.",
        environment=environment,
        timing=timing,
        risk_level=entry.risk_level,
        anti_cheat_status=entry.anti_cheat_status,
    )
