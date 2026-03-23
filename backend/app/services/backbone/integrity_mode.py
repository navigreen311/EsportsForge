"""IntegrityMode — enforces four-axis compliance at the ForgeCore level.

No feature ever operates outside its permitted context.  Every agent output
passes through ``enforce()`` before reaching the user.
"""

from __future__ import annotations

from datetime import datetime

from app.schemas.integrity import (
    ComplianceResult,
    Environment,
    FeatureCompliance,
    FilteredOutput,
    IntegritySettings,
    RiskLevel,
    Timing,
)
from app.services.backbone.mode_integrity_matrix import (
    COMPLIANCE_REGISTRY,
    validate_feature,
)


# ---------------------------------------------------------------------------
# In-memory store (replaced by DB / Redis in production)
# ---------------------------------------------------------------------------
_user_modes: dict[str, IntegritySettings] = {}


# ---------------------------------------------------------------------------
# IntegrityMode service
# ---------------------------------------------------------------------------

class IntegrityMode:
    """Compliance gatekeeper for every feature in EsportsForge."""

    # -- Mode management ----------------------------------------------------

    @staticmethod
    def get_active_mode(user_id: str) -> IntegritySettings:
        """Return the current compliance mode for *user_id*.

        Defaults to the safest possible mode (offline lab, pre-game) when no
        mode has been explicitly set.
        """
        if user_id in _user_modes:
            return _user_modes[user_id]

        default = IntegritySettings(
            user_id=user_id,
            environment=Environment.OFFLINE_LAB,
            timing=Timing.PRE_GAME,
        )
        _user_modes[user_id] = default
        return default

    @staticmethod
    def set_mode(
        user_id: str,
        environment: Environment,
        timing: Timing,
    ) -> IntegritySettings:
        """Set the active compliance mode for *user_id*."""
        mode = IntegritySettings(
            user_id=user_id,
            environment=environment,
            timing=timing,
            enforced=True,
            updated_at=datetime.utcnow(),
        )
        _user_modes[user_id] = mode
        return mode

    # -- Compliance checks --------------------------------------------------

    @staticmethod
    def check_feature_compliance(
        feature_name: str,
        mode: IntegritySettings,
    ) -> ComplianceResult:
        """Can *feature_name* run under the given *mode*?"""
        return validate_feature(feature_name, mode.environment, mode.timing)

    @staticmethod
    def get_restricted_features(mode: IntegritySettings) -> list[str]:
        """Return feature names that are **blocked** under *mode*."""
        blocked: list[str] = []
        for name in COMPLIANCE_REGISTRY:
            result = validate_feature(name, mode.environment, mode.timing)
            if not result.allowed:
                blocked.append(name)
        return blocked

    # -- Output enforcement -------------------------------------------------

    @staticmethod
    def enforce(
        agent_output: dict,
        mode: IntegritySettings,
    ) -> FilteredOutput:
        """Filter *agent_output* through the compliance layer.

        Keys whose names match a blocked feature are redacted from the output.
        """
        restricted = set(IntegrityMode.get_restricted_features(mode))
        original_keys = list(agent_output.keys())
        redacted_keys: list[str] = []
        filtered: dict = {}

        for key, value in agent_output.items():
            if key in restricted:
                redacted_keys.append(key)
            else:
                filtered[key] = value

        return FilteredOutput(
            original_keys=original_keys,
            output=filtered,
            redacted_keys=redacted_keys,
            mode=mode,
        )

    # -- Matrix introspection -----------------------------------------------

    @staticmethod
    def get_compliance_matrix() -> dict[str, FeatureCompliance]:
        """Return the full four-axis matrix for every registered feature."""
        return dict(COMPLIANCE_REGISTRY)
