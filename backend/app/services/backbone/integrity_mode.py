"""IntegrityMode — enforces four-axis compliance at the ForgeCore level.

No feature ever operates outside its permitted context.  Every agent output
passes through ``enforce()`` before reaching the user.
"""

from __future__ import annotations

import uuid as _uuid
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.integrity_mode import (
    AntiCheatStatus,
    GameEnvironment,
    IntegrityMode as IntegrityModeModel,
)
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


# Map between schema enums and model enums
_ENV_TO_MODEL: dict[Environment, GameEnvironment] = {
    Environment.OFFLINE_LAB: GameEnvironment.OFFLINE_LAB,
    Environment.RANKED: GameEnvironment.RANKED,
    Environment.TOURNAMENT: GameEnvironment.TOURNAMENT,
    Environment.BROADCAST: GameEnvironment.BROADCAST,
}
_MODEL_TO_ENV: dict[GameEnvironment, Environment] = {v: k for k, v in _ENV_TO_MODEL.items()}


# ---------------------------------------------------------------------------
# In-memory fallback store
# ---------------------------------------------------------------------------
_user_modes: dict[str, IntegritySettings] = {}


# ---------------------------------------------------------------------------
# IntegrityMode service
# ---------------------------------------------------------------------------

class IntegrityMode:
    """Compliance gatekeeper for every feature in EsportsForge."""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    # -- Mode management ----------------------------------------------------

    async def get_active_mode(self, user_id: str) -> IntegritySettings:
        """Return the current compliance mode for *user_id* from DB.

        Defaults to the safest possible mode (offline lab, pre-game) when no
        mode has been explicitly set.
        """
        # Query DB
        try:
            uid = _uuid.UUID(user_id)
            result = await self.db.execute(
                select(IntegrityModeModel).where(IntegrityModeModel.user_id == uid)
            )
            db_mode = result.scalar_one_or_none()
            if db_mode:
                env = _MODEL_TO_ENV.get(db_mode.environment, Environment.OFFLINE_LAB)
                return IntegritySettings(
                    user_id=user_id,
                    environment=env,
                    timing=Timing.PRE_GAME,
                    enforced=True,
                )
        except (ValueError, Exception):
            pass

        # Fallback to in-memory
        if user_id in _user_modes:
            return _user_modes[user_id]

        default = IntegritySettings(
            user_id=user_id,
            environment=Environment.OFFLINE_LAB,
            timing=Timing.PRE_GAME,
        )
        _user_modes[user_id] = default
        return default

    async def set_mode(
        self,
        user_id: str,
        environment: Environment,
        timing: Timing,
    ) -> IntegritySettings:
        """Set the active compliance mode for *user_id* and persist to DB."""
        mode = IntegritySettings(
            user_id=user_id,
            environment=environment,
            timing=timing,
            enforced=True,
            updated_at=datetime.utcnow(),
        )
        _user_modes[user_id] = mode

        # Persist to database
        try:
            uid = _uuid.UUID(user_id)
            model_env = _ENV_TO_MODEL.get(environment, GameEnvironment.OFFLINE_LAB)
            result = await self.db.execute(
                select(IntegrityModeModel).where(IntegrityModeModel.user_id == uid)
            )
            db_mode = result.scalar_one_or_none()
            if db_mode:
                db_mode.environment = model_env
            else:
                db_mode = IntegrityModeModel(
                    user_id=uid,
                    environment=model_env,
                    anti_cheat_status=AntiCheatStatus.COMPLIANT,
                )
                self.db.add(db_mode)
            await self.db.flush()
        except (ValueError, Exception):
            pass

        return mode

    # -- Compliance checks --------------------------------------------------

    @staticmethod
    def check_feature_compliance(
        feature_name: str,
        mode: IntegritySettings,
    ) -> ComplianceResult:
        """Can *feature_name* run under the given *mode*?"""
        return validate_feature(feature_name, mode.environment, mode.timing)

    def get_restricted_features(self, mode: IntegritySettings) -> list[str]:
        """Return feature names that are **blocked** under *mode*."""
        blocked: list[str] = []
        for name in COMPLIANCE_REGISTRY:
            result = validate_feature(name, mode.environment, mode.timing)
            if not result.allowed:
                blocked.append(name)
        return blocked

    # -- Output enforcement -------------------------------------------------

    def enforce(
        self,
        agent_output: dict,
        mode: IntegritySettings,
    ) -> FilteredOutput:
        """Filter *agent_output* through the compliance layer.

        Keys whose names match a blocked feature are redacted from the output.
        """
        restricted = set(self.get_restricted_features(mode))
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
