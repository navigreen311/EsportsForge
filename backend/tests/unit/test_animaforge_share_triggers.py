"""Unit tests for AnimaForge share-win trigger detection (Agent #9)."""

from __future__ import annotations

import pytest

from app.services.animaforge.share_triggers import (
    BENCHMARK_TOP_PERCENTILE,
    IMPACTRANK_MIN_IMPROVEMENT_PCT,
    PLAYER_TWIN_THRESHOLD,
    WIN_STREAK_MILESTONES,
    check_share_win_triggers,
    detect_benchmark_milestone,
    detect_impactrank_fix,
    detect_playertwin_milestone,
    detect_tournament_win,
    detect_win_streak,
)


class TestTournamentWin:
    def test_fires_on_tournament_final_win(self):
        trigger = detect_tournament_win(
            "madden-26",
            {
                "mode": "tournament",
                "result": "win",
                "tournament_final": True,
                "tournament_name": "Spring Madness",
                "tournament_record": "5-0",
            },
        )
        assert trigger is not None
        assert trigger.type == "tournament-win"
        assert trigger.data["tournament_name"] == "Spring Madness"
        assert trigger.data["record"] == "5-0"
        assert trigger.data["title_id"] == "madden-26"

    def test_skips_non_tournament(self):
        assert detect_tournament_win("madden-26", {"mode": "ranked", "result": "win"}) is None

    def test_skips_loss(self):
        assert (
            detect_tournament_win(
                "madden-26",
                {"mode": "tournament", "result": "loss", "tournament_final": True},
            )
            is None
        )

    def test_skips_non_final_win(self):
        assert (
            detect_tournament_win(
                "madden-26",
                {"mode": "tournament", "result": "win", "tournament_final": False},
            )
            is None
        )


class TestBenchmarkMilestone:
    @pytest.mark.asyncio
    async def test_fires_on_new_top_10(self):
        triggers = await detect_benchmark_milestone(
            "user-1",
            "madden-26",
            {
                "new_benchmarks": [
                    {"name": "Pre-Snap Read", "percentile": 8, "previously_achieved": False},
                ]
            },
        )
        assert len(triggers) == 1
        assert triggers[0].type == "benchmark-milestone"
        assert triggers[0].data["skill"] == "Pre-Snap Read"
        assert triggers[0].data["percentile"] == 8

    @pytest.mark.asyncio
    async def test_skips_already_achieved(self):
        triggers = await detect_benchmark_milestone(
            "user-1",
            "madden-26",
            {
                "new_benchmarks": [
                    {"name": "Foo", "percentile": 5, "previously_achieved": True},
                ]
            },
        )
        assert triggers == []

    @pytest.mark.asyncio
    async def test_skips_below_top_10(self):
        triggers = await detect_benchmark_milestone(
            "user-1",
            "madden-26",
            {
                "new_benchmarks": [
                    {"name": "Foo", "percentile": BENCHMARK_TOP_PERCENTILE + 5},
                ]
            },
        )
        assert triggers == []

    @pytest.mark.asyncio
    async def test_no_benchmarks_returns_empty(self):
        triggers = await detect_benchmark_milestone("user-1", "madden-26", {})
        assert triggers == []


class TestWinStreak:
    @pytest.mark.parametrize("streak", list(WIN_STREAK_MILESTONES))
    @pytest.mark.asyncio
    async def test_fires_on_milestone(self, streak: int):
        trigger = await detect_win_streak("user-1", "nba-2k26", {"current_streak": streak})
        assert trigger is not None
        assert trigger.type == "win-streak"
        assert trigger.data["streak"] == streak
        assert trigger.data["title_id"] == "nba-2k26"

    @pytest.mark.asyncio
    async def test_skips_non_milestone(self):
        assert (
            await detect_win_streak("user-1", "nba-2k26", {"current_streak": 7}) is None
        )

    @pytest.mark.asyncio
    async def test_skips_when_streak_missing(self):
        assert await detect_win_streak("user-1", "nba-2k26", {}) is None

    @pytest.mark.asyncio
    async def test_handles_invalid_streak_value(self):
        assert (
            await detect_win_streak("user-1", "nba-2k26", {"current_streak": "abc"})
            is None
        )


class TestImpactRankFix:
    @pytest.mark.asyncio
    async def test_fires_on_3pct_or_more_improvement(self):
        triggers = await detect_impactrank_fix(
            "user-1",
            "madden-26",
            {
                "roi_confirmations": [
                    {"priority_name": "Red Zone Reads", "win_rate_improvement": 4.2},
                ]
            },
        )
        assert len(triggers) == 1
        assert triggers[0].type == "impactrank-fix"
        assert triggers[0].data["fix_name"] == "Red Zone Reads"
        assert triggers[0].data["improvement"] == 4.2

    @pytest.mark.asyncio
    async def test_skips_below_threshold(self):
        triggers = await detect_impactrank_fix(
            "user-1",
            "madden-26",
            {
                "roi_confirmations": [
                    {
                        "priority_name": "Foo",
                        "win_rate_improvement": IMPACTRANK_MIN_IMPROVEMENT_PCT - 0.5,
                    }
                ]
            },
        )
        assert triggers == []


class TestPlayerTwinMilestone:
    def test_fires_on_first_75pct(self):
        trigger = detect_playertwin_milestone(
            "madden-26",
            {
                "player_twin": {
                    "accuracy": PLAYER_TWIN_THRESHOLD,
                    "games_played": 42,
                    "threshold_75_previously_reached": False,
                    "insight": "Reads coverage well",
                }
            },
        )
        assert trigger is not None
        assert trigger.type == "playertwin-milestone"
        assert trigger.data["accuracy"] == 0.75
        assert trigger.data["games_played"] == 42

    def test_skips_when_already_reached(self):
        trigger = detect_playertwin_milestone(
            "madden-26",
            {
                "player_twin": {
                    "accuracy": 0.82,
                    "threshold_75_previously_reached": True,
                }
            },
        )
        assert trigger is None

    def test_skips_below_threshold(self):
        trigger = detect_playertwin_milestone(
            "madden-26",
            {"player_twin": {"accuracy": 0.74}},
        )
        assert trigger is None


class TestOrchestrator:
    @pytest.mark.asyncio
    async def test_orchestrator_fires_multiple(self):
        triggers = await check_share_win_triggers(
            "user-1",
            "madden-26",
            {
                "mode": "tournament",
                "result": "win",
                "tournament_final": True,
                "tournament_name": "Spring",
                "current_streak": 5,
                "new_benchmarks": [
                    {"name": "Reads", "percentile": 9, "previously_achieved": False}
                ],
                "roi_confirmations": [
                    {"priority_name": "Coverage", "win_rate_improvement": 5.0}
                ],
                "player_twin": {
                    "accuracy": 0.78,
                    "games_played": 30,
                    "threshold_75_previously_reached": False,
                },
            },
        )
        types = {t.type for t in triggers}
        assert "tournament-win" in types
        assert "win-streak" in types
        assert "benchmark-milestone" in types
        assert "impactrank-fix" in types
        assert "playertwin-milestone" in types

    @pytest.mark.asyncio
    async def test_orchestrator_empty_session(self):
        triggers = await check_share_win_triggers("user-1", "madden-26", {})
        assert triggers == []

    @pytest.mark.asyncio
    async def test_orchestrator_swallows_detector_errors(self, monkeypatch):
        from app.services.animaforge import share_triggers

        def boom(*args, **kwargs):
            raise RuntimeError("boom")

        monkeypatch.setattr(share_triggers, "detect_tournament_win", boom)

        # Should not raise; other detectors keep running.
        triggers = await share_triggers.check_share_win_triggers(
            "user-1",
            "madden-26",
            {"current_streak": 5},
        )
        assert any(t.type == "win-streak" for t in triggers)
