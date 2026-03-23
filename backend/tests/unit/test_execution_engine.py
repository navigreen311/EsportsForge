"""Unit tests for ExecutionEngine — pressure differential, transfer rates, scoring."""

from __future__ import annotations

import pytest

from app.schemas.player_twin import (
    GameMode,
    SessionData,
)
from app.services.backbone import execution_engine


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture(autouse=True)
def _clean_store():
    """Reset the execution engine store before each test."""
    execution_engine.reset_store()
    yield
    execution_engine.reset_store()


def _make_session(
    user_id: str = "user1",
    title: str = "madden26",
    mode: GameMode = GameMode.RANKED,
    skill_events: list | None = None,
    pressure_moments: list | None = None,
    session_id: str = "sess-001",
) -> SessionData:
    return SessionData(
        session_id=session_id,
        user_id=user_id,
        title=title,
        mode=mode,
        result="win",
        skill_events=skill_events or [],
        pressure_moments=pressure_moments or [],
    )


# ---------------------------------------------------------------------------
# Basic scoring
# ---------------------------------------------------------------------------

class TestScoreExecution:
    """Test score_execution for individual skill dimensions."""

    def test_no_data_returns_zero(self):
        score = execution_engine.score_execution("user1", "madden26", "passing")
        assert score.score == 0.0
        assert score.sample_size == 0

    def test_single_observation(self):
        session = _make_session(
            skill_events=[{"skill": "passing", "success": 0.75}],
        )
        execution_engine.ingest_session("user1", session)
        score = execution_engine.score_execution("user1", "madden26", "passing")
        assert score.score == 0.75
        assert score.sample_size == 1

    def test_multiple_observations_averaged(self):
        session = _make_session(
            skill_events=[
                {"skill": "passing", "success": 0.6},
                {"skill": "passing", "success": 0.8},
                {"skill": "passing", "success": 1.0},
            ],
        )
        execution_engine.ingest_session("user1", session)
        score = execution_engine.score_execution("user1", "madden26", "passing")
        assert score.score == pytest.approx(0.8, abs=0.01)
        assert score.sample_size == 3

    def test_pressure_score_isolated(self):
        session = _make_session(
            skill_events=[
                {"skill": "passing", "success": 0.9, "pressure": False},
                {"skill": "passing", "success": 0.9, "pressure": False},
                {"skill": "passing", "success": 0.4, "pressure": True},
            ],
        )
        execution_engine.ingest_session("user1", session)
        score = execution_engine.score_execution("user1", "madden26", "passing")
        # Overall: (0.9+0.9+0.4)/3 ≈ 0.7333
        assert score.score == pytest.approx(0.7333, abs=0.01)
        # Pressure-only: 0.4
        assert score.pressure_score == pytest.approx(0.4, abs=0.01)

    def test_trend_detection(self):
        """Earlier observations bad, later observations good → positive trend."""
        events = (
            [{"skill": "rushing", "success": 0.3}] * 4
            + [{"skill": "rushing", "success": 0.9}] * 4
        )
        session = _make_session(skill_events=events)
        execution_engine.ingest_session("user1", session)
        score = execution_engine.score_execution("user1", "madden26", "rushing")
        assert score.trend > 0  # improving

    def test_get_all_scores(self):
        session = _make_session(
            skill_events=[
                {"skill": "passing", "success": 0.8},
                {"skill": "rushing", "success": 0.6},
                {"skill": "defense", "success": 0.5},
            ],
        )
        execution_engine.ingest_session("user1", session)
        scores = execution_engine.get_all_scores("user1", "madden26")
        skill_names = {s.skill for s in scores}
        assert skill_names == {"passing", "rushing", "defense"}


# ---------------------------------------------------------------------------
# Pressure differential
# ---------------------------------------------------------------------------

class TestPressureDifferential:
    """Test get_pressure_differential."""

    def test_no_data_returns_zeros(self):
        pd = execution_engine.get_pressure_differential("user1", "madden26")
        assert pd.normal_avg == 0.0
        assert pd.pressure_avg == 0.0
        assert pd.differential == 0.0

    def test_worse_under_pressure(self):
        session = _make_session(
            skill_events=[
                {"skill": "passing", "success": 0.9, "pressure": False},
                {"skill": "passing", "success": 0.8, "pressure": False},
                {"skill": "passing", "success": 0.3, "pressure": True},
                {"skill": "passing", "success": 0.4, "pressure": True},
            ],
        )
        execution_engine.ingest_session("user1", session)
        pd = execution_engine.get_pressure_differential("user1", "madden26")
        assert pd.normal_avg == pytest.approx(0.85, abs=0.01)
        assert pd.pressure_avg == pytest.approx(0.35, abs=0.01)
        assert pd.differential < 0  # worse under pressure
        assert pd.clutch_rating < 0.6  # poor clutch

    def test_clutch_player(self):
        """Player who performs equally under pressure gets clutch_rating ≈ 1.0."""
        session = _make_session(
            skill_events=[
                {"skill": "passing", "success": 0.8, "pressure": False},
                {"skill": "passing", "success": 0.8, "pressure": True},
            ],
        )
        execution_engine.ingest_session("user1", session)
        pd = execution_engine.get_pressure_differential("user1", "madden26")
        assert pd.clutch_rating == pytest.approx(1.0, abs=0.01)

    def test_pressure_from_pressure_moments(self):
        """Pressure moments also contribute to pressure observations."""
        session = _make_session(
            skill_events=[
                {"skill": "clock_mgmt", "success": 0.9, "pressure": False},
            ],
            pressure_moments=[
                {"skill": "clock_mgmt", "outcome": 0.2},
            ],
        )
        execution_engine.ingest_session("user1", session)
        pd = execution_engine.get_pressure_differential("user1", "madden26")
        assert pd.pressure_avg < pd.normal_avg


# ---------------------------------------------------------------------------
# Transfer rates
# ---------------------------------------------------------------------------

class TestTransferRate:
    """Test get_transfer_rate between game modes."""

    def test_no_data_returns_zero(self):
        tr = execution_engine.get_transfer_rate("user1", "passing", GameMode.LAB, GameMode.RANKED)
        assert tr.rate == 0.0
        assert tr.sample_size == 0

    def test_perfect_transfer(self):
        """Same score in lab and ranked → rate = 1.0."""
        lab = _make_session(
            session_id="lab-1",
            mode=GameMode.LAB,
            skill_events=[{"skill": "passing", "success": 0.8}],
        )
        ranked = _make_session(
            session_id="ranked-1",
            mode=GameMode.RANKED,
            skill_events=[{"skill": "passing", "success": 0.8}],
        )
        execution_engine.ingest_session("user1", lab)
        execution_engine.ingest_session("user1", ranked)

        tr = execution_engine.get_transfer_rate("user1", "passing", GameMode.LAB, GameMode.RANKED)
        assert tr.rate == 1.0
        assert tr.sample_size == 1

    def test_degraded_transfer(self):
        """Worse in ranked than lab → rate < 1.0."""
        lab = _make_session(
            session_id="lab-1",
            mode=GameMode.LAB,
            skill_events=[{"skill": "passing", "success": 1.0}],
        )
        ranked = _make_session(
            session_id="ranked-1",
            mode=GameMode.RANKED,
            skill_events=[{"skill": "passing", "success": 0.5}],
        )
        execution_engine.ingest_session("user1", lab)
        execution_engine.ingest_session("user1", ranked)

        tr = execution_engine.get_transfer_rate("user1", "passing", GameMode.LAB, GameMode.RANKED)
        assert tr.rate == 0.5
        assert tr.sample_size == 1

    def test_transfer_capped_at_one(self):
        """If ranked > lab (unusual), rate is capped at 1.0."""
        lab = _make_session(
            session_id="lab-1",
            mode=GameMode.LAB,
            skill_events=[{"skill": "passing", "success": 0.5}],
        )
        ranked = _make_session(
            session_id="ranked-1",
            mode=GameMode.RANKED,
            skill_events=[{"skill": "passing", "success": 0.9}],
        )
        execution_engine.ingest_session("user1", lab)
        execution_engine.ingest_session("user1", ranked)

        tr = execution_engine.get_transfer_rate("user1", "passing", GameMode.LAB, GameMode.RANKED)
        assert tr.rate == 1.0


# ---------------------------------------------------------------------------
# Multi-session accumulation
# ---------------------------------------------------------------------------

class TestMultiSession:
    """Verify that multiple sessions accumulate correctly."""

    def test_scores_accumulate_across_sessions(self):
        for i in range(5):
            session = _make_session(
                session_id=f"sess-{i}",
                skill_events=[{"skill": "passing", "success": 0.6 + i * 0.05}],
            )
            execution_engine.ingest_session("user1", session)

        score = execution_engine.score_execution("user1", "madden26", "passing")
        assert score.sample_size == 5
        # avg of 0.6, 0.65, 0.7, 0.75, 0.8 = 0.7
        assert score.score == pytest.approx(0.7, abs=0.01)
