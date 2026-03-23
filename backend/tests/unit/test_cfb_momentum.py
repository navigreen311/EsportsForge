"""Tests for MomentumGuard — tracking, prediction, exploitation, recovery."""

from __future__ import annotations

import pytest

from app.schemas.cfb26.momentum import (
    ActionInput,
    GameStateInput,
    MomentumDirection,
    MomentumState,
)
from app.services.agents.cfb26.momentum_guard import MomentumGuard


@pytest.fixture
def engine() -> MomentumGuard:
    """Fresh MomentumGuard instance per test."""
    return MomentumGuard()


def _make_game_state(**overrides) -> GameStateInput:
    """Helper to build a GameStateInput with sensible defaults."""
    defaults = {
        "home_team": "Alabama",
        "away_team": "Auburn",
        "home_score": 14,
        "away_score": 7,
        "quarter": 2,
        "game_clock": "8:30",
        "possession": "home",
        "down": 1,
        "distance": 10,
        "field_position": 35,
        "is_home_game": True,
        "stadium_noise_level": 0.7,
        "recent_events": [],
    }
    defaults.update(overrides)
    return GameStateInput(**defaults)


# ---------------------------------------------------------------------------
# Track momentum
# ---------------------------------------------------------------------------

class TestTrackMomentum:
    """Tests for track_momentum."""

    def test_neutral_game_state(self, engine: MomentumGuard) -> None:
        state = _make_game_state(home_score=7, away_score=7, recent_events=[])
        result = engine.track_momentum(state)
        assert isinstance(result, MomentumState)
        assert -1.0 <= result.meter_value <= 1.0
        assert result.home_team == "Alabama"
        assert result.away_team == "Auburn"

    def test_big_lead_gives_positive_momentum(self, engine: MomentumGuard) -> None:
        state = _make_game_state(home_score=28, away_score=0)
        result = engine.track_momentum(state)
        assert result.meter_value > 0.0

    def test_big_deficit_gives_negative_momentum(self, engine: MomentumGuard) -> None:
        state = _make_game_state(home_score=0, away_score=28)
        result = engine.track_momentum(state)
        assert result.meter_value < 0.0

    def test_turnover_shifts_momentum(self, engine: MomentumGuard) -> None:
        state_no_event = _make_game_state(home_score=7, away_score=7)
        state_with_event = _make_game_state(
            home_score=7, away_score=7, recent_events=["turnover"]
        )
        result_no = engine.track_momentum(state_no_event)
        result_with = engine.track_momentum(state_with_event)
        # Turnover should shift momentum
        assert result_with.meter_value != result_no.meter_value

    def test_multiple_triggers_compound(self, engine: MomentumGuard) -> None:
        state = _make_game_state(
            recent_events=["turnover", "big_play", "scoring_drive"]
        )
        result = engine.track_momentum(state)
        assert len(result.recent_triggers) >= 2

    def test_home_field_boost(self, engine: MomentumGuard) -> None:
        home = _make_game_state(is_home_game=True, home_score=7, away_score=7)
        away = _make_game_state(is_home_game=False, home_score=7, away_score=7)
        result_home = engine.track_momentum(home)
        result_away = engine.track_momentum(away)
        # Home should have higher momentum
        assert result_home.meter_value > result_away.meter_value

    def test_meter_bounded(self, engine: MomentumGuard) -> None:
        state = _make_game_state(
            home_score=56, away_score=0,
            recent_events=["turnover", "big_play", "fourth_down_stop", "goal_line_stand"],
            stadium_noise_level=1.0,
        )
        result = engine.track_momentum(state)
        assert result.meter_value <= 1.0

    def test_direction_critical_high(self, engine: MomentumGuard) -> None:
        state = _make_game_state(
            home_score=35, away_score=0,
            recent_events=["turnover", "big_play"],
            stadium_noise_level=0.9,
        )
        result = engine.track_momentum(state)
        assert result.direction in (
            MomentumDirection.RISING,
            MomentumDirection.CRITICAL_HIGH,
        )


# ---------------------------------------------------------------------------
# Predict momentum shift
# ---------------------------------------------------------------------------

class TestPredictMomentumShift:
    """Tests for predict_momentum_shift."""

    def test_deep_pass_positive_shift(self, engine: MomentumGuard) -> None:
        state = _make_game_state()
        action = ActionInput(action_type="deep_pass", aggression=0.8)
        result = engine.predict_momentum_shift(state, action)
        assert result.predicted_shift != 0.0
        assert -1.0 <= result.new_meter_value <= 1.0

    def test_conservative_play_minimal_shift(self, engine: MomentumGuard) -> None:
        state = _make_game_state()
        action = ActionInput(action_type="run_play", aggression=0.2)
        result = engine.predict_momentum_shift(state, action)
        assert abs(result.predicted_shift) < 0.1

    def test_high_aggression_increases_risk(self, engine: MomentumGuard) -> None:
        state = _make_game_state(home_score=0, away_score=21)
        low_action = ActionInput(action_type="deep_pass", aggression=0.2)
        high_action = ActionInput(action_type="deep_pass", aggression=0.9)
        low_result = engine.predict_momentum_shift(state, low_action)
        high_result = engine.predict_momentum_shift(state, high_action)
        # Higher aggression when behind = higher risk
        risk_order = {"low": 0, "medium": 1, "high": 2, "critical": 3}
        assert risk_order.get(high_result.risk_level, 0) >= risk_order.get(low_result.risk_level, 0)

    def test_prediction_has_reasoning(self, engine: MomentumGuard) -> None:
        state = _make_game_state()
        action = ActionInput(action_type="trick_play", aggression=0.7)
        result = engine.predict_momentum_shift(state, action)
        assert len(result.reasoning) > 0

    def test_prediction_direction_valid(self, engine: MomentumGuard) -> None:
        state = _make_game_state()
        action = ActionInput(action_type="field_goal", aggression=0.3)
        result = engine.predict_momentum_shift(state, action)
        assert result.new_direction in MomentumDirection


# ---------------------------------------------------------------------------
# Exploit momentum
# ---------------------------------------------------------------------------

class TestMomentumExploit:
    """Tests for get_momentum_exploit."""

    def test_critical_high_aggressive(self, engine: MomentumGuard) -> None:
        state = MomentumState(
            meter_value=0.8,
            direction=MomentumDirection.CRITICAL_HIGH,
            velocity=0.2,
        )
        exploit = engine.get_momentum_exploit(state)
        assert exploit.aggression_level >= 0.8
        assert exploit.tempo_recommendation == "hurry_up"
        assert len(exploit.recommended_plays) > 0

    def test_critical_low_conservative(self, engine: MomentumGuard) -> None:
        state = MomentumState(
            meter_value=-0.8,
            direction=MomentumDirection.CRITICAL_LOW,
            velocity=-0.2,
        )
        exploit = engine.get_momentum_exploit(state)
        assert exploit.aggression_level <= 0.3
        assert exploit.tempo_recommendation == "slow_down"

    def test_neutral_balanced(self, engine: MomentumGuard) -> None:
        state = MomentumState(
            meter_value=0.0,
            direction=MomentumDirection.NEUTRAL,
            velocity=0.0,
        )
        exploit = engine.get_momentum_exploit(state)
        assert 0.3 <= exploit.aggression_level <= 0.7
        assert len(exploit.key_advantages) > 0

    def test_exploit_has_window(self, engine: MomentumGuard) -> None:
        state = MomentumState(
            meter_value=0.5,
            direction=MomentumDirection.RISING,
            velocity=0.1,
        )
        exploit = engine.get_momentum_exploit(state)
        assert exploit.window_plays >= 1


# ---------------------------------------------------------------------------
# Momentum recovery
# ---------------------------------------------------------------------------

class TestMomentumRecovery:
    """Tests for get_momentum_recovery."""

    def test_dire_recovery(self, engine: MomentumGuard) -> None:
        state = MomentumState(
            meter_value=-0.7,
            direction=MomentumDirection.CRITICAL_LOW,
            velocity=-0.3,
        )
        recovery = engine.get_momentum_recovery(state)
        assert recovery.severity == "dire"
        assert recovery.timeout_recommendation is True
        assert len(recovery.immediate_actions) > 0

    def test_mild_recovery(self, engine: MomentumGuard) -> None:
        state = MomentumState(
            meter_value=0.0,
            direction=MomentumDirection.NEUTRAL,
            velocity=0.0,
        )
        recovery = engine.get_momentum_recovery(state)
        assert recovery.severity == "mild"
        assert recovery.timeout_recommendation is False

    def test_moderate_recovery(self, engine: MomentumGuard) -> None:
        state = MomentumState(
            meter_value=-0.2,
            direction=MomentumDirection.FALLING,
            velocity=-0.1,
        )
        recovery = engine.get_momentum_recovery(state)
        assert recovery.severity == "moderate"
        assert recovery.estimated_plays_to_neutral > 0

    def test_recovery_has_style_shift(self, engine: MomentumGuard) -> None:
        state = MomentumState(
            meter_value=-0.4,
            direction=MomentumDirection.CRITICAL_LOW,
            velocity=-0.2,
        )
        recovery = engine.get_momentum_recovery(state)
        assert len(recovery.play_style_shift) > 0
        assert len(recovery.risk_acceptance) > 0
