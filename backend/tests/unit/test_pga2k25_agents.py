"""Unit tests for PGA 2K25 agents — SwingForge, GreenIQ, WindLine, Dispersion, RankedTours."""

from __future__ import annotations

import uuid

import pytest

from app.schemas.pga2k25.swing import (
    ClubCategory,
    ClubMissProfile,
    SwingDiagnosis,
    SwingSystem,
)
from app.schemas.pga2k25.green import (
    GreenSpeed,
    PressurePuttingMode,
    PuttAnalysis,
    PuttDifficulty,
    ThreePuttRisk,
)
from app.schemas.pga2k25.wind import (
    ShotConfidence,
    WindAdjustedSelection,
    WindCondition,
    WindDirection,
)
from app.schemas.pga2k25.dispersion import (
    DispersionMap,
    SessionShot,
)
from app.schemas.pga2k25.ranked import (
    CourseCondition,
    RankedEnvironment,
    RankedTier,
    SocietyPrep,
    TourReport,
    TourType,
)

from app.services.agents.pga2k25.swing_forge import SwingForge
from app.services.agents.pga2k25.green_iq import GreenIQ
from app.services.agents.pga2k25.wind_line import WindLineAI
from app.services.agents.pga2k25.dispersion_maps import DispersionMaps
from app.services.agents.pga2k25.ranked_tours import RankedToursAI


@pytest.fixture
def user_id() -> uuid.UUID:
    return uuid.uuid4()


# ===========================================================================
# SwingForge
# ===========================================================================


class TestSwingForge:
    @pytest.fixture
    def forge(self) -> SwingForge:
        return SwingForge()

    @pytest.mark.asyncio
    async def test_diagnose_evoswing(self, forge: SwingForge, user_id: uuid.UUID) -> None:
        result = await forge.diagnose(user_id, SwingSystem.EVOSWING)
        assert isinstance(result, SwingDiagnosis)
        assert result.swing_system == SwingSystem.EVOSWING
        assert len(result.faults) > 0
        assert len(result.club_profiles) > 0

    @pytest.mark.asyncio
    async def test_diagnose_swing_stick(self, forge: SwingForge, user_id: uuid.UUID) -> None:
        result = await forge.diagnose(user_id, SwingSystem.SWING_STICK)
        assert result.swing_system == SwingSystem.SWING_STICK
        assert any("stick" in f.fault_name for f in result.faults)

    @pytest.mark.asyncio
    async def test_pressure_drift_included(self, forge: SwingForge, user_id: uuid.UUID) -> None:
        result = await forge.diagnose(user_id, include_pressure=True)
        assert len(result.pressure_drift) > 0

    @pytest.mark.asyncio
    async def test_pressure_drift_excluded(self, forge: SwingForge, user_id: uuid.UUID) -> None:
        result = await forge.diagnose(user_id, include_pressure=False)
        assert len(result.pressure_drift) == 0

    @pytest.mark.asyncio
    async def test_overall_consistency_in_range(self, forge: SwingForge, user_id: uuid.UUID) -> None:
        result = await forge.diagnose(user_id)
        assert 0.0 <= result.overall_consistency <= 1.0

    @pytest.mark.asyncio
    async def test_priority_fix_set(self, forge: SwingForge, user_id: uuid.UUID) -> None:
        result = await forge.diagnose(user_id)
        assert result.priority_fix is not None

    @pytest.mark.asyncio
    async def test_get_club_profile(self, forge: SwingForge, user_id: uuid.UUID) -> None:
        profile = await forge.get_club_profile(user_id, ClubCategory.DRIVER)
        assert isinstance(profile, ClubMissProfile)
        assert profile.club_category == ClubCategory.DRIVER


# ===========================================================================
# GreenIQ
# ===========================================================================


class TestGreenIQ:
    @pytest.fixture
    def green(self) -> GreenIQ:
        return GreenIQ()

    @pytest.mark.asyncio
    async def test_analyze_short_putt(self, green: GreenIQ, user_id: uuid.UUID) -> None:
        result = await green.analyze_putt(user_id, "East Lake", 1, 5.0)
        assert isinstance(result, PuttAnalysis)
        assert result.make_probability > 0.5

    @pytest.mark.asyncio
    async def test_analyze_long_putt(self, green: GreenIQ, user_id: uuid.UUID) -> None:
        result = await green.analyze_putt(user_id, "East Lake", 1, 45.0)
        assert result.make_probability < 0.10
        assert result.three_putt_risk.probability > 0.15

    @pytest.mark.asyncio
    async def test_fast_greens_increase_three_putt_risk(self, green: GreenIQ, user_id: uuid.UUID) -> None:
        medium = await green.analyze_putt(user_id, "East Lake", 1, 30.0, green_speed=GreenSpeed.MEDIUM)
        fast = await green.analyze_putt(user_id, "East Lake", 1, 30.0, green_speed=GreenSpeed.TOURNAMENT)
        assert fast.three_putt_risk.probability > medium.three_putt_risk.probability

    @pytest.mark.asyncio
    async def test_pressure_mode_for_long_putt(self, green: GreenIQ, user_id: uuid.UUID) -> None:
        result = await green.analyze_putt(user_id, "East Lake", 1, 50.0)
        assert result.pressure_mode in (
            PressurePuttingMode.SAFE_TWO_PUTT,
            PressurePuttingMode.LAG_AND_TAP,
        )

    @pytest.mark.asyncio
    async def test_tap_in_pressure_mode(self, green: GreenIQ, user_id: uuid.UUID) -> None:
        result = await green.analyze_putt(user_id, "East Lake", 1, 2.0)
        assert result.pressure_mode == PressurePuttingMode.AGGRESSIVE

    @pytest.mark.asyncio
    async def test_three_putt_risk_standalone(self, green: GreenIQ) -> None:
        risk = await green.get_three_putt_risk(40.0, GreenSpeed.FAST)
        assert isinstance(risk, ThreePuttRisk)
        assert risk.probability > 0.0

    @pytest.mark.asyncio
    async def test_read_quality_decreases_with_distance(self, green: GreenIQ, user_id: uuid.UUID) -> None:
        short = await green.analyze_putt(user_id, "East Lake", 1, 5.0)
        long = await green.analyze_putt(user_id, "East Lake", 1, 50.0)
        assert short.read_quality_score > long.read_quality_score


# ===========================================================================
# WindLine AI
# ===========================================================================


class TestWindLineAI:
    @pytest.fixture
    def wind_ai(self) -> WindLineAI:
        return WindLineAI()

    @pytest.mark.asyncio
    async def test_headwind_clubs_up(self, wind_ai: WindLineAI, user_id: uuid.UUID) -> None:
        wind = WindCondition(speed_mph=15.0, direction=WindDirection.HEADWIND)
        result = await wind_ai.get_wind_adjusted_selection(
            user_id, target_distance=150.0, wind=wind,
        )
        assert isinstance(result, WindAdjustedSelection)
        # Wind-adjusted distance should be greater than target (need more club)
        assert result.wind_adjusted_distance > 150.0

    @pytest.mark.asyncio
    async def test_tailwind_clubs_down(self, wind_ai: WindLineAI, user_id: uuid.UUID) -> None:
        wind = WindCondition(speed_mph=15.0, direction=WindDirection.TAILWIND)
        result = await wind_ai.get_wind_adjusted_selection(
            user_id, target_distance=150.0, wind=wind,
        )
        assert result.wind_adjusted_distance < 150.0

    @pytest.mark.asyncio
    async def test_no_wind_minimal_adjustment(self, wind_ai: WindLineAI, user_id: uuid.UUID) -> None:
        wind = WindCondition(speed_mph=0.0, direction=WindDirection.N)
        result = await wind_ai.get_wind_adjusted_selection(
            user_id, target_distance=150.0, wind=wind,
        )
        assert abs(result.wind_adjusted_distance - 150.0) < 5.0

    @pytest.mark.asyncio
    async def test_strong_wind_low_trajectory(self, wind_ai: WindLineAI, user_id: uuid.UUID) -> None:
        wind = WindCondition(speed_mph=25.0, direction=WindDirection.HEADWIND)
        result = await wind_ai.get_wind_adjusted_selection(
            user_id, target_distance=150.0, wind=wind,
        )
        assert result.trajectory.trajectory.value in ("stinger", "low")

    @pytest.mark.asyncio
    async def test_gusting_increases_adjustment(self, wind_ai: WindLineAI, user_id: uuid.UUID) -> None:
        base_wind = WindCondition(speed_mph=10.0, direction=WindDirection.HEADWIND)
        gust_wind = WindCondition(
            speed_mph=10.0, direction=WindDirection.HEADWIND,
            gusting=True, gust_speed_mph=20.0,
        )
        base = await wind_ai.get_wind_adjusted_selection(user_id, 150.0, base_wind)
        gust = await wind_ai.get_wind_adjusted_selection(user_id, 150.0, gust_wind)
        assert gust.wind_adjusted_distance > base.wind_adjusted_distance

    @pytest.mark.asyncio
    async def test_confidence_degrades_with_wind(self, wind_ai: WindLineAI, user_id: uuid.UUID) -> None:
        calm = WindCondition(speed_mph=2.0, direction=WindDirection.N)
        storm = WindCondition(speed_mph=30.0, direction=WindDirection.HEADWIND, gusting=True, gust_speed_mph=40.0)

        calm_r = await wind_ai.get_wind_adjusted_selection(user_id, 150.0, calm)
        storm_r = await wind_ai.get_wind_adjusted_selection(user_id, 150.0, storm)

        confidence_order = [ShotConfidence.HIGH, ShotConfidence.MEDIUM, ShotConfidence.LOW, ShotConfidence.RISKY]
        assert confidence_order.index(calm_r.confidence) <= confidence_order.index(storm_r.confidence)


# ===========================================================================
# Dispersion Maps
# ===========================================================================


class TestDispersionMaps:
    @pytest.fixture
    def disp(self) -> DispersionMaps:
        return DispersionMaps()

    @pytest.fixture
    def sample_shots(self) -> list[SessionShot]:
        sid = uuid.uuid4()
        shots = []
        for i in range(10):
            shots.append(SessionShot(
                session_id=sid,
                hole_number=(i % 18) + 1,
                shot_number=1,
                club="7-iron",
                intended_distance=160.0,
                actual_distance=155.0 + (i % 5),
                offline_yards=-3.0 + (i % 7),
                long_short_yards=-2.0 + (i % 5),
                pressure_situation=i > 7,
            ))
        for i in range(8):
            shots.append(SessionShot(
                session_id=sid,
                hole_number=(i % 18) + 1,
                shot_number=1,
                club="driver",
                intended_distance=280.0,
                actual_distance=270.0 + (i % 10),
                offline_yards=-8.0 + (i % 16),
                long_short_yards=-5.0 + (i % 10),
            ))
        return shots

    @pytest.mark.asyncio
    async def test_build_map_from_shots(
        self, disp: DispersionMaps, user_id: uuid.UUID, sample_shots: list[SessionShot],
    ) -> None:
        result = await disp.build_dispersion_map(user_id, sample_shots)
        assert isinstance(result, DispersionMap)
        assert result.total_shots_analyzed == len(sample_shots)
        assert len(result.clubs) > 0

    @pytest.mark.asyncio
    async def test_club_dispersion_has_grade(
        self, disp: DispersionMaps, user_id: uuid.UUID, sample_shots: list[SessionShot],
    ) -> None:
        result = await disp.build_dispersion_map(user_id, sample_shots)
        for club in result.clubs:
            assert club.consistency_grade != ""

    @pytest.mark.asyncio
    async def test_most_and_least_consistent(
        self, disp: DispersionMaps, user_id: uuid.UUID, sample_shots: list[SessionShot],
    ) -> None:
        result = await disp.build_dispersion_map(user_id, sample_shots)
        assert result.most_consistent_club is not None
        assert result.least_consistent_club is not None

    @pytest.mark.asyncio
    async def test_empty_shots_returns_empty_map(
        self, disp: DispersionMaps, user_id: uuid.UUID,
    ) -> None:
        result = await disp.build_dispersion_map(user_id, [])
        assert result.total_shots_analyzed == 0
        assert len(result.clubs) == 0

    @pytest.mark.asyncio
    async def test_min_shots_filter(
        self, disp: DispersionMaps, user_id: uuid.UUID, sample_shots: list[SessionShot],
    ) -> None:
        result = await disp.build_dispersion_map(
            user_id, sample_shots, min_shots_per_club=20,
        )
        # No club should have 20+ shots in our sample
        assert len(result.clubs) == 0


# ===========================================================================
# RankedTours AI
# ===========================================================================


class TestRankedToursAI:
    @pytest.fixture
    def ranked(self) -> RankedToursAI:
        return RankedToursAI()

    @pytest.mark.asyncio
    async def test_ranked_status(self, ranked: RankedToursAI, user_id: uuid.UUID) -> None:
        result = await ranked.get_ranked_status(
            user_id, tier_points=1500, recent_results=["W", "W", "L", "W", "L"],
        )
        assert isinstance(result, RankedEnvironment)
        assert result.current_tier == RankedTier.GOLD
        assert result.win_rate == 0.6

    @pytest.mark.asyncio
    async def test_tier_progression(self, ranked: RankedToursAI, user_id: uuid.UUID) -> None:
        bronze = await ranked.get_ranked_status(user_id, tier_points=0)
        assert bronze.current_tier == RankedTier.BRONZE

        legend = await ranked.get_ranked_status(user_id, tier_points=5000)
        assert legend.current_tier == RankedTier.LEGEND

    @pytest.mark.asyncio
    async def test_points_to_next_tier(self, ranked: RankedToursAI, user_id: uuid.UUID) -> None:
        result = await ranked.get_ranked_status(user_id, tier_points=400)
        assert result.points_to_next_tier == 100  # 500 - 400

    @pytest.mark.asyncio
    async def test_tour_report(self, ranked: RankedToursAI, user_id: uuid.UUID) -> None:
        result = await ranked.generate_tour_report(
            user_id,
            tour_type=TourType.RANKED_STROKE,
            finishes=[1, 3, 5, 2, 8],
            scores=[-5.0, -3.0, -1.0, -4.0, 1.0],
        )
        assert isinstance(result, TourReport)
        assert result.best_finish == 1
        assert result.worst_finish == 8

    @pytest.mark.asyncio
    async def test_society_prep(self, ranked: RankedToursAI, user_id: uuid.UUID) -> None:
        result = await ranked.prepare_for_society(
            user_id,
            society_name="Test Society",
            event_name="Weekly Event",
            course_name="TPC Sawgrass",
            course_condition=CourseCondition.TOURNAMENT,
        )
        assert isinstance(result, SocietyPrep)
        assert len(result.course_notes) > 0
        assert len(result.preparation_checklist) > 0
        assert result.risk_level == "conservative"

    @pytest.mark.asyncio
    async def test_windy_society_has_wind_prep(self, ranked: RankedToursAI, user_id: uuid.UUID) -> None:
        result = await ranked.prepare_for_society(
            user_id,
            society_name="Test Society",
            event_name="Windy Event",
            course_name="St Andrews",
            course_condition=CourseCondition.WINDY,
        )
        assert any("wind" in note.lower() for note in result.course_notes)
        assert any("wind" in step.lower() for step in result.preparation_checklist)
