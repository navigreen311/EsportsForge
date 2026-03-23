"""Unit tests for the Dynamic Calibration Engine."""

from __future__ import annotations

import pytest

from app.schemas.simulation import (
    CalibrationConfig,
    CalibrationDirection,
    CalibrationLevel,
    DifficultyAdjustment,
)
from app.services.backbone import dynamic_calibration


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture(autouse=True)
def _clear_state():
    """Reset in-memory stores between tests."""
    dynamic_calibration._calibrations.clear()
    dynamic_calibration._history.clear()
    yield


# ===========================================================================
# calibrate
# ===========================================================================

class TestCalibrate:
    def test_sets_difficulty_above_ceiling(self):
        cfg = dynamic_calibration.calibrate("u1", "zone_read", current_ceiling=0.60)
        assert isinstance(cfg, CalibrationConfig)
        assert cfg.difficulty_value > 0.60

    def test_clamps_at_max(self):
        cfg = dynamic_calibration.calibrate("u1", "zone_read", current_ceiling=0.99)
        assert cfg.difficulty_value <= 1.0

    def test_assigns_correct_level(self):
        cfg = dynamic_calibration.calibrate("u1", "blitz", current_ceiling=0.80)
        assert cfg.level in (CalibrationLevel.ELITE, CalibrationLevel.MASTER)

    def test_low_ceiling_gives_low_level(self):
        cfg = dynamic_calibration.calibrate("u1", "basics", current_ceiling=0.10)
        assert cfg.level in (CalibrationLevel.BEGINNER, CalibrationLevel.DEVELOPING)


# ===========================================================================
# get_calibration_level
# ===========================================================================

class TestGetCalibrationLevel:
    def test_returns_default_for_new_user(self):
        cfg = dynamic_calibration.get_calibration_level("new_user", "passing")
        assert cfg.level == CalibrationLevel.INTERMEDIATE
        assert cfg.difficulty_value == 0.40

    def test_returns_existing_config(self):
        dynamic_calibration.calibrate("u1", "rushing", current_ceiling=0.70)
        cfg = dynamic_calibration.get_calibration_level("u1", "rushing")
        assert cfg.difficulty_value > 0.70


# ===========================================================================
# adjust_after_rep
# ===========================================================================

class TestAdjustAfterRep:
    def test_success_increases_difficulty(self):
        dynamic_calibration.get_calibration_level("u1", "sk1")  # init
        adj = dynamic_calibration.adjust_after_rep("u1", "sk1", success=True)
        assert isinstance(adj, DifficultyAdjustment)
        assert adj.new_difficulty >= adj.previous_difficulty
        assert adj.direction == CalibrationDirection.UP

    def test_failure_decreases_difficulty(self):
        dynamic_calibration.get_calibration_level("u1", "sk1")
        adj = dynamic_calibration.adjust_after_rep("u1", "sk1", success=False)
        assert adj.new_difficulty <= adj.previous_difficulty
        assert adj.direction == CalibrationDirection.DOWN

    def test_streak_success_bumps_harder(self):
        dynamic_calibration.get_calibration_level("u1", "sk1")
        for _ in range(4):
            dynamic_calibration.adjust_after_rep("u1", "sk1", success=True)
        # 5th success triggers streak bump
        adj = dynamic_calibration.adjust_after_rep("u1", "sk1", success=True)
        assert "streak" in adj.reason.lower()

    def test_streak_failure_dials_back(self):
        dynamic_calibration.get_calibration_level("u1", "sk1")
        for _ in range(2):
            dynamic_calibration.adjust_after_rep("u1", "sk1", success=False)
        # 3rd failure triggers streak dial-back
        adj = dynamic_calibration.adjust_after_rep("u1", "sk1", success=False)
        assert "streak" in adj.reason.lower()
        assert adj.direction == CalibrationDirection.DOWN

    def test_total_reps_increments(self):
        dynamic_calibration.adjust_after_rep("u1", "sk1", success=True)
        dynamic_calibration.adjust_after_rep("u1", "sk1", success=False)
        cfg = dynamic_calibration.get_calibration_level("u1", "sk1")
        assert cfg.total_reps == 2

    def test_difficulty_stays_in_bounds(self):
        # Push difficulty high with many successes
        for _ in range(30):
            dynamic_calibration.adjust_after_rep("u1", "sk1", success=True)
        cfg = dynamic_calibration.get_calibration_level("u1", "sk1")
        assert cfg.difficulty_value <= 1.0

        # Push difficulty low with many failures
        for _ in range(60):
            dynamic_calibration.adjust_after_rep("u2", "sk1", success=False)
        cfg2 = dynamic_calibration.get_calibration_level("u2", "sk1")
        assert cfg2.difficulty_value >= 0.0


# ===========================================================================
# detect_coasting
# ===========================================================================

class TestDetectCoasting:
    def test_not_coasting_with_few_reps(self):
        dynamic_calibration.adjust_after_rep("u1", "sk1", success=True)
        assert dynamic_calibration.detect_coasting("u1", "sk1") is False

    def test_coasting_when_always_succeeding(self):
        for _ in range(10):
            dynamic_calibration.adjust_after_rep("u1", "sk1", success=True)
        assert dynamic_calibration.detect_coasting("u1", "sk1") is True

    def test_not_coasting_with_mixed_results(self):
        for i in range(10):
            dynamic_calibration.adjust_after_rep("u1", "sk1", success=(i % 3 != 0))
        assert dynamic_calibration.detect_coasting("u1", "sk1") is False


# ===========================================================================
# detect_frustration
# ===========================================================================

class TestDetectFrustration:
    def test_not_frustrated_with_few_reps(self):
        dynamic_calibration.adjust_after_rep("u1", "sk1", success=False)
        assert dynamic_calibration.detect_frustration("u1", "sk1") is False

    def test_frustrated_when_always_failing(self):
        for _ in range(10):
            dynamic_calibration.adjust_after_rep("u1", "sk1", success=False)
        assert dynamic_calibration.detect_frustration("u1", "sk1") is True

    def test_not_frustrated_with_decent_rate(self):
        for i in range(10):
            dynamic_calibration.adjust_after_rep("u1", "sk1", success=(i % 2 == 0))
        assert dynamic_calibration.detect_frustration("u1", "sk1") is False


# ===========================================================================
# get_optimal_challenge_point
# ===========================================================================

class TestOptimalChallengePoint:
    def test_empty_history_returns_default(self):
        result = dynamic_calibration.get_optimal_challenge_point([])
        assert result == 0.40

    def test_high_success_rate_increases_difficulty(self):
        result = dynamic_calibration.get_optimal_challenge_point([0.9, 0.95, 0.88, 0.92])
        assert result > 0.50

    def test_low_success_rate_decreases_difficulty(self):
        result = dynamic_calibration.get_optimal_challenge_point([0.3, 0.25, 0.35, 0.28])
        assert result < 0.50

    def test_at_target_stays_near_center(self):
        result = dynamic_calibration.get_optimal_challenge_point([0.70, 0.70, 0.70])
        assert 0.45 <= result <= 0.55

    def test_result_in_bounds(self):
        result = dynamic_calibration.get_optimal_challenge_point([1.0] * 20)
        assert 0.0 <= result <= 1.0
        result2 = dynamic_calibration.get_optimal_challenge_point([0.0] * 20)
        assert 0.0 <= result2 <= 1.0
