"""ComboEV — expected value weighted combo analysis, guard break detection, jab economy.

Calculates the expected value (damage per stamina cost) of punch combinations,
identifies guard-breaking sequences, and optimizes jab usage economy.
"""

from __future__ import annotations

import logging
from typing import Any

from app.schemas.undisputed.boxing import (
    ComboAnalysis,
    ComboRating,
    GuardBreakReport,
    JabEconomyReport,
    PunchData,
    PunchType,
)

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Punch base data
# ---------------------------------------------------------------------------

_PUNCH_DATA: dict[PunchType, dict[str, float]] = {
    PunchType.JAB: {"damage": 3.0, "stamina_cost": 2.0, "speed": 0.95, "accuracy": 0.85, "guard_impact": 0.10},
    PunchType.CROSS: {"damage": 8.0, "stamina_cost": 5.0, "speed": 0.75, "accuracy": 0.70, "guard_impact": 0.25},
    PunchType.LEAD_HOOK: {"damage": 7.0, "stamina_cost": 4.5, "speed": 0.80, "accuracy": 0.65, "guard_impact": 0.30},
    PunchType.REAR_HOOK: {"damage": 9.0, "stamina_cost": 5.5, "speed": 0.70, "accuracy": 0.60, "guard_impact": 0.35},
    PunchType.LEAD_UPPERCUT: {"damage": 6.5, "stamina_cost": 4.0, "speed": 0.78, "accuracy": 0.60, "guard_impact": 0.25},
    PunchType.REAR_UPPERCUT: {"damage": 10.0, "stamina_cost": 6.0, "speed": 0.65, "accuracy": 0.55, "guard_impact": 0.40},
    PunchType.BODY_JAB: {"damage": 2.5, "stamina_cost": 2.5, "speed": 0.90, "accuracy": 0.80, "guard_impact": 0.05},
    PunchType.BODY_HOOK: {"damage": 7.5, "stamina_cost": 5.0, "speed": 0.72, "accuracy": 0.65, "guard_impact": 0.15},
    PunchType.BODY_UPPERCUT: {"damage": 8.0, "stamina_cost": 5.5, "speed": 0.68, "accuracy": 0.58, "guard_impact": 0.20},
    PunchType.OVERHAND: {"damage": 11.0, "stamina_cost": 7.0, "speed": 0.55, "accuracy": 0.45, "guard_impact": 0.45},
}

# Common combo templates
_COMBO_LIBRARY: list[dict[str, Any]] = [
    {"name": "1-2", "punches": [PunchType.JAB, PunchType.CROSS], "situation": "Range finding"},
    {"name": "1-1-2", "punches": [PunchType.JAB, PunchType.JAB, PunchType.CROSS], "situation": "Setting up the cross"},
    {"name": "1-2-3", "punches": [PunchType.JAB, PunchType.CROSS, PunchType.LEAD_HOOK], "situation": "Combination attack"},
    {"name": "1-2-5-2", "punches": [PunchType.JAB, PunchType.CROSS, PunchType.LEAD_UPPERCUT, PunchType.CROSS], "situation": "Inside fighting"},
    {"name": "3-2-3", "punches": [PunchType.LEAD_HOOK, PunchType.CROSS, PunchType.LEAD_HOOK], "situation": "Mid-range exchanges"},
    {"name": "Body-Body-Head", "punches": [PunchType.BODY_JAB, PunchType.BODY_HOOK, PunchType.LEAD_HOOK], "situation": "Level change attack"},
    {"name": "Jab-Body-Overhand", "punches": [PunchType.JAB, PunchType.BODY_HOOK, PunchType.OVERHAND], "situation": "Dropping guard with body work"},
    {"name": "1-6-3-2", "punches": [PunchType.JAB, PunchType.REAR_UPPERCUT, PunchType.LEAD_HOOK, PunchType.CROSS], "situation": "Finishing sequence"},
]


class ComboEV:
    """Undisputed combo expected-value engine.

    Calculates EV (damage per stamina cost) for combinations, detects
    guard-breaking sequences, and optimizes jab economy.
    """

    # ------------------------------------------------------------------
    # EV-weighted combo analysis
    # ------------------------------------------------------------------

    def analyze_combo(
        self,
        punches: list[PunchType],
        opponent_guard: str = "high",
        distance: str = "mid",
    ) -> ComboAnalysis:
        """Calculate the expected value of a punch combination.

        EV = total expected damage / total stamina cost.
        Adjusts for opponent guard position and distance.
        """
        if not punches:
            return ComboAnalysis(
                punches=[], total_damage=0, total_stamina=0, ev=0,
                rating=ComboRating.POOR, notes=["No punches provided."],
            )

        total_damage = 0.0
        total_stamina = 0.0
        punch_details: list[PunchData] = []

        for i, punch in enumerate(punches):
            data = _PUNCH_DATA.get(punch, _PUNCH_DATA[PunchType.JAB])

            # Guard modifier
            damage_mod = 1.0
            if opponent_guard == "high" and "BODY" in punch.value.upper():
                damage_mod = 1.3  # Body shots land when guard is high
            elif opponent_guard == "low" and "BODY" not in punch.value.upper():
                damage_mod = 1.2  # Head shots land when guard is low
            elif opponent_guard == "high" and punch in (PunchType.OVERHAND, PunchType.REAR_HOOK):
                damage_mod = 0.7  # Power shots blocked by high guard

            # Distance modifier
            if distance == "close" and punch in (PunchType.LEAD_UPPERCUT, PunchType.REAR_UPPERCUT, PunchType.BODY_HOOK):
                damage_mod *= 1.2
            elif distance == "far" and punch == PunchType.JAB:
                damage_mod *= 1.1
            elif distance == "far" and punch in (PunchType.REAR_UPPERCUT, PunchType.BODY_UPPERCUT):
                damage_mod *= 0.6  # Uppercuts dont reach at range

            # Combo chain bonus: later punches in a chain do slightly more damage
            chain_bonus = 1.0 + (i * 0.05)

            adjusted_damage = data["damage"] * damage_mod * chain_bonus * data["accuracy"]
            total_damage += adjusted_damage
            total_stamina += data["stamina_cost"]

            punch_details.append(PunchData(
                punch_type=punch,
                base_damage=data["damage"],
                adjusted_damage=round(adjusted_damage, 2),
                stamina_cost=data["stamina_cost"],
                accuracy=data["accuracy"],
            ))

        ev = total_damage / max(total_stamina, 0.1)

        if ev >= 1.3:
            rating = ComboRating.ELITE
        elif ev >= 1.0:
            rating = ComboRating.STRONG
        elif ev >= 0.7:
            rating = ComboRating.AVERAGE
        else:
            rating = ComboRating.POOR

        notes: list[str] = []
        if total_stamina > 20:
            notes.append("High stamina cost — only throw this combo when you have gas in the tank.")
        if len(punches) > 4:
            notes.append("Long combo — risk getting countered. Only use when opponent is hurt.")
        if rating == ComboRating.ELITE:
            notes.append("Excellent damage-to-cost ratio. This combo is meta.")

        return ComboAnalysis(
            punches=punch_details,
            total_damage=round(total_damage, 2),
            total_stamina=round(total_stamina, 2),
            ev=round(ev, 3),
            rating=rating,
            opponent_guard=opponent_guard,
            distance=distance,
            notes=notes,
        )

    # ------------------------------------------------------------------
    # Guard break detection
    # ------------------------------------------------------------------

    def find_guard_breaks(
        self,
        opponent_guard: str = "high",
    ) -> GuardBreakReport:
        """Find combos that break through a specific guard position.

        Evaluates guard impact accumulation across combo sequences.
        """
        breaking_combos: list[dict[str, Any]] = []

        for combo in _COMBO_LIBRARY:
            guard_impact_total = 0.0
            for punch in combo["punches"]:
                data = _PUNCH_DATA.get(punch, {})
                impact = data.get("guard_impact", 0.1)

                # Guard-specific multiplier
                if opponent_guard == "high" and "BODY" in punch.value.upper():
                    impact *= 0.5  # Body shots dont break high guard
                elif opponent_guard == "high" and punch in (PunchType.OVERHAND, PunchType.REAR_HOOK):
                    impact *= 1.4  # Heavy shots stress the high guard
                elif opponent_guard == "low" and punch in (PunchType.LEAD_HOOK, PunchType.CROSS):
                    impact *= 1.3

                guard_impact_total += impact

            if guard_impact_total >= 0.6:
                breaking_combos.append({
                    "name": combo["name"],
                    "punches": [p.value for p in combo["punches"]],
                    "guard_impact": round(guard_impact_total, 3),
                    "situation": combo["situation"],
                })

        breaking_combos.sort(key=lambda c: c["guard_impact"], reverse=True)

        tips: list[str] = []
        if opponent_guard == "high":
            tips.append("Target the body first to force them to lower guard, then go upstairs.")
            tips.append("Overhands and rear hooks stress the high guard the most.")
        elif opponent_guard == "low":
            tips.append("Head hooks and crosses exploit the low guard.")
            tips.append("Feint to the body, then throw upstairs.")

        return GuardBreakReport(
            opponent_guard=opponent_guard,
            breaking_combos=breaking_combos,
            tips=tips,
        )

    # ------------------------------------------------------------------
    # Jab economy analysis
    # ------------------------------------------------------------------

    def analyze_jab_economy(
        self,
        jabs_thrown: int,
        jabs_landed: int,
        total_punches_thrown: int,
        rounds_fought: int,
    ) -> JabEconomyReport:
        """Analyze jab usage efficiency across a fight.

        Calculates jab percentage, accuracy, stamina investment, and
        recommends adjustments.
        """
        jab_data = _PUNCH_DATA[PunchType.JAB]
        jab_pct = jabs_thrown / max(total_punches_thrown, 1)
        jab_accuracy = jabs_landed / max(jabs_thrown, 1)
        jabs_per_round = jabs_thrown / max(rounds_fought, 1)

        stamina_spent_on_jabs = jabs_thrown * jab_data["stamina_cost"]
        total_jab_damage = jabs_landed * jab_data["damage"]
        jab_ev = total_jab_damage / max(stamina_spent_on_jabs, 0.1)

        notes: list[str] = []
        if jab_pct < 0.25:
            notes.append("Low jab usage — establish the jab to control distance and set up combos.")
        elif jab_pct > 0.60:
            notes.append("Over-relying on the jab — mix in power shots and combos.")
        else:
            notes.append("Good jab-to-power balance.")

        if jab_accuracy < 0.40:
            notes.append("Jab accuracy is low — focus on timing and range. Dont throw wild jabs.")
        elif jab_accuracy > 0.70:
            notes.append("Excellent jab accuracy — use it to set up everything.")

        if jabs_per_round < 10:
            notes.append("Throw more jabs per round — target 15-20 for ring control.")
        elif jabs_per_round > 30:
            notes.append("High jab volume — watch stamina drain in later rounds.")

        optimal_pct = 0.35
        grade = "A" if abs(jab_pct - optimal_pct) < 0.10 and jab_accuracy > 0.55 else (
            "B" if jab_accuracy > 0.45 else "C"
        )

        return JabEconomyReport(
            jabs_thrown=jabs_thrown,
            jabs_landed=jabs_landed,
            jab_pct=round(jab_pct, 3),
            jab_accuracy=round(jab_accuracy, 3),
            jabs_per_round=round(jabs_per_round, 1),
            stamina_spent=round(stamina_spent_on_jabs, 1),
            total_jab_damage=round(total_jab_damage, 1),
            jab_ev=round(jab_ev, 3),
            grade=grade,
            notes=notes,
        )

    # ------------------------------------------------------------------
    # Combo library access
    # ------------------------------------------------------------------

    def get_combo_library(self, situation: str | None = None) -> list[dict[str, Any]]:
        """Return combos from the library, optionally filtered by situation."""
        if situation:
            return [
                {**c, "punches": [p.value for p in c["punches"]]}
                for c in _COMBO_LIBRARY
                if situation.lower() in c["situation"].lower()
            ]
        return [{**c, "punches": [p.value for p in c["punches"]]} for c in _COMBO_LIBRARY]


# Module-level singleton
combo_ev = ComboEV()
