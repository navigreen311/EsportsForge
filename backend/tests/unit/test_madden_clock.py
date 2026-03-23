"""Unit tests for ClockAI — clock management intelligence."""

import pytest

from app.schemas.madden26.clock import (
    ClockAction,
    ClockDecision,
    FourthDownChoice,
    GameState,
    PlayType,
)
from app.services.agents.madden26.clock_ai import ClockAI


@pytest.fixture
def clock_ai() -> ClockAI:
    return ClockAI()


def _make_state(**overrides) -> GameState:
    """Helper to build a GameState with sensible defaults."""
    defaults = dict(
        quarter=4,
        time_remaining_seconds=120,
        score_user=21,
        score_opponent=14,
        down=1,
        yards_to_go=10,
        yard_line=50,
        timeouts_user=3,
        timeouts_opponent=3,
        is_user_possession=True,
        is_two_minute_warning_used=False,
    )
    defaults.update(overrides)
    return GameState(**defaults)


# -----------------------------------------------------------------------
# get_clock_decision
# -----------------------------------------------------------------------

class TestClockDecision:
    def test_kneel_when_leading_late(self, clock_ai: ClockAI):
        """Should recommend kneeling when leading with little time left."""
        gs = _make_state(
            score_user=28,
            score_opponent=14,
            time_remaining_seconds=45,
            down=1,
        )
        decision = clock_ai.get_clock_decision(gs)
        assert decision.action == ClockAction.KNEEL
        assert decision.recommended_play_type == PlayType.KNEEL
        assert decision.urgency < 0.5

    def test_hurry_up_when_trailing_late(self, clock_ai: ClockAI):
        """Should recommend hurry-up when trailing in Q4 under 4 min."""
        gs = _make_state(
            score_user=14,
            score_opponent=21,
            time_remaining_seconds=180,
        )
        decision = clock_ai.get_clock_decision(gs)
        assert decision.action == ClockAction.HURRY_UP
        assert decision.urgency > 0.0
        assert "trailing" in decision.reasoning.lower()

    def test_milk_clock_when_leading(self, clock_ai: ClockAI):
        """Should recommend milking clock when leading in second half."""
        gs = _make_state(
            quarter=3,
            score_user=21,
            score_opponent=7,
            time_remaining_seconds=600,
        )
        decision = clock_ai.get_clock_decision(gs)
        assert decision.action == ClockAction.MILK_CLOCK
        assert decision.recommended_play_type == PlayType.RUN

    def test_normal_tempo_early_game(self, clock_ai: ClockAI):
        """Normal tempo in early-game neutral situations."""
        gs = _make_state(
            quarter=1,
            score_user=0,
            score_opponent=0,
            time_remaining_seconds=900,
        )
        decision = clock_ai.get_clock_decision(gs)
        assert decision.action == ClockAction.NORMAL

    def test_returns_clock_decision_type(self, clock_ai: ClockAI):
        gs = _make_state()
        decision = clock_ai.get_clock_decision(gs)
        assert isinstance(decision, ClockDecision)


# -----------------------------------------------------------------------
# two_minute_drill
# -----------------------------------------------------------------------

class TestTwoMinuteDrill:
    def test_generates_play_sequence(self, clock_ai: ClockAI):
        gs = _make_state(
            score_user=14,
            score_opponent=21,
            time_remaining_seconds=120,
            yard_line=25,
        )
        plan = clock_ai.two_minute_drill(gs)
        assert plan.total_plays_planned > 0
        assert len(plan.play_sequence) == plan.total_plays_planned
        assert 0.0 <= plan.estimated_score_probability <= 1.0

    def test_no_plays_when_no_time(self, clock_ai: ClockAI):
        gs = _make_state(time_remaining_seconds=0)
        plan = clock_ai.two_minute_drill(gs)
        assert plan.total_plays_planned == 0

    def test_plan_includes_pass_plays(self, clock_ai: ClockAI):
        gs = _make_state(
            time_remaining_seconds=90,
            yard_line=30,
        )
        plan = clock_ai.two_minute_drill(gs)
        play_types = {p.play_type for p in plan.play_sequence}
        # 2-minute drill should use passing plays
        passing = {PlayType.PASS_SHORT, PlayType.PASS_MEDIUM, PlayType.PASS_DEEP}
        assert play_types & passing, "Expected at least one pass play in 2-min drill"


# -----------------------------------------------------------------------
# fourth_down_decision
# -----------------------------------------------------------------------

class TestFourthDownDecision:
    def test_go_for_it_when_trailing_late(self, clock_ai: ClockAI):
        gs = _make_state(
            score_user=14,
            score_opponent=21,
            time_remaining_seconds=60,
            down=4,
            yards_to_go=3,
            yard_line=65,
        )
        decision = clock_ai.fourth_down_decision(gs)
        assert decision.recommendation == FourthDownChoice.GO_FOR_IT

    def test_field_goal_when_in_range(self, clock_ai: ClockAI):
        gs = _make_state(
            quarter=2,
            score_user=14,
            score_opponent=14,
            time_remaining_seconds=600,
            down=4,
            yards_to_go=8,
            yard_line=75,  # 25 yards from endzone -> ~42 yard FG
        )
        decision = clock_ai.fourth_down_decision(gs)
        assert decision.recommendation == FourthDownChoice.FIELD_GOAL
        assert decision.fg_probability is not None
        assert decision.fg_probability > 0.5

    def test_punt_on_long_yardage(self, clock_ai: ClockAI):
        gs = _make_state(
            quarter=2,
            score_user=14,
            score_opponent=14,
            time_remaining_seconds=800,
            down=4,
            yards_to_go=15,
            yard_line=30,
        )
        decision = clock_ai.fourth_down_decision(gs)
        assert decision.recommendation == FourthDownChoice.PUNT

    def test_probabilities_in_range(self, clock_ai: ClockAI):
        gs = _make_state(down=4, yards_to_go=5)
        decision = clock_ai.fourth_down_decision(gs)
        assert 0.0 <= decision.go_probability <= 1.0
        assert decision.break_even_yards > 0


# -----------------------------------------------------------------------
# end_game_scenario
# -----------------------------------------------------------------------

class TestEndGameScenario:
    def test_trailing_scenario(self, clock_ai: ClockAI):
        gs = _make_state(
            score_user=14,
            score_opponent=21,
            time_remaining_seconds=90,
        )
        plan = clock_ai.end_game_scenario(gs)
        assert "trailing" in plan.scenario_label
        assert plan.play_sequence  # Should have plays
        assert 0.0 <= plan.win_probability <= 1.0

    def test_leading_scenario(self, clock_ai: ClockAI):
        gs = _make_state(
            score_user=28,
            score_opponent=14,
            time_remaining_seconds=90,
        )
        plan = clock_ai.end_game_scenario(gs)
        assert "leading" in plan.scenario_label

    def test_tied_scenario(self, clock_ai: ClockAI):
        gs = _make_state(
            score_user=21,
            score_opponent=21,
            time_remaining_seconds=90,
        )
        plan = clock_ai.end_game_scenario(gs)
        assert "tied" in plan.scenario_label


# -----------------------------------------------------------------------
# evaluate_timeout_usage
# -----------------------------------------------------------------------

class TestTimeoutUsage:
    def test_use_timeout_on_defense_trailing(self, clock_ai: ClockAI):
        gs = _make_state(
            score_user=14,
            score_opponent=21,
            is_user_possession=False,
            time_remaining_seconds=120,
        )
        advice = clock_ai.evaluate_timeout_usage(gs)
        assert advice.should_use_timeout is True
        assert advice.timeouts_after == 2

    def test_no_timeout_when_none_left(self, clock_ai: ClockAI):
        gs = _make_state(timeouts_user=0)
        advice = clock_ai.evaluate_timeout_usage(gs)
        assert advice.should_use_timeout is False
        assert advice.timeouts_after == 0

    def test_save_timeouts_in_normal_play(self, clock_ai: ClockAI):
        gs = _make_state(
            quarter=2,
            time_remaining_seconds=600,
            score_user=14,
            score_opponent=14,
        )
        advice = clock_ai.evaluate_timeout_usage(gs)
        assert advice.should_use_timeout is False


# -----------------------------------------------------------------------
# simulate_scenario
# -----------------------------------------------------------------------

class TestSimulation:
    def test_basic_simulation(self, clock_ai: ClockAI):
        gs = _make_state(
            yard_line=50,
            time_remaining_seconds=120,
        )
        result = clock_ai.simulate_scenario(gs, ["pass_medium_1", "run_play_2", "pass_short_3"])
        assert len(result.play_outcomes) == 3
        assert result.final_time_remaining < 120
        assert result.summary

    def test_simulation_stops_at_zero_time(self, clock_ai: ClockAI):
        gs = _make_state(time_remaining_seconds=10)
        result = clock_ai.simulate_scenario(gs, ["run_1"] * 10)
        assert len(result.play_outcomes) <= 10
        assert result.final_time_remaining >= 0

    def test_touchdown_scoring(self, clock_ai: ClockAI):
        """Plays near the goal line should result in a touchdown."""
        gs = _make_state(
            yard_line=95,
            time_remaining_seconds=300,
        )
        result = clock_ai.simulate_scenario(gs, ["pass_medium_1", "pass_medium_2"])
        # First play should score (95 + 9 >= 99)
        assert result.final_score_user > gs.score_user
