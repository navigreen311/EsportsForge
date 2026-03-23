"""BankrollForge — session bankroll calculator, stop-loss/win discipline, variance modeling.

Provides mathematically grounded bankroll management for video poker
including session sizing, ruin probability, stop-loss/win-goal enforcement,
and variance-aware play duration estimates.
"""

from __future__ import annotations

import logging
import math
from typing import Any

from app.schemas.video_poker.bankroll import (
    BankrollPlan,
    RiskLevel,
    RuinProbability,
    SessionBudget,
    StopLossConfig,
    VarianceProfile,
    WinGoalStatus,
)
from app.schemas.video_poker.strategy import VariantType

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Variance parameters per variant (standard deviation per hand in bet units)
# ---------------------------------------------------------------------------

VARIANCE_BY_VARIANT: dict[VariantType, float] = {
    VariantType.JACKS_OR_BETTER: 4.42,
    VariantType.DEUCES_WILD: 5.08,
    VariantType.DOUBLE_BONUS: 6.35,
    VariantType.DOUBLE_DOUBLE_BONUS: 7.04,
    VariantType.JOKER_POKER: 5.65,
}

# RTP with perfect play
RTP_BY_VARIANT: dict[VariantType, float] = {
    VariantType.JACKS_OR_BETTER: 99.54,
    VariantType.DEUCES_WILD: 100.76,
    VariantType.DOUBLE_BONUS: 100.17,
    VariantType.DOUBLE_DOUBLE_BONUS: 98.98,
    VariantType.JOKER_POKER: 100.64,
}

# Risk tolerance multipliers for bankroll sizing
RISK_MULTIPLIERS: dict[RiskLevel, float] = {
    RiskLevel.CONSERVATIVE: 3.0,
    RiskLevel.MODERATE: 2.0,
    RiskLevel.AGGRESSIVE: 1.5,
}

# Default stop-loss percentages
DEFAULT_STOP_LOSS_PCT = 40.0
DEFAULT_WIN_GOAL_PCT = 30.0

# Responsible gambling absolute limits
MAX_SESSION_HOURS = 4.0
MAX_DAILY_SESSIONS = 3


# ---------------------------------------------------------------------------
# BankrollForge
# ---------------------------------------------------------------------------

class BankrollForge:
    """Bankroll management engine for video poker sessions."""

    def calculate_session_bankroll(
        self,
        total_bankroll: float,
        bet_size: float,
        variant: VariantType = VariantType.JACKS_OR_BETTER,
        risk_level: RiskLevel = RiskLevel.MODERATE,
        target_hours: float = 2.0,
    ) -> SessionBudget:
        """Calculate the optimal session bankroll based on total funds and risk tolerance.

        Uses variance modeling to determine how much to bring to a session.
        """
        if total_bankroll <= 0 or bet_size <= 0:
            return SessionBudget(
                session_bankroll=0.0,
                bet_size=bet_size,
                total_bankroll=total_bankroll,
                hands_supported=0,
                estimated_duration_hours=0.0,
                stop_loss=0.0,
                win_goal=0.0,
                risk_level=risk_level,
                warning=None if total_bankroll > 0 else "Invalid bankroll or bet size.",
            )

        sd = VARIANCE_BY_VARIANT.get(variant, 4.42)
        multiplier = RISK_MULTIPLIERS.get(risk_level, 2.0)

        # Hands per hour (average video poker pace)
        hands_per_hour = 400
        target_hands = int(target_hours * hands_per_hour)

        # Session bankroll = multiplier * SD * sqrt(hands) * bet_size
        session_bet_units = multiplier * sd * math.sqrt(target_hands)
        session_bankroll = round(session_bet_units * bet_size, 2)

        # Cap at percentage of total bankroll (never risk more than 20%)
        max_session = total_bankroll * 0.20
        if session_bankroll > max_session:
            session_bankroll = round(max_session, 2)
            target_hands = int((session_bankroll / bet_size / (multiplier * sd)) ** 2)
            target_hours = target_hands / hands_per_hour

        hands_supported = int(session_bankroll / bet_size) if bet_size > 0 else 0
        estimated_hours = round(hands_supported / hands_per_hour, 1)

        # Enforce max session time
        if estimated_hours > MAX_SESSION_HOURS:
            estimated_hours = MAX_SESSION_HOURS
            hands_supported = int(MAX_SESSION_HOURS * hands_per_hour)
            session_bankroll = round(hands_supported * bet_size * 0.5, 2)

        stop_loss = round(session_bankroll * (DEFAULT_STOP_LOSS_PCT / 100), 2)
        win_goal = round(session_bankroll * (DEFAULT_WIN_GOAL_PCT / 100), 2)

        warning = None
        if session_bankroll > total_bankroll * 0.15:
            warning = (
                "Session bankroll exceeds 15% of total funds. "
                "Consider lowering bet size or session duration."
            )

        return SessionBudget(
            session_bankroll=session_bankroll,
            bet_size=bet_size,
            total_bankroll=total_bankroll,
            hands_supported=hands_supported,
            estimated_duration_hours=estimated_hours,
            stop_loss=stop_loss,
            win_goal=win_goal,
            risk_level=risk_level,
            warning=warning,
        )

    def configure_stop_loss(
        self,
        session_bankroll: float,
        stop_loss_pct: float = DEFAULT_STOP_LOSS_PCT,
        win_goal_pct: float = DEFAULT_WIN_GOAL_PCT,
        trailing_stop: bool = False,
    ) -> StopLossConfig:
        """Configure stop-loss and win-goal discipline for a session."""
        stop_loss_amount = round(session_bankroll * (stop_loss_pct / 100), 2)
        win_goal_amount = round(session_bankroll * (win_goal_pct / 100), 2)

        return StopLossConfig(
            session_bankroll=session_bankroll,
            stop_loss_pct=stop_loss_pct,
            stop_loss_amount=stop_loss_amount,
            win_goal_pct=win_goal_pct,
            win_goal_amount=win_goal_amount,
            trailing_stop_enabled=trailing_stop,
            walk_away_floor=round(session_bankroll - stop_loss_amount, 2),
            walk_away_ceiling=round(session_bankroll + win_goal_amount, 2),
            rules=[
                f"STOP if balance drops to ${session_bankroll - stop_loss_amount:.2f} "
                f"(loss of ${stop_loss_amount:.2f}).",
                f"LOCK PROFIT if balance reaches ${session_bankroll + win_goal_amount:.2f} "
                f"(gain of ${win_goal_amount:.2f}).",
                "Never chase losses past the stop-loss.",
                "Never increase bet size to recover losses.",
                f"Maximum session duration: {MAX_SESSION_HOURS} hours.",
            ],
        )

    def check_win_goal(
        self,
        session_bankroll: float,
        current_balance: float,
        config: StopLossConfig,
        peak_balance: float | None = None,
    ) -> WinGoalStatus:
        """Check current session status against stop-loss and win-goal.

        Returns action guidance: continue, lock_profit, or stop.
        """
        net_result = current_balance - session_bankroll
        loss_pct = abs(net_result) / session_bankroll * 100 if net_result < 0 else 0.0

        # Stop-loss check
        if current_balance <= config.walk_away_floor:
            return WinGoalStatus(
                action="stop",
                reason="stop_loss_hit",
                current_balance=current_balance,
                net_result=round(net_result, 2),
                message=(
                    f"STOP — Stop-loss triggered. Lost ${abs(net_result):.2f} "
                    f"({loss_pct:.1f}% of session bankroll)."
                ),
                pct_of_stop_loss=round(loss_pct, 1),
                pct_of_win_goal=0.0,
            )

        # Win-goal check
        if current_balance >= config.walk_away_ceiling:
            gain_pct = net_result / session_bankroll * 100
            return WinGoalStatus(
                action="lock_profit",
                reason="win_goal_reached",
                current_balance=current_balance,
                net_result=round(net_result, 2),
                message=(
                    f"WIN GOAL reached! Up ${net_result:.2f} "
                    f"({gain_pct:.1f}%). Lock profits and consider stopping."
                ),
                pct_of_stop_loss=0.0,
                pct_of_win_goal=round(gain_pct, 1),
            )

        # Trailing stop check
        if config.trailing_stop_enabled and peak_balance is not None:
            trail_threshold = peak_balance * 0.75
            if current_balance < trail_threshold and net_result > 0:
                return WinGoalStatus(
                    action="lock_profit",
                    reason="trailing_stop",
                    current_balance=current_balance,
                    net_result=round(net_result, 2),
                    message=(
                        f"Trailing stop: balance dropped 25% from peak "
                        f"(${peak_balance:.2f} -> ${current_balance:.2f}). "
                        f"Lock remaining ${net_result:.2f} profit."
                    ),
                    pct_of_stop_loss=0.0,
                    pct_of_win_goal=round(net_result / session_bankroll * 100, 1),
                )

        # Continue
        progress_to_stop = round(loss_pct / config.stop_loss_pct * 100, 1) if net_result < 0 else 0.0
        progress_to_win = (
            round(net_result / config.win_goal_amount * 100, 1)
            if net_result > 0 and config.win_goal_amount > 0
            else 0.0
        )

        return WinGoalStatus(
            action="continue",
            reason="within_limits",
            current_balance=current_balance,
            net_result=round(net_result, 2),
            message=f"Session in progress. Net: ${net_result:+.2f}.",
            pct_of_stop_loss=progress_to_stop,
            pct_of_win_goal=progress_to_win,
        )

    def model_variance(
        self,
        variant: VariantType = VariantType.JACKS_OR_BETTER,
        bet_size: float = 1.25,
        num_hands: int = 1000,
    ) -> VarianceProfile:
        """Model expected variance over a number of hands.

        Provides confidence intervals for session outcomes.
        """
        sd_per_hand = VARIANCE_BY_VARIANT.get(variant, 4.42)
        rtp = RTP_BY_VARIANT.get(variant, 99.54) / 100.0
        house_edge = 1.0 - rtp

        # Expected loss in bet units
        expected_loss_units = house_edge * num_hands
        expected_loss_dollars = round(expected_loss_units * bet_size, 2)

        # Standard deviation over N hands
        session_sd_units = sd_per_hand * math.sqrt(num_hands)
        session_sd_dollars = round(session_sd_units * bet_size, 2)

        # Confidence intervals
        ci_68_low = round((-expected_loss_units - session_sd_units) * bet_size, 2)
        ci_68_high = round((-expected_loss_units + session_sd_units) * bet_size, 2)
        ci_95_low = round((-expected_loss_units - 2 * session_sd_units) * bet_size, 2)
        ci_95_high = round((-expected_loss_units + 2 * session_sd_units) * bet_size, 2)

        # Probability of being ahead
        z_score = expected_loss_units / session_sd_units if session_sd_units > 0 else 0
        # Approximate using complementary CDF
        prob_ahead = round(0.5 * (1 + math.erf(-z_score / math.sqrt(2))) * 100, 1)

        return VarianceProfile(
            variant=variant,
            bet_size=bet_size,
            num_hands=num_hands,
            sd_per_hand=sd_per_hand,
            session_sd_dollars=session_sd_dollars,
            expected_loss_dollars=expected_loss_dollars,
            ci_68_range=(ci_68_low, ci_68_high),
            ci_95_range=(ci_95_low, ci_95_high),
            prob_ahead_pct=prob_ahead,
            risk_assessment=self._assess_risk(prob_ahead, session_sd_dollars, bet_size),
        )

    def calculate_ruin_probability(
        self,
        bankroll: float,
        bet_size: float,
        variant: VariantType = VariantType.JACKS_OR_BETTER,
        target_hands: int = 5000,
    ) -> RuinProbability:
        """Estimate probability of losing entire bankroll over target hands."""
        if bankroll <= 0 or bet_size <= 0:
            return RuinProbability(
                ruin_pct=100.0,
                bankroll=bankroll,
                bet_size=bet_size,
                target_hands=target_hands,
                bankroll_to_bet_ratio=0.0,
                assessment="Insufficient bankroll.",
            )

        sd = VARIANCE_BY_VARIANT.get(variant, 4.42)
        rtp = RTP_BY_VARIANT.get(variant, 99.54) / 100.0
        edge = 1.0 - rtp

        bankroll_units = bankroll / bet_size
        session_sd = sd * math.sqrt(target_hands)
        expected_loss = edge * target_hands

        # Simplified ruin approximation
        z = (bankroll_units - expected_loss) / session_sd if session_sd > 0 else 10
        ruin_pct = round(max(0.0, min(100.0, (1 - 0.5 * (1 + math.erf(z / math.sqrt(2)))) * 100)), 2)

        ratio = round(bankroll_units, 1)

        if ruin_pct < 1:
            assessment = "Very safe bankroll for this session length."
        elif ruin_pct < 5:
            assessment = "Low risk of ruin — good bankroll management."
        elif ruin_pct < 15:
            assessment = "Moderate risk — consider shorter sessions or smaller bets."
        elif ruin_pct < 30:
            assessment = "High risk of ruin — reduce bet size or session length."
        else:
            assessment = "DANGER — very high ruin probability. Reduce stakes immediately."

        return RuinProbability(
            ruin_pct=ruin_pct,
            bankroll=bankroll,
            bet_size=bet_size,
            target_hands=target_hands,
            bankroll_to_bet_ratio=ratio,
            assessment=assessment,
        )

    def create_bankroll_plan(
        self,
        total_bankroll: float,
        variant: VariantType = VariantType.JACKS_OR_BETTER,
        risk_level: RiskLevel = RiskLevel.MODERATE,
        sessions_per_week: int = 3,
    ) -> BankrollPlan:
        """Create a comprehensive bankroll management plan."""
        # Determine appropriate bet size (bankroll / recommended units)
        unit_targets = {
            RiskLevel.CONSERVATIVE: 2000,
            RiskLevel.MODERATE: 1000,
            RiskLevel.AGGRESSIVE: 500,
        }
        target_units = unit_targets.get(risk_level, 1000)
        recommended_bet = round(total_bankroll / target_units, 2)

        # Snap to common denominations
        common_bets = [0.25, 0.50, 1.00, 1.25, 2.50, 5.00, 10.00, 25.00]
        recommended_bet = min(common_bets, key=lambda x: abs(x - recommended_bet))

        session_budget = self.calculate_session_bankroll(
            total_bankroll, recommended_bet, variant, risk_level,
        )

        ruin = self.calculate_ruin_probability(
            total_bankroll, recommended_bet, variant,
        )

        variance = self.model_variance(variant, recommended_bet, 800)

        # Weekly plan
        weekly_exposure = session_budget.session_bankroll * sessions_per_week
        weekly_expected_loss = variance.expected_loss_dollars * sessions_per_week

        return BankrollPlan(
            total_bankroll=total_bankroll,
            recommended_bet_size=recommended_bet,
            session_bankroll=session_budget.session_bankroll,
            sessions_per_week=sessions_per_week,
            weekly_exposure=round(weekly_exposure, 2),
            weekly_expected_cost=round(abs(weekly_expected_loss), 2),
            ruin_probability_pct=ruin.ruin_pct,
            risk_level=risk_level,
            variant=variant,
            rules=[
                f"Bet size: ${recommended_bet:.2f} per hand (5 coins = ${recommended_bet * 5:.2f}).",
                f"Session bankroll: ${session_budget.session_bankroll:.2f}.",
                f"Stop-loss: ${session_budget.stop_loss:.2f} per session.",
                f"Win goal: ${session_budget.win_goal:.2f} per session.",
                f"Max {sessions_per_week} sessions per week.",
                f"Max {MAX_SESSION_HOURS} hours per session.",
                "Never borrow money to gamble.",
                "Never chase losses.",
            ],
        )

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _assess_risk(
        prob_ahead: float,
        session_sd: float,
        bet_size: float,
    ) -> str:
        if prob_ahead >= 50:
            return "Favorable — positive EV variant with adequate bankroll."
        if prob_ahead >= 45:
            return "Near-even — small house edge, variance dominates short-term."
        if prob_ahead >= 35:
            return "Moderate — expect short-term swings, long-term house edge."
        return "High variance — significant bankroll swings expected."
