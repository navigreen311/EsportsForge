"""Unit tests for Madden 26 SchemeAI service."""

from __future__ import annotations

import pytest

from app.schemas.madden26.scheme import (
    CoverageMatrix,
    CoverageType,
    SchemeAnalysis,
    SchemeTendency,
    Situation,
)
from app.services.agents.madden26.scheme_ai import SchemeAI


@pytest.fixture
def scheme_ai() -> SchemeAI:
    return SchemeAI()


# ---------------------------------------------------------------------------
# list_schemes
# ---------------------------------------------------------------------------


class TestListSchemes:
    def test_returns_non_empty_list(self, scheme_ai: SchemeAI) -> None:
        schemes = scheme_ai.list_schemes()
        assert isinstance(schemes, list)
        assert len(schemes) > 0

    def test_each_scheme_has_name_and_description(self, scheme_ai: SchemeAI) -> None:
        for s in scheme_ai.list_schemes():
            assert "name" in s
            assert "description" in s


# ---------------------------------------------------------------------------
# analyze_scheme
# ---------------------------------------------------------------------------


class TestAnalyzeScheme:
    @pytest.mark.asyncio
    async def test_west_coast_analysis(self, scheme_ai: SchemeAI) -> None:
        result = await scheme_ai.analyze_scheme("west_coast")
        assert isinstance(result, SchemeAnalysis)
        assert result.scheme == "west_coast"
        assert len(result.strengths) > 0
        assert len(result.weaknesses) > 0
        assert len(result.core_concepts) > 0
        assert isinstance(result.coverage_answers, CoverageMatrix)

    @pytest.mark.asyncio
    async def test_unknown_scheme_returns_default(self, scheme_ai: SchemeAI) -> None:
        result = await scheme_ai.analyze_scheme("totally_unknown_scheme")
        assert isinstance(result, SchemeAnalysis)
        assert result.scheme == "totally_unknown_scheme"

    @pytest.mark.asyncio
    async def test_analysis_has_recommended_playbooks(self, scheme_ai: SchemeAI) -> None:
        result = await scheme_ai.analyze_scheme("west_coast")
        assert isinstance(result.recommended_playbooks, list)
        assert len(result.recommended_playbooks) > 0

    @pytest.mark.asyncio
    async def test_analysis_has_best_formations(self, scheme_ai: SchemeAI) -> None:
        result = await scheme_ai.analyze_scheme("spread")
        assert len(result.best_formations) > 0


# ---------------------------------------------------------------------------
# get_concept_stack
# ---------------------------------------------------------------------------


class TestGetConceptStack:
    @pytest.mark.asyncio
    async def test_returns_concepts_for_matching_down(self, scheme_ai: SchemeAI) -> None:
        concepts = await scheme_ai.get_concept_stack("Gun Doubles", "1st_and_10")
        assert len(concepts) > 0
        for c in concepts:
            assert c.formation == "Gun Doubles"

    @pytest.mark.asyncio
    async def test_stackable_ordering(self, scheme_ai: SchemeAI) -> None:
        concepts = await scheme_ai.get_concept_stack("Gun Spread", "3rd_and_long")
        # Should have at least one concept
        assert len(concepts) >= 1
        # Each concept should have stackable_with populated
        for c in concepts:
            assert isinstance(c.stackable_with, list)

    @pytest.mark.asyncio
    async def test_empty_for_nonmatching_down(self, scheme_ai: SchemeAI) -> None:
        concepts = await scheme_ai.get_concept_stack("Gun Spread", "zzz_no_match")
        assert len(concepts) == 0


# ---------------------------------------------------------------------------
# build_coverage_answer_matrix
# ---------------------------------------------------------------------------


class TestCoverageAnswerMatrix:
    @pytest.mark.asyncio
    async def test_matrix_has_all_coverages(self, scheme_ai: SchemeAI) -> None:
        matrix = await scheme_ai.build_coverage_answer_matrix("west_coast")
        assert isinstance(matrix, CoverageMatrix)
        coverage_types_in_matrix = {a.coverage for a in matrix.answers}
        for ct in CoverageType:
            assert ct in coverage_types_in_matrix, f"Missing answer for {ct}"

    @pytest.mark.asyncio
    async def test_matrix_confidence_in_range(self, scheme_ai: SchemeAI) -> None:
        matrix = await scheme_ai.build_coverage_answer_matrix("spread")
        for answer in matrix.answers:
            assert 0.0 <= answer.confidence <= 1.0

    @pytest.mark.asyncio
    async def test_matrix_has_generated_at(self, scheme_ai: SchemeAI) -> None:
        matrix = await scheme_ai.build_coverage_answer_matrix("west_coast")
        assert matrix.generated_at is not None
        assert len(matrix.generated_at) > 0


# ---------------------------------------------------------------------------
# suggest_hot_routes
# ---------------------------------------------------------------------------


class TestSuggestHotRoutes:
    @pytest.mark.asyncio
    async def test_returns_suggestions_for_cover_0(self, scheme_ai: SchemeAI) -> None:
        routes = await scheme_ai.suggest_hot_routes("PA Boot Over", CoverageType.COVER_0)
        assert len(routes) > 0
        for hr in routes:
            assert hr.receiver
            assert hr.suggested_route
            assert hr.reason

    @pytest.mark.asyncio
    async def test_returns_suggestions_for_man_press(self, scheme_ai: SchemeAI) -> None:
        routes = await scheme_ai.suggest_hot_routes("Mesh Cross", CoverageType.MAN_PRESS)
        assert len(routes) > 0

    @pytest.mark.asyncio
    async def test_fallback_for_unmatched_coverage(self, scheme_ai: SchemeAI) -> None:
        routes = await scheme_ai.suggest_hot_routes("Some Play", CoverageType.COVER_6)
        assert len(routes) >= 1  # fallback default


# ---------------------------------------------------------------------------
# get_situation_plays
# ---------------------------------------------------------------------------


class TestGetSituationPlays:
    @pytest.mark.asyncio
    async def test_red_zone_plays(self, scheme_ai: SchemeAI) -> None:
        plays = await scheme_ai.get_situation_plays("west_coast", Situation.RED_ZONE)
        assert len(plays) > 0
        for p in plays:
            assert p.play_name
            assert p.formation

    @pytest.mark.asyncio
    async def test_two_minute_plays(self, scheme_ai: SchemeAI) -> None:
        plays = await scheme_ai.get_situation_plays("spread", Situation.TWO_MINUTE)
        assert len(plays) > 0

    @pytest.mark.asyncio
    async def test_unmatched_situation_returns_default(self, scheme_ai: SchemeAI) -> None:
        plays = await scheme_ai.get_situation_plays("spread", Situation.FOURTH_DOWN)
        assert len(plays) >= 1  # fallback default


# ---------------------------------------------------------------------------
# detect_scheme_tendency
# ---------------------------------------------------------------------------


class TestDetectSchemeTendency:
    @pytest.mark.asyncio
    async def test_empty_history(self, scheme_ai: SchemeAI) -> None:
        result = await scheme_ai.detect_scheme_tendency([])
        assert isinstance(result, SchemeTendency)
        assert result.total_plays_analyzed == 0
        assert result.predictability_score == 0.0

    @pytest.mark.asyncio
    async def test_predictable_history(self, scheme_ai: SchemeAI) -> None:
        """A history with the same play 10 times should be highly predictable."""
        history = [
            {"play_name": "Mesh Cross", "formation": "Gun Bunch", "play_type": "pass"}
        ] * 10
        result = await scheme_ai.detect_scheme_tendency(history)
        assert result.total_plays_analyzed == 10
        assert result.predictability_score > 0.5
        assert len(result.most_called_plays) > 0
        assert result.most_called_plays[0]["play"] == "Mesh Cross"

    @pytest.mark.asyncio
    async def test_balanced_history(self, scheme_ai: SchemeAI) -> None:
        """Diverse play calling should yield lower predictability."""
        history = [
            {"play_name": f"Play_{i}", "formation": f"Form_{i % 4}", "play_type": "pass" if i % 2 else "run"}
            for i in range(20)
        ]
        result = await scheme_ai.detect_scheme_tendency(history)
        assert result.total_plays_analyzed == 20
        assert result.predictability_score < 0.5

    @pytest.mark.asyncio
    async def test_run_heavy_warning(self, scheme_ai: SchemeAI) -> None:
        history = [
            {"play_name": f"Run_{i}", "formation": "I-Form", "play_type": "run"}
            for i in range(8)
        ] + [
            {"play_name": "Pass_1", "formation": "Gun", "play_type": "pass"},
            {"play_name": "Pass_2", "formation": "Gun", "play_type": "pass"},
        ]
        result = await scheme_ai.detect_scheme_tendency(history)
        assert result.run_pass_ratio["run"] > 0.7
        assert any("run" in s.lower() for s in result.predictable_situations)
