"""SquadForge AI — chemistry optimizer, budget-to-win-rate optimizer, card value tracker.

Builds optimal squads from available cards, maximizes chemistry links,
tracks card market values, and projects budget-to-performance ratios.
"""

from __future__ import annotations

import logging
from collections import defaultdict
from typing import Any

from app.schemas.eafc26.squad import (
    BudgetOptimization,
    CardValue,
    CardValueTrend,
    ChemistryLink,
    ChemistryReport,
    ChemistryType,
    PlayerCard,
    SquadAnalysis,
    SquadSlot,
)

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Chemistry scoring rules
# ---------------------------------------------------------------------------

_CHEM_WEIGHTS: dict[ChemistryType, float] = {
    ChemistryType.NATION: 1.0,
    ChemistryType.LEAGUE: 1.5,
    ChemistryType.CLUB: 2.0,
    ChemistryType.HERO: 1.8,
}

_POSITION_ADJACENCY: dict[str, list[str]] = {
    "GK": ["CB"],
    "CB": ["GK", "CB", "LB", "RB"],
    "LB": ["CB", "LM", "LWB"],
    "RB": ["CB", "RM", "RWB"],
    "LWB": ["LB", "LM", "CM"],
    "RWB": ["RB", "RM", "CM"],
    "CDM": ["CB", "CM"],
    "CM": ["CDM", "CM", "CAM", "LM", "RM"],
    "LM": ["LB", "LW", "CM"],
    "RM": ["RB", "RW", "CM"],
    "CAM": ["CM", "CF", "LW", "RW"],
    "CF": ["CAM", "ST"],
    "LW": ["LM", "CAM", "ST"],
    "RW": ["RM", "CAM", "ST"],
    "ST": ["CF", "LW", "RW", "ST"],
}

# Market value baselines by card tier
_TIER_VALUE_RANGES: dict[str, tuple[int, int]] = {
    "bronze": (200, 1_500),
    "silver": (300, 5_000),
    "gold": (600, 50_000),
    "rare_gold": (1_000, 200_000),
    "totw": (10_000, 500_000),
    "hero": (30_000, 800_000),
    "icon": (50_000, 5_000_000),
    "toty": (200_000, 10_000_000),
    "tots": (100_000, 8_000_000),
}

# Win-rate per overall-rating band (approximated)
_OVR_WIN_RATE: list[tuple[int, float]] = [
    (95, 0.72),
    (90, 0.62),
    (87, 0.55),
    (85, 0.50),
    (83, 0.45),
    (80, 0.40),
    (75, 0.32),
    (0, 0.25),
]


class SquadForge:
    """EA FC 26 squad chemistry and budget optimization engine.

    Tracks card values, maximizes chemistry, and projects budget efficiency.
    """

    def __init__(self) -> None:
        self._card_history: dict[str, list[CardValue]] = defaultdict(list)
        self._squad_cache: dict[str, SquadAnalysis] = {}

    # ------------------------------------------------------------------
    # Chemistry optimizer
    # ------------------------------------------------------------------

    def optimize_chemistry(
        self,
        squad_slots: list[SquadSlot],
    ) -> ChemistryReport:
        """Analyze every adjacent pair in a squad and return a full chemistry report.

        Evaluates nation, league, and club links between neighboring positions,
        assigns a total chemistry score (0-33), and suggests swaps.
        """
        links: list[ChemistryLink] = []
        total_score = 0.0

        for slot in squad_slots:
            pos = slot.position.upper()
            neighbors = _POSITION_ADJACENCY.get(pos, [])
            for other in squad_slots:
                if other is slot:
                    continue
                if other.position.upper() not in neighbors:
                    continue

                link_score, link_type = self._compute_link(slot.card, other.card)
                if link_score > 0:
                    links.append(ChemistryLink(
                        player_a=slot.card.name,
                        player_b=other.card.name,
                        chemistry_type=link_type,
                        strength=round(link_score, 2),
                    ))
                    total_score += link_score

        # Normalize to 0-33 scale
        max_possible = len(squad_slots) * 3.0
        chem_out_of_33 = min(33, round((total_score / max(max_possible, 1)) * 33, 1))

        # Build suggestions
        suggestions: list[str] = []
        weak_slots = [s for s in squad_slots if self._slot_chem(s, squad_slots) < 1.0]
        for ws in weak_slots[:3]:
            suggestions.append(
                f"Consider replacing {ws.card.name} ({ws.position}) — low chemistry "
                f"with neighbors. Look for a {ws.card.league} / {ws.card.nation} link."
            )

        if chem_out_of_33 < 20:
            suggestions.append(
                "Overall chemistry is below 20. Focus on league or club clusters."
            )

        return ChemistryReport(
            total_chemistry=chem_out_of_33,
            max_chemistry=33,
            links=links,
            weak_positions=[ws.position for ws in weak_slots],
            suggestions=suggestions,
        )

    # ------------------------------------------------------------------
    # Budget-to-win-rate optimizer
    # ------------------------------------------------------------------

    def optimize_budget(
        self,
        budget_coins: int,
        preferred_formation: str = "4-3-3",
        preferred_league: str | None = None,
    ) -> BudgetOptimization:
        """Given a budget, project the best achievable win-rate.

        Distributes spend across positions according to impact weighting,
        estimates the overall rating achievable, and maps to a win-rate.
        """
        position_weights = {
            "ST": 0.18, "CAM": 0.12, "CM": 0.10, "CB": 0.14,
            "LW": 0.08, "RW": 0.08, "CDM": 0.07,
            "LB": 0.06, "RB": 0.06, "GK": 0.05, "LM": 0.03, "RM": 0.03,
        }

        allocations: dict[str, int] = {}
        estimated_ratings: dict[str, int] = {}
        for pos, weight in position_weights.items():
            alloc = int(budget_coins * weight)
            allocations[pos] = alloc
            estimated_ratings[pos] = self._coins_to_ovr(alloc)

        avg_ovr = round(sum(estimated_ratings.values()) / max(len(estimated_ratings), 1), 1)
        projected_wr = self._ovr_to_win_rate(avg_ovr)

        tips: list[str] = []
        if budget_coins < 50_000:
            tips.append("At this budget, target meta gold cards with strong pace and passing.")
            tips.append("Use a single-league squad to guarantee full chemistry.")
        elif budget_coins < 500_000:
            tips.append("Mix TOTW and rare golds. Invest heavily in ST and CB positions.")
        else:
            tips.append("You can afford Icons or TOTY. Anchor the spine (ST, CAM, CB, GK).")

        if preferred_league:
            tips.append(f"Building around {preferred_league} — look for SBC-value players.")

        return BudgetOptimization(
            budget_coins=budget_coins,
            formation=preferred_formation,
            position_allocations=allocations,
            estimated_ratings=estimated_ratings,
            average_overall=avg_ovr,
            projected_win_rate=round(projected_wr, 3),
            tips=tips,
        )

    # ------------------------------------------------------------------
    # Card value tracker
    # ------------------------------------------------------------------

    def track_card_value(self, card: PlayerCard) -> CardValue:
        """Record and return the current estimated value of a card.

        Estimates value from tier, overall rating, and demand factors.
        """
        base_lo, base_hi = _TIER_VALUE_RANGES.get(card.tier, (500, 10_000))
        ovr_factor = max(0.0, (card.overall - 75) / 24.0)
        estimated = int(base_lo + (base_hi - base_lo) * ovr_factor)

        # Pace premium in the FC meta
        if card.pace and card.pace >= 90:
            estimated = int(estimated * 1.35)

        # Position scarcity premium
        scarce = {"ST", "CB", "GK"}
        if card.position.upper() in scarce:
            estimated = int(estimated * 1.15)

        cv = CardValue(
            card_name=card.name,
            tier=card.tier,
            overall=card.overall,
            estimated_value=estimated,
            trend=self._compute_trend(card.name, estimated),
        )
        self._card_history[card.name].append(cv)
        return cv

    def get_card_history(self, card_name: str) -> list[CardValue]:
        """Return price history for a tracked card."""
        return list(self._card_history.get(card_name, []))

    # ------------------------------------------------------------------
    # Full squad analysis
    # ------------------------------------------------------------------

    def analyze_squad(
        self,
        squad_slots: list[SquadSlot],
        budget_coins: int | None = None,
    ) -> SquadAnalysis:
        """Run a comprehensive squad analysis combining chemistry and value."""
        chem = self.optimize_chemistry(squad_slots)
        total_value = 0
        card_values: list[CardValue] = []
        for s in squad_slots:
            cv = self.track_card_value(s.card)
            card_values.append(cv)
            total_value += cv.estimated_value

        avg_ovr = sum(s.card.overall for s in squad_slots) / max(len(squad_slots), 1)
        projected_wr = self._ovr_to_win_rate(avg_ovr)

        value_rating = "good"
        if budget_coins and total_value > budget_coins * 1.2:
            value_rating = "over_budget"
        elif budget_coins and total_value < budget_coins * 0.6:
            value_rating = "under_spent"

        return SquadAnalysis(
            chemistry=chem,
            card_values=card_values,
            total_estimated_value=total_value,
            average_overall=round(avg_ovr, 1),
            projected_win_rate=round(projected_wr, 3),
            value_rating=value_rating,
            improvement_suggestions=chem.suggestions,
        )

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _compute_link(a: PlayerCard, b: PlayerCard) -> tuple[float, ChemistryType]:
        best_score = 0.0
        best_type = ChemistryType.NATION
        if a.club and b.club and a.club == b.club:
            score = _CHEM_WEIGHTS[ChemistryType.CLUB]
            if score > best_score:
                best_score, best_type = score, ChemistryType.CLUB
        if a.league and b.league and a.league == b.league:
            score = _CHEM_WEIGHTS[ChemistryType.LEAGUE]
            if score > best_score:
                best_score, best_type = score, ChemistryType.LEAGUE
        if a.nation and b.nation and a.nation == b.nation:
            score = _CHEM_WEIGHTS[ChemistryType.NATION]
            if score > best_score:
                best_score, best_type = score, ChemistryType.NATION
        return best_score, best_type

    def _slot_chem(self, slot: SquadSlot, all_slots: list[SquadSlot]) -> float:
        total = 0.0
        pos = slot.position.upper()
        neighbors = _POSITION_ADJACENCY.get(pos, [])
        for other in all_slots:
            if other is slot:
                continue
            if other.position.upper() in neighbors:
                score, _ = self._compute_link(slot.card, other.card)
                total += score
        return total

    def _compute_trend(self, card_name: str, current_value: int) -> CardValueTrend:
        history = self._card_history.get(card_name, [])
        if len(history) < 2:
            return CardValueTrend.STABLE
        prev = history[-1].estimated_value
        delta_pct = (current_value - prev) / max(prev, 1)
        if delta_pct > 0.05:
            return CardValueTrend.RISING
        if delta_pct < -0.05:
            return CardValueTrend.FALLING
        return CardValueTrend.STABLE

    @staticmethod
    def _coins_to_ovr(coins: int) -> int:
        if coins >= 1_000_000:
            return 93
        if coins >= 500_000:
            return 90
        if coins >= 200_000:
            return 88
        if coins >= 100_000:
            return 86
        if coins >= 50_000:
            return 84
        if coins >= 20_000:
            return 82
        if coins >= 5_000:
            return 79
        return 75

    @staticmethod
    def _ovr_to_win_rate(ovr: float) -> float:
        for threshold, wr in _OVR_WIN_RATE:
            if ovr >= threshold:
                return wr
        return 0.25


# Module-level singleton
squad_forge = SquadForge()
