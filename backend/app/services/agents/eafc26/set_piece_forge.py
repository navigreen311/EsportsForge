"""SetPieceForge — corner routine builder, free kick optimizer, penalty pressure trainer.

Provides AI-driven set piece routines with optimized player positioning,
delivery analysis, and penalty shootout psychology modeling.
"""

from __future__ import annotations

import logging
import random
from typing import Any

from app.schemas.eafc26.tactics import (
    CornerRoutine,
    DeliveryType,
    FreeKickSetup,
    PenaltyAnalysis,
    PenaltyDirection,
    SetPieceReport,
)

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Corner routine library
# ---------------------------------------------------------------------------

_CORNER_ROUTINES: list[dict[str, Any]] = [
    {
        "name": "Near Post Flick",
        "delivery": "inswinger",
        "target_zone": "near_post",
        "runners": ["ST near post", "CB far post", "CM edge of box"],
        "success_rate": 0.12,
        "description": (
            "Inswinging delivery to the near post. Tallest attacker attacks "
            "the near post for a flick-on to the far post runner."
        ),
        "counter_tip": "Defender must mark the near post tightly.",
    },
    {
        "name": "Far Post Lob",
        "delivery": "outswinger",
        "target_zone": "far_post",
        "runners": ["CB far post", "ST six-yard box", "CM penalty spot"],
        "success_rate": 0.09,
        "description": (
            "Outswinging delivery to the far post. Tall CB attacks the space "
            "behind the defense for a header."
        ),
        "counter_tip": "Move GK to the far post and man-mark the tallest attacker.",
    },
    {
        "name": "Short Corner Pull-Back",
        "delivery": "short",
        "target_zone": "edge_of_box",
        "runners": ["LW short option", "CAM edge of box", "CM recycler"],
        "success_rate": 0.07,
        "description": (
            "Short corner to the wing player who plays it back to the edge "
            "of the box. CAM arrives late for a low driven shot."
        ),
        "counter_tip": "Press the short option immediately.",
    },
    {
        "name": "Train Routine",
        "delivery": "inswinger",
        "target_zone": "six_yard_box",
        "runners": ["CB lead runner", "ST follow runner", "CDM decoy"],
        "success_rate": 0.14,
        "description": (
            "Two players run in a line toward the six-yard box. The lead runner "
            "is a decoy who drags the marker, creating space for the follower."
        ),
        "counter_tip": "Switch to zonal marking to cover the area, not the runners.",
    },
]

# ---------------------------------------------------------------------------
# Free kick reference data
# ---------------------------------------------------------------------------

_FK_POWER_CURVES: dict[str, dict[str, Any]] = {
    "close": {  # 18-22 yards
        "range_yards": "18-22",
        "optimal_power": 2.5,
        "curve_amount": "high",
        "aim_offset": "1.5 bars above wall",
        "success_rate": 0.18,
        "technique": "Driven free kick with heavy curl around the wall",
    },
    "medium": {  # 23-28 yards
        "range_yards": "23-28",
        "optimal_power": 3.0,
        "curve_amount": "medium",
        "aim_offset": "1 bar above wall",
        "success_rate": 0.12,
        "technique": "Standard curling free kick, aim for the top corner",
    },
    "long": {  # 29-35 yards
        "range_yards": "29-35",
        "optimal_power": 3.5,
        "curve_amount": "low",
        "aim_offset": "0.5 bars above wall",
        "success_rate": 0.06,
        "technique": "Knuckleball or dipping shot — power over finesse",
    },
}

# ---------------------------------------------------------------------------
# Penalty psychology model
# ---------------------------------------------------------------------------

_DIRECTION_PROBS: dict[PenaltyDirection, float] = {
    PenaltyDirection.LEFT_LOW: 0.18,
    PenaltyDirection.LEFT_MID: 0.12,
    PenaltyDirection.LEFT_HIGH: 0.05,
    PenaltyDirection.CENTER_LOW: 0.08,
    PenaltyDirection.CENTER_MID: 0.10,
    PenaltyDirection.CENTER_HIGH: 0.02,
    PenaltyDirection.RIGHT_LOW: 0.20,
    PenaltyDirection.RIGHT_MID: 0.13,
    PenaltyDirection.RIGHT_HIGH: 0.04,
}

# GK save probability per direction
_GK_SAVE_PROBS: dict[PenaltyDirection, float] = {
    PenaltyDirection.LEFT_LOW: 0.25,
    PenaltyDirection.LEFT_MID: 0.30,
    PenaltyDirection.LEFT_HIGH: 0.10,
    PenaltyDirection.CENTER_LOW: 0.45,
    PenaltyDirection.CENTER_MID: 0.50,
    PenaltyDirection.CENTER_HIGH: 0.05,
    PenaltyDirection.RIGHT_LOW: 0.25,
    PenaltyDirection.RIGHT_MID: 0.30,
    PenaltyDirection.RIGHT_HIGH: 0.10,
}

_PRESSURE_MULTIPLIER: dict[str, float] = {
    "low": 1.0,
    "medium": 0.92,
    "high": 0.82,
    "shootout_decisive": 0.70,
}


class SetPieceForge:
    """EA FC 26 set piece optimization engine.

    Builds corner routines, optimizes free kick technique, and models
    penalty shootout psychology under pressure.
    """

    # ------------------------------------------------------------------
    # Corner routine builder
    # ------------------------------------------------------------------

    def build_corner_routine(
        self,
        tallest_attacker: str = "CB",
        preferred_delivery: str = "inswinger",
        opponent_marking: str = "man",
    ) -> CornerRoutine:
        """Build the optimal corner routine given squad and opponent context.

        Considers the tallest attacker, delivery preference, and opponent
        marking type to recommend the best routine.
        """
        # Filter routines by delivery preference
        candidates = [
            r for r in _CORNER_ROUTINES
            if r["delivery"] == preferred_delivery
        ]
        if not candidates:
            candidates = list(_CORNER_ROUTINES)

        # Boost routines that exploit marking type
        scored: list[tuple[dict, float]] = []
        for routine in candidates:
            score = routine["success_rate"]
            if opponent_marking == "man" and "decoy" in routine.get("description", "").lower():
                score *= 1.4  # decoy runs exploit man marking
            if opponent_marking == "zonal" and routine["target_zone"] == "six_yard_box":
                score *= 0.7  # zonal covers the box well
            if opponent_marking == "zonal" and routine["target_zone"] == "edge_of_box":
                score *= 1.3  # edge of box attacks gaps in zones
            scored.append((routine, score))

        scored.sort(key=lambda x: x[1], reverse=True)
        best = scored[0][0]

        delivery = DeliveryType.INSWINGER
        if best["delivery"] == "outswinger":
            delivery = DeliveryType.OUTSWINGER
        elif best["delivery"] == "short":
            delivery = DeliveryType.SHORT
        elif best["delivery"] == "driven":
            delivery = DeliveryType.DRIVEN

        return CornerRoutine(
            name=best["name"],
            delivery=delivery,
            target_zone=best["target_zone"],
            runners=best["runners"],
            success_rate=best["success_rate"],
            description=best["description"],
            counter_tip=best["counter_tip"],
            opponent_marking=opponent_marking,
        )

    def list_corner_routines(self) -> list[CornerRoutine]:
        """Return all available corner routines."""
        routines: list[CornerRoutine] = []
        for r in _CORNER_ROUTINES:
            delivery = {"inswinger": DeliveryType.INSWINGER, "outswinger": DeliveryType.OUTSWINGER,
                        "short": DeliveryType.SHORT, "driven": DeliveryType.DRIVEN}
            routines.append(CornerRoutine(
                name=r["name"],
                delivery=delivery.get(r["delivery"], DeliveryType.INSWINGER),
                target_zone=r["target_zone"],
                runners=r["runners"],
                success_rate=r["success_rate"],
                description=r["description"],
                counter_tip=r["counter_tip"],
            ))
        return routines

    # ------------------------------------------------------------------
    # Free kick optimizer
    # ------------------------------------------------------------------

    def optimize_free_kick(
        self,
        distance_yards: float,
        free_kick_accuracy: int = 80,
        curve_stat: int = 80,
        wall_size: int = 4,
    ) -> FreeKickSetup:
        """Generate optimal free kick technique for the given distance and player stats.

        Factors in distance, player accuracy/curve attributes, and wall configuration.
        """
        if distance_yards <= 22:
            zone = "close"
        elif distance_yards <= 28:
            zone = "medium"
        else:
            zone = "long"

        fk_data = _FK_POWER_CURVES[zone]

        # Adjust success rate based on player stats
        stat_factor = ((free_kick_accuracy + curve_stat) / 2) / 85.0
        adjusted_success = min(0.35, fk_data["success_rate"] * stat_factor)

        # Wall adjustment
        if wall_size >= 5:
            adjusted_success *= 0.85
        elif wall_size <= 3:
            adjusted_success *= 1.15

        technique = fk_data["technique"]
        if curve_stat >= 88 and zone in ("close", "medium"):
            technique = "Power curve — use the curl stat advantage to bend it around the wall"
            adjusted_success *= 1.1

        return FreeKickSetup(
            distance_yards=distance_yards,
            zone=zone,
            optimal_power=fk_data["optimal_power"],
            curve_amount=fk_data["curve_amount"],
            aim_offset=fk_data["aim_offset"],
            technique=technique,
            success_rate=round(min(adjusted_success, 0.35), 3),
            wall_size=wall_size,
            tip=(
                f"From {distance_yards:.0f} yards: {fk_data['aim_offset']} aim, "
                f"power bar to {fk_data['optimal_power']}. "
                f"{'Add curl for extra bend.' if curve_stat >= 85 else 'Focus on power and placement.'}"
            ),
        )

    # ------------------------------------------------------------------
    # Penalty pressure trainer
    # ------------------------------------------------------------------

    def analyze_penalty(
        self,
        taker_composure: int = 80,
        pressure_level: str = "medium",
        opponent_gk_tendency: str | None = None,
        penalty_number: int = 1,
    ) -> PenaltyAnalysis:
        """Analyze the optimal penalty direction under pressure.

        Models the taker's composure, situation pressure, and GK tendencies
        to recommend the highest-EV direction.
        """
        pressure_mult = _PRESSURE_MULTIPLIER.get(pressure_level, 0.92)
        composure_factor = taker_composure / 85.0

        # Compute EV for each direction
        ev_by_direction: dict[PenaltyDirection, float] = {}
        for direction, base_prob in _DIRECTION_PROBS.items():
            save_prob = _GK_SAVE_PROBS[direction]

            # Adjust for GK tendency
            if opponent_gk_tendency == "dive_left" and "LEFT" in direction.value.upper():
                save_prob = min(0.8, save_prob * 1.5)
            elif opponent_gk_tendency == "dive_right" and "RIGHT" in direction.value.upper():
                save_prob = min(0.8, save_prob * 1.5)
            elif opponent_gk_tendency == "stay_center" and "CENTER" in direction.value.upper():
                save_prob = min(0.8, save_prob * 1.5)

            # Scoring probability = (1 - save_prob) * composure * pressure
            score_prob = (1 - save_prob) * composure_factor * pressure_mult

            # Penalize high shots under pressure
            if "HIGH" in direction.value.upper() and pressure_level in ("high", "shootout_decisive"):
                score_prob *= 0.70

            ev_by_direction[direction] = round(score_prob, 3)

        # Sort by EV
        sorted_dirs = sorted(ev_by_direction.items(), key=lambda x: x[1], reverse=True)
        best = sorted_dirs[0]
        second = sorted_dirs[1]

        # Build advice
        advice: list[str] = []
        if pressure_level in ("high", "shootout_decisive"):
            advice.append("High pressure — go low and hard. Avoid ambitious top-corner attempts.")
        if opponent_gk_tendency:
            advice.append(f"GK tends to {opponent_gk_tendency} — aim to the opposite side.")
        if taker_composure < 70:
            advice.append("Low composure player — use the stutter run-up to settle nerves.")
        if penalty_number >= 4:
            advice.append("Late in the shootout — GK may gamble. Consider a Panenka if composure is high.")

        return PenaltyAnalysis(
            recommended_direction=best[0],
            score_probability=best[1],
            alternative_direction=second[0],
            alternative_probability=second[1],
            ev_by_direction=ev_by_direction,
            pressure_level=pressure_level,
            composure_factor=round(composure_factor, 3),
            advice=advice,
        )

    # ------------------------------------------------------------------
    # Full set piece report
    # ------------------------------------------------------------------

    def generate_report(
        self,
        tallest_attacker: str = "CB",
        free_kick_accuracy: int = 80,
        curve_stat: int = 80,
        taker_composure: int = 80,
    ) -> SetPieceReport:
        """Generate a comprehensive set piece report covering corners, FKs, and penalties."""
        corner = self.build_corner_routine(tallest_attacker=tallest_attacker)
        fk_close = self.optimize_free_kick(20, free_kick_accuracy, curve_stat)
        fk_medium = self.optimize_free_kick(25, free_kick_accuracy, curve_stat)
        penalty = self.analyze_penalty(taker_composure)

        return SetPieceReport(
            corner_routine=corner,
            free_kick_close=fk_close,
            free_kick_medium=fk_medium,
            penalty_analysis=penalty,
            overall_set_piece_rating=self._compute_set_piece_rating(
                free_kick_accuracy, curve_stat, taker_composure,
            ),
        )

    @staticmethod
    def _compute_set_piece_rating(fk_acc: int, curve: int, composure: int) -> str:
        avg = (fk_acc + curve + composure) / 3
        if avg >= 88:
            return "Elite"
        if avg >= 80:
            return "Strong"
        if avg >= 70:
            return "Average"
        return "Below Average"


# Module-level singleton
set_piece_forge = SetPieceForge()
