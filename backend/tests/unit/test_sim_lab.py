"""Unit tests for SimLab AI — scenario sandbox and decision tree builder."""

from __future__ import annotations

import pytest

from app.schemas.simulation import (
    DecisionTree,
    GameState,
    Scenario,
    ScenarioType,
    SimulationResult,
)
from app.services.backbone import sim_lab


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_state(**overrides) -> GameState:
    defaults = {
        "title": "madden26",
        "quarter": 4,
        "time_remaining": 120.0,
        "score_home": 21,
        "score_away": 24,
        "possession": "home",
        "down": 3,
        "yards_to_go": 7,
        "field_position": 55,
    }
    defaults.update(overrides)
    return GameState(**defaults)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture(autouse=True)
def _clear_stores():
    """Reset in-memory stores between tests."""
    sim_lab._user_scenarios.clear()
    sim_lab._scenario_library.clear()
    yield


# ===========================================================================
# create_scenario
# ===========================================================================

class TestCreateScenario:
    def test_returns_scenario_with_id(self):
        state = _make_state()
        scenario = sim_lab.create_scenario(state, what_if="Opponent switches to zone")
        assert isinstance(scenario, Scenario)
        assert scenario.id
        assert scenario.what_if == "Opponent switches to zone"

    def test_default_name_from_what_if(self):
        state = _make_state()
        scenario = sim_lab.create_scenario(state, what_if="Run up the middle")
        assert scenario.name == "Run up the middle"

    def test_unnamed_when_no_what_if(self):
        state = _make_state()
        scenario = sim_lab.create_scenario(state)
        assert scenario.name == "Unnamed scenario"

    def test_preserves_game_state(self):
        state = _make_state(quarter=2, score_home=14)
        scenario = sim_lab.create_scenario(state)
        assert scenario.base_state.quarter == 2
        assert scenario.base_state.score_home == 14


# ===========================================================================
# simulate
# ===========================================================================

class TestSimulate:
    def test_returns_simulation_result(self):
        state = _make_state()
        scenario = sim_lab.create_scenario(state, what_if="Blitz from the edge")
        result = sim_lab.simulate(scenario, depth=3)
        assert isinstance(result, SimulationResult)
        assert result.scenario_id == scenario.id

    def test_decision_tree_has_correct_depth(self):
        state = _make_state()
        scenario = sim_lab.create_scenario(state)
        result = sim_lab.simulate(scenario, depth=2)
        assert result.decision_tree.depth == 2

    def test_best_path_is_populated(self):
        state = _make_state()
        scenario = sim_lab.create_scenario(state)
        result = sim_lab.simulate(scenario, depth=3)
        assert len(result.decision_tree.best_path) >= 1

    def test_win_probability_in_range(self):
        state = _make_state()
        scenario = sim_lab.create_scenario(state)
        result = sim_lab.simulate(scenario)
        assert 0.0 <= result.win_probability <= 1.0

    def test_analysis_is_non_empty(self):
        state = _make_state()
        scenario = sim_lab.create_scenario(state)
        result = sim_lab.simulate(scenario)
        assert len(result.analysis) > 0


# ===========================================================================
# get_best_response
# ===========================================================================

class TestGetBestResponse:
    def test_advantage_returns_conservative(self):
        state = _make_state(score_home=35, score_away=7)
        scenario = sim_lab.create_scenario(state)
        resp = sim_lab.get_best_response(scenario)
        assert "advantage" in resp.lower() or "clock" in resp.lower()

    def test_trailing_returns_aggressive(self):
        state = _make_state(score_home=7, score_away=28)
        scenario = sim_lab.create_scenario(state)
        resp = sim_lab.get_best_response(scenario)
        assert "aggress" in resp.lower() or "desper" in resp.lower()

    def test_returns_non_empty_string(self):
        state = _make_state()
        scenario = sim_lab.create_scenario(state)
        resp = sim_lab.get_best_response(scenario)
        assert isinstance(resp, str) and len(resp) > 0


# ===========================================================================
# build_decision_tree
# ===========================================================================

class TestBuildDecisionTree:
    def test_returns_decision_tree(self):
        tree = sim_lab.build_decision_tree("3rd and long", depth=2)
        assert isinstance(tree, DecisionTree)

    def test_root_label_matches_situation(self):
        tree = sim_lab.build_decision_tree("Blitz read", depth=2)
        assert tree.root.label == "Blitz read"

    def test_depth_is_clamped(self):
        tree = sim_lab.build_decision_tree("test", depth=10)
        assert tree.depth == 6  # max is 6

    def test_children_exist_at_depth_greater_than_1(self):
        tree = sim_lab.build_decision_tree("test", depth=2)
        assert len(tree.root.children) > 0

    def test_depth_1_has_no_grandchildren(self):
        tree = sim_lab.build_decision_tree("test", depth=1)
        for child in tree.root.children:
            assert len(child.children) == 0


# ===========================================================================
# get_scenario_library
# ===========================================================================

class TestScenarioLibrary:
    def test_returns_non_empty_for_any_title(self):
        library = sim_lab.get_scenario_library("madden26")
        assert len(library) > 0

    def test_all_scenarios_have_correct_title(self):
        library = sim_lab.get_scenario_library("nba2k26")
        for s in library:
            assert s.base_state.title == "nba2k26"

    def test_caches_library(self):
        lib1 = sim_lab.get_scenario_library("madden26")
        lib2 = sim_lab.get_scenario_library("madden26")
        assert lib1[0].id == lib2[0].id


# ===========================================================================
# save_scenario
# ===========================================================================

class TestSaveScenario:
    def test_save_and_retrieve(self):
        state = _make_state()
        scenario = sim_lab.create_scenario(state, what_if="Test save")
        sim_lab.save_scenario("user1", scenario)
        assert "user1" in sim_lab._user_scenarios
        assert any(s.id == scenario.id for s in sim_lab._user_scenarios["user1"])

    def test_no_duplicates_on_re_save(self):
        state = _make_state()
        scenario = sim_lab.create_scenario(state, what_if="Dup test")
        sim_lab.save_scenario("user1", scenario)
        sim_lab.save_scenario("user1", scenario)
        assert len([s for s in sim_lab._user_scenarios["user1"] if s.id == scenario.id]) == 1
