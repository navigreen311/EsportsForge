"""Unit tests for PlayerTwin — profile generation, execution scoring, identity filtering."""

from __future__ import annotations

import pytest

from app.schemas.player_twin import (
    BootstrapRequest,
    CanExecuteResponse,
    GameMode,
    PlayerTwinProfile,
    PlayStyle,
    PressureLevel,
    RecommendationInput,
    SessionData,
)
from app.services.backbone import player_twin
from app.services.backbone import identity_engine


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture(autouse=True)
def _clean_stores():
    """Reset all in-memory stores before each test."""
    player_twin.reset_store()
    yield
    player_twin.reset_store()


def _make_session(
    user_id: str = "user1",
    title: str = "madden26",
    mode: GameMode = GameMode.RANKED,
    result: str = "win",
    plays: list | None = None,
    skill_events: list | None = None,
    pressure_moments: list | None = None,
    session_id: str = "sess-001",
) -> SessionData:
    return SessionData(
        session_id=session_id,
        user_id=user_id,
        title=title,
        mode=mode,
        result=result,
        plays=plays or [],
        skill_events=skill_events or [],
        pressure_moments=pressure_moments or [],
    )


# ---------------------------------------------------------------------------
# Profile generation
# ---------------------------------------------------------------------------

class TestProfileGeneration:
    """Test get_profile and update_from_session."""

    def test_fresh_profile_has_zero_confidence(self):
        profile = player_twin.get_profile("user1", "madden26")
        assert isinstance(profile, PlayerTwinProfile)
        assert profile.confidence == 0.0
        assert profile.sessions_analyzed == 0
        assert profile.user_id == "user1"
        assert profile.title == "madden26"

    def test_profile_confidence_grows_with_sessions(self):
        for i in range(5):
            session = _make_session(
                session_id=f"sess-{i}",
                skill_events=[{"skill": "passing", "success": 0.8}],
            )
            player_twin.update_from_session("user1", session)

        profile = player_twin.get_profile("user1", "madden26")
        assert profile.sessions_analyzed == 5
        assert profile.confidence == 0.5  # 5 / 10 threshold

    def test_profile_per_title_isolation(self):
        s1 = _make_session(title="madden26", skill_events=[{"skill": "passing", "success": 0.9}])
        s2 = _make_session(title="cfb26", skill_events=[{"skill": "passing", "success": 0.3}])
        player_twin.update_from_session("user1", s1)
        player_twin.update_from_session("user1", s2)

        p_madden = player_twin.get_profile("user1", "madden26")
        p_cfb = player_twin.get_profile("user1", "cfb26")
        assert p_madden.sessions_analyzed == 1
        assert p_cfb.sessions_analyzed == 1

    def test_update_extracts_panic_patterns(self):
        session = _make_session(
            pressure_moments=[
                {
                    "pattern": "early_timeout",
                    "trigger": "4th_quarter_deficit",
                    "outcome": 0.2,
                    "description": "Calls timeout too early",
                }
            ],
        )
        player_twin.update_from_session("user1", session)
        patterns = player_twin.get_panic_patterns("user1", "madden26")
        assert len(patterns) == 1
        assert patterns[0].pattern_id == "early_timeout"
        assert patterns[0].severity > 0.5

    def test_update_extracts_tendencies(self):
        session = _make_session(
            plays=[
                {"category": "run", "aggressive": True},
                {"category": "run", "aggressive": True},
                {"category": "pass", "aggressive": False},
            ],
        )
        player_twin.update_from_session("user1", session)
        tendencies = player_twin.get_tendencies("user1", "madden26")
        assert len(tendencies.entries) == 2
        run_entry = next(e for e in tendencies.entries if e.category == "run")
        assert run_entry.weight > 0.5


# ---------------------------------------------------------------------------
# Execution scoring via PlayerTwin facade
# ---------------------------------------------------------------------------

class TestExecutionCeiling:
    """Test get_execution_ceiling."""

    def test_no_data_returns_zero(self):
        score = player_twin.get_execution_ceiling("user1", "madden26", "passing")
        assert score.score == 0.0
        assert score.sample_size == 0

    def test_scores_reflect_session_data(self):
        session = _make_session(
            skill_events=[
                {"skill": "passing", "success": 0.9},
                {"skill": "passing", "success": 0.7},
                {"skill": "rushing", "success": 0.5},
            ],
        )
        player_twin.update_from_session("user1", session)

        passing = player_twin.get_execution_ceiling("user1", "madden26", "passing")
        assert passing.score == 0.8  # (0.9 + 0.7) / 2
        assert passing.sample_size == 2

        rushing = player_twin.get_execution_ceiling("user1", "madden26", "rushing")
        assert rushing.score == 0.5
        assert rushing.sample_size == 1


# ---------------------------------------------------------------------------
# Identity filtering
# ---------------------------------------------------------------------------

class TestIdentityFiltering:
    """Test can_execute and identity-based filtering."""

    def test_can_execute_with_matching_skills(self):
        session = _make_session(
            skill_events=[
                {"skill": "zone_read", "success": 0.9},
                {"skill": "zone_read", "success": 0.85},
            ],
            plays=[{"aggressive": True, "risky": True, "fast": True, "creative": False}],
        )
        player_twin.update_from_session("user1", session)

        rec = RecommendationInput(
            action="run zone read",
            required_skills=["zone_read"],
            difficulty=0.5,
            pressure_context=PressureLevel.MEDIUM,
        )
        result = player_twin.can_execute("user1", rec)
        assert result.can_execute is True
        assert result.confidence > 0.0

    def test_cannot_execute_when_skill_too_low(self):
        session = _make_session(
            skill_events=[
                {"skill": "zone_read", "success": 0.2},
                {"skill": "zone_read", "success": 0.1},
            ],
        )
        player_twin.update_from_session("user1", session)

        rec = RecommendationInput(
            action="run zone read",
            required_skills=["zone_read"],
            difficulty=0.8,
            pressure_context=PressureLevel.LOW,
        )
        result = player_twin.can_execute("user1", rec)
        assert result.can_execute is False
        assert "zone_read" in result.limiting_skills

    def test_identity_filter_rejects_high_risk_for_conservative_player(self):
        # Make player conservative via observed behavior
        identity_engine.update_identity("user1", {
            "title": "madden26",
            "risk_tolerance": 0.1,
            "aggression": 0.1,
            "pace": 0.2,
        })

        rec = RecommendationInput(
            action="aggressive blitz",
            required_skills=[],
            difficulty=0.9,
            pressure_context=PressureLevel.HIGH,
        )
        identity = identity_engine.get_identity("user1", "madden26")
        result = identity_engine.filter_recommendation(rec, identity)
        assert result.can_execute is False


# ---------------------------------------------------------------------------
# Bootstrap (onboarding)
# ---------------------------------------------------------------------------

class TestBootstrap:
    """Test bootstrap_from_sessions."""

    def test_bootstrap_from_multiple_sessions(self):
        sessions = [
            _make_session(
                session_id=f"boot-{i}",
                skill_events=[
                    {"skill": "passing", "success": 0.7 + i * 0.05},
                    {"skill": "rushing", "success": 0.5},
                ],
                plays=[
                    {"category": "pass", "aggressive": True, "risky": False, "fast": True, "creative": False},
                ],
            )
            for i in range(3)
        ]

        profile = player_twin.bootstrap_from_sessions("user1", sessions)
        assert profile.sessions_analyzed == 3
        assert profile.confidence == pytest.approx(0.3, abs=0.01)
        assert len(profile.execution_scores) >= 2

    def test_bootstrap_requires_at_least_one_session(self):
        with pytest.raises(ValueError, match="at least one session"):
            player_twin.bootstrap_from_sessions("user1", [])


# ---------------------------------------------------------------------------
# Benchmark comparison
# ---------------------------------------------------------------------------

class TestBenchmark:
    """Test compare_to_benchmark."""

    def test_benchmark_with_scores(self):
        session = _make_session(
            skill_events=[
                {"skill": "passing", "success": 0.8},
                {"skill": "rushing", "success": 0.3},
            ],
        )
        player_twin.update_from_session("user1", session)

        bm = player_twin.compare_to_benchmark("user1", "madden26", 50)
        assert "passing" in bm.dimensions
        assert bm.dimensions["passing"] == 80.0
        assert "passing" in bm.strengths
        assert "rushing" not in bm.strengths

    def test_benchmark_empty_profile(self):
        bm = player_twin.compare_to_benchmark("user1", "madden26", 50)
        assert bm.overall_percentile == 0.0
        assert bm.dimensions == {}
