"""Unit tests for MatchupAI + ReadAI — Madden 26 matchup detection and reads."""

from __future__ import annotations

import pytest

from app.schemas.madden26.matchup import (
    AdvantageType,
    BlitzSource,
    ConfidenceLevel,
    CoverageType,
    MotionType,
)
from app.schemas.madden26.roster import (
    MismatchSeverity,
    PersonnelPackage,
    Player,
    PlayerRating,
    Position,
    RosterData,
)
from app.services.agents.madden26.matchup_ai import MatchupAI
from app.services.agents.madden26.read_ai import ReadAI


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_player(
    name: str,
    position: Position,
    overall: int = 80,
    speed: int = 80,
    *,
    acceleration: int = 80,
    agility: int = 80,
    strength: int = 80,
    awareness: int = 80,
    catching: int | None = None,
    route_running: int | None = None,
    man_coverage: int | None = None,
    zone_coverage: int | None = None,
    team: str = "Test",
) -> Player:
    return Player(
        name=name,
        position=position,
        team=team,
        ratings=PlayerRating(
            overall=overall,
            speed=speed,
            acceleration=acceleration,
            agility=agility,
            strength=strength,
            awareness=awareness,
            catching=catching,
            route_running=route_running,
            man_coverage=man_coverage,
            zone_coverage=zone_coverage,
        ),
    )


def _offense() -> RosterData:
    return RosterData(team_name="Off", players=[
        _make_player("FastWR", Position.WR, 90, 96, route_running=92, catching=89),
        _make_player("SlotWR", Position.WR, 82, 90, route_running=86, catching=83),
        _make_player("BigTE", Position.TE, 84, 82, strength=90, catching=80, route_running=76),
        _make_player("SpeedHB", Position.HB, 85, 93, acceleration=94, catching=75),
    ])


def _defense() -> RosterData:
    return RosterData(team_name="Def", players=[
        _make_player("CB1", Position.CB, 85, 89, man_coverage=87, zone_coverage=84),
        _make_player("CB2", Position.CB, 76, 83, man_coverage=78, zone_coverage=75),
        _make_player("FS", Position.FS, 80, 86, man_coverage=74, zone_coverage=80),
        _make_player("SS", Position.SS, 78, 82, man_coverage=70, zone_coverage=76),
        _make_player("MLB", Position.MLB, 83, 74, strength=87, awareness=89),
        _make_player("LOLB", Position.LOLB, 80, 78, strength=82),
        _make_player("ROLB", Position.ROLB, 79, 77, strength=80),
    ])


@pytest.fixture
def matchup_ai() -> MatchupAI:
    return MatchupAI()


@pytest.fixture
def read_ai() -> ReadAI:
    return ReadAI()


@pytest.fixture
def offense() -> RosterData:
    return _offense()


@pytest.fixture
def defense() -> RosterData:
    return _defense()


# ===========================================================================
# MatchupAI tests
# ===========================================================================

class TestFindMatchupAdvantages:
    def test_finds_advantages(self, matchup_ai: MatchupAI, offense: RosterData, defense: RosterData):
        advs = matchup_ai.find_matchup_advantages(offense, defense)
        assert len(advs) > 0

    def test_sorted_by_score(self, matchup_ai: MatchupAI, offense: RosterData, defense: RosterData):
        advs = matchup_ai.find_matchup_advantages(offense, defense)
        scores = [a.advantage_score for a in advs]
        assert scores == sorted(scores, reverse=True)

    def test_speed_advantage_detected(self, matchup_ai: MatchupAI):
        """FastWR (96 speed) vs slow MLB (74 speed) should produce a speed advantage."""
        off = RosterData(team_name="Off", players=[
            _make_player("FastWR", Position.WR, 90, 96, route_running=92, catching=89),
        ])
        deff = RosterData(team_name="Def", players=[
            _make_player("SlowMLB", Position.MLB, 83, 74),
        ])
        advs = matchup_ai.find_matchup_advantages(off, deff)
        speed_advs = [a for a in advs if a.advantage_type == AdvantageType.SPEED]
        assert len(speed_advs) >= 1
        assert speed_advs[0].advantage_score > 0

    def test_no_advantage_when_defense_dominant(self, matchup_ai: MatchupAI):
        """If defense outclasses offense, no advantages should surface."""
        off = RosterData(team_name="Off", players=[
            _make_player("SlowWR", Position.WR, 70, 75, route_running=70, catching=72),
        ])
        deff = RosterData(team_name="Def", players=[
            _make_player("EliteCB", Position.CB, 95, 96, man_coverage=95, zone_coverage=93),
        ])
        advs = matchup_ai.find_matchup_advantages(off, deff)
        assert len(advs) == 0


class TestIsolateLeverageMatchup:
    def test_returns_leverage(self, matchup_ai: MatchupAI, offense: RosterData):
        result = matchup_ai.isolate_leverage_matchup(offense.players, "Gun Spread")
        assert result.target_player
        assert result.leverage_score > 0
        assert result.route_suggestion
        assert result.formation_alignment

    def test_no_skill_players(self, matchup_ai: MatchupAI):
        linemen = [_make_player("LT", Position.LT, 80, 65, strength=90)]
        result = matchup_ai.isolate_leverage_matchup(linemen, "I-Form")
        assert result.leverage_score == 0

    def test_best_player_is_chosen(self, matchup_ai: MatchupAI):
        players = [
            _make_player("SlowWR", Position.WR, 75, 78, route_running=75, catching=74),
            _make_player("EliteWR", Position.WR, 95, 97, route_running=95, catching=93),
        ]
        result = matchup_ai.isolate_leverage_matchup(players, "Gun Trips")
        assert result.target_player == "EliteWR"


class TestSuggestMotion:
    def test_wr_gets_jet(self, matchup_ai: MatchupAI):
        from app.schemas.madden26.matchup import LeverageMatchup
        lev = LeverageMatchup(
            target_player="FastWR", target_position=Position.WR,
            matched_against="CB2", matched_position=Position.CB,
            leverage_score=85, route_suggestion="Streak",
            formation_alignment="Wide", reasoning="Speed",
        )
        motion = matchup_ai.suggest_motion_to_create(lev)
        assert motion.motion_type == MotionType.JET
        assert motion.motion_player == "FastWR"
        assert motion.if_man
        assert motion.if_zone

    def test_te_gets_trade(self, matchup_ai: MatchupAI):
        from app.schemas.madden26.matchup import LeverageMatchup
        lev = LeverageMatchup(
            target_player="BigTE", target_position=Position.TE,
            matched_against="MLB", matched_position=Position.MLB,
            leverage_score=70, route_suggestion="Seam",
            formation_alignment="Inline", reasoning="Size",
        )
        motion = matchup_ai.suggest_motion_to_create(lev)
        assert motion.motion_type == MotionType.TRADE

    def test_hb_gets_orbit(self, matchup_ai: MatchupAI):
        from app.schemas.madden26.matchup import LeverageMatchup
        lev = LeverageMatchup(
            target_player="SpeedHB", target_position=Position.HB,
            matched_against="SS", matched_position=Position.SS,
            leverage_score=75, route_suggestion="Wheel",
            formation_alignment="Backfield", reasoning="Speed",
        )
        motion = matchup_ai.suggest_motion_to_create(lev)
        assert motion.motion_type == MotionType.ORBIT


class TestEvaluateGrouping:
    def test_evaluates_11_personnel(self, matchup_ai: MatchupAI, defense: RosterData):
        pkg = PersonnelPackage(
            code="11", description="1 HB, 1 TE, 3 WR",
            available_players={"QB": ["QB1"], "HB": ["HB1"], "TE": ["TE1"], "WR": ["WR1", "WR2", "WR3"], "OL": ["LT", "LG", "C", "RG", "RT"]},
            effectiveness_score=82.0,
        )
        result = matchup_ai.evaluate_personnel_grouping(pkg, defense)
        assert result.grouping_code == "11"
        assert result.effectiveness_score > 0
        assert len(result.strengths) > 0
        assert len(result.recommended_plays) > 0
        assert result.verdict


class TestMatchupHistory:
    def test_returns_results(self, matchup_ai: MatchupAI):
        history = [
            {"game_id": "g1", "opponent_name": "Rival", "user_score": 28, "opponent_score": 14, "timestamp": "2026-01-01"},
            {"game_id": "g2", "opponent_name": "Rival", "user_score": 10, "opponent_score": 24, "timestamp": "2026-01-15"},
        ]
        results = matchup_ai.get_matchup_history("user1", "opp1", history=history)
        assert len(results) == 2
        assert results[0].result == "win"
        assert results[1].result == "loss"

    def test_empty_history(self, matchup_ai: MatchupAI):
        results = matchup_ai.get_matchup_history("user1", "opp1")
        assert results == []


# ===========================================================================
# ReadAI tests
# ===========================================================================

class TestIdentifyCoverage:
    def test_cover_1(self, read_ai: ReadAI):
        info = {"safety_count_deep": 1, "press": True, "soft_coverage": False, "asymmetric": False}
        result = read_ai.identify_coverage(info)
        assert result.primary_coverage == CoverageType.COVER_1
        assert result.confidence in ConfidenceLevel
        assert len(result.indicators) > 0
        assert len(result.vulnerable_zones) > 0

    def test_cover_2(self, read_ai: ReadAI):
        info = {"safety_count_deep": 2, "press": False, "soft_coverage": False, "asymmetric": False}
        result = read_ai.identify_coverage(info)
        assert result.primary_coverage == CoverageType.COVER_2

    def test_cover_3(self, read_ai: ReadAI):
        info = {"safety_count_deep": 1, "press": False}
        result = read_ai.identify_coverage(info)
        assert result.primary_coverage == CoverageType.COVER_3

    def test_cover_4(self, read_ai: ReadAI):
        info = {"safety_count_deep": 2, "press": False, "soft_coverage": True}
        result = read_ai.identify_coverage(info)
        assert result.primary_coverage == CoverageType.COVER_4

    def test_cover_0(self, read_ai: ReadAI):
        info = {"safety_count_deep": 0, "press": True}
        result = read_ai.identify_coverage(info)
        assert result.primary_coverage == CoverageType.COVER_0

    def test_cover_6(self, read_ai: ReadAI):
        info = {"safety_count_deep": 2, "press": False, "soft_coverage": False, "asymmetric": True}
        result = read_ai.identify_coverage(info)
        assert result.primary_coverage == CoverageType.COVER_6


class TestIdentifyBlitz:
    def test_blitz_detected(self, read_ai: ReadAI):
        info = {
            "defenders_near_los": 6,
            "blitz_indicators": ["MLB creeping to A-gap", "SS in the box"],
            "rushed_last_play": 5,
        }
        result = read_ai.identify_blitz(info)
        assert result.blitz_detected is True
        assert result.blitz_probability >= 0.5
        assert result.number_of_rushers >= 5
        assert result.hot_route_suggestion
        assert result.protection_adjustment

    def test_no_blitz(self, read_ai: ReadAI):
        info = {"defenders_near_los": 4, "blitz_indicators": [], "rushed_last_play": 4}
        result = read_ai.identify_blitz(info)
        assert result.blitz_detected is False
        assert result.blitz_probability < 0.5

    def test_cb_blitz_source(self, read_ai: ReadAI):
        info = {
            "defenders_near_los": 6,
            "blitz_indicators": ["CB creeping toward LOS"],
            "rushed_last_play": 6,
        }
        result = read_ai.identify_blitz(info)
        assert result.blitz_detected is True
        assert result.likely_source == BlitzSource.CB


class TestPatternRecognition:
    def test_detects_run_tendency(self, read_ai: ReadAI):
        history = [
            {"situation": "3rd_and_short", "play_type": "run"} for _ in range(8)
        ] + [
            {"situation": "3rd_and_short", "play_type": "pass"} for _ in range(2)
        ]
        patterns = read_ai.get_pattern_recognition(history)
        assert len(patterns) >= 1
        run_pattern = next((p for p in patterns if "run" in p.pattern_name.lower()), None)
        assert run_pattern is not None
        assert run_pattern.frequency >= 0.7
        assert run_pattern.counter_strategy

    def test_empty_history(self, read_ai: ReadAI):
        patterns = read_ai.get_pattern_recognition([])
        assert patterns == []

    def test_small_sample_ignored(self, read_ai: ReadAI):
        """Fewer than 3 plays in a situation should be ignored."""
        history = [
            {"situation": "goal_line", "play_type": "run"},
            {"situation": "goal_line", "play_type": "run"},
        ]
        patterns = read_ai.get_pattern_recognition(history)
        assert len(patterns) == 0


class TestSuggestAudible:
    def test_audible_for_cover_2(self, read_ai: ReadAI):
        from app.schemas.madden26.matchup import CoverageRead, CoverageType, ConfidenceLevel
        coverage = CoverageRead(
            primary_coverage=CoverageType.COVER_2,
            confidence=ConfidenceLevel.HIGH,
            indicators=["Two deep safeties"],
            vulnerable_zones=["Deep middle"],
            recommended_targets=["Seam route"],
        )
        audible = read_ai.suggest_audible(coverage, "HB Dive")
        assert audible.original_play == "HB Dive"
        assert audible.audible_to == "Four Verticals"
        assert audible.confidence == ConfidenceLevel.HIGH
        assert audible.risk_level == MismatchSeverity.LOW

    def test_audible_for_cover_0(self, read_ai: ReadAI):
        from app.schemas.madden26.matchup import CoverageRead, CoverageType, ConfidenceLevel
        coverage = CoverageRead(
            primary_coverage=CoverageType.COVER_0,
            confidence=ConfidenceLevel.MEDIUM,
            indicators=["No deep safety"],
            vulnerable_zones=["Deep"],
            recommended_targets=["Go route"],
        )
        audible = read_ai.suggest_audible(coverage, "PA Crossers")
        assert audible.audible_to == "Quick Slants"
        assert audible.risk_level == MismatchSeverity.MEDIUM
