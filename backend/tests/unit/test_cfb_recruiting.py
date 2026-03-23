"""Tests for RecruitingIQ — board optimization, evaluation, position needs, roadmap."""

from __future__ import annotations

import pytest

from app.schemas.cfb26.recruiting import (
    DynastyStateInput,
    PipelineStage,
    Position,
    RecruitData,
    RecruitPriority,
    RosterInput,
)
from app.services.agents.cfb26.recruiting_iq import RecruitingIQ


@pytest.fixture
def engine() -> RecruitingIQ:
    """Fresh RecruitingIQ instance per test."""
    return RecruitingIQ()


def _make_roster(positions: list[str] | None = None) -> list[dict]:
    """Helper to build a basic roster."""
    if positions is None:
        positions = ["QB", "QB", "RB", "RB", "RB", "WR", "WR", "WR", "WR",
                      "TE", "TE", "OL", "OL", "OL", "OL", "OL",
                      "DL", "DL", "DL", "DL", "LB", "LB", "LB", "LB",
                      "CB", "CB", "CB", "S", "S", "S", "K", "P"]
    return [
        {
            "name": f"Player_{i}",
            "position": pos,
            "overall": 72 + (i % 10),
            "year": ["freshman", "sophomore", "junior", "senior"][i % 4],
            "development": "normal",
        }
        for i, pos in enumerate(positions)
    ]


def _make_recruit(**overrides) -> RecruitData:
    """Helper to build a RecruitData."""
    defaults = {
        "name": "Test Recruit",
        "position": Position.QB,
        "star_rating": 4,
        "overall_rating": 82,
        "state": "TX",
        "interest_level": 0.6,
        "pipeline_stage": PipelineStage.SCOUTED,
    }
    defaults.update(overrides)
    return RecruitData(**defaults)


# ---------------------------------------------------------------------------
# Recruit evaluation
# ---------------------------------------------------------------------------

class TestEvaluateRecruit:
    """Tests for evaluate_recruit."""

    def test_five_star_high_grade(self, engine: RecruitingIQ) -> None:
        recruit = _make_recruit(star_rating=5, overall_rating=95, interest_level=0.9)
        result = engine.evaluate_recruit(recruit, "spread_rpo")
        assert result.overall_grade >= 0.6
        assert result.development_ceiling >= 0.9
        assert result.worth_pursuing is True

    def test_one_star_low_grade(self, engine: RecruitingIQ) -> None:
        recruit = _make_recruit(star_rating=1, overall_rating=55, interest_level=0.1)
        result = engine.evaluate_recruit(recruit, "spread_rpo")
        assert result.overall_grade < 0.5
        assert result.development_ceiling < 0.4

    def test_scheme_fit_affects_grade(self, engine: RecruitingIQ) -> None:
        wr = _make_recruit(position=Position.WR, star_rating=4)
        # Air Raid values WR highly, triple option does not
        air_raid_eval = engine.evaluate_recruit(wr, "air_raid")
        triple_eval = engine.evaluate_recruit(wr, "triple_option")
        assert air_raid_eval.scheme_fit > triple_eval.scheme_fit

    def test_evaluation_has_reasoning(self, engine: RecruitingIQ) -> None:
        recruit = _make_recruit()
        result = engine.evaluate_recruit(recruit, "spread_rpo")
        assert len(result.reasoning) > 0
        assert recruit.position.value in result.reasoning

    def test_position_need_affects_grade(self, engine: RecruitingIQ) -> None:
        from app.schemas.cfb26.recruiting import PositionNeed
        need_map = {
            Position.QB: PositionNeed(
                position=Position.QB,
                urgency=RecruitPriority.MUST_HAVE,
                current_depth=1,
                ideal_depth=3,
            ),
        }
        recruit = _make_recruit(position=Position.QB)
        with_need = engine.evaluate_recruit(recruit, "spread_rpo", need_map)

        no_need = engine.evaluate_recruit(recruit, "spread_rpo", {})
        assert with_need.position_need_match > no_need.position_need_match


# ---------------------------------------------------------------------------
# Position needs
# ---------------------------------------------------------------------------

class TestPositionNeeds:
    """Tests for get_position_needs."""

    def test_thin_position_flagged(self, engine: RecruitingIQ) -> None:
        # Roster with no QBs
        roster = _make_roster(["RB", "WR", "WR", "OL", "OL", "DL", "LB", "CB", "S"])
        result = engine.get_position_needs(RosterInput(players=roster))
        qb_need = next(n for n in result if n.position == Position.QB)
        assert qb_need.urgency in (RecruitPriority.MUST_HAVE, RecruitPriority.HIGH)
        assert qb_need.current_depth == 0

    def test_deep_position_low_priority(self, engine: RecruitingIQ) -> None:
        # Roster loaded at WR
        positions = ["WR"] * 8 + ["QB", "RB", "OL", "DL", "LB", "CB", "S"]
        roster = _make_roster(positions)
        result = engine.get_position_needs(RosterInput(players=roster))
        wr_need = next(n for n in result if n.position == Position.WR)
        assert wr_need.urgency in (RecruitPriority.LOW, RecruitPriority.DEPTH)

    def test_graduating_seniors_increase_urgency(self, engine: RecruitingIQ) -> None:
        roster = [
            {"name": "QB1", "position": "QB", "overall": 85, "year": "senior"},
            {"name": "QB2", "position": "QB", "overall": 70, "year": "senior"},
        ]
        result = engine.get_position_needs(RosterInput(players=roster))
        qb_need = next(n for n in result if n.position == Position.QB)
        # Both QBs graduating should be urgent
        assert qb_need.graduating_count == 2

    def test_needs_sorted_by_urgency(self, engine: RecruitingIQ) -> None:
        roster = _make_roster()
        result = engine.get_position_needs(RosterInput(players=roster))
        priority_order = {
            RecruitPriority.MUST_HAVE: 0,
            RecruitPriority.HIGH: 1,
            RecruitPriority.MEDIUM: 2,
            RecruitPriority.LOW: 3,
            RecruitPriority.DEPTH: 4,
        }
        for i in range(len(result) - 1):
            assert priority_order[result[i].urgency] <= priority_order[result[i + 1].urgency]


# ---------------------------------------------------------------------------
# Recruiting board
# ---------------------------------------------------------------------------

class TestRecruitingBoard:
    """Tests for optimize_recruiting_board."""

    def test_board_ranks_recruits(self, engine: RecruitingIQ) -> None:
        dynasty = DynastyStateInput(
            user_id="user_1",
            school="Alabama",
            current_roster=_make_roster(),
            available_recruits=[
                {
                    "name": "Recruit A",
                    "position": "QB",
                    "star_rating": 5,
                    "overall_rating": 95,
                    "interest_level": 0.9,
                    "pipeline_stage": "scouted",
                },
                {
                    "name": "Recruit B",
                    "position": "WR",
                    "star_rating": 3,
                    "overall_rating": 72,
                    "interest_level": 0.4,
                    "pipeline_stage": "identified",
                },
            ],
            scholarships_available=25,
        )
        board = engine.optimize_recruiting_board(dynasty)
        assert len(board.entries) == 2
        assert board.entries[0].rank_on_board == 1
        assert board.entries[1].rank_on_board == 2
        assert board.user_id == "user_1"
        assert board.school == "Alabama"

    def test_empty_board(self, engine: RecruitingIQ) -> None:
        dynasty = DynastyStateInput(
            user_id="user_1",
            school="TeamX",
            current_roster=_make_roster(),
            available_recruits=[],
        )
        board = engine.optimize_recruiting_board(dynasty)
        assert len(board.entries) == 0

    def test_board_entries_have_action_items(self, engine: RecruitingIQ) -> None:
        dynasty = DynastyStateInput(
            user_id="user_1",
            school="Ohio State",
            current_roster=_make_roster(),
            available_recruits=[
                {
                    "name": "Top QB",
                    "position": "QB",
                    "star_rating": 5,
                    "overall_rating": 96,
                    "interest_level": 0.3,
                    "pipeline_stage": "identified",
                },
            ],
        )
        board = engine.optimize_recruiting_board(dynasty)
        assert len(board.entries) == 1
        assert len(board.entries[0].action_items) > 0


# ---------------------------------------------------------------------------
# Roster roadmap
# ---------------------------------------------------------------------------

class TestRosterRoadmap:
    """Tests for build_roster_roadmap."""

    def test_roadmap_basic(self, engine: RecruitingIQ) -> None:
        roster = _make_roster()
        roadmap = engine.build_roster_roadmap(
            current_roster=roster,
            years=3,
            user_id="user_1",
            school="Clemson",
        )
        assert roadmap.total_years == 3
        assert len(roadmap.year_plans) == 3
        assert roadmap.school == "Clemson"
        assert roadmap.starting_overall > 0

    def test_roadmap_has_championship_window(self, engine: RecruitingIQ) -> None:
        roster = _make_roster()
        roadmap = engine.build_roster_roadmap(
            current_roster=roster, years=5,
        )
        assert "Year" in roadmap.championship_window
        assert "peak" in roadmap.championship_window.lower()

    def test_roadmap_projects_improvement(self, engine: RecruitingIQ) -> None:
        # Young roster should improve over time
        roster = [
            {"name": f"P_{i}", "position": "QB", "overall": 65,
             "year": "freshman", "development": "star"}
            for i in range(5)
        ]
        roadmap = engine.build_roster_roadmap(current_roster=roster, years=3)
        assert roadmap.target_overall > roadmap.starting_overall

    def test_single_year_roadmap(self, engine: RecruitingIQ) -> None:
        roster = _make_roster()
        roadmap = engine.build_roster_roadmap(current_roster=roster, years=1)
        assert roadmap.total_years == 1
        assert len(roadmap.year_plans) == 1
