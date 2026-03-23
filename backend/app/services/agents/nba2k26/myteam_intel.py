"""MyTeam Intelligence — meta lineup tracker, auction house value, chemistry optimizer.

Analyzes MyTeam lineups for competitive meta viability, tracks auction house market
trends, and optimizes team chemistry for maximum stat boosts.
"""

from __future__ import annotations

import logging
from collections import defaultdict

from app.schemas.nba2k26.gameplay import (
    AuctionSnipe,
    LineupSlot,
    MyTeamCard,
    MyTeamLineup,
)

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Card tier rankings and market values
# ---------------------------------------------------------------------------

CARD_TIER_ORDER = ["emerald", "sapphire", "ruby", "amethyst", "diamond", "pink_diamond", "galaxy_opal", "dark_matter"]

CARD_TIER_VALUE_RANGE: dict[str, tuple[int, int]] = {
    "emerald": (500, 2000),
    "sapphire": (1500, 5000),
    "ruby": (3000, 15000),
    "amethyst": (10000, 50000),
    "diamond": (30000, 150000),
    "pink_diamond": (80000, 400000),
    "galaxy_opal": (200000, 800000),
    "dark_matter": (500000, 2000000),
}

# ---------------------------------------------------------------------------
# Meta lineup archetypes
# ---------------------------------------------------------------------------

META_LINEUPS: dict[str, dict] = {
    "speed_boost_five": {
        "description": "All 5 positions can speed boost — ultimate spacing",
        "positions": {"pg": 95, "sg": 90, "sf": 88, "pf": 85, "c": 82},
        "meta_score": 0.92,
        "strengths": ["Fast breaks", "Floor spacing", "Defensive versatility"],
        "weaknesses": ["Rebounding", "Post defense"],
    },
    "twin_towers": {
        "description": "Two dominant bigs with three shooters",
        "positions": {"pg": 90, "sg": 88, "sf": 86, "pf": 94, "c": 95},
        "meta_score": 0.85,
        "strengths": ["Rebounding", "Paint scoring", "Rim protection"],
        "weaknesses": ["Transition defense", "Perimeter switches"],
    },
    "lockdown_squad": {
        "description": "Elite defenders at every position",
        "positions": {"pg": 88, "sg": 90, "sf": 92, "pf": 90, "c": 91},
        "meta_score": 0.88,
        "strengths": ["Defense", "Forced turnovers", "Transition"],
        "weaknesses": ["Half-court offense", "Three-point shooting"],
    },
    "three_hunt": {
        "description": "Five-out offense, everyone can shoot threes",
        "positions": {"pg": 92, "sg": 91, "sf": 89, "pf": 87, "c": 85},
        "meta_score": 0.90,
        "strengths": ["Three-point volume", "Floor spacing", "Pick-and-pop"],
        "weaknesses": ["Interior scoring", "Offensive rebounding"],
    },
}

# ---------------------------------------------------------------------------
# Chemistry boost rules
# ---------------------------------------------------------------------------

CHEMISTRY_RULES: list[dict] = [
    {
        "name": "Team Chemistry",
        "condition": "All 5 starters share a team",
        "boost": 0.10,
        "stat_boost": "+3 to all stats",
    },
    {
        "name": "Era Chemistry",
        "condition": "All 5 starters from the same era (e.g., 2010s)",
        "boost": 0.08,
        "stat_boost": "+2 to all stats",
    },
    {
        "name": "Dynamic Duo",
        "condition": "Two linked players in lineup (e.g., Jordan + Pippen)",
        "boost": 0.12,
        "stat_boost": "+4 to shared stats for the duo",
    },
    {
        "name": "Position Lock",
        "condition": "All players at their natural position",
        "boost": 0.05,
        "stat_boost": "+1 to all stats, no penalty",
    },
    {
        "name": "Height Balance",
        "condition": "Ascending height from PG to C",
        "boost": 0.03,
        "stat_boost": "+1 rebounding and interior defense",
    },
]

# Dynamic duo pairs
DYNAMIC_DUOS: list[tuple[str, str]] = [
    ("Michael Jordan", "Scottie Pippen"),
    ("LeBron James", "Dwyane Wade"),
    ("Kobe Bryant", "Shaquille O'Neal"),
    ("Stephen Curry", "Klay Thompson"),
    ("Kevin Durant", "Russell Westbrook"),
    ("Magic Johnson", "Kareem Abdul-Jabbar"),
    ("Tim Duncan", "Tony Parker"),
    ("Larry Bird", "Kevin McHale"),
]


class MyTeamIntel:
    """MyTeam intelligence engine.

    Tracks meta lineups, evaluates auction house value, optimizes chemistry,
    and recommends roster upgrades.
    """

    def __init__(self) -> None:
        self._user_lineups: dict[str, MyTeamLineup] = {}
        self._market_history: dict[str, list[int]] = defaultdict(list)

    # ------------------------------------------------------------------
    # Meta lineup analysis
    # ------------------------------------------------------------------

    def analyze_lineup(self, lineup: MyTeamLineup) -> dict:
        """Analyze a lineup for meta viability, chemistry, and weaknesses.

        Returns comprehensive analysis including meta score, chemistry breakdown,
        upgrade recommendations, and closest meta archetype.
        """
        chemistry = self.calculate_chemistry(lineup)
        meta_score = self._calculate_meta_score(lineup)
        archetype = self._find_closest_meta_archetype(lineup)
        weaknesses = self._identify_weaknesses(lineup)
        upgrades = self._suggest_upgrades(lineup, weaknesses)

        analysis = {
            "lineup_name": lineup.name,
            "total_chemistry": round(chemistry, 3),
            "meta_score": round(meta_score, 3),
            "closest_meta_archetype": archetype,
            "estimated_overall": lineup.estimated_overall,
            "weaknesses": weaknesses,
            "upgrade_suggestions": upgrades,
            "starter_ratings": [
                {"position": s.position, "player": s.card.player_name, "overall": s.card.overall_rating}
                for s in lineup.starters
            ],
        }

        logger.info(
            "Lineup analyzed: name=%s meta_score=%.3f chemistry=%.3f",
            lineup.name, meta_score, chemistry,
        )
        return analysis

    def _calculate_meta_score(self, lineup: MyTeamLineup) -> float:
        """Calculate how well a lineup fits the current meta (0-1)."""
        if not lineup.starters:
            return 0.0

        # Score based on card tiers
        tier_scores = []
        for slot in lineup.starters:
            tier_idx = CARD_TIER_ORDER.index(slot.card.tier) if slot.card.tier in CARD_TIER_ORDER else 0
            tier_scores.append(tier_idx / (len(CARD_TIER_ORDER) - 1))

        avg_tier = sum(tier_scores) / len(tier_scores) if tier_scores else 0.0

        # Score based on overall ratings
        avg_ovr = sum(s.card.overall_rating for s in lineup.starters) / max(len(lineup.starters), 1)
        ovr_score = max(0.0, (avg_ovr - 70) / 29)  # 70-99 range mapped to 0-1

        # Badge density
        total_badges = sum(len(s.card.badges) for s in lineup.starters)
        badge_score = min(1.0, total_badges / 50)  # ~10 badges per player = max

        return round(avg_tier * 0.3 + ovr_score * 0.5 + badge_score * 0.2, 3)

    def _find_closest_meta_archetype(self, lineup: MyTeamLineup) -> str:
        """Find the closest meta lineup archetype."""
        if not lineup.starters:
            return "unknown"

        avg_ovr = sum(s.card.overall_rating for s in lineup.starters) / len(lineup.starters)

        best_match = ""
        best_diff = float("inf")

        for name, meta in META_LINEUPS.items():
            meta_avg = sum(meta["positions"].values()) / len(meta["positions"])
            diff = abs(avg_ovr - meta_avg)
            if diff < best_diff:
                best_diff = diff
                best_match = name

        return best_match

    def _identify_weaknesses(self, lineup: MyTeamLineup) -> list[str]:
        """Identify lineup weaknesses."""
        weaknesses: list[str] = []

        if not lineup.starters:
            return ["No starters set"]

        # Check for low-tier cards
        for slot in lineup.starters:
            if slot.card.tier in ("emerald", "sapphire"):
                weaknesses.append(f"{slot.position.upper()} ({slot.card.player_name}) is below meta tier")

        # Check overall balance
        overalls = [s.card.overall_rating for s in lineup.starters]
        if max(overalls) - min(overalls) > 10:
            weaknesses.append("Large overall gap between starters — weakest link exploitable")

        # Check bench depth
        if len(lineup.bench) < 3:
            weaknesses.append("Thin bench — fatigue will be an issue in close games")

        if not weaknesses:
            weaknesses.append("No major weaknesses identified")

        return weaknesses

    def _suggest_upgrades(self, lineup: MyTeamLineup, weaknesses: list[str]) -> list[str]:
        """Suggest roster upgrades based on weaknesses."""
        suggestions: list[str] = []

        for slot in lineup.starters:
            tier_idx = CARD_TIER_ORDER.index(slot.card.tier) if slot.card.tier in CARD_TIER_ORDER else 0
            if tier_idx < 3:  # Below amethyst
                suggestions.append(
                    f"Upgrade {slot.position.upper()} — look for amethyst+ cards under 15K MT"
                )

        if len(lineup.bench) < 5:
            suggestions.append("Add bench depth — at least 5 reliable bench players")

        if not suggestions:
            suggestions.append("Lineup is competitive — focus on chemistry optimization")

        return suggestions

    # ------------------------------------------------------------------
    # Chemistry optimizer
    # ------------------------------------------------------------------

    def calculate_chemistry(self, lineup: MyTeamLineup) -> float:
        """Calculate total lineup chemistry based on chemistry rules.

        Evaluates all chemistry conditions and sums applicable boosts.
        """
        if not lineup.starters:
            return 0.0

        total_boost = 0.0

        # Position lock check
        natural_positions = all(
            slot.card.position.lower() == slot.position.lower()
            for slot in lineup.starters
        )
        if natural_positions:
            total_boost += 0.05

        # Dynamic duo check
        player_names = {s.card.player_name for s in lineup.starters}
        for p1, p2 in DYNAMIC_DUOS:
            if p1 in player_names and p2 in player_names:
                total_boost += 0.12
                break  # Only count best duo

        # Height balance check
        heights_ascending = True
        for i in range(len(lineup.starters) - 1):
            if lineup.starters[i].card.overall_rating > lineup.starters[i + 1].card.overall_rating:
                heights_ascending = False
                break
        if heights_ascending and len(lineup.starters) >= 3:
            total_boost += 0.03

        return min(total_boost + 0.5, 1.0)  # Base chemistry of 0.5

    def optimize_chemistry(self, lineup: MyTeamLineup) -> dict:
        """Recommend chemistry optimizations for a lineup.

        Suggests player swaps, position changes, and duo pairings.
        """
        current_chem = self.calculate_chemistry(lineup)
        recommendations: list[str] = []

        # Check for off-position players
        for slot in lineup.starters:
            if slot.card.position.lower() != slot.position.lower():
                recommendations.append(
                    f"Move {slot.card.player_name} to their natural {slot.card.position.upper()} position"
                )

        # Check for potential dynamic duos
        player_names = {s.card.player_name for s in lineup.starters}
        for p1, p2 in DYNAMIC_DUOS:
            if p1 in player_names and p2 not in player_names:
                recommendations.append(f"Add {p2} to activate Dynamic Duo with {p1}")
            elif p2 in player_names and p1 not in player_names:
                recommendations.append(f"Add {p1} to activate Dynamic Duo with {p2}")

        if not recommendations:
            recommendations.append("Chemistry is already optimized")

        return {
            "current_chemistry": round(current_chem, 3),
            "max_possible_chemistry": 1.0,
            "recommendations": recommendations,
            "active_boosts": [
                r["name"] for r in CHEMISTRY_RULES
                if current_chem >= 0.5 + r["boost"]
            ],
        }

    # ------------------------------------------------------------------
    # Auction house intelligence
    # ------------------------------------------------------------------

    def evaluate_card_value(self, card: MyTeamCard) -> AuctionSnipe:
        """Evaluate whether a card is undervalued on the auction house.

        Compares current price to estimated market value and computes profit margin.
        """
        value_range = CARD_TIER_VALUE_RANGE.get(card.tier, (1000, 5000))
        base_value = (value_range[0] + value_range[1]) // 2

        # Adjust for overall rating
        ovr_mult = 1.0 + (card.overall_rating - 80) * 0.03
        market_value = int(base_value * max(ovr_mult, 0.5))

        # Adjust for badges
        badge_bonus = len(card.badges) * 500
        market_value += badge_bonus

        profit = market_value - card.auction_value
        tax = int(market_value * 0.10)  # 10% auction tax
        net_profit = profit - tax

        confidence = 0.5
        if net_profit > market_value * 0.2:
            confidence = 0.85
        elif net_profit > 0:
            confidence = 0.65
        elif net_profit < -market_value * 0.1:
            confidence = 0.25

        reason = ""
        if net_profit > market_value * 0.3:
            reason = f"Major snipe — {card.player_name} is significantly undervalued"
        elif net_profit > 0:
            reason = f"Modest profit opportunity on {card.player_name}"
        else:
            reason = f"Overpriced — {card.player_name} is above market value"

        # Record for history
        self._market_history[card.card_id].append(card.auction_value)

        return AuctionSnipe(
            card=card,
            current_price=card.auction_value,
            market_value=market_value,
            profit_margin=net_profit,
            confidence=round(confidence, 3),
            reason=reason,
        )

    def get_market_trends(self, card_id: str) -> dict:
        """Get price trend data for a specific card."""
        history = self._market_history.get(card_id, [])
        if not history:
            return {"card_id": card_id, "trend": "no_data", "prices": []}

        avg = sum(history) / len(history)
        trend = "stable"
        if len(history) >= 3:
            recent_avg = sum(history[-3:]) / 3
            if recent_avg > avg * 1.1:
                trend = "rising"
            elif recent_avg < avg * 0.9:
                trend = "falling"

        return {
            "card_id": card_id,
            "trend": trend,
            "current_price": history[-1],
            "average_price": int(avg),
            "min_price": min(history),
            "max_price": max(history),
            "data_points": len(history),
        }


# Module-level singleton
myteam_intel = MyTeamIntel()
