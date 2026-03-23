"""Unit tests for ResponsibleGamblingGuard — compliance safeguards."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest

from app.schemas.video_poker.responsible_gambling import (
    AlertSeverity,
    CoolingOffPeriod,
    LossLimitConfig,
    ProblemGamblingRiskLevel,
    SelfExclusionConfig,
    SessionTimeLimit,
)
from app.services.agents.video_poker.responsible_gambling import (
    ResponsibleGamblingGuard,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def guard() -> ResponsibleGamblingGuard:
    return ResponsibleGamblingGuard()


@pytest.fixture
def now() -> datetime:
    return datetime(2026, 3, 22, 12, 0, 0, tzinfo=timezone.utc)


# ---------------------------------------------------------------------------
# Session Time Limits
# ---------------------------------------------------------------------------

class TestSessionTimeLimits:
    def test_create_default_limit(self, guard: ResponsibleGamblingGuard, now: datetime) -> None:
        limit = guard.create_session_time_limit("user-1", start_time=now)
        assert limit.max_minutes == 240
        assert limit.user_id == "user-1"
        assert limit.expires_at == now + timedelta(minutes=240)

    def test_create_custom_limit(self, guard: ResponsibleGamblingGuard, now: datetime) -> None:
        limit = guard.create_session_time_limit("user-1", max_minutes=60, start_time=now)
        assert limit.max_minutes == 60

    def test_limit_caps_at_maximum(self, guard: ResponsibleGamblingGuard, now: datetime) -> None:
        limit = guard.create_session_time_limit("user-1", max_minutes=600, start_time=now)
        assert limit.max_minutes == 240  # Capped

    def test_minimum_session_time(self, guard: ResponsibleGamblingGuard, now: datetime) -> None:
        limit = guard.create_session_time_limit("user-1", max_minutes=5, start_time=now)
        assert limit.max_minutes == 15  # Minimum

    def test_continue_within_limit(self, guard: ResponsibleGamblingGuard, now: datetime) -> None:
        limit = guard.create_session_time_limit("user-1", max_minutes=120, start_time=now)
        status = guard.check_session_time(limit, now + timedelta(minutes=30))
        assert status.action == "continue"
        assert status.remaining_minutes == pytest.approx(90.0, abs=0.1)

    def test_warn_near_limit(self, guard: ResponsibleGamblingGuard, now: datetime) -> None:
        limit = guard.create_session_time_limit("user-1", max_minutes=120, start_time=now)
        status = guard.check_session_time(limit, now + timedelta(minutes=110))
        assert status.action == "warn"

    def test_force_stop_at_limit(self, guard: ResponsibleGamblingGuard, now: datetime) -> None:
        limit = guard.create_session_time_limit("user-1", max_minutes=120, start_time=now)
        status = guard.check_session_time(limit, now + timedelta(minutes=125))
        assert status.action == "force_stop"
        assert status.must_break is True
        assert status.break_until is not None


# ---------------------------------------------------------------------------
# Self-Exclusion
# ---------------------------------------------------------------------------

class TestSelfExclusion:
    def test_temporary_exclusion(self, guard: ResponsibleGamblingGuard) -> None:
        config = guard.create_self_exclusion("user-1", duration_days=90)
        assert config.is_permanent is False
        assert config.duration_days == 90
        assert config.can_be_reversed is False
        assert config.end_date is not None

    def test_permanent_exclusion(self, guard: ResponsibleGamblingGuard) -> None:
        config = guard.create_self_exclusion("user-1", permanent=True)
        assert config.is_permanent is True
        assert config.end_date is None
        assert config.can_be_reversed is False

    def test_minimum_exclusion_period(self, guard: ResponsibleGamblingGuard) -> None:
        config = guard.create_self_exclusion("user-1", duration_days=7)
        assert config.duration_days == 30  # Minimum enforced

    def test_active_exclusion_blocks_play(self, guard: ResponsibleGamblingGuard) -> None:
        config = guard.create_self_exclusion("user-1", duration_days=90)
        status = guard.check_self_exclusion(config)
        assert status.is_excluded is True
        assert status.can_play is False

    def test_expired_exclusion_allows_play(self, guard: ResponsibleGamblingGuard) -> None:
        config = guard.create_self_exclusion("user-1", duration_days=30)
        future = datetime.now(timezone.utc) + timedelta(days=31)
        status = guard.check_self_exclusion(config, current_time=future)
        assert status.is_excluded is False
        assert status.can_play is True

    def test_no_exclusion_allows_play(self, guard: ResponsibleGamblingGuard) -> None:
        status = guard.check_self_exclusion(None)
        assert status.can_play is True

    def test_permanent_exclusion_blocks_forever(self, guard: ResponsibleGamblingGuard) -> None:
        config = guard.create_self_exclusion("user-1", permanent=True)
        far_future = datetime.now(timezone.utc) + timedelta(days=3650)
        status = guard.check_self_exclusion(config, current_time=far_future)
        assert status.is_excluded is True
        assert status.can_play is False


# ---------------------------------------------------------------------------
# Loss Limits
# ---------------------------------------------------------------------------

class TestLossLimits:
    def test_configure_defaults(self, guard: ResponsibleGamblingGuard) -> None:
        config = guard.configure_loss_limits("user-1")
        assert config.daily_limit == 200.0
        assert config.weekly_limit == 500.0
        assert config.monthly_limit == 1500.0

    def test_configure_custom(self, guard: ResponsibleGamblingGuard) -> None:
        config = guard.configure_loss_limits("user-1", daily_limit=100, weekly_limit=300, monthly_limit=800)
        assert config.daily_limit == 100.0

    def test_within_limits_can_continue(self, guard: ResponsibleGamblingGuard) -> None:
        config = guard.configure_loss_limits("user-1")
        status = guard.check_loss_limits(config, daily_losses=50)
        assert status.can_continue is True

    def test_daily_limit_reached_blocks(self, guard: ResponsibleGamblingGuard) -> None:
        config = guard.configure_loss_limits("user-1", daily_limit=100)
        status = guard.check_loss_limits(config, daily_losses=100)
        assert status.can_continue is False
        assert any(a.severity == AlertSeverity.CRITICAL for a in status.alerts)

    def test_weekly_limit_reached_blocks(self, guard: ResponsibleGamblingGuard) -> None:
        config = guard.configure_loss_limits("user-1", weekly_limit=300)
        status = guard.check_loss_limits(config, weekly_losses=300)
        assert status.can_continue is False

    def test_approaching_limit_warns(self, guard: ResponsibleGamblingGuard) -> None:
        config = guard.configure_loss_limits("user-1", daily_limit=100)
        status = guard.check_loss_limits(config, daily_losses=85)
        assert status.can_continue is True
        assert any(a.severity == AlertSeverity.WARNING for a in status.alerts)


# ---------------------------------------------------------------------------
# Problem Gambling Detection
# ---------------------------------------------------------------------------

class TestProblemGamblingDetection:
    def test_no_signals_returns_none(self, guard: ResponsibleGamblingGuard) -> None:
        result = guard.detect_problem_signals("user-1", session_history=[])
        assert result.risk_level == ProblemGamblingRiskLevel.NONE
        assert result.risk_score == 0.0

    def test_chasing_losses_detected(self, guard: ResponsibleGamblingGuard) -> None:
        """Escalating bets should be detected."""
        bets = [1.0] * 15 + [2.0, 4.0, 8.0, 16.0, 32.0]
        result = guard.detect_problem_signals(
            "user-1",
            session_history=[],
            bet_history=bets,
        )
        assert result.risk_score > 0
        assert any("chasing" in s.category for s in result.signals)

    def test_extended_sessions_detected(self, guard: ResponsibleGamblingGuard) -> None:
        sessions = [
            {"duration_hours": 7, "start_hour": 14},
            {"duration_hours": 8, "start_hour": 10},
        ]
        result = guard.detect_problem_signals("user-1", session_history=sessions)
        assert any("extended" in s.category for s in result.signals)

    def test_rapid_deposits_detected(self, guard: ResponsibleGamblingGuard) -> None:
        now = datetime.now(timezone.utc)
        deposits = [now, now + timedelta(minutes=10), now + timedelta(minutes=20)]
        result = guard.detect_problem_signals(
            "user-1",
            session_history=[],
            deposit_timestamps=deposits,
        )
        assert any("rapid" in s.category for s in result.signals)

    def test_high_risk_includes_helplines(self, guard: ResponsibleGamblingGuard) -> None:
        """High-risk detection must include helpline numbers."""
        now = datetime.now(timezone.utc)
        deposits = [now, now + timedelta(minutes=5), now + timedelta(minutes=10)]
        bets = [1.0] * 15 + [2.0, 4.0, 8.0, 16.0, 32.0]
        sessions = [
            {"duration_hours": 7, "start_hour": 2},
            {"duration_hours": 8, "start_hour": 1},
        ]
        result = guard.detect_problem_signals(
            "user-1",
            session_history=sessions,
            bet_history=bets,
            deposit_timestamps=deposits,
        )
        assert len(result.helpline_numbers) > 0
        assert result.disclaimer != ""


# ---------------------------------------------------------------------------
# Cooling-Off Period
# ---------------------------------------------------------------------------

class TestCoolingOff:
    def test_create_cooling_off(self, guard: ResponsibleGamblingGuard) -> None:
        period = guard.enforce_cooling_off("user-1", hours=48)
        assert period.duration_hours == 48
        assert period.can_be_shortened is False
        assert period.is_active is True

    def test_minimum_cooling_off(self, guard: ResponsibleGamblingGuard) -> None:
        period = guard.enforce_cooling_off("user-1", hours=6)
        assert period.duration_hours == 24  # Minimum enforced

    def test_active_cooling_off_blocks(self, guard: ResponsibleGamblingGuard) -> None:
        period = guard.enforce_cooling_off("user-1", hours=24)
        is_active = guard.check_cooling_off(period)
        assert is_active is True

    def test_expired_cooling_off_allows(self, guard: ResponsibleGamblingGuard) -> None:
        period = guard.enforce_cooling_off("user-1", hours=24)
        future = datetime.now(timezone.utc) + timedelta(hours=25)
        is_active = guard.check_cooling_off(period, current_time=future)
        assert is_active is False


# ---------------------------------------------------------------------------
# Full Compliance Check
# ---------------------------------------------------------------------------

class TestFullComplianceCheck:
    def test_clean_user_can_play(self, guard: ResponsibleGamblingGuard) -> None:
        status = guard.full_compliance_check("user-1")
        assert status.can_play is True
        assert len(status.blocks) == 0

    def test_excluded_user_blocked(self, guard: ResponsibleGamblingGuard) -> None:
        exclusion = guard.create_self_exclusion("user-1", duration_days=90)
        status = guard.full_compliance_check("user-1", self_exclusion=exclusion)
        assert status.can_play is False
        assert len(status.blocks) > 0

    def test_loss_limit_exceeded_blocks(self, guard: ResponsibleGamblingGuard) -> None:
        config = guard.configure_loss_limits("user-1", daily_limit=100)
        status = guard.full_compliance_check(
            "user-1",
            loss_config=config,
            daily_losses=150,
        )
        assert status.can_play is False

    def test_cooling_off_blocks(self, guard: ResponsibleGamblingGuard) -> None:
        period = guard.enforce_cooling_off("user-1", hours=24)
        status = guard.full_compliance_check("user-1", cooling_off=period)
        assert status.can_play is False

    def test_multiple_blocks_all_reported(self, guard: ResponsibleGamblingGuard) -> None:
        exclusion = guard.create_self_exclusion("user-1", duration_days=90)
        period = guard.enforce_cooling_off("user-1", hours=24)
        status = guard.full_compliance_check(
            "user-1",
            self_exclusion=exclusion,
            cooling_off=period,
        )
        assert status.can_play is False
        assert len(status.blocks) >= 2
