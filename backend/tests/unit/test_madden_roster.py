"""Unit tests for RosterIQ — Madden 26 personnel analysis engine."""

from __future__ import annotations

import pytest

from app.schemas.madden26.roster import (
    MismatchSeverity,
    Player,
    PlayerRating,
    Position,
    RosterData,
    SchemeType,
)
from app.services.agents.madden26.roster_iq import RosterIQ


# ---------------------------------------------------------------------------
# Fixtures
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
    throw_power: int | None = None,
    throw_accuracy_short: int | None = None,
    throw_accuracy_mid: int | None = None,
    throw_accuracy_deep: int | None = None,
    man_coverage: int | None = None,
    zone_coverage: int | None = None,
    team: str = "Test Team",
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
            throw_power=throw_power,
            throw_accuracy_short=throw_accuracy_short,
            throw_accuracy_mid=throw_accuracy_mid,
            throw_accuracy_deep=throw_accuracy_deep,
            man_coverage=man_coverage,
            zone_coverage=zone_coverage,
        ),
    )


def _build_offense_roster() -> RosterData:
    """Minimal viable offense roster with all required positions."""
    players = [
        _make_player("QB1", Position.QB, 88, 78, throw_power=92, throw_accuracy_short=90),
        _make_player("HB1", Position.HB, 85, 92, acceleration=93, agility=90, catching=75),
        _make_player("WR1", Position.WR, 90, 95, route_running=92, catching=89),
        _make_player("WR2", Position.WR, 82, 91, route_running=85, catching=83),
        _make_player("WR3", Position.WR, 78, 88, route_running=80, catching=78),
        _make_player("TE1", Position.TE, 83, 82, catching=80, route_running=76, strength=85),
        _make_player("LT1", Position.LT, 84, 72, strength=90),
        _make_player("LG1", Position.LG, 80, 68, strength=88),
        _make_player("C1", Position.C, 82, 65, strength=86, awareness=88),
        _make_player("RG1", Position.RG, 79, 67, strength=87),
        _make_player("RT1", Position.RT, 81, 70, strength=89),
    ]
    return RosterData(team_name="Test Offense", players=players)


def _build_defense_roster() -> RosterData:
    """Minimal viable defense roster."""
    players = [
        _make_player("CB1", Position.CB, 85, 90, man_coverage=88, zone_coverage=85),
        _make_player("CB2", Position.CB, 78, 85, man_coverage=80, zone_coverage=78),
        _make_player("FS1", Position.FS, 82, 87, man_coverage=75, zone_coverage=82),
        _make_player("SS1", Position.SS, 80, 83, man_coverage=72, zone_coverage=78),
        _make_player("MLB1", Position.MLB, 84, 76, awareness=88, strength=86),
        _make_player("LOLB1", Position.LOLB, 81, 80, strength=82),
        _make_player("ROLB1", Position.ROLB, 79, 78, strength=80),
        _make_player("LE1", Position.LE, 83, 75, strength=90),
        _make_player("RE1", Position.RE, 80, 77, strength=88),
        _make_player("DT1", Position.DT, 82, 65, strength=95),
    ]
    return RosterData(team_name="Test Defense", players=players)


@pytest.fixture
def roster_iq() -> RosterIQ:
    return RosterIQ()


@pytest.fixture
def offense_roster() -> RosterData:
    return _build_offense_roster()


@pytest.fixture
def defense_roster() -> RosterData:
    return _build_defense_roster()


# ---------------------------------------------------------------------------
# Tests: analyze_roster
# ---------------------------------------------------------------------------

class TestAnalyzeRoster:
    def test_returns_valid_analysis(self, roster_iq: RosterIQ, offense_roster: RosterData):
        result = roster_iq.analyze_roster(offense_roster)
        assert result.team_name == "Test Offense"
        assert result.overall_grade in ("A+", "A", "A-", "B+", "B", "B-", "C+", "C", "C-", "D+", "D", "D-", "F")
        assert 0 <= result.overall_score <= 100
        assert len(result.position_grades) > 0
        assert len(result.top_players) > 0
        assert result.summary

    def test_position_grades_have_scores(self, roster_iq: RosterIQ, offense_roster: RosterData):
        result = roster_iq.analyze_roster(offense_roster)
        for pg in result.position_grades:
            assert 0 <= pg.score <= 100
            assert pg.grade
            assert pg.group

    def test_top_players_sorted_by_overall(self, roster_iq: RosterIQ, offense_roster: RosterData):
        result = roster_iq.analyze_roster(offense_roster)
        overalls = [p.ratings.overall for p in result.top_players]
        assert overalls == sorted(overalls, reverse=True)

    def test_scheme_fit_is_valid(self, roster_iq: RosterIQ, offense_roster: RosterData):
        result = roster_iq.analyze_roster(offense_roster)
        assert result.scheme_fit in SchemeType


# ---------------------------------------------------------------------------
# Tests: get_personnel_packages
# ---------------------------------------------------------------------------

class TestGetPersonnelPackages:
    def test_returns_packages(self, roster_iq: RosterIQ, offense_roster: RosterData):
        packages = roster_iq.get_personnel_packages(offense_roster)
        assert len(packages) >= 1
        codes = [p.code for p in packages]
        assert "11" in codes  # Should always be available with 3 WR, 1 TE, 1 HB

    def test_packages_sorted_by_effectiveness(self, roster_iq: RosterIQ, offense_roster: RosterData):
        packages = roster_iq.get_personnel_packages(offense_roster)
        scores = [p.effectiveness_score for p in packages]
        assert scores == sorted(scores, reverse=True)

    def test_package_has_required_fields(self, roster_iq: RosterIQ, offense_roster: RosterData):
        packages = roster_iq.get_personnel_packages(offense_roster)
        for pkg in packages:
            assert pkg.code
            assert pkg.description
            assert "QB" in pkg.available_players
            assert "OL" in pkg.available_players
            assert pkg.effectiveness_score >= 0


# ---------------------------------------------------------------------------
# Tests: detect_speed_mismatches
# ---------------------------------------------------------------------------

class TestDetectSpeedMismatches:
    def test_finds_mismatches(self, roster_iq: RosterIQ, offense_roster: RosterData, defense_roster: RosterData):
        mismatches = roster_iq.detect_speed_mismatches(offense_roster, defense_roster)
        assert len(mismatches) > 0

    def test_mismatches_sorted_by_delta(self, roster_iq: RosterIQ, offense_roster: RosterData, defense_roster: RosterData):
        mismatches = roster_iq.detect_speed_mismatches(offense_roster, defense_roster)
        deltas = [m.speed_delta for m in mismatches]
        assert deltas == sorted(deltas, reverse=True)

    def test_wr1_vs_slow_lb_is_critical(self, roster_iq: RosterIQ):
        """WR1 (speed 95) vs MLB (speed 72) = 23-point gap -> critical."""
        off = RosterData(team_name="Off", players=[
            _make_player("Speedster", Position.WR, 90, 95, route_running=90, catching=88),
        ])
        deff = RosterData(team_name="Def", players=[
            _make_player("SlowLB", Position.MLB, 84, 72),
        ])
        mismatches = roster_iq.detect_speed_mismatches(off, deff)
        assert len(mismatches) == 1
        assert mismatches[0].severity == MismatchSeverity.CRITICAL
        assert mismatches[0].speed_delta == 23

    def test_no_mismatch_when_defense_faster(self, roster_iq: RosterIQ):
        off = RosterData(team_name="Off", players=[
            _make_player("SlowTE", Position.TE, 78, 75),
        ])
        deff = RosterData(team_name="Def", players=[
            _make_player("FastCB", Position.CB, 85, 95),
        ])
        mismatches = roster_iq.detect_speed_mismatches(off, deff)
        assert len(mismatches) == 0

    def test_exploit_tip_present(self, roster_iq: RosterIQ, offense_roster: RosterData, defense_roster: RosterData):
        mismatches = roster_iq.detect_speed_mismatches(offense_roster, defense_roster)
        for m in mismatches:
            assert m.exploit_tip


# ---------------------------------------------------------------------------
# Tests: recommend_scheme_for_roster
# ---------------------------------------------------------------------------

class TestRecommendScheme:
    def test_returns_scheme(self, roster_iq: RosterIQ, offense_roster: RosterData):
        rec = roster_iq.recommend_scheme_for_roster(offense_roster)
        assert rec.primary_scheme in SchemeType
        assert 0 <= rec.confidence <= 1.0
        assert rec.reasoning
        assert len(rec.key_players_for_scheme) > 0
        assert len(rec.playbook_suggestions) > 0

    def test_speed_roster_favors_spread(self, roster_iq: RosterIQ):
        """A roster heavy on speed/route running should lean spread or air raid."""
        players = [
            _make_player("QB", Position.QB, 88, 85, throw_power=90, throw_accuracy_short=88, throw_accuracy_deep=90),
            _make_player("WR1", Position.WR, 92, 97, route_running=94, catching=91),
            _make_player("WR2", Position.WR, 88, 95, route_running=90, catching=87),
            _make_player("WR3", Position.WR, 85, 93, route_running=88, catching=85),
            _make_player("HB", Position.HB, 80, 90, acceleration=92, catching=78),
            _make_player("TE", Position.TE, 78, 84, catching=76, route_running=72),
            _make_player("LT", Position.LT, 75, 70, strength=82),
            _make_player("LG", Position.LG, 73, 68, strength=80),
            _make_player("C", Position.C, 74, 65, strength=79),
            _make_player("RG", Position.RG, 72, 66, strength=78),
            _make_player("RT", Position.RT, 74, 69, strength=81),
        ]
        roster = RosterData(team_name="Speed Team", players=players)
        rec = roster_iq.recommend_scheme_for_roster(roster)
        assert rec.primary_scheme in (SchemeType.SPREAD, SchemeType.AIR_RAID, SchemeType.RPO_HEAVY)


# ---------------------------------------------------------------------------
# Tests: get_patch_adjusted_ratings
# ---------------------------------------------------------------------------

class TestPatchAdjustedRatings:
    def test_buff(self, roster_iq: RosterIQ):
        result = roster_iq.get_patch_adjusted_ratings(
            "TestPlayer", "1.06",
            base_ratings=PlayerRating(overall=82, speed=85, acceleration=83, agility=80, strength=78, awareness=80),
            patch_deltas={"speed": 3, "acceleration": 2},
        )
        assert result.net_impact == "buffed"
        assert result.adjusted_overall > result.original_overall
        assert result.rating_changes["speed"] == 3

    def test_nerf(self, roster_iq: RosterIQ):
        result = roster_iq.get_patch_adjusted_ratings(
            "NerfedPlayer", "1.06",
            base_ratings=PlayerRating(overall=90, speed=92, acceleration=90, agility=88, strength=80, awareness=85),
            patch_deltas={"speed": -5, "acceleration": -3},
        )
        assert result.net_impact == "nerfed"
        assert result.adjusted_overall < result.original_overall

    def test_unchanged(self, roster_iq: RosterIQ):
        result = roster_iq.get_patch_adjusted_ratings(
            "Unchanged", "1.06",
            base_ratings=PlayerRating(overall=80, speed=80, acceleration=80, agility=80, strength=80, awareness=80),
            patch_deltas={},
        )
        assert result.net_impact == "unchanged"
        assert result.adjusted_overall == result.original_overall


# ---------------------------------------------------------------------------
# Tests: get_ratings_impact_alert
# ---------------------------------------------------------------------------

class TestRatingsImpactAlert:
    def test_parses_known_changes(self, roster_iq: RosterIQ):
        changes = roster_iq.get_ratings_impact_alert(
            "Patch 1.06 notes...",
            known_changes=[
                {"player_name": "Player A", "position": "QB", "team": "Team1", "attribute": "throw_power", "old_value": 88, "new_value": 92},
                {"player_name": "Player B", "position": "CB", "team": "Team2", "attribute": "speed", "old_value": 90, "new_value": 87},
            ],
        )
        assert len(changes) == 2
        # Sorted by abs(delta) desc — Player A (+4) first, Player B (-3) second
        assert changes[0].player_name == "Player A"
        assert changes[0].delta == 4
        assert changes[1].delta == -3

    def test_empty_when_no_changes(self, roster_iq: RosterIQ):
        changes = roster_iq.get_ratings_impact_alert("No changes this patch")
        assert changes == []


# ---------------------------------------------------------------------------
# Tests: find_hidden_gems
# ---------------------------------------------------------------------------

class TestFindHiddenGems:
    def test_finds_gems(self, roster_iq: RosterIQ):
        """A player with high scheme-relevant stats but low OVR should be a gem."""
        players = [
            _make_player("QB", Position.QB, 85, 80, throw_power=88, throw_accuracy_short=86),
            _make_player("Underrated WR", Position.WR, 72, 93, route_running=90, catching=87, agility=91),
            _make_player("Star WR", Position.WR, 92, 94, route_running=93, catching=92),
            _make_player("HB", Position.HB, 80, 85, acceleration=87, catching=70),
            _make_player("TE", Position.TE, 78, 80, catching=75),
            _make_player("LT", Position.LT, 80, 70, strength=85),
            _make_player("LG", Position.LG, 78, 68, strength=83),
            _make_player("C", Position.C, 79, 65, strength=82),
            _make_player("RG", Position.RG, 77, 66, strength=81),
            _make_player("RT", Position.RT, 79, 69, strength=84),
        ]
        roster = RosterData(team_name="Gem Test", players=players)
        gems = roster_iq.find_hidden_gems(roster)
        gem_names = [g.player.name for g in gems]
        assert "Underrated WR" in gem_names

    def test_no_gems_for_elite_roster(self, roster_iq: RosterIQ):
        """All 90+ OVR players should not be flagged as hidden gems."""
        players = [
            _make_player("QB", Position.QB, 95, 88, throw_power=95),
            _make_player("WR1", Position.WR, 96, 97, route_running=95, catching=94),
            _make_player("HB", Position.HB, 93, 94, acceleration=95, catching=85),
            _make_player("LT", Position.LT, 92, 72, strength=95),
            _make_player("LG", Position.LG, 90, 68, strength=92),
            _make_player("C", Position.C, 91, 65, strength=91),
            _make_player("RG", Position.RG, 90, 67, strength=90),
            _make_player("RT", Position.RT, 91, 70, strength=93),
        ]
        roster = RosterData(team_name="Elite", players=players)
        gems = roster_iq.find_hidden_gems(roster)
        assert len(gems) == 0
