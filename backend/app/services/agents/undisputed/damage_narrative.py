"""DamageNarrative — long-fight damage sequencing and punch economy for Undisputed.

Models accumulative damage over a full fight, tracks punch economy (output vs cost),
and generates a damage narrative to guide late-fight strategy.
"""

from __future__ import annotations

import logging
from typing import Any

from app.schemas.undisputed.boxing import (
    DamageState,
    DamageTimeline,
    PunchEconomyReport,
)

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Damage accumulation model
# ---------------------------------------------------------------------------

_DAMAGE_DECAY_PER_ROUND = 0.03  # Natural recovery between rounds
_DAMAGE_THRESHOLDS: dict[str, float] = {
    "fresh": 0.15,
    "worn": 0.35,
    "hurt": 0.55,
    "danger": 0.75,
    "desperate": 0.90,
}

_PUNCH_BASE_DAMAGE: dict[str, float] = {
    "jab": 2.0, "cross": 6.0, "hook": 7.0, "uppercut": 8.0,
    "body": 4.0, "overhand": 9.0, "power": 7.5,
}


class DamageNarrative:
    """Undisputed long-fight damage sequencing engine.

    Tracks cumulative damage over rounds, models punch economy,
    and generates strategic narratives for late-fight scenarios.
    """

    def __init__(self) -> None:
        self._fight_logs: dict[str, list[dict[str, Any]]] = {}

    # ------------------------------------------------------------------
    # Damage sequencing
    # ------------------------------------------------------------------

    def update_damage_state(
        self,
        fight_id: str,
        round_num: int,
        punches_absorbed: dict[str, int],
        knockdowns_taken: int = 0,
    ) -> DamageState:
        """Update cumulative damage state after a round.

        punches_absorbed: dict mapping punch type to count absorbed.
        """
        self._fight_logs.setdefault(fight_id, [])

        # Calculate round damage
        round_damage = 0.0
        for punch_type, count in punches_absorbed.items():
            base = _PUNCH_BASE_DAMAGE.get(punch_type, 5.0)
            round_damage += base * count

        # Knockdown damage spike
        round_damage += knockdowns_taken * 25.0

        # Normalize to 0-1 scale (100 = max realistic damage per round)
        round_damage_normalized = min(1.0, round_damage / 100.0)

        # Get previous cumulative damage
        prev_cumulative = 0.0
        if self._fight_logs[fight_id]:
            prev_cumulative = self._fight_logs[fight_id][-1].get("cumulative", 0.0)

        # Apply decay (rest between rounds)
        recovered = prev_cumulative * _DAMAGE_DECAY_PER_ROUND
        cumulative = prev_cumulative - recovered + round_damage_normalized
        cumulative = min(1.0, max(0.0, cumulative))

        # Classify state
        state_label = "fresh"
        for label, threshold in _DAMAGE_THRESHOLDS.items():
            if cumulative <= threshold:
                state_label = label
                break
        else:
            state_label = "desperate"

        # Store
        entry = {
            "round": round_num,
            "round_damage": round(round_damage_normalized, 3),
            "cumulative": round(cumulative, 3),
            "state": state_label,
            "knockdowns": knockdowns_taken,
        }
        self._fight_logs[fight_id].append(entry)

        # Strategy advice
        advice: list[str] = []
        if state_label == "fresh":
            advice.append("Minimal damage taken — fight your fight.")
        elif state_label == "worn":
            advice.append("Starting to accumulate damage. Be more selective with exchanges.")
        elif state_label == "hurt":
            advice.append("Significant damage — avoid firefights. Clinch and move.")
        elif state_label == "danger":
            advice.append("In the danger zone — one big shot could end it. Survive and recover.")
            advice.append("Use the clinch. Move laterally. Do not trade punches.")
        elif state_label == "desperate":
            advice.append("CRITICAL: Near stoppage levels. Consider if you need a KO to win.")
            advice.append("If ahead on cards, survive. If behind, calculated aggression only.")

        return DamageState(
            fight_id=fight_id,
            round_num=round_num,
            round_damage=round(round_damage_normalized, 3),
            cumulative_damage=round(cumulative, 3),
            state=state_label,
            recovery=round(recovered, 3),
            advice=advice,
        )

    # ------------------------------------------------------------------
    # Damage timeline
    # ------------------------------------------------------------------

    def get_damage_timeline(self, fight_id: str) -> DamageTimeline:
        """Get the full damage timeline for a fight."""
        logs = self._fight_logs.get(fight_id, [])

        rounds: list[dict[str, Any]] = []
        for entry in logs:
            rounds.append({
                "round": entry["round"],
                "damage_taken": entry["round_damage"],
                "cumulative": entry["cumulative"],
                "state": entry["state"],
            })

        peak_damage_round = 0
        peak_damage = 0.0
        for entry in logs:
            if entry["round_damage"] > peak_damage:
                peak_damage = entry["round_damage"]
                peak_damage_round = entry["round"]

        current_state = logs[-1]["state"] if logs else "fresh"
        cumulative = logs[-1]["cumulative"] if logs else 0.0

        narrative = self._build_narrative(logs)

        return DamageTimeline(
            fight_id=fight_id,
            rounds=rounds,
            current_state=current_state,
            cumulative_damage=round(cumulative, 3),
            peak_damage_round=peak_damage_round,
            peak_round_damage=round(peak_damage, 3),
            narrative=narrative,
        )

    # ------------------------------------------------------------------
    # Punch economy
    # ------------------------------------------------------------------

    def analyze_punch_economy(
        self,
        punches_thrown: int,
        punches_landed: int,
        damage_dealt: float,
        stamina_spent: float,
        rounds_fought: int,
    ) -> PunchEconomyReport:
        """Analyze punch economy — damage output relative to stamina investment.

        Higher economy = more efficient fighter. Measures damage per stamina unit
        and activity rate.
        """
        accuracy = punches_landed / max(punches_thrown, 1)
        per_round_thrown = punches_thrown / max(rounds_fought, 1)
        per_round_landed = punches_landed / max(rounds_fought, 1)

        economy = damage_dealt / max(stamina_spent, 0.1)
        damage_per_punch = damage_dealt / max(punches_landed, 1)

        if economy >= 1.5:
            grade = "A"
        elif economy >= 1.0:
            grade = "B"
        elif economy >= 0.7:
            grade = "C"
        else:
            grade = "D"

        notes: list[str] = []
        if accuracy < 0.30:
            notes.append("Low accuracy is wasting stamina. Be more selective.")
        if per_round_thrown < 20:
            notes.append("Low output — throw more punches to keep the judges interested.")
        elif per_round_thrown > 60:
            notes.append("Very high output — watch for stamina drain in late rounds.")
        if economy < 0.7:
            notes.append("Poor punch economy — you are spending more than you are earning.")
        if damage_per_punch > 5:
            notes.append("Heavy hands — each landed punch carries significant impact.")

        return PunchEconomyReport(
            punches_thrown=punches_thrown,
            punches_landed=punches_landed,
            accuracy=round(accuracy, 3),
            damage_dealt=round(damage_dealt, 2),
            stamina_spent=round(stamina_spent, 2),
            economy=round(economy, 3),
            damage_per_punch=round(damage_per_punch, 2),
            per_round_thrown=round(per_round_thrown, 1),
            per_round_landed=round(per_round_landed, 1),
            grade=grade,
            notes=notes,
        )

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _build_narrative(logs: list[dict[str, Any]]) -> str:
        if not logs:
            return "No fight data available."

        states_seen = [entry["state"] for entry in logs]
        latest = states_seen[-1]
        rounds = len(logs)

        if latest == "fresh":
            return f"Through {rounds} round(s), minimal damage absorbed. Fighter is fresh and dangerous."
        elif latest == "worn":
            return f"After {rounds} round(s), wear is showing. Damage is accumulating but manageable."
        elif latest == "hurt":
            return f"{rounds} rounds of combat have taken a toll. Fighter is hurt and needs to be careful."
        elif latest == "danger":
            return f"After {rounds} brutal rounds, fighter is in the danger zone. One more big shot could end it."
        else:
            return f"Desperate situation after {rounds} rounds. Fighter is on borrowed time."


# Module-level singleton
damage_narrative = DamageNarrative()
