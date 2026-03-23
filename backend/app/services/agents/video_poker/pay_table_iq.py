"""PayTableIQ — return-to-player calculator, best-game scanner, walk-away trigger.

Analyzes video poker pay tables to calculate theoretical RTP, compares
available machines, and signals when a table's payout structure is
unfavorable enough to warrant walking away.
"""

from __future__ import annotations

import logging
from typing import Any

from app.schemas.video_poker.pay_table import (
    GameComparison,
    PayTableEntry,
    PayTableRating,
    RTPBreakdown,
    WalkAwaySignal,
    WalkAwayReason,
)
from app.schemas.video_poker.strategy import HandRanking, VariantType

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Full-pay RTP references (theoretical optimal play)
# ---------------------------------------------------------------------------

FULL_PAY_RTP: dict[VariantType, float] = {
    VariantType.JACKS_OR_BETTER: 99.54,
    VariantType.DEUCES_WILD: 100.76,
    VariantType.DOUBLE_BONUS: 100.17,
    VariantType.DOUBLE_DOUBLE_BONUS: 98.98,
    VariantType.JOKER_POKER: 100.64,
}

# Standard full-pay tables (coins per 1-coin bet)
FULL_PAY_TABLES: dict[VariantType, dict[str, int]] = {
    VariantType.JACKS_OR_BETTER: {
        "royal_flush": 800,
        "straight_flush": 50,
        "four_of_a_kind": 25,
        "full_house": 9,
        "flush": 6,
        "straight": 4,
        "three_of_a_kind": 3,
        "two_pair": 2,
        "jacks_or_better": 1,
    },
    VariantType.DEUCES_WILD: {
        "royal_flush": 800,
        "four_deuces": 200,
        "wild_royal": 25,
        "five_of_a_kind": 15,
        "straight_flush": 9,
        "four_of_a_kind": 5,
        "full_house": 3,
        "flush": 2,
        "straight": 2,
        "three_of_a_kind": 1,
    },
    VariantType.DOUBLE_BONUS: {
        "royal_flush": 800,
        "straight_flush": 50,
        "four_aces": 160,
        "four_2s_3s_4s": 80,
        "four_of_a_kind": 50,
        "full_house": 10,
        "flush": 7,
        "straight": 5,
        "three_of_a_kind": 3,
        "two_pair": 1,
        "jacks_or_better": 1,
    },
}

# Hand probability weights for RTP calculation (Jacks or Better baseline)
HAND_FREQUENCIES: dict[str, float] = {
    "royal_flush": 0.00002,
    "straight_flush": 0.00011,
    "four_of_a_kind": 0.00236,
    "full_house": 0.01151,
    "flush": 0.01101,
    "straight": 0.01123,
    "three_of_a_kind": 0.07445,
    "two_pair": 0.12928,
    "jacks_or_better": 0.21459,
}

# Walk-away thresholds
WALK_AWAY_RTP_THRESHOLD = 97.0  # Below this, strongly recommend walking away
CAUTION_RTP_THRESHOLD = 98.5    # Below this, flag caution


# ---------------------------------------------------------------------------
# PayTableIQ
# ---------------------------------------------------------------------------

class PayTableIQ:
    """Video poker pay table intelligence — evaluates, compares, and alerts."""

    def calculate_rtp(
        self,
        pay_table: list[PayTableEntry],
        variant: VariantType = VariantType.JACKS_OR_BETTER,
    ) -> RTPBreakdown:
        """Calculate theoretical return-to-player from a pay table.

        Uses hand frequency weights and pay amounts to compute expected
        return per coin wagered.
        """
        total_return = 0.0
        hand_contributions: list[dict[str, Any]] = []

        for entry in pay_table:
            frequency = HAND_FREQUENCIES.get(entry.hand_name, 0.0)
            contribution = frequency * entry.payout
            total_return += contribution
            hand_contributions.append({
                "hand": entry.hand_name,
                "payout": entry.payout,
                "frequency": round(frequency, 6),
                "contribution_pct": round(contribution * 100, 4),
            })

        rtp_pct = round(total_return * 100, 2)
        full_pay = FULL_PAY_RTP.get(variant, 99.54)
        deviation = round(rtp_pct - full_pay, 2)

        if rtp_pct >= full_pay - 0.1:
            quality = "full_pay"
        elif rtp_pct >= CAUTION_RTP_THRESHOLD:
            quality = "near_full_pay"
        elif rtp_pct >= WALK_AWAY_RTP_THRESHOLD:
            quality = "short_pay"
        else:
            quality = "avoid"

        return RTPBreakdown(
            rtp_pct=rtp_pct,
            full_pay_rtp=full_pay,
            deviation_from_full=deviation,
            quality_rating=quality,
            hand_contributions=hand_contributions,
            house_edge_pct=round(100.0 - rtp_pct, 2),
            variant=variant,
        )

    def compare_games(
        self,
        games: list[dict[str, Any]],
    ) -> GameComparison:
        """Compare multiple available video poker games and rank them.

        Each game dict: {name, variant, pay_table: list[PayTableEntry]}
        """
        ratings: list[PayTableRating] = []

        for game in games:
            variant = game.get("variant", VariantType.JACKS_OR_BETTER)
            pay_table = game.get("pay_table", [])
            name = game.get("name", "Unknown")

            rtp = self.calculate_rtp(pay_table, variant)

            rating = PayTableRating(
                game_name=name,
                variant=variant,
                rtp_pct=rtp.rtp_pct,
                house_edge_pct=rtp.house_edge_pct,
                quality_rating=rtp.quality_rating,
                full_pay_deviation=rtp.deviation_from_full,
                recommendation=self._make_recommendation(rtp),
            )
            ratings.append(rating)

        # Sort by RTP descending
        ratings.sort(key=lambda r: r.rtp_pct, reverse=True)
        best = ratings[0] if ratings else None
        worst = ratings[-1] if ratings else None

        return GameComparison(
            ratings=ratings,
            best_game=best.game_name if best else None,
            best_rtp=best.rtp_pct if best else 0.0,
            worst_game=worst.game_name if worst else None,
            worst_rtp=worst.rtp_pct if worst else 0.0,
            rtp_spread=round(
                (best.rtp_pct - worst.rtp_pct) if best and worst else 0.0, 2
            ),
            recommendation=(
                f"Play {best.game_name} ({best.rtp_pct}% RTP) — "
                f"{best.rtp_pct - worst.rtp_pct:.2f}% better than {worst.game_name}."
                if best and worst and len(ratings) > 1
                else "Only one game available."
            ),
        )

    def check_walk_away(
        self,
        rtp_pct: float,
        session_loss_pct: float = 0.0,
        hands_played: int = 0,
    ) -> WalkAwaySignal:
        """Determine if the player should walk away from the current game.

        Considers both pay table quality AND session performance.
        """
        reasons: list[WalkAwayReason] = []
        severity = "ok"

        # Pay table quality check
        if rtp_pct < WALK_AWAY_RTP_THRESHOLD:
            reasons.append(WalkAwayReason(
                factor="pay_table_quality",
                detail=f"RTP {rtp_pct}% is below {WALK_AWAY_RTP_THRESHOLD}% threshold.",
                weight=0.8,
            ))
            severity = "walk_away"
        elif rtp_pct < CAUTION_RTP_THRESHOLD:
            reasons.append(WalkAwayReason(
                factor="pay_table_quality",
                detail=f"RTP {rtp_pct}% is below full-pay. Consider finding a better machine.",
                weight=0.4,
            ))
            if severity == "ok":
                severity = "caution"

        # Session loss check
        if session_loss_pct >= 50.0:
            reasons.append(WalkAwayReason(
                factor="session_loss",
                detail=f"Session loss of {session_loss_pct:.1f}% of bankroll — stop-loss triggered.",
                weight=0.9,
            ))
            severity = "walk_away"
        elif session_loss_pct >= 30.0:
            reasons.append(WalkAwayReason(
                factor="session_loss",
                detail=f"Session loss of {session_loss_pct:.1f}% — approaching stop-loss.",
                weight=0.5,
            ))
            if severity == "ok":
                severity = "caution"

        # Extended play fatigue
        if hands_played >= 500:
            reasons.append(WalkAwayReason(
                factor="session_length",
                detail=f"{hands_played} hands played — fatigue increases mistake rate.",
                weight=0.3,
            ))
            if severity == "ok":
                severity = "caution"

        should_walk = severity == "walk_away"
        total_weight = sum(r.weight for r in reasons) if reasons else 0.0

        return WalkAwaySignal(
            should_walk_away=should_walk,
            severity=severity,
            reasons=reasons,
            urgency_score=round(min(total_weight, 1.0), 2),
            recommendation=(
                "STOP PLAYING — unfavorable conditions detected."
                if should_walk
                else "Continue with awareness."
                if severity == "caution"
                else "Conditions acceptable — play on."
            ),
        )

    def scan_best_game(
        self,
        available_games: list[dict[str, Any]],
    ) -> dict[str, Any]:
        """Quick scan to find the single best available game.

        Returns the game with highest RTP and a summary.
        """
        if not available_games:
            return {"found": False, "message": "No games available to scan."}

        comparison = self.compare_games(available_games)
        best = comparison.ratings[0] if comparison.ratings else None

        if not best:
            return {"found": False, "message": "Could not evaluate any games."}

        return {
            "found": True,
            "game_name": best.game_name,
            "variant": best.variant,
            "rtp_pct": best.rtp_pct,
            "quality": best.quality_rating,
            "recommendation": best.recommendation,
            "should_play": best.rtp_pct >= WALK_AWAY_RTP_THRESHOLD,
        }

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _make_recommendation(rtp: RTPBreakdown) -> str:
        if rtp.quality_rating == "full_pay":
            return f"Excellent! Full-pay {rtp.variant.value} at {rtp.rtp_pct}% RTP."
        if rtp.quality_rating == "near_full_pay":
            return (
                f"Good table — {rtp.deviation_from_full:+.2f}% from full pay. "
                f"Acceptable for play."
            )
        if rtp.quality_rating == "short_pay":
            return (
                f"Short-pay table ({rtp.rtp_pct}% RTP). "
                f"Look for a better machine if possible."
            )
        return (
            f"AVOID — {rtp.rtp_pct}% RTP is unacceptable. "
            f"House edge of {rtp.house_edge_pct}% is too high."
        )
