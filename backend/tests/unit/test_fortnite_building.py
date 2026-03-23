"""Tests for BuildForge FN and EditForge — build sequences, edit speed, anti-cheat."""

from __future__ import annotations

import pytest

from app.schemas.fortnite.gameplay import (
    AntiCheatFlag,
    BuildSequenceAnalysis,
    BuildType,
    EditAttempt,
    EditShape,
    MasteryTier,
)
from app.services.agents.fortnite.build_forge import BuildForgeFN
from app.services.agents.fortnite.edit_forge import EditForge


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def build_engine() -> BuildForgeFN:
    """Fresh BuildForgeFN instance per test."""
    return BuildForgeFN()


@pytest.fixture
def edit_engine() -> EditForge:
    """Fresh EditForge instance per test."""
    return EditForge()


# ===========================================================================
# BuildForge FN tests
# ===========================================================================

class TestBuildForgeFN:
    """Tests for BuildForgeFN agent."""

    def test_get_sequence_template(self, build_engine: BuildForgeFN) -> None:
        """Sequence template returns correct steps for ramp-wall."""
        template = build_engine.get_sequence_template(BuildType.RAMP_WALL)
        assert len(template) == 4
        assert template[0].action == "place wall"
        assert template[1].action == "place ramp"

    def test_get_target_time(self, build_engine: BuildForgeFN) -> None:
        """Target time sums all step targets."""
        target = build_engine.get_target_time(BuildType.RAMP_WALL)
        assert target == 320  # 80 + 60 + 120 + 60

    def test_analyze_sequence_basic(self, build_engine: BuildForgeFN) -> None:
        """Basic sequence analysis returns valid result."""
        result = build_engine.analyze_sequence(
            user_id="test-user",
            build_type=BuildType.RAMP_WALL,
            step_times_ms=[100, 80, 150, 80],
            placement_hits=3,
            placement_total=4,
        )
        assert result.user_id == "test-user"
        assert result.build_type == BuildType.RAMP_WALL
        assert result.total_time_ms == 410
        assert result.target_time_ms == 320
        assert 0.0 <= result.efficiency_score <= 1.0
        assert result.placement_accuracy == 0.75
        assert result.anti_cheat == AntiCheatFlag.CLEAN

    def test_analyze_sequence_fast_gets_higher_mastery(
        self, build_engine: BuildForgeFN
    ) -> None:
        """Faster execution should yield higher mastery tier."""
        fast = build_engine.analyze_sequence(
            user_id="fast-user",
            build_type=BuildType.RAMP_WALL,
            step_times_ms=[60, 50, 90, 50],
            placement_hits=4,
            placement_total=4,
        )
        slow = build_engine.analyze_sequence(
            user_id="slow-user",
            build_type=BuildType.RAMP_WALL,
            step_times_ms=[200, 180, 300, 180],
            placement_hits=2,
            placement_total=4,
        )
        # Fast user should have better or equal tier
        fast_idx = list(MasteryTier).index(fast.mastery_tier)
        slow_idx = list(MasteryTier).index(slow.mastery_tier)
        assert fast_idx >= slow_idx

    def test_anti_cheat_flags_impossibly_fast(
        self, build_engine: BuildForgeFN
    ) -> None:
        """Sub-30ms steps should trigger timing anomaly flag."""
        result = build_engine.analyze_sequence(
            user_id="cheater",
            build_type=BuildType.RAMP_WALL,
            step_times_ms=[20, 15, 25, 10],
            placement_hits=4,
            placement_total=4,
        )
        assert result.anti_cheat == AntiCheatFlag.TIMING_ANOMALY

    def test_anti_cheat_flags_macro_identical_times(
        self, build_engine: BuildForgeFN
    ) -> None:
        """Identical step times suggest macro usage."""
        result = build_engine.analyze_sequence(
            user_id="macro-user",
            build_type=BuildType.RAMP_WALL,
            step_times_ms=[100, 100, 100, 100],
            placement_hits=4,
            placement_total=4,
        )
        assert result.anti_cheat == AntiCheatFlag.MACRO_DETECTED

    def test_prescribe_drills(self, build_engine: BuildForgeFN) -> None:
        """Drill prescription targets weak sequences."""
        analyses = [
            build_engine.analyze_sequence(
                user_id="test",
                build_type=BuildType.RAMP_WALL,
                step_times_ms=[200, 180, 300, 180],
                placement_hits=2,
                placement_total=4,
            ),
            build_engine.analyze_sequence(
                user_id="test",
                build_type=BuildType.NINETIES,
                step_times_ms=[150, 170, 200, 180, 200, 160],
                placement_hits=4,
                placement_total=6,
            ),
        ]
        drills = build_engine.prescribe_drills(analyses)
        assert len(drills) > 0
        assert all(d.reps_prescribed >= 5 for d in drills)

    def test_generate_report(self, build_engine: BuildForgeFN) -> None:
        """Full report includes analyses, mastery, drills."""
        analyses = [
            build_engine.analyze_sequence(
                user_id="test",
                build_type=BuildType.RAMP_WALL,
                step_times_ms=[100, 80, 150, 80],
                placement_hits=3,
                placement_total=4,
            ),
        ]
        report = build_engine.generate_report("test", analyses)
        assert report.user_id == "test"
        assert len(report.sequences_analyzed) == 1
        assert report.weakest_sequence is not None
        assert report.strongest_sequence is not None

    def test_generate_report_empty(self, build_engine: BuildForgeFN) -> None:
        """Empty analyses produce a valid empty report."""
        report = build_engine.generate_report("test", [])
        assert report.overall_mastery == MasteryTier.BEGINNER
        assert len(report.drills) == 0

    def test_improvement_tips_generated(self, build_engine: BuildForgeFN) -> None:
        """Analysis with slow steps should generate tips."""
        result = build_engine.analyze_sequence(
            user_id="test",
            build_type=BuildType.WATERFALL,
            step_times_ms=[200, 300, 250, 400, 300],
            placement_hits=3,
            placement_total=5,
        )
        assert len(result.improvement_tips) > 0


# ===========================================================================
# EditForge tests
# ===========================================================================

class TestEditForge:
    """Tests for EditForge agent."""

    def test_build_speed_profile(self, edit_engine: EditForge) -> None:
        """Speed profile calculates per-shape averages."""
        attempts = [
            EditAttempt(shape=EditShape.TRIANGLE, time_ms=200, successful=True),
            EditAttempt(shape=EditShape.TRIANGLE, time_ms=190, successful=True),
            EditAttempt(shape=EditShape.ARCH, time_ms=250, successful=True),
            EditAttempt(shape=EditShape.DOOR, time_ms=300, successful=False),
        ]
        profile = edit_engine.build_speed_profile("test-user", attempts)
        assert profile.user_id == "test-user"
        assert EditShape.TRIANGLE in profile.shape_speeds
        assert profile.shape_speeds[EditShape.TRIANGLE] == pytest.approx(195.0, abs=1)
        assert profile.anti_cheat == AntiCheatFlag.CLEAN

    def test_speed_profile_pressure_penalty(self, edit_engine: EditForge) -> None:
        """Pressure penalty reflects accuracy drop under pressure."""
        attempts = [
            EditAttempt(shape=EditShape.TRIANGLE, time_ms=200, successful=True, under_pressure=False),
            EditAttempt(shape=EditShape.TRIANGLE, time_ms=200, successful=True, under_pressure=False),
            EditAttempt(shape=EditShape.TRIANGLE, time_ms=250, successful=False, under_pressure=True),
            EditAttempt(shape=EditShape.TRIANGLE, time_ms=260, successful=False, under_pressure=True),
        ]
        profile = edit_engine.build_speed_profile("test", attempts)
        assert profile.pressure_penalty > 0  # Should detect drop

    def test_anti_cheat_impossibly_fast_edits(self, edit_engine: EditForge) -> None:
        """Sub-50ms edits should trigger timing anomaly."""
        attempts = [
            EditAttempt(shape=EditShape.TRIANGLE, time_ms=30, successful=True),
            EditAttempt(shape=EditShape.ARCH, time_ms=25, successful=True),
        ]
        flag = edit_engine.verify_anti_cheat(attempts)
        assert flag == AntiCheatFlag.TIMING_ANOMALY

    def test_anti_cheat_macro_detection(self, edit_engine: EditForge) -> None:
        """Identical timings across many attempts suggest macro."""
        attempts = [
            EditAttempt(shape=EditShape.TRIANGLE, time_ms=150, successful=True),
            EditAttempt(shape=EditShape.ARCH, time_ms=150, successful=True),
            EditAttempt(shape=EditShape.DOOR, time_ms=150, successful=True),
            EditAttempt(shape=EditShape.WINDOW, time_ms=150, successful=True),
            EditAttempt(shape=EditShape.HALF_WALL, time_ms=150, successful=True),
        ]
        flag = edit_engine.verify_anti_cheat(attempts)
        assert flag == AntiCheatFlag.MACRO_DETECTED

    def test_evaluate_drill(self, edit_engine: EditForge) -> None:
        """Drill evaluation returns valid result with calibration."""
        attempts = [
            EditAttempt(shape=EditShape.TRIANGLE, time_ms=200, successful=True),
            EditAttempt(shape=EditShape.ARCH, time_ms=220, successful=True),
            EditAttempt(shape=EditShape.DOOR, time_ms=250, successful=True),
            EditAttempt(shape=EditShape.WINDOW, time_ms=230, successful=False),
        ]
        result = edit_engine.evaluate_drill("test-user", attempts)
        assert result.user_id == "test-user"
        assert result.accuracy == pytest.approx(0.75, abs=0.01)
        assert len(result.shapes_drilled) > 0
        assert "version" in result.dynamic_calibration

    def test_dynamic_calibration_increases_difficulty(
        self, edit_engine: EditForge
    ) -> None:
        """High accuracy should increase difficulty."""
        initial = edit_engine.get_calibration("cal-user")
        edit_engine.update_calibration("cal-user", accuracy=0.95)
        updated = edit_engine.get_calibration("cal-user")
        assert updated["pressure_level"] >= initial.get("pressure_level", 0.5)

    def test_dynamic_calibration_decreases_difficulty(
        self, edit_engine: EditForge
    ) -> None:
        """Low accuracy should decrease difficulty."""
        edit_engine.update_calibration("cal-user2", accuracy=0.95)  # First raise
        mid = edit_engine.get_calibration("cal-user2")
        edit_engine.update_calibration("cal-user2", accuracy=0.30)  # Then lower
        low = edit_engine.get_calibration("cal-user2")
        assert low["pressure_level"] <= mid["pressure_level"]

    def test_improvement_notes_generated(self, edit_engine: EditForge) -> None:
        """Low accuracy drill should produce improvement notes."""
        attempts = [
            EditAttempt(shape=EditShape.TRIANGLE, time_ms=400, successful=False),
            EditAttempt(shape=EditShape.ARCH, time_ms=500, successful=False),
            EditAttempt(shape=EditShape.DOOR, time_ms=350, successful=True),
        ]
        result = edit_engine.evaluate_drill("test", attempts)
        assert len(result.improvement_notes) > 0
