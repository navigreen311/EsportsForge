"""Responsible Gambling Compliance — legally required safeguards for video poker.

Implements session time limits, self-exclusion, loss limit tracking,
problem gambling detection signals, and cooling-off period enforcement.

This module is NON-NEGOTIABLE — all video poker features MUST route through
these compliance checks. Disabling or bypassing these safeguards is prohibited.
"""

from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone
from typing import Any

from app.schemas.video_poker.responsible_gambling import (
    ComplianceStatus,
    CoolingOffPeriod,
    GamblingAlert,
    AlertSeverity,
    LossLimitConfig,
    LossLimitStatus,
    ProblemGamblingSignal,
    ProblemGamblingRiskLevel,
    SelfExclusionConfig,
    SelfExclusionStatus,
    SessionTimeLimit,
    SessionTimeLimitStatus,
    ResponsibleGamblingProfile,
)

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Regulatory constants
# ---------------------------------------------------------------------------

# Maximum session duration before mandatory break
MAX_SESSION_MINUTES = 240  # 4 hours
MANDATORY_BREAK_MINUTES = 30
WARNING_BEFORE_LIMIT_MINUTES = 15

# Loss limit defaults
DEFAULT_DAILY_LOSS_LIMIT = 200.0
DEFAULT_WEEKLY_LOSS_LIMIT = 500.0
DEFAULT_MONTHLY_LOSS_LIMIT = 1500.0

# Minimum cooling-off periods
MIN_COOLING_OFF_HOURS = 24
MAX_COOLING_OFF_DAYS = 365

# Self-exclusion minimum periods
MIN_SELF_EXCLUSION_DAYS = 30
PERMANENT_EXCLUSION_MARKER = -1

# Problem gambling detection thresholds
CHASING_LOSS_THRESHOLD = 3  # Increased bets after losses
EXTENDED_SESSION_THRESHOLD_HOURS = 6
RAPID_DEPOSIT_THRESHOLD = 3  # Deposits within 1 hour
ESCALATING_BETS_WINDOW = 20  # Hands to check for escalation


# ---------------------------------------------------------------------------
# ResponsibleGamblingGuard
# ---------------------------------------------------------------------------

class ResponsibleGamblingGuard:
    """Legally mandated responsible gambling compliance engine.

    All video poker operations MUST pass through compliance checks
    before proceeding. This guard cannot be disabled.
    """

    # ------------------------------------------------------------------
    # Session Time Limits
    # ------------------------------------------------------------------

    def create_session_time_limit(
        self,
        user_id: str,
        max_minutes: int | None = None,
        start_time: datetime | None = None,
    ) -> SessionTimeLimit:
        """Create a session time limit. Defaults to regulatory maximum."""
        if max_minutes is None or max_minutes > MAX_SESSION_MINUTES:
            max_minutes = MAX_SESSION_MINUTES

        if max_minutes < 15:
            max_minutes = 15  # Minimum 15-minute sessions

        now = start_time or datetime.now(timezone.utc)

        return SessionTimeLimit(
            user_id=user_id,
            start_time=now,
            max_minutes=max_minutes,
            warning_at_minutes=max_minutes - WARNING_BEFORE_LIMIT_MINUTES,
            expires_at=now + timedelta(minutes=max_minutes),
            mandatory_break_minutes=MANDATORY_BREAK_MINUTES,
        )

    def check_session_time(
        self,
        limit: SessionTimeLimit,
        current_time: datetime | None = None,
    ) -> SessionTimeLimitStatus:
        """Check if a session has exceeded its time limit.

        Returns enforcement action: continue, warn, or force_stop.
        """
        now = current_time or datetime.now(timezone.utc)
        elapsed = (now - limit.start_time).total_seconds() / 60.0
        remaining = max(0.0, limit.max_minutes - elapsed)

        if elapsed >= limit.max_minutes:
            return SessionTimeLimitStatus(
                action="force_stop",
                elapsed_minutes=round(elapsed, 1),
                remaining_minutes=0.0,
                message=(
                    f"SESSION TIME LIMIT REACHED ({limit.max_minutes} minutes). "
                    f"Mandatory {MANDATORY_BREAK_MINUTES}-minute break required. "
                    f"Session will be suspended."
                ),
                must_break=True,
                break_until=now + timedelta(minutes=MANDATORY_BREAK_MINUTES),
            )

        if elapsed >= limit.warning_at_minutes:
            return SessionTimeLimitStatus(
                action="warn",
                elapsed_minutes=round(elapsed, 1),
                remaining_minutes=round(remaining, 1),
                message=(
                    f"WARNING: {remaining:.0f} minutes remaining in session. "
                    f"Consider wrapping up. Mandatory break at {limit.max_minutes} minutes."
                ),
                must_break=False,
                break_until=None,
            )

        return SessionTimeLimitStatus(
            action="continue",
            elapsed_minutes=round(elapsed, 1),
            remaining_minutes=round(remaining, 1),
            message=f"Session active. {remaining:.0f} minutes remaining.",
            must_break=False,
            break_until=None,
        )

    # ------------------------------------------------------------------
    # Self-Exclusion
    # ------------------------------------------------------------------

    def create_self_exclusion(
        self,
        user_id: str,
        duration_days: int | None = None,
        permanent: bool = False,
        reason: str = "",
    ) -> SelfExclusionConfig:
        """Create a self-exclusion period. Cannot be reversed early.

        Self-exclusion is a serious commitment — once activated, the user
        cannot access video poker features until the period expires.
        Permanent exclusion has no expiry.
        """
        now = datetime.now(timezone.utc)

        if permanent:
            return SelfExclusionConfig(
                user_id=user_id,
                is_permanent=True,
                start_date=now,
                end_date=None,
                duration_days=PERMANENT_EXCLUSION_MARKER,
                reason=reason,
                can_be_reversed=False,
                helpline_numbers=self._get_helpline_numbers(),
                confirmation_required=True,
                message=(
                    "PERMANENT SELF-EXCLUSION activated. You will no longer "
                    "have access to video poker features. This cannot be undone. "
                    "If you need support, please contact the helplines provided."
                ),
            )

        if duration_days is None or duration_days < MIN_SELF_EXCLUSION_DAYS:
            duration_days = MIN_SELF_EXCLUSION_DAYS

        end_date = now + timedelta(days=duration_days)

        return SelfExclusionConfig(
            user_id=user_id,
            is_permanent=False,
            start_date=now,
            end_date=end_date,
            duration_days=duration_days,
            reason=reason,
            can_be_reversed=False,
            helpline_numbers=self._get_helpline_numbers(),
            confirmation_required=True,
            message=(
                f"Self-exclusion activated for {duration_days} days "
                f"(until {end_date.strftime('%Y-%m-%d')}). "
                f"This cannot be shortened once confirmed. "
                f"Support resources are available below."
            ),
        )

    def check_self_exclusion(
        self,
        exclusion: SelfExclusionConfig | None,
        current_time: datetime | None = None,
    ) -> SelfExclusionStatus:
        """Check if a user is currently self-excluded."""
        if exclusion is None:
            return SelfExclusionStatus(
                is_excluded=False,
                message="No active self-exclusion.",
                can_play=True,
                remaining_days=None,
            )

        now = current_time or datetime.now(timezone.utc)

        if exclusion.is_permanent:
            return SelfExclusionStatus(
                is_excluded=True,
                message=(
                    "Permanent self-exclusion is active. Access to video poker "
                    "features is permanently restricted."
                ),
                can_play=False,
                remaining_days=None,
            )

        if exclusion.end_date and now >= exclusion.end_date:
            return SelfExclusionStatus(
                is_excluded=False,
                message=(
                    "Self-exclusion period has expired. You may resume play, "
                    "but please consider if you are ready."
                ),
                can_play=True,
                remaining_days=0,
            )

        remaining = (exclusion.end_date - now).days if exclusion.end_date else 0

        return SelfExclusionStatus(
            is_excluded=True,
            message=(
                f"Self-exclusion active. {remaining} days remaining "
                f"(until {exclusion.end_date.strftime('%Y-%m-%d') if exclusion.end_date else 'N/A'}). "
                f"Access is restricted."
            ),
            can_play=False,
            remaining_days=remaining,
        )

    # ------------------------------------------------------------------
    # Loss Limit Tracking
    # ------------------------------------------------------------------

    def configure_loss_limits(
        self,
        user_id: str,
        daily_limit: float | None = None,
        weekly_limit: float | None = None,
        monthly_limit: float | None = None,
    ) -> LossLimitConfig:
        """Configure loss limits. Users can lower limits immediately
        but raising limits requires a 24-hour cooling-off period.
        """
        return LossLimitConfig(
            user_id=user_id,
            daily_limit=daily_limit or DEFAULT_DAILY_LOSS_LIMIT,
            weekly_limit=weekly_limit or DEFAULT_WEEKLY_LOSS_LIMIT,
            monthly_limit=monthly_limit or DEFAULT_MONTHLY_LOSS_LIMIT,
            cooling_off_for_increase_hours=24,
            message=(
                "Loss limits configured. Lowering limits takes effect immediately. "
                "Increasing limits requires a 24-hour cooling-off period."
            ),
        )

    def check_loss_limits(
        self,
        config: LossLimitConfig,
        daily_losses: float = 0.0,
        weekly_losses: float = 0.0,
        monthly_losses: float = 0.0,
    ) -> LossLimitStatus:
        """Check current losses against configured limits."""
        alerts: list[GamblingAlert] = []
        can_continue = True

        # Daily check
        daily_pct = (daily_losses / config.daily_limit * 100) if config.daily_limit > 0 else 0
        if daily_losses >= config.daily_limit:
            can_continue = False
            alerts.append(GamblingAlert(
                severity=AlertSeverity.CRITICAL,
                category="daily_loss_limit",
                message=f"DAILY LOSS LIMIT REACHED (${daily_losses:.2f} / ${config.daily_limit:.2f}). Play suspended until tomorrow.",
            ))
        elif daily_pct >= 80:
            alerts.append(GamblingAlert(
                severity=AlertSeverity.WARNING,
                category="daily_loss_limit",
                message=f"Approaching daily loss limit: ${daily_losses:.2f} / ${config.daily_limit:.2f} ({daily_pct:.0f}%).",
            ))

        # Weekly check
        weekly_pct = (weekly_losses / config.weekly_limit * 100) if config.weekly_limit > 0 else 0
        if weekly_losses >= config.weekly_limit:
            can_continue = False
            alerts.append(GamblingAlert(
                severity=AlertSeverity.CRITICAL,
                category="weekly_loss_limit",
                message=f"WEEKLY LOSS LIMIT REACHED (${weekly_losses:.2f} / ${config.weekly_limit:.2f}). Play suspended until next week.",
            ))
        elif weekly_pct >= 80:
            alerts.append(GamblingAlert(
                severity=AlertSeverity.WARNING,
                category="weekly_loss_limit",
                message=f"Approaching weekly loss limit: ${weekly_losses:.2f} / ${config.weekly_limit:.2f} ({weekly_pct:.0f}%).",
            ))

        # Monthly check
        monthly_pct = (monthly_losses / config.monthly_limit * 100) if config.monthly_limit > 0 else 0
        if monthly_losses >= config.monthly_limit:
            can_continue = False
            alerts.append(GamblingAlert(
                severity=AlertSeverity.CRITICAL,
                category="monthly_loss_limit",
                message=f"MONTHLY LOSS LIMIT REACHED (${monthly_losses:.2f} / ${config.monthly_limit:.2f}). Play suspended until next month.",
            ))
        elif monthly_pct >= 80:
            alerts.append(GamblingAlert(
                severity=AlertSeverity.WARNING,
                category="monthly_loss_limit",
                message=f"Approaching monthly loss limit: ${monthly_losses:.2f} / ${config.monthly_limit:.2f} ({monthly_pct:.0f}%).",
            ))

        return LossLimitStatus(
            can_continue=can_continue,
            daily_losses=daily_losses,
            daily_limit=config.daily_limit,
            daily_pct=round(daily_pct, 1),
            weekly_losses=weekly_losses,
            weekly_limit=config.weekly_limit,
            weekly_pct=round(weekly_pct, 1),
            monthly_losses=monthly_losses,
            monthly_limit=config.monthly_limit,
            monthly_pct=round(monthly_pct, 1),
            alerts=alerts,
        )

    # ------------------------------------------------------------------
    # Problem Gambling Detection
    # ------------------------------------------------------------------

    def detect_problem_signals(
        self,
        user_id: str,
        session_history: list[dict[str, Any]],
        bet_history: list[float] | None = None,
        deposit_timestamps: list[datetime] | None = None,
    ) -> ProblemGamblingSignal:
        """Detect potential problem gambling signals from behavioral patterns.

        THIS IS NOT A DIAGNOSIS — it flags patterns that correlate with
        problem gambling for user awareness and optional intervention.
        """
        signals: list[GamblingAlert] = []
        risk_score = 0.0

        # Signal 1: Chasing losses (increasing bets after losses)
        if bet_history and len(bet_history) >= ESCALATING_BETS_WINDOW:
            recent = bet_history[-ESCALATING_BETS_WINDOW:]
            increases_after_loss = 0
            for i in range(1, len(recent)):
                if recent[i] > recent[i - 1] * 1.5:
                    increases_after_loss += 1

            if increases_after_loss >= CHASING_LOSS_THRESHOLD:
                risk_score += 0.3
                signals.append(GamblingAlert(
                    severity=AlertSeverity.WARNING,
                    category="chasing_losses",
                    message=(
                        f"Pattern detected: bet size increased {increases_after_loss} times "
                        f"in recent {ESCALATING_BETS_WINDOW} hands. "
                        f"Chasing losses is a key problem gambling indicator."
                    ),
                ))

        # Signal 2: Extended sessions
        long_sessions = [
            s for s in session_history
            if s.get("duration_hours", 0) >= EXTENDED_SESSION_THRESHOLD_HOURS
        ]
        if len(long_sessions) >= 2:
            risk_score += 0.2
            signals.append(GamblingAlert(
                severity=AlertSeverity.WARNING,
                category="extended_sessions",
                message=(
                    f"{len(long_sessions)} sessions exceeded {EXTENDED_SESSION_THRESHOLD_HOURS} hours. "
                    f"Prolonged gambling sessions increase risk."
                ),
            ))

        # Signal 3: Rapid deposits
        if deposit_timestamps and len(deposit_timestamps) >= RAPID_DEPOSIT_THRESHOLD:
            sorted_deposits = sorted(deposit_timestamps)
            for i in range(len(sorted_deposits) - RAPID_DEPOSIT_THRESHOLD + 1):
                window = sorted_deposits[i:i + RAPID_DEPOSIT_THRESHOLD]
                if (window[-1] - window[0]).total_seconds() <= 3600:
                    risk_score += 0.25
                    signals.append(GamblingAlert(
                        severity=AlertSeverity.HIGH,
                        category="rapid_deposits",
                        message=(
                            f"{RAPID_DEPOSIT_THRESHOLD} deposits within 1 hour detected. "
                            f"Frequent re-depositing is a strong problem gambling signal."
                        ),
                    ))
                    break

        # Signal 4: Increasing session frequency
        if len(session_history) >= 7:
            recent_week = session_history[-7:]
            prior_week = session_history[-14:-7] if len(session_history) >= 14 else []
            if prior_week and len(recent_week) >= len(prior_week) * 1.5:
                risk_score += 0.15
                signals.append(GamblingAlert(
                    severity=AlertSeverity.INFO,
                    category="increasing_frequency",
                    message="Session frequency has increased significantly over the past week.",
                ))

        # Signal 5: Playing during unusual hours (late night)
        late_sessions = [
            s for s in session_history
            if s.get("start_hour", 12) >= 23 or s.get("start_hour", 12) <= 4
        ]
        if len(late_sessions) >= 3:
            risk_score += 0.1
            signals.append(GamblingAlert(
                severity=AlertSeverity.INFO,
                category="late_night_play",
                message=(
                    f"{len(late_sessions)} late-night sessions detected. "
                    f"Playing during unusual hours can indicate compulsive patterns."
                ),
            ))

        risk_score = round(min(risk_score, 1.0), 2)

        if risk_score >= 0.6:
            level = ProblemGamblingRiskLevel.HIGH
        elif risk_score >= 0.3:
            level = ProblemGamblingRiskLevel.MODERATE
        elif risk_score > 0:
            level = ProblemGamblingRiskLevel.LOW
        else:
            level = ProblemGamblingRiskLevel.NONE

        return ProblemGamblingSignal(
            user_id=user_id,
            risk_level=level,
            risk_score=risk_score,
            signals=signals,
            recommendation=self._problem_gambling_recommendation(level),
            helpline_numbers=self._get_helpline_numbers() if risk_score > 0 else [],
            disclaimer=(
                "This assessment is based on behavioral pattern analysis and is "
                "NOT a clinical diagnosis. If you are concerned about your gambling, "
                "please contact a professional helpline."
            ),
        )

    # ------------------------------------------------------------------
    # Cooling-Off Period
    # ------------------------------------------------------------------

    def enforce_cooling_off(
        self,
        user_id: str,
        hours: int = MIN_COOLING_OFF_HOURS,
        reason: str = "user_requested",
    ) -> CoolingOffPeriod:
        """Activate a cooling-off period. Cannot be shortened once activated."""
        if hours < MIN_COOLING_OFF_HOURS:
            hours = MIN_COOLING_OFF_HOURS

        now = datetime.now(timezone.utc)
        end = now + timedelta(hours=hours)

        return CoolingOffPeriod(
            user_id=user_id,
            start_time=now,
            end_time=end,
            duration_hours=hours,
            reason=reason,
            is_active=True,
            can_be_shortened=False,
            message=(
                f"Cooling-off period activated for {hours} hours "
                f"(until {end.strftime('%Y-%m-%d %H:%M UTC')}). "
                f"This cannot be shortened."
            ),
        )

    def check_cooling_off(
        self,
        period: CoolingOffPeriod | None,
        current_time: datetime | None = None,
    ) -> bool:
        """Return True if cooling-off is active (user cannot play)."""
        if period is None:
            return False
        now = current_time or datetime.now(timezone.utc)
        return now < period.end_time

    # ------------------------------------------------------------------
    # Comprehensive Compliance Check
    # ------------------------------------------------------------------

    def full_compliance_check(
        self,
        user_id: str,
        self_exclusion: SelfExclusionConfig | None = None,
        cooling_off: CoolingOffPeriod | None = None,
        session_limit: SessionTimeLimit | None = None,
        loss_config: LossLimitConfig | None = None,
        daily_losses: float = 0.0,
        weekly_losses: float = 0.0,
        monthly_losses: float = 0.0,
        current_time: datetime | None = None,
    ) -> ComplianceStatus:
        """Run ALL compliance checks and return unified status.

        This is the gateway function — call before every video poker action.
        """
        now = current_time or datetime.now(timezone.utc)
        blocks: list[str] = []
        warnings: list[str] = []

        # Self-exclusion
        exclusion_status = self.check_self_exclusion(self_exclusion, now)
        if exclusion_status.is_excluded:
            blocks.append(exclusion_status.message)

        # Cooling-off
        if self.check_cooling_off(cooling_off, now):
            blocks.append(
                f"Cooling-off period active until {cooling_off.end_time.strftime('%Y-%m-%d %H:%M UTC')}."  # type: ignore[union-attr]
            )

        # Session time
        if session_limit:
            time_status = self.check_session_time(session_limit, now)
            if time_status.action == "force_stop":
                blocks.append(time_status.message)
            elif time_status.action == "warn":
                warnings.append(time_status.message)

        # Loss limits
        if loss_config:
            loss_status = self.check_loss_limits(
                loss_config, daily_losses, weekly_losses, monthly_losses,
            )
            if not loss_status.can_continue:
                for alert in loss_status.alerts:
                    if alert.severity == AlertSeverity.CRITICAL:
                        blocks.append(alert.message)
            for alert in loss_status.alerts:
                if alert.severity == AlertSeverity.WARNING:
                    warnings.append(alert.message)

        can_play = len(blocks) == 0

        return ComplianceStatus(
            user_id=user_id,
            can_play=can_play,
            blocks=blocks,
            warnings=warnings,
            checked_at=now,
            message=(
                "All compliance checks passed."
                if can_play
                else "ACCESS BLOCKED: " + " | ".join(blocks)
            ),
        )

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _get_helpline_numbers() -> list[dict[str, str]]:
        return [
            {"name": "National Problem Gambling Helpline", "number": "1-800-522-4700", "available": "24/7"},
            {"name": "NCPG Text Line", "number": "Text HOME to 741741", "available": "24/7"},
            {"name": "Gamblers Anonymous", "number": "https://www.gamblersanonymous.org", "available": "Online"},
            {"name": "National Council on Problem Gambling", "number": "https://www.ncpgambling.org", "available": "Online"},
        ]

    @staticmethod
    def _problem_gambling_recommendation(level: ProblemGamblingRiskLevel) -> str:
        if level == ProblemGamblingRiskLevel.HIGH:
            return (
                "Multiple problem gambling indicators detected. We strongly recommend "
                "taking a break and speaking with a gambling counselor. "
                "Consider activating self-exclusion. Helpline: 1-800-522-4700."
            )
        if level == ProblemGamblingRiskLevel.MODERATE:
            return (
                "Some concerning patterns detected. Please review your gambling habits "
                "and consider setting stricter loss limits or taking a cooling-off period."
            )
        if level == ProblemGamblingRiskLevel.LOW:
            return (
                "Minor signals detected. Stay mindful of your gambling habits "
                "and remember to play within your limits."
            )
        return "No problem gambling signals detected. Continue playing responsibly."
