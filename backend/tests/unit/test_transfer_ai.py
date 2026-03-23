"""Unit tests for TransferAI — practice-to-competition transfer engine."""

from __future__ import annotations

import pytest

from app.schemas.transfer_ai import (
    CompetitionPackage,
    FalseConfidence,
    GameMode,
    ModeComparison,
    TransferRate,
)
from app.services.backbone.transfer_ai import TransferAI


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def engine() -> TransferAI:
    return TransferAI()


# ---------------------------------------------------------------------------
# measure_transfer_rate
# ---------------------------------------------------------------------------

class TestMeasureTransferRate:
    """Tests for TransferAI.measure_transfer_rate."""

    @pytest.mark.asyncio
    async def test_returns_transfer_rate_model(self, engine: TransferAI):
        result = await engine.measure_transfer_rate(
            "user1", "zone_read", GameMode.LAB, GameMode.RANKED
        )
        assert isinstance(result, TransferRate)
        assert result.user_id == "user1"
        assert result.skill == "zone_read"
        assert result.from_mode == GameMode.LAB
        assert result.to_mode == GameMode.RANKED

    @pytest.mark.asyncio
    async def test_zero_attempts_gives_zero_rates(self, engine: TransferAI):
        """With no data, rates should be 0 and verdict false-confidence."""
        result = await engine.measure_transfer_rate(
            "user1", "crossover", GameMode.LAB, GameMode.TOURNAMENT
        )
        assert result.from_mode_success_rate == 0.0
        assert result.to_mode_success_rate == 0.0
        assert result.transfer_rate == 0.0
        assert result.is_reliable is False

    @pytest.mark.asyncio
    async def test_with_mocked_stats(self, engine: TransferAI, monkeypatch):
        """Inject stats to verify transfer calculation."""

        async def mock_stats(self, user_id, skill, mode):
            if mode == GameMode.LAB:
                return {"attempts": 100, "successes": 90, "avg_exec_time_ms": 50}
            return {"attempts": 50, "successes": 35, "avg_exec_time_ms": 80}

        monkeypatch.setattr(TransferAI, "_get_skill_stats", mock_stats)

        result = await engine.measure_transfer_rate(
            "user1", "slant_route", GameMode.LAB, GameMode.RANKED
        )
        assert result.from_mode_success_rate == 0.9
        assert result.to_mode_success_rate == 0.7
        # transfer_rate = 0.7 / 0.9 ≈ 0.778
        assert 0.77 < result.transfer_rate < 0.79
        assert result.is_reliable is True
        assert result.verdict == "solid"

    @pytest.mark.asyncio
    async def test_elite_transfer_verdict(self, engine: TransferAI, monkeypatch):
        async def mock_stats(self, user_id, skill, mode):
            if mode == GameMode.LAB:
                return {"attempts": 100, "successes": 95, "avg_exec_time_ms": 40}
            return {"attempts": 80, "successes": 88, "avg_exec_time_ms": 42}

        monkeypatch.setattr(TransferAI, "_get_skill_stats", mock_stats)

        result = await engine.measure_transfer_rate(
            "pro1", "option_read", GameMode.LAB, GameMode.TOURNAMENT
        )
        # 88/80 = 1.1, 95/100 = 0.95, transfer = 1.1/0.95 ≈ 1.158 → capped at 1.0
        assert result.transfer_rate == 1.0
        assert result.verdict == "elite-transfer"

    @pytest.mark.asyncio
    async def test_false_confidence_verdict(self, engine: TransferAI, monkeypatch):
        async def mock_stats(self, user_id, skill, mode):
            if mode == GameMode.LAB:
                return {"attempts": 100, "successes": 90, "avg_exec_time_ms": 40}
            return {"attempts": 50, "successes": 10, "avg_exec_time_ms": 120}

        monkeypatch.setattr(TransferAI, "_get_skill_stats", mock_stats)

        result = await engine.measure_transfer_rate(
            "user1", "trick_play", GameMode.LAB, GameMode.TOURNAMENT
        )
        assert result.verdict == "false-confidence"


# ---------------------------------------------------------------------------
# flag_false_confidence
# ---------------------------------------------------------------------------

class TestFlagFalseConfidence:

    @pytest.mark.asyncio
    async def test_empty_skills_returns_empty(self, engine: TransferAI):
        result = await engine.flag_false_confidence("user1", "madden26")
        assert result == []
        assert isinstance(result, list)

    @pytest.mark.asyncio
    async def test_flags_lab_only_skills(self, engine: TransferAI, monkeypatch):
        async def mock_skills(self, user_id, title):
            return ["pa_crosser", "fb_dive"]

        async def mock_stats(self, user_id, skill, mode):
            if skill == "pa_crosser":
                if mode == GameMode.LAB:
                    return {"attempts": 100, "successes": 95, "avg_exec_time_ms": 30}
                if mode == GameMode.RANKED:
                    return {"attempts": 50, "successes": 10, "avg_exec_time_ms": 100}
                return {"attempts": 30, "successes": 5, "avg_exec_time_ms": 120}
            # fb_dive transfers fine
            return {"attempts": 50, "successes": 40, "avg_exec_time_ms": 50}

        monkeypatch.setattr(TransferAI, "_get_all_skills", mock_skills)
        monkeypatch.setattr(TransferAI, "_get_skill_stats", mock_stats)

        result = await engine.flag_false_confidence("user1", "madden26")
        assert len(result) == 1
        assert isinstance(result[0], FalseConfidence)
        assert result[0].skill == "pa_crosser"
        assert result[0].risk_level in ("high", "critical")
        assert result[0].drop_off_pct > 50


# ---------------------------------------------------------------------------
# build_competition_ready_package
# ---------------------------------------------------------------------------

class TestCompetitionReadyPackage:

    @pytest.mark.asyncio
    async def test_empty_data_returns_empty_package(self, engine: TransferAI):
        result = await engine.build_competition_ready_package("user1", "madden26")
        assert isinstance(result, CompetitionPackage)
        assert result.proven_plays == []
        assert result.readiness_score == 0.0

    @pytest.mark.asyncio
    async def test_filters_unproven_plays(self, engine: TransferAI, monkeypatch):
        async def mock_skills(self, user_id, title):
            return ["proven_play", "unproven_play", "low_success_play"]

        async def mock_tournament_plays(self, user_id, title):
            plays = []
            # proven_play: 8 uses, 6 successes
            for i in range(8):
                plays.append({
                    "skill": "proven_play",
                    "success": i < 6,
                    "pressure_index": 0.7,
                    "tournament_name": "EsportsForge Open",
                })
            # unproven_play: only 2 uses (below threshold)
            for i in range(2):
                plays.append({
                    "skill": "unproven_play",
                    "success": True,
                    "pressure_index": 0.5,
                    "tournament_name": "Local Weekly",
                })
            # low_success_play: 10 uses but only 2 successes
            for i in range(10):
                plays.append({
                    "skill": "low_success_play",
                    "success": i < 2,
                    "pressure_index": 0.8,
                    "tournament_name": "Major",
                })
            return plays

        monkeypatch.setattr(TransferAI, "_get_all_skills", mock_skills)
        monkeypatch.setattr(TransferAI, "_get_tournament_plays", mock_tournament_plays)

        result = await engine.build_competition_ready_package("user1", "madden26")
        assert len(result.proven_plays) == 1
        assert result.proven_plays[0].skill == "proven_play"
        assert "unproven_play" in result.excluded_plays
        assert "low_success_play" in result.excluded_plays
        assert result.total_lab_plays == 3
        assert result.total_proven == 1


# ---------------------------------------------------------------------------
# get_mode_comparison
# ---------------------------------------------------------------------------

class TestModeComparison:

    @pytest.mark.asyncio
    async def test_returns_mode_comparison_model(self, engine: TransferAI):
        result = await engine.get_mode_comparison("user1", "madden26")
        assert isinstance(result, ModeComparison)
        assert result.user_id == "user1"
        assert result.title == "madden26"
        assert len(result.mode_stats) == 4  # lab, practice, ranked, tournament

    @pytest.mark.asyncio
    async def test_mode_comparison_with_data(self, engine: TransferAI, monkeypatch):
        async def mock_skills(self, user_id, title):
            return ["skill_a"]

        async def mock_stats(self, user_id, skill, mode):
            rates = {
                GameMode.LAB: 90,
                GameMode.PRACTICE: 85,
                GameMode.RANKED: 60,
                GameMode.TOURNAMENT: 40,
            }
            s = rates.get(mode, 50)
            return {"attempts": 100, "successes": s, "avg_exec_time_ms": 50.0}

        monkeypatch.setattr(TransferAI, "_get_all_skills", mock_skills)
        monkeypatch.setattr(TransferAI, "_get_skill_stats", mock_stats)

        result = await engine.get_mode_comparison("user1", "madden26")
        # Lab should be highest, tournament lowest
        lab_stat = next(s for s in result.mode_stats if s.mode == GameMode.LAB)
        tourney_stat = next(s for s in result.mode_stats if s.mode == GameMode.TOURNAMENT)
        assert lab_stat.success_rate > tourney_stat.success_rate
        assert "drop" in result.biggest_gap.lower() or "%" in result.biggest_gap


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

class TestHelpers:

    def test_verdict_elite(self):
        assert TransferAI._verdict(0.95) == "elite-transfer"

    def test_verdict_solid(self):
        assert TransferAI._verdict(0.80) == "solid"

    def test_verdict_leaking(self):
        assert TransferAI._verdict(0.60) == "leaking"

    def test_verdict_false_confidence(self):
        assert TransferAI._verdict(0.30) == "false-confidence"

    def test_risk_level_critical(self):
        assert TransferAI._risk_level(75) == "critical"

    def test_risk_level_high(self):
        assert TransferAI._risk_level(55) == "high"

    def test_risk_level_medium(self):
        assert TransferAI._risk_level(35) == "medium"

    def test_risk_level_low(self):
        assert TransferAI._risk_level(15) == "low"

    def test_letter_grade_a_plus(self):
        assert TransferAI._letter_grade(0.96) == "A+"

    def test_letter_grade_f(self):
        assert TransferAI._letter_grade(0.10) == "F"
