"""BaserunningAI — stolen base probability, go/hold/tag decisions for MLB The Show 26.

Models stolen base success probability, provides real-time go/hold/tag
decisions, and evaluates baserunning aggression settings.
"""

from __future__ import annotations

import logging
from typing import Any

from app.schemas.mlb26.hitting import (
    BaserunningDecision,
    DecisionType,
    StolenBaseAnalysis,
    TagUpAnalysis,
)

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Stolen base model constants
# ---------------------------------------------------------------------------

_BASE_STEAL_SUCCESS: dict[str, float] = {
    "second": 0.72,
    "third": 0.65,
    "home": 0.40,
}

# Speed thresholds (in-game speed attribute)
_SPEED_MODIFIERS: list[tuple[int, float]] = [
    (95, 0.20),   # elite speed bonus
    (85, 0.12),
    (75, 0.05),
    (65, 0.0),
    (55, -0.08),
    (0, -0.18),
]

# Catcher arm strength modifiers
_CATCHER_ARM_MODIFIERS: list[tuple[int, float]] = [
    (95, -0.18),
    (85, -0.12),
    (75, -0.05),
    (65, 0.0),
    (55, 0.08),
    (0, 0.15),
]

# Pitcher slide step / pickoff modifiers
_PITCHER_HOLD_MODIFIERS: dict[str, float] = {
    "quick": -0.10,
    "average": 0.0,
    "slow": 0.12,
}

# Tag-up decision model
_TAG_OUTFIELD_DEPTH: dict[str, float] = {
    "shallow": 0.30,  # low chance of scoring
    "medium": 0.60,
    "deep": 0.82,
    "warning_track": 0.90,
}

_TAG_ARM_MODIFIERS: dict[str, float] = {
    "cannon": -0.20,
    "strong": -0.10,
    "average": 0.0,
    "weak": 0.12,
}


class BaserunningAI:
    """MLB The Show 26 baserunning decision engine.

    Calculates stolen base probabilities, provides go/hold/tag decisions,
    and evaluates baserunning risk/reward.
    """

    # ------------------------------------------------------------------
    # Stolen base probability
    # ------------------------------------------------------------------

    def calculate_steal_probability(
        self,
        target_base: str = "second",
        runner_speed: int = 75,
        runner_steal: int = 70,
        catcher_arm: int = 75,
        pitcher_hold: str = "average",
        lead_size: str = "normal",
        count: str = "1-1",
    ) -> StolenBaseAnalysis:
        """Calculate the probability of a successful stolen base attempt.

        Factors in runner speed/steal ratings, catcher arm, pitcher hold time,
        lead size, and count leverage.
        """
        base_prob = _BASE_STEAL_SUCCESS.get(target_base, 0.65)

        # Speed modifier
        speed_mod = 0.0
        for threshold, mod in _SPEED_MODIFIERS:
            if runner_speed >= threshold:
                speed_mod = mod
                break

        # Steal attribute factor
        steal_factor = (runner_steal - 65) * 0.003

        # Catcher arm
        arm_mod = 0.0
        for threshold, mod in _CATCHER_ARM_MODIFIERS:
            if catcher_arm >= threshold:
                arm_mod = mod
                break

        # Pitcher hold
        hold_mod = _PITCHER_HOLD_MODIFIERS.get(pitcher_hold, 0.0)

        # Lead size
        lead_mod = {"short": -0.06, "normal": 0.0, "aggressive": 0.08}.get(lead_size, 0.0)

        # Count leverage — breaking ball counts are better steal counts
        count_mod = 0.0
        if count in ("1-0", "2-0", "3-1", "1-1"):
            count_mod = 0.04  # Pitcher more likely to throw offspeed
        elif count in ("0-2", "1-2"):
            count_mod = -0.03  # Pitcher may pitchout or fastball

        total_prob = base_prob + speed_mod + steal_factor + arm_mod + hold_mod + lead_mod + count_mod
        total_prob = max(0.05, min(0.98, total_prob))

        # Decision
        if total_prob >= 0.75:
            decision = "green_light"
            advice = "High probability steal — send the runner."
        elif total_prob >= 0.60:
            decision = "situational"
            advice = "Decent odds — steal in favorable counts or when you need the base."
        else:
            decision = "hold"
            advice = "Low success probability — hold the runner."

        factors: list[str] = []
        if speed_mod >= 0.12:
            factors.append(f"Elite speed ({runner_speed}) gives a significant advantage.")
        if arm_mod <= -0.12:
            factors.append(f"Catcher arm ({catcher_arm}) is a major deterrent.")
        if hold_mod >= 0.10:
            factors.append("Pitcher is slow to home — exploit the timing.")
        if count_mod > 0:
            factors.append(f"Count {count} favors a steal attempt.")

        return StolenBaseAnalysis(
            target_base=target_base,
            success_probability=round(total_prob, 3),
            decision=decision,
            advice=advice,
            factors=factors,
            runner_speed=runner_speed,
            catcher_arm=catcher_arm,
        )

    # ------------------------------------------------------------------
    # Go / Hold decision
    # ------------------------------------------------------------------

    def go_or_hold(
        self,
        runner_speed: int,
        ball_location: str = "outfield",
        fielder_arm: str = "average",
        outs: int = 1,
        run_value: str = "tying",
        base_from: str = "second",
    ) -> BaserunningDecision:
        """Decide whether to send a runner or hold based on ball in play context.

        Evaluates the ball location, fielder arm, game situation, and outs
        to make a go/hold recommendation.
        """
        # Base probability from ball location
        loc_probs: dict[str, float] = {
            "infield_left": 0.15,
            "infield_right": 0.20,
            "infield_middle": 0.10,
            "outfield_left": 0.65,
            "outfield_center": 0.55,
            "outfield_right": 0.70,
            "outfield": 0.60,
            "gap": 0.85,
            "wall": 0.92,
        }
        base_prob = loc_probs.get(ball_location, 0.50)

        # Arm adjustment
        arm_adj = _TAG_ARM_MODIFIERS.get(fielder_arm, 0.0)
        base_prob += arm_adj

        # Speed adjustment
        speed_adj = (runner_speed - 70) * 0.004
        base_prob += speed_adj

        # Outs adjustment — more conservative with 0 outs
        if outs == 0:
            base_prob -= 0.08
        elif outs == 2:
            base_prob += 0.05

        # Run value adjustment
        if run_value == "go_ahead":
            base_prob -= 0.05  # Be conservative with go-ahead run
        elif run_value == "insurance":
            base_prob += 0.05  # Can afford risk with insurance run

        base_prob = max(0.05, min(0.98, base_prob))

        if base_prob >= 0.65:
            decision = DecisionType.GO
            advice = "Send the runner — high probability of scoring."
        elif base_prob >= 0.45:
            decision = DecisionType.HOLD
            advice = "Hold — too risky given the situation."
        else:
            decision = DecisionType.HOLD
            advice = "Definitely hold — the throw will beat the runner."

        return BaserunningDecision(
            decision=decision,
            success_probability=round(base_prob, 3),
            advice=advice,
            base_from=base_from,
            outs=outs,
            run_value=run_value,
        )

    # ------------------------------------------------------------------
    # Tag up decision
    # ------------------------------------------------------------------

    def tag_up_decision(
        self,
        runner_speed: int,
        outfield_depth: str = "medium",
        fielder_arm: str = "average",
        outs: int = 0,
        base_from: str = "third",
    ) -> TagUpAnalysis:
        """Decide whether to tag up on a fly ball.

        Models the outfield depth, arm strength, runner speed, and
        out situation to recommend tag or stay.
        """
        base_prob = _TAG_OUTFIELD_DEPTH.get(outfield_depth, 0.60)
        arm_adj = _TAG_ARM_MODIFIERS.get(fielder_arm, 0.0)
        speed_adj = (runner_speed - 70) * 0.004

        total_prob = base_prob + arm_adj + speed_adj
        total_prob = max(0.05, min(0.98, total_prob))

        # Tagging from second to third is less valuable than third to home
        if base_from == "second":
            # Lower the threshold — need higher probability for the risk
            threshold = 0.70
        else:
            threshold = 0.55

        should_tag = total_prob >= threshold

        notes: list[str] = []
        if outfield_depth == "deep" or outfield_depth == "warning_track":
            notes.append("Deep fly — good tagging opportunity.")
        if fielder_arm == "cannon":
            notes.append("Elite arm — be cautious on the tag.")
        if outs == 2:
            notes.append("Two outs — runner should be going on contact anyway.")
            should_tag = True  # Always tag with 2 outs on a catch

        return TagUpAnalysis(
            should_tag=should_tag,
            success_probability=round(total_prob, 3),
            outfield_depth=outfield_depth,
            fielder_arm=fielder_arm,
            runner_speed=runner_speed,
            base_from=base_from,
            notes=notes,
        )


# Module-level singleton
baserunning_ai = BaserunningAI()
