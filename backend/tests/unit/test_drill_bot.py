"""Tests for DrillBot — drill generation, queue management, rep tracking, calibration."""

from __future__ import annotations

from uuid import uuid4

import pytest

from app.schemas.drill import (
    DrillQueue,
    DrillResult,
    DrillSession,
    DrillSpec,
    DrillStatus,
    DrillType,
    PersonalizedDrill,
)
from app.services.backbone.drill_bot import (
    DrillBot,
    _drill_queues,
    _drill_results,
    _drill_sessions,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture(autouse=True)
def _clear_state():
    """Reset in-memory stores between tests."""
    _drill_queues.clear()
    _drill_results.clear()
    _drill_sessions.clear()
    yield
    _drill_queues.clear()
    _drill_results.clear()
    _drill_sessions.clear()


@pytest.fixture
def bot() -> DrillBot:
    return DrillBot()


@pytest.fixture
def sample_weakness() -> dict:
    return {
        "label": "Poor red-zone playcalling",
        "category": "decision",
        "impact_score": 0.7,
    }


@pytest.fixture
def mechanical_weakness() -> dict:
    return {
        "label": "Slow stick adjustments",
        "category": "mechanical",
        "impact_score": 0.5,
    }


# ---------------------------------------------------------------------------
# generate_drill tests
# ---------------------------------------------------------------------------

class TestGenerateDrill:
    def test_returns_personalized_drill(self, bot: DrillBot, sample_weakness: dict):
        result = bot.generate_drill("player-1", "madden26", sample_weakness)

        assert isinstance(result, PersonalizedDrill)
        assert result.user_id == "player-1"
        assert result.drill_spec.title == "madden26"
        assert result.drill_spec.weakness_label == "Poor red-zone playcalling"

    def test_drill_type_matches_weakness_category(self, bot: DrillBot, sample_weakness: dict):
        result = bot.generate_drill("player-1", "madden26", sample_weakness)
        assert result.drill_spec.drill_type == DrillType.DECISION

    def test_mechanical_weakness_maps_to_mechanical_drill(self, bot: DrillBot, mechanical_weakness: dict):
        result = bot.generate_drill("player-1", "madden26", mechanical_weakness)
        assert result.drill_spec.drill_type == DrillType.MECHANICAL

    def test_adds_to_drill_queue(self, bot: DrillBot, sample_weakness: dict):
        bot.generate_drill("player-1", "madden26", sample_weakness)
        assert ("player-1", "madden26") in _drill_queues
        assert len(_drill_queues[("player-1", "madden26")]) == 1

    def test_multiple_drills_queue_correctly(self, bot: DrillBot, sample_weakness: dict, mechanical_weakness: dict):
        bot.generate_drill("player-1", "madden26", sample_weakness)
        bot.generate_drill("player-1", "madden26", mechanical_weakness)
        assert len(_drill_queues[("player-1", "madden26")]) == 2

    def test_drill_has_reason(self, bot: DrillBot, sample_weakness: dict):
        result = bot.generate_drill("player-1", "madden26", sample_weakness)
        assert "Poor red-zone playcalling" in result.reason
        assert "decision" in result.reason

    def test_unknown_category_defaults_to_decision(self, bot: DrillBot):
        weakness = {"label": "Mystery issue", "category": "unknown_cat"}
        result = bot.generate_drill("player-1", "madden26", weakness)
        assert result.drill_spec.drill_type == DrillType.DECISION

    def test_drill_spec_has_instructions(self, bot: DrillBot, sample_weakness: dict):
        result = bot.generate_drill("player-1", "madden26", sample_weakness)
        assert len(result.drill_spec.instructions) > 0


# ---------------------------------------------------------------------------
# get_drill_queue tests
# ---------------------------------------------------------------------------

class TestGetDrillQueue:
    def test_empty_queue(self, bot: DrillBot):
        queue = bot.get_drill_queue("player-1", "madden26")
        assert isinstance(queue, DrillQueue)
        assert len(queue.drills) == 0
        assert queue.pending_count == 0

    def test_queue_contains_generated_drills(self, bot: DrillBot, sample_weakness: dict):
        bot.generate_drill("player-1", "madden26", sample_weakness)
        queue = bot.get_drill_queue("player-1", "madden26")
        assert len(queue.drills) == 1
        assert queue.pending_count == 1

    def test_queue_has_estimated_time(self, bot: DrillBot, sample_weakness: dict):
        bot.generate_drill("player-1", "madden26", sample_weakness)
        queue = bot.get_drill_queue("player-1", "madden26")
        assert queue.total_estimated_minutes > 0


# ---------------------------------------------------------------------------
# complete_rep tests
# ---------------------------------------------------------------------------

class TestCompleteRep:
    def test_successful_rep_increments_counters(self, bot: DrillBot, sample_weakness: dict):
        drill = bot.generate_drill("player-1", "madden26", sample_weakness)
        session_id = list(_drill_sessions.keys())[0]
        session = bot.complete_rep("player-1", session_id, success=True)

        assert session.reps_completed == 1
        assert session.reps_successful == 1
        assert session.status == DrillStatus.IN_PROGRESS

    def test_failed_rep_increments_completed_only(self, bot: DrillBot, sample_weakness: dict):
        bot.generate_drill("player-1", "madden26", sample_weakness)
        session_id = list(_drill_sessions.keys())[0]
        session = bot.complete_rep("player-1", session_id, success=False)

        assert session.reps_completed == 1
        assert session.reps_successful == 0

    def test_completing_all_reps_marks_session_complete(self, bot: DrillBot, sample_weakness: dict):
        bot.generate_drill("player-1", "madden26", sample_weakness)
        session_id = list(_drill_sessions.keys())[0]
        reps_needed = _drill_sessions[session_id].drill_spec.reps_required

        for i in range(reps_needed):
            session = bot.complete_rep("player-1", session_id, success=True)

        assert session.status == DrillStatus.COMPLETED
        assert session.completed_at is not None

    def test_completion_records_result(self, bot: DrillBot, sample_weakness: dict):
        bot.generate_drill("player-1", "madden26", sample_weakness)
        session_id = list(_drill_sessions.keys())[0]
        reps_needed = _drill_sessions[session_id].drill_spec.reps_required

        for _ in range(reps_needed):
            bot.complete_rep("player-1", session_id, success=True)

        results = _drill_results.get(("player-1", "madden26"), [])
        assert len(results) == 1
        assert results[0].success_rate == 1.0

    def test_wrong_user_raises_error(self, bot: DrillBot, sample_weakness: dict):
        bot.generate_drill("player-1", "madden26", sample_weakness)
        session_id = list(_drill_sessions.keys())[0]

        with pytest.raises(ValueError, match="does not belong"):
            bot.complete_rep("player-2", session_id, success=True)

    def test_nonexistent_drill_raises_error(self, bot: DrillBot):
        with pytest.raises(ValueError, match="not found"):
            bot.complete_rep("player-1", uuid4(), success=True)


# ---------------------------------------------------------------------------
# get_drill_progress tests
# ---------------------------------------------------------------------------

class TestGetDrillProgress:
    def test_empty_progress(self, bot: DrillBot):
        progress = bot.get_drill_progress("player-1", "madden26")
        assert progress == {}

    def test_progress_after_completion(self, bot: DrillBot, sample_weakness: dict):
        bot.generate_drill("player-1", "madden26", sample_weakness)
        session_id = list(_drill_sessions.keys())[0]
        reps = _drill_sessions[session_id].drill_spec.reps_required

        for i in range(reps):
            bot.complete_rep("player-1", session_id, success=(i % 2 == 0))

        progress = bot.get_drill_progress("player-1", "madden26")
        assert "Poor red-zone playcalling" in progress
        p = progress["Poor red-zone playcalling"]
        assert p["total_drills_completed"] == 1
        assert p["total_reps"] == reps


# ---------------------------------------------------------------------------
# calibrate_drill_difficulty tests
# ---------------------------------------------------------------------------

class TestCalibrateDrillDifficulty:
    def test_not_enough_reps_returns_unchanged(self, bot: DrillBot, sample_weakness: dict):
        bot.generate_drill("player-1", "madden26", sample_weakness)
        session_id = list(_drill_sessions.keys())[0]

        # Only 1 rep — not enough to calibrate
        bot.complete_rep("player-1", session_id, success=True)
        original_diff = _drill_sessions[session_id].current_difficulty

        session = bot.calibrate_drill_difficulty("player-1", session_id)
        assert session.current_difficulty == original_diff

    def test_too_easy_bumps_difficulty_up(self, bot: DrillBot, sample_weakness: dict):
        bot.generate_drill("player-1", "madden26", sample_weakness)
        session_id = list(_drill_sessions.keys())[0]

        # All successes → too easy
        for _ in range(5):
            bot.complete_rep("player-1", session_id, success=True)

        original_diff = _drill_sessions[session_id].current_difficulty
        session = bot.calibrate_drill_difficulty("player-1", session_id)
        assert session.current_difficulty > original_diff

    def test_too_hard_reduces_difficulty(self, bot: DrillBot, sample_weakness: dict):
        bot.generate_drill("player-1", "madden26", sample_weakness)
        session_id = list(_drill_sessions.keys())[0]

        # All failures → too hard
        for _ in range(5):
            bot.complete_rep("player-1", session_id, success=False)

        original_diff = _drill_sessions[session_id].current_difficulty
        session = bot.calibrate_drill_difficulty("player-1", session_id)
        assert session.current_difficulty < original_diff

    def test_nonexistent_drill_raises_error(self, bot: DrillBot):
        with pytest.raises(ValueError, match="not found"):
            bot.calibrate_drill_difficulty("player-1", uuid4())
