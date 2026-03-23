"""Unit tests for the Confidence Tracker service."""

from __future__ import annotations

import pytest

from app.schemas.mental import (
    MomentumDirection,
    ReadinessLevel,
)
from app.services.backbone import confidence_tracker


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture(autouse=True)
def _clean_state():
    """Reset in-memory stores before each test."""
    confidence_tracker._reset()
    yield
    confidence_tracker._reset()


def _seed_games(user_id: str, title: str, wins: int, losses: int, **extra):
    """Helper to seed game history with wins followed by losses."""
    for i in range(wins):
        confidence_tracker.record_game(user_id, {
            "title": title,
            "won": True,
            "clutch": extra.get("clutch", False),
            "close_game": extra.get("close_game", False),
            "comeback": extra.get("comeback", False),
        })
    for i in range(losses):
        confidence_tracker.record_game(user_id, {
            "title": title,
            "won": False,
            "clutch": extra.get("clutch", False),
            "close_game": extra.get("close_game", False),
            "comeback": False,
        })


# ===========================================================================
# get_confidence_score
# ===========================================================================


class TestGetConfidenceScore:
    def test_no_data_returns_baseline(self):
        result = confidence_tracker.get_confidence_score("u1", "madden26")
        assert result.overall == 0.5
        assert result.sample_size == 0

    def test_all_wins_high_confidence(self):
        _seed_games("u1", "madden26", wins=10, losses=0)
        result = confidence_tracker.get_confidence_score("u1", "madden26")
        assert result.overall > 0.8
        assert result.win_rate_30d == 1.0
        assert result.sample_size == 10

    def test_all_losses_low_confidence(self):
        _seed_games("u1", "madden26", wins=0, losses=10)
        result = confidence_tracker.get_confidence_score("u1", "madden26")
        assert result.overall < 0.3
        assert result.win_rate_30d == 0.0

    def test_mixed_results(self):
        _seed_games("u1", "madden26", wins=6, losses=4)
        result = confidence_tracker.get_confidence_score("u1", "madden26")
        assert 0.3 < result.overall < 0.9
        assert result.sample_size == 10

    def test_filters_by_title(self):
        _seed_games("u1", "madden26", wins=10, losses=0)
        _seed_games("u1", "fc25", wins=0, losses=10)
        madden = confidence_tracker.get_confidence_score("u1", "madden26")
        fc = confidence_tracker.get_confidence_score("u1", "fc25")
        assert madden.overall > fc.overall

    def test_clutch_games_influence_score(self):
        for _ in range(5):
            confidence_tracker.record_game("u1", {
                "title": "madden26", "won": True, "clutch": True,
                "close_game": False, "comeback": False,
            })
        for _ in range(5):
            confidence_tracker.record_game("u1", {
                "title": "madden26", "won": True, "clutch": False,
                "close_game": False, "comeback": False,
            })
        result = confidence_tracker.get_confidence_score("u1", "madden26")
        assert result.clutch_rate == 1.0


# ===========================================================================
# track_clutch_performance
# ===========================================================================


class TestTrackClutchPerformance:
    def test_no_data(self):
        result = confidence_tracker.track_clutch_performance("u1")
        assert result.clutch_rate == 0.0
        assert result.clutch_games == 0

    def test_clutch_stats(self):
        for _ in range(3):
            confidence_tracker.record_game("u1", {
                "title": "madden26", "won": True, "clutch": True,
                "close_game": True, "comeback": True,
            })
        confidence_tracker.record_game("u1", {
            "title": "madden26", "won": False, "clutch": True,
            "close_game": True, "comeback": False,
        })
        result = confidence_tracker.track_clutch_performance("u1")
        assert result.clutch_games == 4
        assert result.clutch_rate == 0.75
        assert result.comeback_rate == 1.0  # 3 out of 3 comeback games won
        assert result.close_game_win_rate == 0.75


# ===========================================================================
# get_momentum_state
# ===========================================================================


class TestGetMomentumState:
    def test_no_data_stable(self):
        result = confidence_tracker.get_momentum_state("u1")
        assert result.direction == MomentumDirection.STABLE
        assert result.streak_length == 0

    def test_win_streak(self):
        _seed_games("u1", "madden26", wins=5, losses=0)
        result = confidence_tracker.get_momentum_state("u1")
        assert result.direction == MomentumDirection.RISING
        assert result.streak_length == 5
        assert result.streak_type == "win"

    def test_loss_streak(self):
        _seed_games("u1", "madden26", wins=0, losses=5)
        result = confidence_tracker.get_momentum_state("u1")
        assert result.direction == MomentumDirection.FALLING
        assert result.streak_length == 5
        assert result.streak_type == "loss"

    def test_recent_results_captured(self):
        _seed_games("u1", "madden26", wins=3, losses=2)
        result = confidence_tracker.get_momentum_state("u1")
        assert len(result.recent_results) == 5

    def test_session_id_passed_through(self):
        _seed_games("u1", "madden26", wins=1, losses=0)
        result = confidence_tracker.get_momentum_state("u1", session="sess-123")
        assert result.session_id == "sess-123"


# ===========================================================================
# get_pre_game_readiness
# ===========================================================================


class TestGetPreGameReadiness:
    def test_no_data_moderate(self):
        result = confidence_tracker.get_pre_game_readiness("u1", "madden26")
        assert result.level in (ReadinessLevel.MODERATE, ReadinessLevel.LOW, ReadinessLevel.FATIGUED)
        assert 0.0 <= result.composite_score <= 1.0

    def test_high_readiness_with_practice_and_wins(self):
        _seed_games("u1", "madden26", wins=10, losses=0)
        confidence_tracker.record_practice("u1", {"title": "madden26", "duration": 30})
        confidence_tracker.record_practice("u1", {"title": "madden26", "duration": 30})
        result = confidence_tracker.get_pre_game_readiness("u1", "madden26")
        assert result.composite_score > 0.5
        assert result.confidence_factor > 0.7

    def test_fatigue_reduces_readiness(self):
        _seed_games("u1", "madden26", wins=5, losses=0)
        # Record many sessions to simulate fatigue
        for _ in range(5):
            confidence_tracker.record_session("u1", {"title": "madden26"})
        result = confidence_tracker.get_pre_game_readiness("u1", "madden26")
        assert result.fatigue_factor < 0.5

    def test_recommendation_present(self):
        result = confidence_tracker.get_pre_game_readiness("u1", "madden26")
        assert len(result.recommendation) > 0
