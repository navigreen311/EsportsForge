"""Tests for NBA 2K26 gameplay agents — ShotForge, PositioningAI, DribbleForge, MomentumManager."""

from __future__ import annotations

import pytest

from app.schemas.nba2k26.gameplay import (
    CourtPosition,
    DefensiveRole,
    DribbleMoveType,
    MomentumPhase,
    ShotFeedback,
    ShotType,
    TimingGrade,
)
from app.services.agents.nba2k26.dribble_forge import DribbleForge
from app.services.agents.nba2k26.momentum_manager import MomentumManager
from app.services.agents.nba2k26.positioning_ai import PositioningAI
from app.services.agents.nba2k26.shot_forge import ShotForge


# ===========================================================================
# ShotForge tests
# ===========================================================================

@pytest.fixture
def shot_engine() -> ShotForge:
    return ShotForge()


class TestShotTimingAnalysis:
    """Tests for ShotForge.analyze_timing."""

    def test_known_base_returns_timing(self, shot_engine: ShotForge) -> None:
        result = shot_engine.analyze_timing("user1", "Ray Allen")
        assert result.green_window_ms > 0
        assert result.optimal_release_ms > 0
        assert result.jump_shot_base == "Ray Allen"

    def test_fast_speed_reduces_window(self, shot_engine: ShotForge) -> None:
        normal = shot_engine.analyze_timing("u1", "Base 98", release_speed="normal")
        fast = shot_engine.analyze_timing("u2", "Base 98", release_speed="fast")
        assert fast.optimal_release_ms < normal.optimal_release_ms

    def test_unknown_base_uses_defaults(self, shot_engine: ShotForge) -> None:
        result = shot_engine.analyze_timing("u1", "Unknown Base XYZ")
        assert result.green_window_ms > 0


class TestShotRecording:
    """Tests for ShotForge.record_shot."""

    def test_record_updates_stats(self, shot_engine: ShotForge) -> None:
        fb = ShotFeedback(
            shot_type=ShotType.JUMPER, timing_grade=TimingGrade.EXCELLENT,
            release_ms=500.0, was_green=True, was_make=True,
        )
        result = shot_engine.record_shot("user1", fb)
        assert result.samples == 1
        assert result.make_percentage == 1.0
        assert result.green_percentage == 1.0

    def test_multiple_shots_average_correctly(self, shot_engine: ShotForge) -> None:
        for i in range(4):
            fb = ShotFeedback(
                shot_type=ShotType.JUMPER, timing_grade=TimingGrade.EXCELLENT,
                release_ms=500.0, was_green=i < 2, was_make=i < 3,
            )
            shot_engine.record_shot("user1", fb)
        result = shot_engine.record_shot("user1", ShotFeedback(
            shot_type=ShotType.JUMPER, timing_grade=TimingGrade.LATE,
            release_ms=550.0, was_green=False, was_make=False,
        ))
        assert result.samples == 5
        assert 0.0 < result.make_percentage < 1.0


class TestShotTrainingPlan:
    """Tests for ShotForge.generate_training_plan."""

    def test_plan_has_drills(self, shot_engine: ShotForge) -> None:
        plan = shot_engine.generate_training_plan("user1")
        assert len(plan.drills) > 0
        assert len(plan.focus_areas) > 0

    def test_early_releaser_gets_targeted_advice(self, shot_engine: ShotForge) -> None:
        for _ in range(10):
            shot_engine.record_shot("user1", ShotFeedback(
                shot_type=ShotType.JUMPER, timing_grade=TimingGrade.EARLY,
                release_ms=400.0, was_green=False, was_make=False,
            ))
        plan = shot_engine.generate_training_plan("user1")
        assert any("early" in d.lower() or "hold" in d.lower() for d in plan.focus_areas + plan.drills)


class TestShotBaseComparison:
    """Tests for ShotForge.compare_shot_bases."""

    def test_compare_returns_recommendation(self, shot_engine: ShotForge) -> None:
        result = shot_engine.compare_shot_bases("Ray Allen", "Larry Bird")
        assert result["recommendation"] in ("Ray Allen", "Larry Bird")
        assert "green_window_diff_ms" in result


# ===========================================================================
# PositioningAI tests
# ===========================================================================

@pytest.fixture
def pos_engine() -> PositioningAI:
    return PositioningAI()


class TestPositionEvaluation:
    """Tests for PositioningAI.evaluate_position."""

    def test_on_ball_near_man_gets_high_grade(self, pos_engine: PositioningAI) -> None:
        result = pos_engine.evaluate_position(
            "user1", DefensiveRole.ON_BALL,
            current=CourtPosition(x=28.0, y=25.0),
            ball_position=CourtPosition(x=30.0, y=25.0),
            man_position=CourtPosition(x=30.0, y=25.0),
        )
        assert result.rotation_grade > 0.5
        assert len(result.recommendations) > 0

    def test_far_from_optimal_gets_low_grade(self, pos_engine: PositioningAI) -> None:
        result = pos_engine.evaluate_position(
            "user1", DefensiveRole.HELP_SIDE,
            current=CourtPosition(x=80.0, y=45.0),
            ball_position=CourtPosition(x=30.0, y=25.0),
            man_position=CourtPosition(x=25.0, y=10.0),
        )
        assert result.rotation_grade < 0.3
        assert result.distance_off_optimal_ft > 10.0


class TestPnRCoverage:
    """Tests for PositioningAI.analyze_pnr_coverage."""

    def test_drop_coverage_analysis(self, pos_engine: PositioningAI) -> None:
        result = pos_engine.analyze_pnr_coverage(
            "drop",
            ball_handler=CourtPosition(x=30.0, y=25.0),
            screener=CourtPosition(x=28.0, y=23.0),
            defender_on_ball=CourtPosition(x=29.0, y=25.0),
            defender_on_screener=CourtPosition(x=19.0, y=25.0),
        )
        assert result.coverage_type == "drop"
        assert 0.0 <= result.coverage_grade <= 1.0
        assert len(result.coaching_tips) > 0

    def test_high_breakdown_risk_flagged(self, pos_engine: PositioningAI) -> None:
        result = pos_engine.analyze_pnr_coverage(
            "blitz",
            ball_handler=CourtPosition(x=30.0, y=25.0),
            screener=CourtPosition(x=28.0, y=23.0),
            defender_on_ball=CourtPosition(x=50.0, y=10.0),
            defender_on_screener=CourtPosition(x=10.0, y=40.0),
        )
        assert result.breakdown_risk > 0.5


class TestRotationTracking:
    """Tests for PositioningAI.record_rotation."""

    def test_rotation_accuracy_tracks(self, pos_engine: PositioningAI) -> None:
        pos_engine.record_rotation("user1", True, 500.0, DefensiveRole.HELP_SIDE)
        pos_engine.record_rotation("user1", True, 600.0, DefensiveRole.HELP_SIDE)
        result = pos_engine.record_rotation("user1", False, 900.0, DefensiveRole.HELP_SIDE)
        assert result.rotations_analyzed == 3
        assert result.correct_rotations == 2
        assert 0.6 < result.rotation_accuracy < 0.7


# ===========================================================================
# DribbleForge tests
# ===========================================================================

@pytest.fixture
def dribble_engine() -> DribbleForge:
    return DribbleForge()


class TestDribbleCombos:
    """Tests for DribbleForge combo access."""

    def test_get_all_combos(self, dribble_engine: DribbleForge) -> None:
        combos = dribble_engine.get_combos(min_ball_handle=99)
        assert len(combos) > 0

    def test_filter_by_ball_handle(self, dribble_engine: DribbleForge) -> None:
        combos = dribble_engine.get_combos(min_ball_handle=75)
        for c in combos:
            assert c.min_ball_handle <= 75

    def test_get_combo_by_name(self, dribble_engine: DribbleForge) -> None:
        combo = dribble_engine.get_combo_by_name("Hesi-Cross-Stepback")
        assert combo is not None
        assert len(combo.moves) >= 2


class TestIsolationCounters:
    """Tests for DribbleForge isolation counters."""

    def test_known_tendency_returns_counters(self, dribble_engine: DribbleForge) -> None:
        counters = dribble_engine.get_isolation_counters("reaches")
        assert len(counters) > 0
        assert counters[0].success_rate > 0.0

    def test_unknown_tendency_returns_default(self, dribble_engine: DribbleForge) -> None:
        counters = dribble_engine.get_isolation_counters("does_backflips")
        assert len(counters) > 0


class TestDribbleMastery:
    """Tests for DribbleForge mastery tracking."""

    def test_record_iso_updates_mastery(self, dribble_engine: DribbleForge) -> None:
        mastery = dribble_engine.record_iso_attempt("user1", "Hesi-Cross-Stepback", True, 3.5)
        assert mastery.isolation_win_rate == 1.0
        assert mastery.avg_separation_created_ft == 3.5

    def test_multiple_attempts_average(self, dribble_engine: DribbleForge) -> None:
        dribble_engine.record_iso_attempt("user1", "Hesi-Cross-Stepback", True, 4.0)
        dribble_engine.record_iso_attempt("user1", "Hesi-Cross-Stepback", False, 1.0)
        mastery = dribble_engine.record_iso_attempt("user1", "Hesi-Cross-Stepback", True, 3.0)
        assert 0.6 < mastery.isolation_win_rate < 0.7
        assert mastery.pro_comparison != ""

    def test_pro_comparison_returns_data(self, dribble_engine: DribbleForge) -> None:
        for _ in range(5):
            dribble_engine.record_iso_attempt("user1", "Hesi-Cross-Stepback", True, 4.0)
        result = dribble_engine.compare_to_pro("user1", "Kyrie Irving")
        assert "iso_win_rate_diff" in result
        assert "areas_to_improve" in result


# ===========================================================================
# MomentumManager tests
# ===========================================================================

@pytest.fixture
def momentum_engine() -> MomentumManager:
    return MomentumManager()


class TestMomentumTracking:
    """Tests for MomentumManager.update_momentum."""

    def test_neutral_game_is_neutral(self, momentum_engine: MomentumManager) -> None:
        state = momentum_engine.update_momentum("game1", 1, "6:00", 10, 10)
        assert -0.3 < state.momentum_value < 0.3
        assert state.phase in (MomentumPhase.NEUTRAL, MomentumPhase.BUILDING)

    def test_big_lead_gives_positive_momentum(self, momentum_engine: MomentumManager) -> None:
        state = momentum_engine.update_momentum("game1", 3, "5:00", 60, 35)
        assert state.momentum_value > 0.5

    def test_big_deficit_gives_negative_momentum(self, momentum_engine: MomentumManager) -> None:
        state = momentum_engine.update_momentum("game1", 3, "5:00", 35, 60)
        assert state.momentum_value < -0.3

    def test_consecutive_scores_boost_momentum(self, momentum_engine: MomentumManager) -> None:
        state = momentum_engine.update_momentum(
            "game1", 2, "3:00", 30, 25,
            consecutive_scores=5, consecutive_stops=0,
        )
        assert state.run_active is True


class TestRunDetection:
    """Tests for MomentumManager.detect_run."""

    def test_no_history_no_run(self, momentum_engine: MomentumManager) -> None:
        result = momentum_engine.detect_run("game1")
        assert result.run_detected is False

    def test_user_run_detected(self, momentum_engine: MomentumManager) -> None:
        momentum_engine.update_momentum("game1", 2, "6:00", 20, 20)
        momentum_engine.update_momentum(
            "game1", 2, "4:00", 30, 20,
            consecutive_scores=4,
        )
        result = momentum_engine.detect_run("game1")
        assert result.run_detected is True
        assert result.run_type == "user_run"


class TestTimeoutDecision:
    """Tests for MomentumManager.should_call_timeout."""

    def test_no_timeout_when_stable(self, momentum_engine: MomentumManager) -> None:
        momentum_engine.update_momentum("game1", 2, "6:00", 30, 28)
        result = momentum_engine.should_call_timeout("game1")
        assert result.should_call_timeout is False

    def test_timeout_during_collapse(self, momentum_engine: MomentumManager) -> None:
        momentum_engine.update_momentum("game1", 3, "5:00", 40, 55)
        momentum_engine.update_momentum("game1", 3, "3:00", 40, 62)
        result = momentum_engine.should_call_timeout("game1")
        assert result.urgency > 0.5


class TestComebackProtocol:
    """Tests for MomentumManager.generate_comeback_protocol."""

    def test_small_deficit_gets_normal_pace(self, momentum_engine: MomentumManager) -> None:
        result = momentum_engine.generate_comeback_protocol(5, 420.0)
        assert result.pace_recommendation in ("normal", "slow")
        assert result.win_probability > 0.0

    def test_large_deficit_gets_frantic_pace(self, momentum_engine: MomentumManager) -> None:
        result = momentum_engine.generate_comeback_protocol(18, 90.0)
        assert result.pace_recommendation == "frantic"
        assert len(result.defensive_adjustments) > 0

    def test_comeback_has_strategy_phases(self, momentum_engine: MomentumManager) -> None:
        result = momentum_engine.generate_comeback_protocol(12, 300.0)
        assert len(result.strategy_phases) > 0
        assert len(result.recommended_plays) > 0
        assert len(result.key_thresholds) > 0
