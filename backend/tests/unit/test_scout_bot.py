"""Unit tests for ScoutBot — opponent scouting and dossier generation."""

from __future__ import annotations

import pytest

from app.schemas.opponent import (
    ExploitableWeakness,
    OpponentDossier,
    PlayFrequencyReport,
    Tendency,
    TendencyType,
)
from app.services.backbone.scout_bot import (
    _opponent_store,
    _seed_opponent_data,
    analyze_play_frequency,
    detect_tendencies,
    get_weakness_map,
    scout_opponent,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture(autouse=True)
def _clear_store():
    """Ensure a clean store for every test."""
    _opponent_store.clear()
    yield
    _opponent_store.clear()


def _make_games(count: int = 5, include_plays: bool = True) -> list[dict]:
    """Generate synthetic game data."""
    games = []
    for i in range(count):
        game = {
            "game_id": f"game-{i}",
            "result": "win" if i % 3 != 0 else "loss",
            "score": f"{21 + i}-{14 + i}",
            "key_plays": [f"play-{i}-a", f"play-{i}-b"],
        }
        if include_plays:
            game["plays"] = [
                {"name": "HB Dive", "formation": "Singleback", "situation": "1st & 10"},
                {"name": "PA Crossers", "formation": "Shotgun", "situation": "3rd & long"},
                {"name": "HB Dive", "formation": "Singleback", "situation": "1st & 10"},
            ]
        if i % 2 == 0:
            game["weaknesses"] = [
                {"area": "red zone defense", "severity": 0.7},
            ]
        games.append(game)
    return games


# ---------------------------------------------------------------------------
# scout_opponent
# ---------------------------------------------------------------------------

class TestScoutOpponent:
    def test_returns_dossier_for_known_opponent(self):
        _seed_opponent_data("opp-1", "madden26", _make_games(5))
        dossier = scout_opponent("opp-1", "madden26")

        assert isinstance(dossier, OpponentDossier)
        assert dossier.opponent_id == "opp-1"
        assert dossier.title == "madden26"
        assert len(dossier.recent_games) == 5

    def test_returns_empty_dossier_for_unknown_opponent(self):
        dossier = scout_opponent("unknown", "madden26")

        assert isinstance(dossier, OpponentDossier)
        assert dossier.opponent_id == "unknown"
        assert len(dossier.recent_games) == 0

    def test_dossier_includes_record(self):
        _seed_opponent_data("opp-2", "madden26", _make_games(6))
        dossier = scout_opponent("opp-2", "madden26")

        total = dossier.record["wins"] + dossier.record["losses"] + dossier.record["draws"]
        assert total == 6

    def test_dossier_limits_to_last_20(self):
        _seed_opponent_data("opp-big", "madden26", _make_games(30))
        dossier = scout_opponent("opp-big", "madden26")

        assert len(dossier.recent_games) == 20

    def test_dossier_has_threat_level(self):
        _seed_opponent_data("opp-3", "madden26", _make_games(5))
        dossier = scout_opponent("opp-3", "madden26")

        assert 0.0 <= dossier.overall_threat_level <= 1.0


# ---------------------------------------------------------------------------
# analyze_play_frequency
# ---------------------------------------------------------------------------

class TestAnalyzePlayFrequency:
    def test_counts_plays_correctly(self):
        games = _make_games(3)
        report = analyze_play_frequency(games, "opp-freq")

        assert isinstance(report, PlayFrequencyReport)
        assert report.total_plays > 0
        # HB Dive appears 2x per game, PA Crossers 1x per game
        assert report.top_plays[0]["play"] == "HB Dive"

    def test_empty_data_returns_zero_plays(self):
        report = analyze_play_frequency([], "empty")

        assert report.total_plays == 0
        assert report.top_plays == []

    def test_formation_distribution(self):
        games = _make_games(3)
        report = analyze_play_frequency(games, "opp-form")

        assert "Singleback" in report.formation_distribution
        assert "Shotgun" in report.formation_distribution

    def test_situation_breakdown(self):
        games = _make_games(2)
        report = analyze_play_frequency(games, "opp-sit")

        assert "1st & 10" in report.situation_breakdown
        assert "3rd & long" in report.situation_breakdown


# ---------------------------------------------------------------------------
# detect_tendencies
# ---------------------------------------------------------------------------

class TestDetectTendencies:
    def test_detects_repeated_tendency(self):
        games = _make_games(5)
        tendencies = detect_tendencies(games)

        assert isinstance(tendencies, list)
        assert all(isinstance(t, Tendency) for t in tendencies)

        # HB Dive on 1st & 10 should be detected (2/3 plays per game)
        first_ten = [t for t in tendencies if "1st" in t.situation]
        assert len(first_ten) > 0
        assert first_ten[0].action == "HB Dive"

    def test_empty_data_returns_no_tendencies(self):
        tendencies = detect_tendencies([])
        assert tendencies == []

    def test_tendencies_sorted_by_confidence(self):
        games = _make_games(10)
        tendencies = detect_tendencies(games)

        if len(tendencies) >= 2:
            for i in range(len(tendencies) - 1):
                assert tendencies[i].confidence >= tendencies[i + 1].confidence

    def test_tendency_type_classification(self):
        games = _make_games(5)
        tendencies = detect_tendencies(games)

        for t in tendencies:
            assert isinstance(t.tendency_type, TendencyType)


# ---------------------------------------------------------------------------
# get_weakness_map
# ---------------------------------------------------------------------------

class TestGetWeaknessMap:
    def test_detects_weaknesses(self):
        games = _make_games(6)
        weaknesses = get_weakness_map(games)

        assert isinstance(weaknesses, list)
        assert len(weaknesses) > 0
        assert all(isinstance(w, ExploitableWeakness) for w in weaknesses)
        assert weaknesses[0].area == "red zone defense"

    def test_empty_data_returns_no_weaknesses(self):
        weaknesses = get_weakness_map([])
        assert weaknesses == []

    def test_weaknesses_sorted_by_severity(self):
        games = _make_games(10)
        # Add a second weakness type
        for g in games:
            g.setdefault("weaknesses", []).append({"area": "pass rush", "severity": 0.3})
        weaknesses = get_weakness_map(games)

        if len(weaknesses) >= 2:
            for i in range(len(weaknesses) - 1):
                assert weaknesses[i].severity >= weaknesses[i + 1].severity
