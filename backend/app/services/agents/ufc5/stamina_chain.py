"""StaminaChain AI — round-by-round stamina economy, whiff punishment model, output discipline.

Models the stamina economy across a 3 or 5 round fight, recommends output budgets,
and identifies whiff punishment opportunities that drain opponent stamina.
"""

from __future__ import annotations

import logging
from typing import Any

from app.schemas.ufc5.combat import (
    StaminaEconomy,
    StaminaPhase,
    StrikeType,
    WhiffPunishment,
)

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

# Stamina cost per strike type
_STRIKE_STAMINA_COST: dict[StrikeType, float] = {
    StrikeType.JAB: 2.0,
    StrikeType.CROSS: 3.5,
    StrikeType.HOOK: 4.0,
    StrikeType.UPPERCUT: 4.5,
    StrikeType.OVERHAND: 5.0,
    StrikeType.BODY_HOOK: 3.5,
    StrikeType.BODY_STRAIGHT: 3.0,
    StrikeType.LEG_KICK: 3.0,
    StrikeType.CALF_KICK: 3.0,
    StrikeType.BODY_KICK: 4.5,
    StrikeType.HEAD_KICK: 6.0,
    StrikeType.SPINNING_BACK_KICK: 7.0,
    StrikeType.SPINNING_BACK_FIST: 6.5,
    StrikeType.FRONT_KICK: 3.5,
    StrikeType.KNEE: 4.0,
    StrikeType.ELBOW: 3.0,
    StrikeType.SUPERMAN_PUNCH: 5.5,
    StrikeType.FLYING_KNEE: 8.0,
}

# Whiff penalty multiplier (missing costs extra)
_WHIFF_MULTIPLIER = 1.5

# Recovery rate per second at rest
_BASE_RECOVERY_RATE = 2.5

# Phase thresholds
_PHASE_THRESHOLDS = [
    (80.0, StaminaPhase.FRESH),
    (60.0, StaminaPhase.CRUISING),
    (40.0, StaminaPhase.CONSERVING),
    (20.0, StaminaPhase.DEPLETED),
    (0.0, StaminaPhase.GASSED),
]

# Recovery frames after whiffed strikes (60fps)
_WHIFF_RECOVERY_FRAMES: dict[StrikeType, int] = {
    StrikeType.JAB: 12,
    StrikeType.CROSS: 18,
    StrikeType.HOOK: 22,
    StrikeType.UPPERCUT: 24,
    StrikeType.OVERHAND: 28,
    StrikeType.BODY_HOOK: 20,
    StrikeType.BODY_STRAIGHT: 16,
    StrikeType.LEG_KICK: 16,
    StrikeType.CALF_KICK: 16,
    StrikeType.BODY_KICK: 25,
    StrikeType.HEAD_KICK: 35,
    StrikeType.SPINNING_BACK_KICK: 40,
    StrikeType.SPINNING_BACK_FIST: 38,
    StrikeType.FRONT_KICK: 22,
    StrikeType.KNEE: 20,
    StrikeType.ELBOW: 18,
    StrikeType.SUPERMAN_PUNCH: 30,
    StrikeType.FLYING_KNEE: 42,
}


class StaminaChain:
    """Round-by-round stamina economy engine.

    Tracks player and opponent stamina, recommends output budgets,
    and models whiff punishment opportunities.
    """

    def __init__(self, total_rounds: int = 3) -> None:
        self._total_rounds = total_rounds
        self._player_stamina = 100.0
        self._opponent_stamina = 100.0
        self._round_history: list[StaminaEconomy] = []
        self._body_damage_factor = 1.0  # increased by body damage

    def reset(self, total_rounds: int = 3) -> None:
        """Reset for a new fight."""
        self._total_rounds = total_rounds
        self._player_stamina = 100.0
        self._opponent_stamina = 100.0
        self._round_history = []
        self._body_damage_factor = 1.0

    def set_body_damage_factor(self, factor: float) -> None:
        """Update the stamina drain multiplier from accumulated body damage."""
        self._body_damage_factor = max(1.0, min(3.0, factor))

    def record_strike(
        self,
        strike: StrikeType,
        landed: bool,
        is_player: bool = True,
    ) -> float:
        """
        Record a strike thrown and return the stamina cost.

        Whiffed strikes cost extra due to recovery and missed energy.
        """
        base_cost = _STRIKE_STAMINA_COST.get(strike, 3.0)
        cost = base_cost * (1.0 if landed else _WHIFF_MULTIPLIER)
        cost *= self._body_damage_factor if is_player else 1.0

        if is_player:
            self._player_stamina = max(0.0, self._player_stamina - cost)
        else:
            self._opponent_stamina = max(0.0, self._opponent_stamina - cost)

        return round(cost, 1)

    def apply_round_recovery(self) -> None:
        """Apply between-round recovery (about 15% stamina back)."""
        recovery = 15.0
        self._player_stamina = min(100.0, self._player_stamina + recovery)
        self._opponent_stamina = min(100.0, self._opponent_stamina + recovery)

    def get_economy(self, round_number: int) -> StaminaEconomy:
        """Generate the stamina economy report for a given round."""
        phase = self._classify_phase(self._player_stamina)
        budget = self._calculate_output_budget(round_number, self._player_stamina)
        pace = self._recommend_pace(round_number, self._player_stamina)
        drain = self._average_drain_rate()

        economy = StaminaEconomy(
            round_number=round_number,
            current_stamina=round(self._player_stamina, 1),
            phase=phase,
            output_budget=budget,
            recovery_rate=_BASE_RECOVERY_RATE,
            drain_rate=round(drain, 1),
            whiff_penalty=round(drain * (_WHIFF_MULTIPLIER - 1), 1),
            recommended_pace=pace,
            opponent_stamina_estimate=round(self._opponent_stamina, 1),
        )
        self._round_history.append(economy)
        return economy

    def get_whiff_punishment_model(self) -> list[WhiffPunishment]:
        """Return whiff punishment opportunities sorted by exploitability."""
        punishments: list[WhiffPunishment] = []
        for strike, frames in sorted(
            _WHIFF_RECOVERY_FRAMES.items(), key=lambda x: x[1], reverse=True
        ):
            cost = _STRIKE_STAMINA_COST.get(strike, 3.0) * _WHIFF_MULTIPLIER
            counters = self._best_counters_for_whiff(frames)
            punishments.append(
                WhiffPunishment(
                    whiff_type=strike,
                    recovery_frames=frames,
                    optimal_counter=counters,
                    stamina_cost_to_opponent=round(cost, 1),
                )
            )
        return punishments

    def get_output_discipline_report(self, round_number: int) -> dict[str, Any]:
        """
        Generate an output discipline report — tells the player whether
        they are over-spending or under-spending stamina.
        """
        economy = self.get_economy(round_number)
        rounds_left = self._total_rounds - round_number
        stamina_per_round_needed = (
            economy.current_stamina / max(rounds_left, 1)
        )

        if economy.current_stamina > 70:
            discipline = "under-spending"
            advice = "You can afford to increase output — stamina reserve is healthy"
        elif economy.current_stamina < 40:
            discipline = "over-spending"
            advice = "Reduce output — conserve for championship rounds"
        else:
            discipline = "balanced"
            advice = "Good output discipline — maintain current pace"

        return {
            "discipline_status": discipline,
            "advice": advice,
            "stamina": round(economy.current_stamina, 1),
            "rounds_remaining": rounds_left,
            "stamina_budget_per_round": round(stamina_per_round_needed, 1),
            "opponent_stamina_estimate": round(self._opponent_stamina, 1),
            "phase": economy.phase.value,
            "recommended_pace": economy.recommended_pace,
        }

    @property
    def player_stamina(self) -> float:
        return round(self._player_stamina, 1)

    @property
    def opponent_stamina(self) -> float:
        return round(self._opponent_stamina, 1)

    # --- private helpers ---

    def _classify_phase(self, stamina: float) -> StaminaPhase:
        for threshold, phase in _PHASE_THRESHOLDS:
            if stamina >= threshold:
                return phase
        return StaminaPhase.GASSED

    def _calculate_output_budget(self, round_number: int, stamina: float) -> int:
        """Estimate how many significant strikes the player can throw this round."""
        avg_cost = 3.5 * self._body_damage_factor
        # Reserve stamina for remaining rounds
        rounds_left = self._total_rounds - round_number
        reserve = rounds_left * 25.0  # want ~25% per remaining round
        available = max(0.0, stamina - reserve)
        return max(0, int(available / avg_cost))

    def _recommend_pace(self, round_number: int, stamina: float) -> str:
        """Recommend a pace based on stamina and round context."""
        is_final_round = round_number == self._total_rounds
        is_championship = self._total_rounds == 5

        if stamina > 75 and is_final_round:
            return "explosive"
        if stamina > 60:
            return "measured"
        if stamina > 35:
            return "conserve"
        if is_final_round and stamina > 20:
            return "explosive"  # empty the tank
        return "survive"

    def _average_drain_rate(self) -> float:
        """Average stamina drain per significant strike."""
        costs = list(_STRIKE_STAMINA_COST.values())
        return sum(costs) / len(costs) * self._body_damage_factor

    def _best_counters_for_whiff(self, frames: int) -> list[StrikeType]:
        """Select best counter strikes that fit within the whiff window."""
        options = [
            (StrikeType.JAB, 8),
            (StrikeType.CROSS, 12),
            (StrikeType.HOOK, 16),
            (StrikeType.UPPERCUT, 20),
            (StrikeType.BODY_HOOK, 16),
        ]
        selected: list[StrikeType] = []
        remaining = frames
        for strike, cost in options:
            if remaining >= cost:
                selected.append(strike)
                remaining -= cost
        return selected or [StrikeType.JAB]
