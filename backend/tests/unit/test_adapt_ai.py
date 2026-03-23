"""Tests for AdaptAI — series analysis, adjustment generation, between-series flow."""

from __future__ import annotations

import pytest

from app.schemas.drill import (
    AdaptRecommendation,
    SeriesAnalysis,
)
from app.services.backbone.adapt_ai import (
    AdaptAI,
    _recommendation_history,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture(autouse=True)
def _clear_state():
    """Reset in-memory stores between tests."""
    _recommendation_history.clear()
    yield
    _recommendation_history.clear()


@pytest.fixture
def ai() -> AdaptAI:
    return AdaptAI()


@pytest.fixture
def winning_series() -> dict:
    return {
        "series_id": "s-001",
        "games": [
            {
                "result": "win",
                "strengths": ["Strong run game"],
                "plays": [
                    {"type": "run", "result": "success"},
                    {"type": "pass", "result": "success"},
                ],
            },
            {
                "result": "win",
                "strengths": ["Dominant defense"],
                "plays": [
                    {"type": "run", "result": "success"},
                    {"type": "run", "result": "success"},
                ],
            },
        ],
    }


@pytest.fixture
def losing_series() -> dict:
    return {
        "series_id": "s-002",
        "games": [
            {
                "result": "loss",
                "weaknesses": ["Turnover prone"],
                "opponent_patterns": ["Opponent blitzes on 3rd down"],
                "plays": [
                    {"type": "pass", "result": "fail"},
                    {"type": "pass", "result": "fail"},
                ],
            },
            {
                "result": "loss",
                "weaknesses": ["Poor clock management"],
                "plays": [
                    {"type": "pass", "result": "fail"},
                    {"type": "run", "result": "success"},
                ],
            },
        ],
    }


@pytest.fixture
def mixed_series() -> dict:
    return {
        "series_id": "s-003",
        "games": [
            {"result": "win", "strengths": ["Quick passing"]},
            {"result": "loss", "weaknesses": ["Red zone efficiency"]},
            {"result": "win", "momentum_shifts": ["Lost momentum after halftime"]},
        ],
    }


# ---------------------------------------------------------------------------
# analyze_series tests
# ---------------------------------------------------------------------------

class TestAnalyzeSeries:
    def test_empty_series(self, ai: AdaptAI):
        analysis = ai.analyze_series({"games": []})
        assert isinstance(analysis, SeriesAnalysis)
        assert analysis.games_played == 0
        assert analysis.wins == 0
        assert analysis.losses == 0

    def test_counts_wins_and_losses(self, ai: AdaptAI, losing_series: dict):
        analysis = ai.analyze_series(losing_series)
        assert analysis.wins == 0
        assert analysis.losses == 2
        assert analysis.games_played == 2

    def test_extracts_strengths(self, ai: AdaptAI, winning_series: dict):
        analysis = ai.analyze_series(winning_series)
        assert "Strong run game" in analysis.strengths_exploited

    def test_extracts_weaknesses(self, ai: AdaptAI, losing_series: dict):
        analysis = ai.analyze_series(losing_series)
        assert "Turnover prone" in analysis.weaknesses_exposed

    def test_extracts_opponent_patterns(self, ai: AdaptAI, losing_series: dict):
        analysis = ai.analyze_series(losing_series)
        assert "Opponent blitzes on 3rd down" in analysis.opponent_patterns

    def test_detects_play_patterns_from_frequency(self, ai: AdaptAI):
        """When a play type exceeds frequency threshold, it's flagged."""
        series = {
            "games": [
                {
                    "result": "loss",
                    "plays": [
                        {"type": "blitz", "result": "success"},
                        {"type": "blitz", "result": "success"},
                        {"type": "blitz", "result": "success"},
                        {"type": "zone", "result": "fail"},
                    ],
                },
            ],
        }
        analysis = ai.analyze_series(series)
        # blitz is 3/4 = 75%, well above threshold
        assert any("blitz" in p for p in analysis.opponent_patterns)


# ---------------------------------------------------------------------------
# generate_quick_adjustment tests
# ---------------------------------------------------------------------------

class TestGenerateQuickAdjustment:
    def test_counters_opponent_pattern_first(self, ai: AdaptAI, losing_series: dict):
        analysis = ai.analyze_series(losing_series)
        rec = ai.generate_quick_adjustment(analysis)

        assert isinstance(rec, AdaptRecommendation)
        assert "Counter opponent pattern" in rec.adjustment
        assert rec.expected_impact >= 0.6

    def test_addresses_weakness_when_no_patterns(self, ai: AdaptAI):
        series = {
            "games": [
                {"result": "loss", "weaknesses": ["Slow hot routes"]},
            ],
        }
        analysis = ai.analyze_series(series)
        rec = ai.generate_quick_adjustment(analysis)
        assert "weakness" in rec.adjustment.lower() or "Shore up" in rec.adjustment

    def test_doubles_down_on_strengths_when_winning(self, ai: AdaptAI, winning_series: dict):
        analysis = ai.analyze_series(winning_series)
        rec = ai.generate_quick_adjustment(analysis)
        assert "Double down" in rec.adjustment or "working" in rec.adjustment

    def test_time_to_implement_is_set(self, ai: AdaptAI, losing_series: dict):
        analysis = ai.analyze_series(losing_series)
        rec = ai.generate_quick_adjustment(analysis)
        assert rec.time_to_implement in ("immediate", "5 minutes")


# ---------------------------------------------------------------------------
# get_between_series_adjustment (end-to-end) tests
# ---------------------------------------------------------------------------

class TestGetBetweenSeriesAdjustment:
    def test_returns_recommendation(self, ai: AdaptAI, losing_series: dict):
        rec = ai.get_between_series_adjustment("player-1", losing_series)
        assert isinstance(rec, AdaptRecommendation)
        assert rec.user_id == "player-1"

    def test_stores_in_history(self, ai: AdaptAI, losing_series: dict):
        ai.get_between_series_adjustment("player-1", losing_series)
        assert "player-1" in _recommendation_history
        assert len(_recommendation_history["player-1"]) == 1

    def test_includes_analysis(self, ai: AdaptAI, losing_series: dict):
        rec = ai.get_between_series_adjustment("player-1", losing_series)
        assert rec.analysis is not None
        assert rec.analysis.games_played == 2
