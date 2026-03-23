"""RoundScore AI — judge-aware round management, round-start scripts, finish protocols.

Models the 10-point-must scoring system, tracks scorecard state across rounds,
generates opening scripts, and determines when to activate finish protocols.
"""

from __future__ import annotations

import logging
from typing import Any

from app.schemas.ufc5.combat import (
    BodyRegion,
    DamageState,
    FinishProtocol,
    JudgeCriteria,
    RoundPlan,
    RoundScore,
    StaminaEconomy,
    StrikeType,
    SubmissionChain,
)

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

# Criteria weights for scoring a round (UFC unified rules priority)
_CRITERIA_WEIGHTS: dict[JudgeCriteria, float] = {
    JudgeCriteria.EFFECTIVE_STRIKING: 0.40,
    JudgeCriteria.EFFECTIVE_GRAPPLING: 0.30,
    JudgeCriteria.AGGRESSION: 0.15,
    JudgeCriteria.OCTAGON_CONTROL: 0.15,
}


class RoundScoreAI:
    """Judge-aware round management engine.

    Tracks cumulative scorecard, generates round-start scripts,
    and triggers finish protocols when conditions are met.
    """

    def __init__(self, total_rounds: int = 3) -> None:
        self._total_rounds = total_rounds
        self._scorecards: list[RoundScore] = []

    def reset(self, total_rounds: int = 3) -> None:
        """Reset for a new fight."""
        self._total_rounds = total_rounds
        self._scorecards = []

    @property
    def scorecards(self) -> list[RoundScore]:
        return list(self._scorecards)

    def score_round(
        self,
        round_number: int,
        sig_strikes_landed: int,
        sig_strikes_absorbed: int,
        takedowns_landed: int = 0,
        takedowns_defended: int = 0,
        control_time: float = 0.0,
        knockdowns_scored: int = 0,
        knockdowns_received: int = 0,
    ) -> RoundScore:
        """
        Score a completed round using 10-point-must system.

        Evaluates all four judging criteria and assigns a score.
        """
        criteria_scores = self._evaluate_criteria(
            sig_strikes_landed=sig_strikes_landed,
            sig_strikes_absorbed=sig_strikes_absorbed,
            takedowns_landed=takedowns_landed,
            control_time=control_time,
            knockdowns_scored=knockdowns_scored,
            knockdowns_received=knockdowns_received,
        )

        # Aggregate weighted score
        weighted = sum(
            criteria_scores[c] * _CRITERIA_WEIGHTS[c] for c in JudgeCriteria
        )

        # Convert to 10-point scale
        player_score, opponent_score = self._to_ten_point(
            weighted, knockdowns_scored, knockdowns_received
        )

        dominant = [c for c, s in criteria_scores.items() if s > 0.55]
        confidence = min(1.0, abs(weighted - 0.5) * 4)
        is_swing = confidence < 0.3

        score = RoundScore(
            round_number=round_number,
            player_score=player_score,
            opponent_score=opponent_score,
            significant_strikes_landed=sig_strikes_landed,
            significant_strikes_absorbed=sig_strikes_absorbed,
            takedowns_landed=takedowns_landed,
            takedowns_defended=takedowns_defended,
            control_time_seconds=control_time,
            knockdowns_scored=knockdowns_scored,
            knockdowns_received=knockdowns_received,
            dominant_criteria=dominant,
            confidence=round(confidence, 2),
            swing_round=is_swing,
        )
        self._scorecards.append(score)
        return score

    def get_scorecard_state(self) -> dict[str, Any]:
        """Return current aggregate scorecard state."""
        player_total = sum(s.player_score for s in self._scorecards)
        opponent_total = sum(s.opponent_score for s in self._scorecards)
        rounds_completed = len(self._scorecards)
        rounds_remaining = self._total_rounds - rounds_completed

        if player_total > opponent_total:
            status = "ahead"
        elif player_total < opponent_total:
            status = "behind"
        else:
            status = "even"

        swing_rounds = [s.round_number for s in self._scorecards if s.swing_round]

        return {
            "player_total": player_total,
            "opponent_total": opponent_total,
            "rounds_completed": rounds_completed,
            "rounds_remaining": rounds_remaining,
            "status": status,
            "margin": player_total - opponent_total,
            "swing_rounds": swing_rounds,
            "needs_finish": status == "behind" and rounds_remaining <= 1,
        }

    def generate_round_plan(
        self,
        round_number: int,
        damage_state: DamageState | None = None,
        stamina_economy: StaminaEconomy | None = None,
    ) -> RoundPlan:
        """
        Generate a tactical plan for the upcoming round.

        Considers scorecard state, damage accumulation, and stamina levels.
        """
        scorecard = self.get_scorecard_state()
        status = scorecard["status"]
        rounds_left = scorecard["rounds_remaining"]

        # Determine pace based on scorecard + stamina
        pace = self._determine_pace(status, rounds_left, stamina_economy)

        # Determine target region
        target = self._determine_target(damage_state)

        # Should we pursue a finish?
        finish_attempt = self._should_pursue_finish(
            status, rounds_left, damage_state, stamina_economy
        )

        # Opening script
        opener = self._build_opening_script(
            round_number, status, pace, target, damage_state
        )

        # Adjustments from previous rounds
        adjustments = self._build_adjustments(round_number)

        return RoundPlan(
            round_number=round_number,
            opening_sequence=opener,
            target_region=target,
            pace=pace,
            finish_attempt=finish_attempt,
            scorecard_status=f"{status} by {abs(scorecard['margin'])}",
            adjustments=adjustments,
        )

    def build_finish_protocol(
        self,
        damage_state: DamageState | None = None,
        stamina_economy: StaminaEconomy | None = None,
        submission_chain: SubmissionChain | None = None,
    ) -> FinishProtocol:
        """Build a finish protocol based on current fight state."""
        triggers: list[str] = []
        method = "TKO"
        strikes: list[StrikeType] = []
        abort: list[str] = []
        stamina_req = 40.0

        # Determine finish method based on state
        if damage_state and damage_state.is_rocked:
            triggers.append("Opponent is rocked")
            method = "TKO"
            strikes = [
                StrikeType.HOOK, StrikeType.HOOK,
                StrikeType.UPPERCUT, StrikeType.OVERHAND,
            ]
        elif damage_state and damage_state.knockout_vulnerability > 0.6:
            triggers.append("Opponent KO vulnerability above 60%")
            method = "KO"
            strikes = [StrikeType.OVERHAND, StrikeType.HOOK, StrikeType.UPPERCUT]
        elif (
            submission_chain
            and stamina_economy
            and stamina_economy.opponent_stamina_estimate < 40
        ):
            triggers.append("Opponent stamina below 40%")
            method = "SUB"
        else:
            triggers.append("Scorecard requires finish to win")
            method = "TKO"
            strikes = [
                StrikeType.JAB, StrikeType.CROSS,
                StrikeType.HOOK, StrikeType.BODY_HOOK,
            ]

        abort = [
            "Player stamina drops below 20%",
            "Opponent recovers full composure",
            "Getting countered cleanly",
        ]

        if stamina_economy:
            stamina_req = max(20.0, stamina_economy.current_stamina * 0.5)

        return FinishProtocol(
            trigger_conditions=triggers,
            method=method,
            strike_sequence=strikes,
            submission_chain=submission_chain,
            stamina_required=round(stamina_req, 1),
            abort_conditions=abort,
        )

    # --- private helpers ---

    def _evaluate_criteria(
        self,
        sig_strikes_landed: int,
        sig_strikes_absorbed: int,
        takedowns_landed: int,
        control_time: float,
        knockdowns_scored: int,
        knockdowns_received: int,
    ) -> dict[JudgeCriteria, float]:
        """Return 0-1 score for each criteria (>0.5 = player winning)."""
        total_strikes = sig_strikes_landed + sig_strikes_absorbed
        striking = (
            sig_strikes_landed / max(total_strikes, 1)
            + (knockdowns_scored - knockdowns_received) * 0.15
        )
        striking = max(0.0, min(1.0, striking))

        grappling = min(1.0, takedowns_landed * 0.15 + control_time / 180.0)

        # Aggression approximated by volume
        aggression = min(
            1.0, sig_strikes_landed / max(sig_strikes_landed + 10, 1)
        )

        # Control approximated by takedowns + control time
        control = min(
            1.0, (takedowns_landed * 0.1 + control_time / 300.0)
        )

        return {
            JudgeCriteria.EFFECTIVE_STRIKING: round(striking, 2),
            JudgeCriteria.EFFECTIVE_GRAPPLING: round(grappling, 2),
            JudgeCriteria.AGGRESSION: round(aggression, 2),
            JudgeCriteria.OCTAGON_CONTROL: round(control, 2),
        }

    def _to_ten_point(
        self,
        weighted: float,
        kd_scored: int,
        kd_received: int,
    ) -> tuple[int, int]:
        """Convert weighted score to 10-point-must."""
        kd_delta = kd_scored - kd_received

        if weighted > 0.65 or kd_delta >= 2:
            return 10, 8  # 10-8 round
        elif weighted > 0.5:
            return 10, 9
        elif weighted > 0.45:
            return 9, 9  # swing round scored even (rare but possible)
        elif kd_delta <= -2:
            return 8, 10
        else:
            return 9, 10

    def _determine_pace(
        self,
        status: str,
        rounds_left: int,
        stamina: StaminaEconomy | None,
    ) -> str:
        if status == "behind" and rounds_left <= 1:
            return "blitz"
        if status == "ahead" and rounds_left <= 1:
            return "coast"
        if stamina and stamina.current_stamina < 35:
            return "survive"
        if status == "behind":
            return "steady"
        return "steady"

    def _determine_target(self, damage: DamageState | None) -> BodyRegion:
        if not damage:
            return BodyRegion.HEAD
        # Target the most damaged region
        regions = {
            BodyRegion.HEAD: damage.head_damage,
            BodyRegion.BODY: damage.body_damage,
            BodyRegion.LEFT_LEG: damage.left_leg_damage,
            BodyRegion.RIGHT_LEG: damage.right_leg_damage,
        }
        return max(regions, key=regions.get)  # type: ignore[arg-type]

    def _should_pursue_finish(
        self,
        status: str,
        rounds_left: int,
        damage: DamageState | None,
        stamina: StaminaEconomy | None,
    ) -> bool:
        if damage and damage.is_rocked:
            return True
        if damage and damage.knockout_vulnerability > 0.6:
            return True
        if status == "behind" and rounds_left <= 1:
            return True
        if stamina and stamina.opponent_stamina_estimate < 25:
            return True
        return False

    def _build_opening_script(
        self,
        round_number: int,
        status: str,
        pace: str,
        target: BodyRegion,
        damage: DamageState | None,
    ) -> list[str]:
        script: list[str] = []

        if round_number == 1:
            script.append("Establish jab range — measure distance")
            script.append("Throw 2-3 leg kicks to test reaction")
            script.append("Feint to read opponent's defensive habits")
        elif pace == "blitz":
            script.append("Immediately pressure forward")
            script.append("Throw high-volume combinations")
            script.append("Do not let opponent breathe")
        elif pace == "coast":
            script.append("Circle and use footwork")
            script.append("Jab and move, avoid exchanges")
            script.append("Win on points — don't take risks")
        else:
            script.append(f"Target {target.value} early to build on prior damage")
            script.append("Establish rhythm with 1-2 combinations")

        if damage and damage.cut_severity.value not in ("none", "minor"):
            script.append("Target the existing cut with elbows")

        return script

    def _build_adjustments(self, round_number: int) -> list[str]:
        if round_number <= 1 or not self._scorecards:
            return []

        last = self._scorecards[-1]
        adjustments: list[str] = []

        if last.significant_strikes_absorbed > last.significant_strikes_landed:
            adjustments.append("Getting out-struck — increase head movement")
        if last.takedowns_landed == 0 and last.takedowns_defended == 0:
            adjustments.append("Consider mixing in takedowns for octagon control")
        if last.knockdowns_received > 0:
            adjustments.append("Got dropped last round — be more defensive early")
        if last.control_time_seconds > 60 and last.opponent_score >= last.player_score:
            adjustments.append("Being controlled too long — prioritize get-ups")
        if last.swing_round:
            adjustments.append("Last round was close — need a clear statement round")

        return adjustments
