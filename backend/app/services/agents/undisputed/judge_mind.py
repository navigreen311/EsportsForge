"""JudgeMind — scorecard logic, round banking strategy, and body work ROI analysis.

Models the scoring system, tracks round-by-round scorecard projection,
calculates when to bank rounds vs when to go for the finish, and
evaluates the return on investment of body work over time.
"""

from __future__ import annotations

import logging
from typing import Any

from app.schemas.undisputed.boxing import (
    BodyWorkROI,
    RoundBankStrategy,
    RoundScore,
    ScorecardProjection,
)

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Scoring criteria weights (10-point must system)
# ---------------------------------------------------------------------------

_SCORING_WEIGHTS: dict[str, float] = {
    "clean_punches_landed": 0.35,
    "effective_aggression": 0.25,
    "ring_generalship": 0.20,
    "defense": 0.20,
}

# Body work damage accumulation model
_BODY_DAMAGE_CURVE: list[tuple[int, float]] = [
    (1, 0.05),   # round 1: minimal accumulated effect
    (3, 0.15),
    (5, 0.30),
    (7, 0.50),
    (9, 0.70),
    (11, 0.85),
    (12, 0.95),
]


class JudgeMind:
    """Undisputed scorecard and strategy engine.

    Projects scorecards, recommends round banking strategy,
    and evaluates body work ROI over multi-round fights.
    """

    # ------------------------------------------------------------------
    # Round scoring
    # ------------------------------------------------------------------

    def score_round(
        self,
        round_num: int,
        player_stats: dict[str, Any],
        opponent_stats: dict[str, Any],
    ) -> RoundScore:
        """Score a single round using the 10-point must system.

        Expected stats: punches_landed, punches_thrown, power_landed,
        body_landed, ring_control (0-1), defense_rating (0-1), knockdowns.
        """
        player_score = self._compute_round_points(player_stats)
        opponent_score = self._compute_round_points(opponent_stats)

        # Knockdown bonus
        player_kd = player_stats.get("knockdowns", 0)
        opponent_kd = opponent_stats.get("knockdowns", 0)

        if player_score > opponent_score:
            score_player = 10
            score_opponent = 9
        elif opponent_score > player_score:
            score_player = 9
            score_opponent = 10
        else:
            score_player = 10
            score_opponent = 10  # Even round

        # Knockdown deductions
        score_opponent -= player_kd  # Each KD scored by player deducts from opponent
        score_player -= opponent_kd

        score_player = max(7, score_player)
        score_opponent = max(7, score_opponent)

        winning = "player" if score_player > score_opponent else (
            "opponent" if score_opponent > score_player else "even"
        )

        key_moment = ""
        if player_kd > 0:
            key_moment = f"Player scored {player_kd} knockdown(s) — dominant round."
        elif opponent_kd > 0:
            key_moment = f"Opponent scored {opponent_kd} knockdown(s) — rough round."
        elif abs(player_score - opponent_score) < 0.5:
            key_moment = "Razor-thin round — could go either way on the cards."

        return RoundScore(
            round_num=round_num,
            player_score=score_player,
            opponent_score=score_opponent,
            winning=winning,
            player_points=round(player_score, 2),
            opponent_points=round(opponent_score, 2),
            key_moment=key_moment,
        )

    # ------------------------------------------------------------------
    # Scorecard projection
    # ------------------------------------------------------------------

    def project_scorecard(
        self,
        round_scores: list[RoundScore],
        total_rounds: int = 12,
    ) -> ScorecardProjection:
        """Project the final scorecard from current round scores.

        Calculates running totals, identifies swing rounds needed,
        and recommends strategy adjustments.
        """
        player_total = sum(r.player_score for r in round_scores)
        opponent_total = sum(r.opponent_score for r in round_scores)
        rounds_completed = len(round_scores)
        rounds_remaining = total_rounds - rounds_completed

        margin = player_total - opponent_total
        player_rounds_won = sum(1 for r in round_scores if r.winning == "player")
        opponent_rounds_won = sum(1 for r in round_scores if r.winning == "opponent")
        even_rounds = sum(1 for r in round_scores if r.winning == "even")

        # Projection
        if rounds_completed > 0:
            avg_margin_per_round = margin / rounds_completed
            projected_margin = margin + (avg_margin_per_round * rounds_remaining)
        else:
            projected_margin = 0.0

        projected_winner = "player" if projected_margin > 0 else (
            "opponent" if projected_margin < 0 else "draw"
        )

        # Strategy recommendation
        strategy: list[str] = []
        if margin >= 3:
            strategy.append("Comfortable lead — protect it. Be smart, don't take risks.")
            strategy.append("Outbox, use the jab, and don't engage in firefights.")
        elif margin >= 1:
            strategy.append("Slight lead — stay disciplined. Win clean rounds.")
        elif margin == 0:
            strategy.append("Even fight — every round matters. Increase activity to sway judges.")
        elif margin >= -2:
            strategy.append("Slight deficit — increase aggression. You need swing rounds.")
        else:
            strategy.append("Behind on the cards — you may need a knockdown or finish.")
            strategy.append("Take calculated risks. Body-head combos to create opportunities.")

        return ScorecardProjection(
            rounds_completed=rounds_completed,
            total_rounds=total_rounds,
            player_total=player_total,
            opponent_total=opponent_total,
            margin=margin,
            player_rounds_won=player_rounds_won,
            opponent_rounds_won=opponent_rounds_won,
            even_rounds=even_rounds,
            projected_winner=projected_winner,
            projected_margin=round(projected_margin, 1),
            strategy=strategy,
        )

    # ------------------------------------------------------------------
    # Round banking strategy
    # ------------------------------------------------------------------

    def round_banking_strategy(
        self,
        round_scores: list[RoundScore],
        total_rounds: int = 12,
        player_stamina_pct: float = 1.0,
        opponent_hurt: bool = False,
    ) -> RoundBankStrategy:
        """Decide whether to bank rounds (coast) or push for a finish.

        Evaluates scorecard position, stamina, and opponent condition
        to recommend the optimal approach.
        """
        margin = sum(r.player_score - r.opponent_score for r in round_scores)
        rounds_remaining = total_rounds - len(round_scores)

        should_bank = False
        should_push = False
        reasoning: list[str] = []

        if margin >= 3 and rounds_remaining <= 4:
            should_bank = True
            reasoning.append("Comfortable lead with few rounds left — bank rounds and coast.")
            reasoning.append("Use the jab, move, and avoid exchanges.")
        elif margin >= 2 and player_stamina_pct < 0.4:
            should_bank = True
            reasoning.append("Ahead but low on stamina — conserve energy and survive.")
        elif opponent_hurt and margin >= 0:
            should_push = True
            reasoning.append("Opponent is hurt — push for the finish NOW.")
            reasoning.append("Double up on body work, then go upstairs with power.")
        elif margin <= -3:
            should_push = True
            reasoning.append("Behind on the cards — you need a knockdown or finish.")
            reasoning.append("Increase aggression, go for broke.")
        else:
            reasoning.append("Fight is competitive — win each round on its merits.")
            reasoning.append("Stay active, land clean, and control the ring.")

        return RoundBankStrategy(
            current_margin=margin,
            rounds_remaining=rounds_remaining,
            should_bank=should_bank,
            should_push=should_push,
            stamina_pct=player_stamina_pct,
            reasoning=reasoning,
        )

    # ------------------------------------------------------------------
    # Body work ROI
    # ------------------------------------------------------------------

    def calculate_body_work_roi(
        self,
        body_punches_landed: int,
        body_punches_per_round: float,
        current_round: int,
        total_rounds: int = 12,
    ) -> BodyWorkROI:
        """Calculate the return on investment of body work over the fight.

        Models the accumulating damage effect of body shots and projects
        when the investment starts paying dividends.
        """
        # Current accumulated damage effect
        accumulated_effect = 0.0
        for threshold_round, effect in _BODY_DAMAGE_CURVE:
            if current_round >= threshold_round:
                accumulated_effect = effect

        # Stamina impact (each body shot drains ~0.5% of opponent stamina)
        stamina_drain = body_punches_landed * 0.005
        stamina_drain_pct = min(0.50, stamina_drain)

        # Projected total body shots
        rounds_remaining = total_rounds - current_round
        projected_total = body_punches_landed + (body_punches_per_round * rounds_remaining)

        # Payoff round: when accumulated effect exceeds 0.5 (significant)
        payoff_round = 12
        for threshold_round, effect in _BODY_DAMAGE_CURVE:
            if effect >= 0.50:
                payoff_round = threshold_round
                break

        roi_assessment = "low"
        if accumulated_effect >= 0.5:
            roi_assessment = "paying_off"
        elif current_round >= payoff_round - 2 and body_punches_per_round >= 3:
            roi_assessment = "approaching_payoff"
        elif body_punches_per_round < 1.5:
            roi_assessment = "insufficient_investment"

        notes: list[str] = []
        if roi_assessment == "paying_off":
            notes.append("Body work is paying off — opponent should be slowing down.")
            notes.append("Mix in head shots now. They will drop their guard to protect the body.")
        elif roi_assessment == "approaching_payoff":
            notes.append(f"Keep investing in body work — payoff expected around round {payoff_round}.")
        elif roi_assessment == "insufficient_investment":
            notes.append("Not enough body work. Target 3-5 body shots per round for meaningful impact.")
        else:
            notes.append("Body work investment is building. Continue the investment.")

        return BodyWorkROI(
            body_punches_landed=body_punches_landed,
            body_per_round=round(body_punches_per_round, 1),
            accumulated_effect=round(accumulated_effect, 3),
            stamina_drain_pct=round(stamina_drain_pct, 3),
            projected_total_body=round(projected_total, 0),
            payoff_round=payoff_round,
            roi_assessment=roi_assessment,
            current_round=current_round,
            notes=notes,
        )

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _compute_round_points(stats: dict[str, Any]) -> float:
        punches_landed = stats.get("punches_landed", 0)
        punches_thrown = stats.get("punches_thrown", 1)
        power_landed = stats.get("power_landed", 0)
        ring_control = stats.get("ring_control", 0.5)
        defense = stats.get("defense_rating", 0.5)

        accuracy = punches_landed / max(punches_thrown, 1)
        clean_punch_score = (punches_landed * 0.3 + power_landed * 0.7) * _SCORING_WEIGHTS["clean_punches_landed"]
        aggression_score = (punches_thrown * 0.01 + accuracy * 5) * _SCORING_WEIGHTS["effective_aggression"]
        generalship_score = ring_control * 10 * _SCORING_WEIGHTS["ring_generalship"]
        defense_score = defense * 10 * _SCORING_WEIGHTS["defense"]

        return clean_punch_score + aggression_score + generalship_score + defense_score


# Module-level singleton
judge_mind = JudgeMind()
