"""IntegrityMode — enforces four-axis compliance at the ForgeCore level.

No feature ever operates outside its permitted context.  Every agent output
passes through ``enforce()`` before reaching the user.
"""

from __future__ import annotations

import functools
from datetime import datetime

from app.schemas.integrity import (
    ComplianceResult,
    Environment,
    FeatureCompliance,
    FilteredOutput,
    IntegritySettings,
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
# Descriptor: sync on class access, async on instance access
# ---------------------------------------------------------------------------

class _InstanceAsync:
    """Return the sync fn when accessed from the class; async bound method from an instance."""

    def __init__(self, sync_fn, async_fn):
        self._sync = sync_fn
        self._async = async_fn

    def __get__(self, obj, objtype=None):
        if obj is None:
            return self._sync
        return functools.partial(self._async, obj)


# ---------------------------------------------------------------------------
# Module-level sync implementations (reused by both call paths)
# ---------------------------------------------------------------------------

def _get_active_mode_impl(user_id: str) -> IntegritySettings:
    if user_id in _user_modes:
        return _user_modes[user_id]
    default = IntegritySettings(
        user_id=user_id,
        environment=Environment.OFFLINE_LAB,
        timing=Timing.PRE_GAME,
    )
    _user_modes[user_id] = default
    return default


def _set_mode_impl(
    user_id: str,
    environment: Environment,
    timing: Timing,
) -> IntegritySettings:
    mode = IntegritySettings(
        user_id=user_id,
        environment=environment,
        timing=timing,
        enforced=True,
        updated_at=datetime.utcnow(),
    )
    _user_modes[user_id] = mode
    return mode


# ---------------------------------------------------------------------------
# IntegrityMode service
# ---------------------------------------------------------------------------

class IntegrityMode:
    """Compliance gatekeeper for every feature in EsportsForge."""

    def __init__(self, db=None, claude_client=None):
        self.db = db
        self.claude_client = claude_client

    # -- Async instance variants (used when db is injected) -----------------

    async def _get_active_mode_async(self, user_id: str) -> IntegritySettings:
        if self.db is not None:
            from sqlalchemy import select
            from app.models.integrity_mode import IntegrityMode as _IMModel

            result = await self.db.execute(
                select(_IMModel).where(_IMModel.user_id == user_id)
            )
            row = result.scalar_one_or_none()
            if row is not None:
                try:
                    env = Environment(row.environment.value)
                except ValueError:
                    env = Environment.OFFLINE_LAB
                mode = IntegritySettings(
                    user_id=user_id,
                    environment=env,
                    timing=Timing.PRE_GAME,
                )
                _user_modes[user_id] = mode
                return mode
        return _get_active_mode_impl(user_id)

    async def _set_mode_async(
        self,
        user_id: str,
        environment: Environment,
        timing: Timing,
    ) -> IntegritySettings:
        mode = _set_mode_impl(user_id, environment, timing)
        if self.db is not None:
            self.db.add(mode)
            await self.db.flush()
        return mode

    # -- Mode management (sync from class, async from instance) -------------

    get_active_mode = _InstanceAsync(_get_active_mode_impl, _get_active_mode_async)
    set_mode = _InstanceAsync(_set_mode_impl, _set_mode_async)

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
