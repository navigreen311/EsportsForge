"""Unit tests for PGA 2K25 CourseIQ agent."""

from __future__ import annotations

import uuid

import pytest

from app.schemas.pga2k25.course import (
    CourseAnalysis,
    HoleStrategy,
    LineEV,
    LineType,
)
from app.services.agents.pga2k25.course_iq import CourseIQ


@pytest.fixture
def course_iq() -> CourseIQ:
    return CourseIQ()


@pytest.fixture
def user_id() -> uuid.UUID:
    return uuid.uuid4()


# ---------------------------------------------------------------------------
# analyze_course
# ---------------------------------------------------------------------------


class TestAnalyzeCourse:
    @pytest.mark.asyncio
    async def test_returns_course_analysis(self, course_iq: CourseIQ, user_id: uuid.UUID) -> None:
        result = await course_iq.analyze_course(user_id, "East Lake")
        assert isinstance(result, CourseAnalysis)
        assert result.course_name == "East Lake"

    @pytest.mark.asyncio
    async def test_has_18_holes(self, course_iq: CourseIQ, user_id: uuid.UUID) -> None:
        result = await course_iq.analyze_course(user_id, "East Lake")
        assert len(result.holes) == 18

    @pytest.mark.asyncio
    async def test_each_hole_has_line_options(self, course_iq: CourseIQ, user_id: uuid.UUID) -> None:
        result = await course_iq.analyze_course(user_id, "East Lake")
        for hole in result.holes:
            assert len(hole.line_options) >= 2
            types = [l.line_type for l in hole.line_options]
            assert LineType.SAFE in types
            assert LineType.AGGRESSIVE in types

    @pytest.mark.asyncio
    async def test_target_score_is_reasonable(self, course_iq: CourseIQ, user_id: uuid.UUID) -> None:
        result = await course_iq.analyze_course(user_id, "East Lake")
        # Target score should be near par (60-90 range)
        assert 60 <= result.target_score <= 90

    @pytest.mark.asyncio
    async def test_bogey_danger_holes_identified(self, course_iq: CourseIQ, user_id: uuid.UUID) -> None:
        result = await course_iq.analyze_course(user_id, "East Lake")
        assert isinstance(result.bogey_danger_holes, list)
        for h in result.bogey_danger_holes:
            assert 1 <= h <= 18

    @pytest.mark.asyncio
    async def test_risk_management_score_in_range(self, course_iq: CourseIQ, user_id: uuid.UUID) -> None:
        result = await course_iq.analyze_course(user_id, "East Lake")
        assert 0.0 <= result.risk_management_score <= 1.0

    @pytest.mark.asyncio
    async def test_unknown_course_uses_defaults(self, course_iq: CourseIQ, user_id: uuid.UUID) -> None:
        result = await course_iq.analyze_course(user_id, "Unknown Fantasy Course")
        assert isinstance(result, CourseAnalysis)
        assert len(result.holes) == 18

    @pytest.mark.asyncio
    async def test_conservative_risk_tolerance(self, course_iq: CourseIQ, user_id: uuid.UUID) -> None:
        result = await course_iq.analyze_course(
            user_id, "East Lake", risk_tolerance=0.1,
        )
        # Most holes should recommend safe line
        safe_count = sum(1 for h in result.holes if h.recommended_line == LineType.SAFE)
        assert safe_count >= 14  # Majority should be safe


# ---------------------------------------------------------------------------
# get_hole_strategy
# ---------------------------------------------------------------------------


class TestGetHoleStrategy:
    @pytest.mark.asyncio
    async def test_returns_hole_strategy(self, course_iq: CourseIQ) -> None:
        result = await course_iq.get_hole_strategy("East Lake", 1)
        assert isinstance(result, HoleStrategy)
        assert result.hole_number == 1

    @pytest.mark.asyncio
    async def test_hole_has_shot_plan(self, course_iq: CourseIQ) -> None:
        result = await course_iq.get_hole_strategy("East Lake", 1)
        assert len(result.shot_plan) > 0

    @pytest.mark.asyncio
    async def test_hole_has_hazards(self, course_iq: CourseIQ) -> None:
        result = await course_iq.get_hole_strategy("East Lake", 1)
        assert len(result.hazards) > 0

    @pytest.mark.asyncio
    async def test_bogey_avoidance_notes_present(self, course_iq: CourseIQ) -> None:
        result = await course_iq.get_hole_strategy("East Lake", 1)
        assert result.bogey_avoidance_notes != ""

    @pytest.mark.asyncio
    async def test_key_miss_identified(self, course_iq: CourseIQ) -> None:
        result = await course_iq.get_hole_strategy("East Lake", 1)
        assert result.key_miss != ""


# ---------------------------------------------------------------------------
# Line EV calculations
# ---------------------------------------------------------------------------


class TestLineEV:
    @pytest.mark.asyncio
    async def test_safe_line_has_lower_bogey_risk(self, course_iq: CourseIQ) -> None:
        result = await course_iq.get_hole_strategy("TPC Sawgrass", 17)
        safe = next(l for l in result.line_options if l.line_type == LineType.SAFE)
        agg = next(l for l in result.line_options if l.line_type == LineType.AGGRESSIVE)
        assert safe.bogey_probability <= agg.bogey_probability

    @pytest.mark.asyncio
    async def test_aggressive_line_has_higher_birdie_chance(self, course_iq: CourseIQ) -> None:
        result = await course_iq.get_hole_strategy("TPC Sawgrass", 9)
        safe = next(l for l in result.line_options if l.line_type == LineType.SAFE)
        agg = next(l for l in result.line_options if l.line_type == LineType.AGGRESSIVE)
        assert agg.birdie_probability >= safe.birdie_probability

    @pytest.mark.asyncio
    async def test_probabilities_sum_to_one(self, course_iq: CourseIQ) -> None:
        result = await course_iq.get_hole_strategy("East Lake", 5)
        for line in result.line_options:
            total = (
                line.birdie_probability
                + line.par_probability
                + line.bogey_probability
                + line.double_or_worse_probability
            )
            assert abs(total - 1.0) < 0.05  # Allow small rounding tolerance
