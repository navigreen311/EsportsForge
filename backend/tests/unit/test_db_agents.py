"""Tests for DB-wired agent services.

Verifies that all title-specific agent services accept AsyncSession
and use it for database operations (or gracefully fall back).
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def mock_db() -> AsyncMock:
    """Return a mock AsyncSession for dependency injection."""
    db = AsyncMock()
    db.execute = AsyncMock()
    db.add = MagicMock()
    db.flush = AsyncMock()
    db.commit = AsyncMock()
    db.rollback = AsyncMock()
    return db


@pytest.fixture
def mock_scalar_result():
    """Helper to build a mock result that returns .scalar_one_or_none()."""
    result = MagicMock()
    result.scalar_one_or_none.return_value = None
    result.scalars.return_value.all.return_value = []
    return result


# ---------------------------------------------------------------------------
# Madden 26 — SchemeAI
# ---------------------------------------------------------------------------


class TestSchemeAI:
    """SchemeAI accepts db and enriches analysis from DB when available."""

    def test_init_accepts_db(self, mock_db: AsyncMock) -> None:
        from app.services.agents.madden26.scheme_ai import SchemeAI

        svc = SchemeAI(mock_db)
        assert svc.db is mock_db

    @pytest.mark.asyncio
    async def test_analyze_scheme_falls_back_to_static(
        self, mock_db: AsyncMock, mock_scalar_result
    ) -> None:
        from app.services.agents.madden26.scheme_ai import SchemeAI

        mock_db.execute.return_value = mock_scalar_result
        svc = SchemeAI(mock_db)
        result = await svc.analyze_scheme("west_coast")
        assert result.scheme == "west_coast"
        assert len(result.strengths) > 0

    @pytest.mark.asyncio
    async def test_get_scheme_from_db_called(
        self, mock_db: AsyncMock, mock_scalar_result
    ) -> None:
        from app.services.agents.madden26.scheme_ai import SchemeAI

        mock_db.execute.return_value = mock_scalar_result
        svc = SchemeAI(mock_db)
        result = await svc._get_scheme_from_db("test_scheme")
        assert result is None
        mock_db.execute.assert_called()


# ---------------------------------------------------------------------------
# Madden 26 — GameplanAI
# ---------------------------------------------------------------------------


class TestGameplanAI:
    """GameplanAI accepts db and persists gameplans."""

    def test_init_accepts_db(self, mock_db: AsyncMock) -> None:
        from app.services.agents.madden26.gameplan_ai import GameplanAI

        svc = GameplanAI(mock_db)
        assert svc.db is mock_db
        assert svc._scheme_ai.db is mock_db

    @pytest.mark.asyncio
    async def test_generate_gameplan_persists(
        self, mock_db: AsyncMock, mock_scalar_result
    ) -> None:
        from app.services.agents.madden26.gameplan_ai import GameplanAI

        mock_db.execute.return_value = mock_scalar_result
        svc = GameplanAI(mock_db)
        user_id = uuid.uuid4()
        gp = await svc.generate_gameplan(user_id=user_id, meta_aware=False)
        assert gp.user_id == user_id
        # Verify DB add + flush were called (gameplan persisted)
        mock_db.add.assert_called_once()
        mock_db.flush.assert_called_once()


# ---------------------------------------------------------------------------
# Madden 26 — KillSheetGenerator
# ---------------------------------------------------------------------------


class TestKillSheetGenerator:
    """KillSheetGenerator accepts db and stores kill sheets."""

    def test_init_accepts_db(self, mock_db: AsyncMock) -> None:
        from app.services.agents.madden26.kill_sheet import KillSheetGenerator

        svc = KillSheetGenerator(mock_db)
        assert svc.db is mock_db

    @pytest.mark.asyncio
    async def test_generate_kill_sheet_persists(self, mock_db: AsyncMock) -> None:
        from app.services.agents.madden26.kill_sheet import KillSheetGenerator
        from app.schemas.madden26.killsheet import OpponentData, Roster

        svc = KillSheetGenerator(mock_db)
        opponent = OpponentData(
            opponent_id="test-opp-id",
            opponent_name="TestOpponent",
            zone_coverage_rate=0.6,
            man_coverage_rate=0.3,
            blitz_rate=0.35,
        )
        roster = Roster(
            qb_overall=85,
            wr1_overall=88,
            rb_overall=82,
            oline_avg=80,
            defense_overall=78,
        )
        sheet = await svc.generate_kill_sheet(
            user_id=str(uuid.uuid4()),
            opponent_data=opponent,
            roster=roster,
        )
        assert len(sheet.kills) == 5
        mock_db.add.assert_called_once()
        mock_db.flush.assert_called_once()


# ---------------------------------------------------------------------------
# Madden 26 — RosterIQ
# ---------------------------------------------------------------------------


class TestRosterIQ:
    """RosterIQ optionally accepts db for player profile lookups."""

    def test_init_accepts_db(self, mock_db: AsyncMock) -> None:
        from app.services.agents.madden26.roster_iq import RosterIQ

        svc = RosterIQ(mock_db)
        assert svc.db is mock_db

    def test_init_without_db(self) -> None:
        from app.services.agents.madden26.roster_iq import RosterIQ

        svc = RosterIQ()
        assert svc.db is None


# ---------------------------------------------------------------------------
# Madden 26 — MatchupAI
# ---------------------------------------------------------------------------


class TestMatchupAI:
    """MatchupAI accepts db and queries opponent history from DB."""

    def test_init_accepts_db(self, mock_db: AsyncMock) -> None:
        from app.services.agents.madden26.matchup_ai import MatchupAI

        svc = MatchupAI(mock_db)
        assert svc.db is mock_db

    @pytest.mark.asyncio
    async def test_get_matchup_history_queries_db(
        self, mock_db: AsyncMock, mock_scalar_result
    ) -> None:
        from app.services.agents.madden26.matchup_ai import MatchupAI

        mock_scalar_result.scalars.return_value.all.return_value = []
        mock_db.execute.return_value = mock_scalar_result
        svc = MatchupAI(mock_db)
        results = await svc.get_matchup_history(
            user_id=str(uuid.uuid4()),
            opponent_id=str(uuid.uuid4()),
        )
        assert results == []
        mock_db.execute.assert_called()


# ---------------------------------------------------------------------------
# Madden 26 — ClockAI
# ---------------------------------------------------------------------------


class TestClockAI:
    """ClockAI accepts db for game session lookups."""

    def test_init_accepts_db(self, mock_db: AsyncMock) -> None:
        from app.services.agents.madden26.clock_ai import ClockAI

        svc = ClockAI(mock_db)
        assert svc.db is mock_db


# ---------------------------------------------------------------------------
# Madden 26 — MCSTracker
# ---------------------------------------------------------------------------


class TestMCSTracker:
    """MCSTracker accepts db for tournament session queries."""

    def test_init_accepts_db(self, mock_db: AsyncMock) -> None:
        from app.services.agents.madden26.mcs_tracker import MCSTracker

        svc = MCSTracker(mock_db)
        assert svc.db is mock_db

    @pytest.mark.asyncio
    async def test_get_tournament_sessions(
        self, mock_db: AsyncMock, mock_scalar_result
    ) -> None:
        from app.services.agents.madden26.mcs_tracker import MCSTracker

        mock_scalar_result.scalars.return_value.all.return_value = []
        mock_db.execute.return_value = mock_scalar_result
        svc = MCSTracker(mock_db)
        sessions = await svc.get_tournament_sessions(str(uuid.uuid4()))
        assert sessions == []


# ---------------------------------------------------------------------------
# CFB 26 — SchemeDepthAI
# ---------------------------------------------------------------------------


class TestSchemeDepthAI:
    """SchemeDepthAI accepts db for CFB scheme queries."""

    def test_init_accepts_db(self, mock_db: AsyncMock) -> None:
        from app.services.agents.cfb26.scheme_depth_ai import SchemeDepthAI

        svc = SchemeDepthAI(mock_db)
        assert svc.db is mock_db

    def test_factory_function(self, mock_db: AsyncMock) -> None:
        from app.services.agents.cfb26.scheme_depth_ai import get_scheme_depth_ai

        svc = get_scheme_depth_ai(mock_db)
        assert svc.db is mock_db

    @pytest.mark.asyncio
    async def test_get_scheme_from_db(
        self, mock_db: AsyncMock, mock_scalar_result
    ) -> None:
        from app.services.agents.cfb26.scheme_depth_ai import SchemeDepthAI

        mock_db.execute.return_value = mock_scalar_result
        svc = SchemeDepthAI(mock_db)
        result = await svc.get_scheme_from_db("air_raid")
        assert result is None


# ---------------------------------------------------------------------------
# CFB 26 — MomentumGuard
# ---------------------------------------------------------------------------


class TestMomentumGuard:
    """MomentumGuard accepts db for game session access."""

    def test_init_accepts_db(self, mock_db: AsyncMock) -> None:
        from app.services.agents.cfb26.momentum_guard import MomentumGuard

        svc = MomentumGuard(mock_db)
        assert svc.db is mock_db

    def test_factory_function(self, mock_db: AsyncMock) -> None:
        from app.services.agents.cfb26.momentum_guard import get_momentum_guard

        svc = get_momentum_guard(mock_db)
        assert svc.db is mock_db


# ---------------------------------------------------------------------------
# CFB 26 — RecruitingIQ
# ---------------------------------------------------------------------------


class TestRecruitingIQ:
    """RecruitingIQ accepts db for recruiting target queries."""

    def test_init_accepts_db(self, mock_db: AsyncMock) -> None:
        from app.services.agents.cfb26.recruiting_iq import RecruitingIQ

        svc = RecruitingIQ(mock_db)
        assert svc.db is mock_db

    def test_factory_function(self, mock_db: AsyncMock) -> None:
        from app.services.agents.cfb26.recruiting_iq import get_recruiting_iq

        svc = get_recruiting_iq(mock_db)
        assert svc.db is mock_db

    @pytest.mark.asyncio
    async def test_get_recruiting_targets(
        self, mock_db: AsyncMock, mock_scalar_result
    ) -> None:
        from app.services.agents.cfb26.recruiting_iq import RecruitingIQ

        mock_scalar_result.scalars.return_value.all.return_value = []
        mock_db.execute.return_value = mock_scalar_result
        svc = RecruitingIQ(mock_db)
        targets = await svc.get_recruiting_targets(str(uuid.uuid4()))
        assert targets == []


# ---------------------------------------------------------------------------
# Backbone — IntegrityMode
# ---------------------------------------------------------------------------


class TestIntegrityModeDB:
    """IntegrityMode accepts db for per-user settings persistence."""

    def test_init_accepts_db(self, mock_db: AsyncMock) -> None:
        from app.services.backbone.integrity_mode import IntegrityMode

        svc = IntegrityMode(mock_db)
        assert svc.db is mock_db

    @pytest.mark.asyncio
    async def test_get_active_mode_queries_db(
        self, mock_db: AsyncMock, mock_scalar_result
    ) -> None:
        from app.services.backbone.integrity_mode import IntegrityMode, _user_modes

        mock_db.execute.return_value = mock_scalar_result
        _user_modes.clear()
        svc = IntegrityMode(mock_db)
        mode = await svc.get_active_mode(str(uuid.uuid4()))
        assert mode.environment.value == "offline_lab"

    @pytest.mark.asyncio
    async def test_set_mode_persists_to_db(
        self, mock_db: AsyncMock, mock_scalar_result
    ) -> None:
        from app.services.backbone.integrity_mode import IntegrityMode
        from app.schemas.integrity import Environment, Timing

        mock_db.execute.return_value = mock_scalar_result
        svc = IntegrityMode(mock_db)
        mode = await svc.set_mode(
            str(uuid.uuid4()),
            Environment.TOURNAMENT,
            Timing.PRE_GAME,
        )
        assert mode.environment == Environment.TOURNAMENT
        mock_db.flush.assert_called()


# ---------------------------------------------------------------------------
# Backbone — InputLab
# ---------------------------------------------------------------------------


class TestInputLabDB:
    """InputLab accepts db for telemetry and drill storage."""

    def test_init_accepts_db(self, mock_db: AsyncMock) -> None:
        from app.services.backbone.input_lab import InputLab

        svc = InputLab(mock_db)
        assert svc.db is mock_db


# ---------------------------------------------------------------------------
# Backbone — TransferAI
# ---------------------------------------------------------------------------


class TestTransferAIDB:
    """TransferAI accepts db for game session queries."""

    def test_init_accepts_db(self, mock_db: AsyncMock) -> None:
        from app.services.backbone.transfer_ai import TransferAI

        svc = TransferAI(mock_db)
        assert svc.db is mock_db

    @pytest.mark.asyncio
    async def test_get_skill_stats_returns_empty_on_no_data(
        self, mock_db: AsyncMock, mock_scalar_result
    ) -> None:
        from app.services.backbone.transfer_ai import TransferAI
        from app.schemas.transfer_ai import GameMode

        mock_scalar_result.scalars.return_value.all.return_value = []
        mock_db.execute.return_value = mock_scalar_result
        svc = TransferAI(mock_db)
        stats = await svc._get_skill_stats(
            str(uuid.uuid4()), "passing", GameMode.RANKED,
        )
        assert stats["attempts"] == 0
        assert stats["successes"] == 0
