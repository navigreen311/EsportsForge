"""Unit tests for IntegrityMode and the four-axis compliance matrix."""

import pytest

from app.schemas.integrity import (
    AntiCheatStatus,
    ComplianceResult,
    Environment,
    RiskLevel,
    Timing,
)
from app.services.backbone.integrity_mode import IntegrityMode, _user_modes
from app.services.backbone.mode_integrity_matrix import (
    COMPLIANCE_REGISTRY,
    validate_feature,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture(autouse=True)
def _clear_state():
    """Reset in-memory stores between tests."""
    _user_modes.clear()
    yield
    _user_modes.clear()


# ---------------------------------------------------------------------------
# Mode management
# ---------------------------------------------------------------------------

class TestModeManagement:
    """Tests for get_active_mode / set_mode."""

    def test_default_mode_is_offline_lab_pre_game(self):
        mode = IntegrityMode.get_active_mode("user-1")
        assert mode.user_id == "user-1"
        assert mode.environment == Environment.OFFLINE_LAB
        assert mode.timing == Timing.PRE_GAME
        assert mode.enforced is True

    def test_set_mode_persists(self):
        IntegrityMode.set_mode("user-2", Environment.TOURNAMENT, Timing.BETWEEN_SERIES)
        mode = IntegrityMode.get_active_mode("user-2")
        assert mode.environment == Environment.TOURNAMENT
        assert mode.timing == Timing.BETWEEN_SERIES

    def test_set_mode_overwrites_previous(self):
        IntegrityMode.set_mode("user-3", Environment.RANKED_ONLINE, Timing.PRE_GAME)
        IntegrityMode.set_mode("user-3", Environment.BROADCAST, Timing.POST_GAME)
        mode = IntegrityMode.get_active_mode("user-3")
        assert mode.environment == Environment.BROADCAST
        assert mode.timing == Timing.POST_GAME


# ---------------------------------------------------------------------------
# Compliance checks
# ---------------------------------------------------------------------------

class TestComplianceChecks:
    """Tests for check_feature_compliance."""

    def test_safe_feature_in_allowed_context(self):
        mode = IntegrityMode.set_mode("u1", Environment.OFFLINE_LAB, Timing.PRE_GAME)
        result = IntegrityMode.check_feature_compliance("forge_data_fabric", mode)
        assert result.allowed is True
        assert result.risk_level == RiskLevel.SAFE

    def test_feature_blocked_by_environment(self):
        mode = IntegrityMode.set_mode("u1", Environment.BROADCAST, Timing.PRE_GAME)
        result = IntegrityMode.check_feature_compliance("player_twin", mode)
        assert result.allowed is False
        assert "environment" in result.reason.lower()

    def test_feature_blocked_by_timing(self):
        mode = IntegrityMode.set_mode("u1", Environment.OFFLINE_LAB, Timing.BETWEEN_SERIES)
        result = IntegrityMode.check_feature_compliance("truth_engine", mode)
        assert result.allowed is False
        assert "timing" in result.reason.lower()

    def test_tournament_restricted_blocked_in_tournament(self):
        mode = IntegrityMode.set_mode("u1", Environment.TOURNAMENT, Timing.PRE_GAME)
        result = IntegrityMode.check_feature_compliance("madden26_adjustments", mode)
        assert result.allowed is False
        assert "tournament-restricted" in result.reason.lower()

    def test_tournament_restricted_allowed_in_ranked(self):
        mode = IntegrityMode.set_mode("u1", Environment.RANKED_ONLINE, Timing.PRE_GAME)
        result = IntegrityMode.check_feature_compliance("madden26_adjustments", mode)
        assert result.allowed is True

    def test_unregistered_feature_blocked(self):
        mode = IntegrityMode.set_mode("u1", Environment.OFFLINE_LAB, Timing.PRE_GAME)
        result = IntegrityMode.check_feature_compliance("nonexistent_feature", mode)
        assert result.allowed is False
        assert "not registered" in result.reason.lower()


# ---------------------------------------------------------------------------
# Restricted features list
# ---------------------------------------------------------------------------

class TestRestrictedFeatures:
    """Tests for get_restricted_features."""

    def test_offline_lab_has_fewest_restrictions(self):
        mode = IntegrityMode.set_mode("u1", Environment.OFFLINE_LAB, Timing.PRE_GAME)
        blocked = IntegrityMode.get_restricted_features(mode)
        # truth_engine only allows POST_GAME timing
        assert "truth_engine" in blocked

    def test_tournament_has_more_restrictions(self):
        mode_offline = IntegrityMode.set_mode("u1", Environment.OFFLINE_LAB, Timing.PRE_GAME)
        mode_tourney = IntegrityMode.set_mode("u2", Environment.TOURNAMENT, Timing.PRE_GAME)
        blocked_offline = IntegrityMode.get_restricted_features(mode_offline)
        blocked_tourney = IntegrityMode.get_restricted_features(mode_tourney)
        assert len(blocked_tourney) >= len(blocked_offline)


# ---------------------------------------------------------------------------
# Enforcement (output filtering)
# ---------------------------------------------------------------------------

class TestEnforcement:
    """Tests for enforce()."""

    def test_allowed_keys_pass_through(self):
        mode = IntegrityMode.set_mode("u1", Environment.OFFLINE_LAB, Timing.PRE_GAME)
        output = {"forge_data_fabric": {"data": "ok"}, "greeting": "hello"}
        filtered = IntegrityMode.enforce(output, mode)
        assert "forge_data_fabric" in filtered.output
        assert "greeting" in filtered.output

    def test_blocked_keys_are_redacted(self):
        mode = IntegrityMode.set_mode("u1", Environment.BROADCAST, Timing.PRE_GAME)
        output = {"player_twin": {"secret": "data"}, "forge_core": {"ok": True}}
        filtered = IntegrityMode.enforce(output, mode)
        assert "player_twin" in filtered.redacted_keys
        assert "player_twin" not in filtered.output
        assert "forge_core" in filtered.output

    def test_original_keys_always_listed(self):
        mode = IntegrityMode.set_mode("u1", Environment.OFFLINE_LAB, Timing.PRE_GAME)
        output = {"a": 1, "b": 2}
        filtered = IntegrityMode.enforce(output, mode)
        assert filtered.original_keys == ["a", "b"]


# ---------------------------------------------------------------------------
# Compliance matrix
# ---------------------------------------------------------------------------

class TestComplianceMatrix:
    """Tests for get_compliance_matrix."""

    def test_matrix_returns_all_registered_features(self):
        matrix = IntegrityMode.get_compliance_matrix()
        assert len(matrix) == len(COMPLIANCE_REGISTRY)
        for name in COMPLIANCE_REGISTRY:
            assert name in matrix

    def test_matrix_entries_have_four_axes(self):
        matrix = IntegrityMode.get_compliance_matrix()
        for entry in matrix.values():
            assert entry.environments is not None
            assert entry.timings is not None
            assert entry.risk_level is not None
            assert entry.anti_cheat_status is not None


# ---------------------------------------------------------------------------
# validate_feature (matrix-level)
# ---------------------------------------------------------------------------

class TestValidateFeature:
    """Direct tests for the matrix validate_feature helper."""

    def test_all_registered_features_have_valid_enums(self):
        for entry in COMPLIANCE_REGISTRY.values():
            assert all(isinstance(e, Environment) for e in entry.environments)
            assert all(isinstance(t, Timing) for t in entry.timings)
            assert isinstance(entry.risk_level, RiskLevel)
            assert isinstance(entry.anti_cheat_status, AntiCheatStatus)

    def test_validate_returns_compliance_result(self):
        result = validate_feature("forge_core", Environment.OFFLINE_LAB, Timing.PRE_GAME)
        assert isinstance(result, ComplianceResult)
