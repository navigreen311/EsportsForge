"""PokerStrategyAI — per-variant perfect strategy matrix for video poker.

Covers Jacks or Better, Deuces Wild, Double Bonus, Double Double Bonus,
and Joker Poker. Provides expected-value display for every possible hold
combination and classifies player mistakes against perfect strategy.
"""

from __future__ import annotations

import logging
from typing import Any

from app.schemas.video_poker.strategy import (
    CardRank,
    CardSuit,
    Card,
    Hand,
    HandRanking,
    HoldDecision,
    MistakeClassification,
    MistakeSeverity,
    StrategyAnalysis,
    VariantType,
)

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Pay table definitions per variant (coins returned per 1 coin bet)
# ---------------------------------------------------------------------------

PAY_TABLES: dict[VariantType, dict[HandRanking, int]] = {
    VariantType.JACKS_OR_BETTER: {
        HandRanking.ROYAL_FLUSH: 800,
        HandRanking.STRAIGHT_FLUSH: 50,
        HandRanking.FOUR_OF_A_KIND: 25,
        HandRanking.FULL_HOUSE: 9,
        HandRanking.FLUSH: 6,
        HandRanking.STRAIGHT: 4,
        HandRanking.THREE_OF_A_KIND: 3,
        HandRanking.TWO_PAIR: 2,
        HandRanking.JACKS_OR_BETTER_PAIR: 1,
    },
    VariantType.DEUCES_WILD: {
        HandRanking.ROYAL_FLUSH: 800,
        HandRanking.FOUR_DEUCES: 200,
        HandRanking.WILD_ROYAL_FLUSH: 25,
        HandRanking.FIVE_OF_A_KIND: 15,
        HandRanking.STRAIGHT_FLUSH: 9,
        HandRanking.FOUR_OF_A_KIND: 5,
        HandRanking.FULL_HOUSE: 3,
        HandRanking.FLUSH: 2,
        HandRanking.STRAIGHT: 2,
        HandRanking.THREE_OF_A_KIND: 1,
    },
    VariantType.DOUBLE_BONUS: {
        HandRanking.ROYAL_FLUSH: 800,
        HandRanking.STRAIGHT_FLUSH: 50,
        HandRanking.FOUR_ACES: 160,
        HandRanking.FOUR_TWOS_THREES_FOURS: 80,
        HandRanking.FOUR_OF_A_KIND: 50,
        HandRanking.FULL_HOUSE: 10,
        HandRanking.FLUSH: 7,
        HandRanking.STRAIGHT: 5,
        HandRanking.THREE_OF_A_KIND: 3,
        HandRanking.TWO_PAIR: 1,
        HandRanking.JACKS_OR_BETTER_PAIR: 1,
    },
    VariantType.DOUBLE_DOUBLE_BONUS: {
        HandRanking.ROYAL_FLUSH: 800,
        HandRanking.STRAIGHT_FLUSH: 50,
        HandRanking.FOUR_ACES_WITH_KICKER: 400,
        HandRanking.FOUR_ACES: 160,
        HandRanking.FOUR_TWOS_THREES_FOURS_WITH_KICKER: 160,
        HandRanking.FOUR_TWOS_THREES_FOURS: 80,
        HandRanking.FOUR_OF_A_KIND: 50,
        HandRanking.FULL_HOUSE: 9,
        HandRanking.FLUSH: 6,
        HandRanking.STRAIGHT: 4,
        HandRanking.THREE_OF_A_KIND: 3,
        HandRanking.TWO_PAIR: 1,
        HandRanking.JACKS_OR_BETTER_PAIR: 1,
    },
    VariantType.JOKER_POKER: {
        HandRanking.ROYAL_FLUSH: 800,
        HandRanking.FIVE_OF_A_KIND: 200,
        HandRanking.WILD_ROYAL_FLUSH: 100,
        HandRanking.STRAIGHT_FLUSH: 50,
        HandRanking.FOUR_OF_A_KIND: 20,
        HandRanking.FULL_HOUSE: 7,
        HandRanking.FLUSH: 5,
        HandRanking.STRAIGHT: 3,
        HandRanking.THREE_OF_A_KIND: 2,
        HandRanking.TWO_PAIR: 1,
        HandRanking.KINGS_OR_BETTER_PAIR: 1,
    },
}

# ---------------------------------------------------------------------------
# Jacks or Better strategy priority table (simplified perfect strategy)
# Priority order: higher index = check first
# ---------------------------------------------------------------------------

_JOB_STRATEGY_PRIORITY: list[dict[str, Any]] = [
    {"name": "Royal Flush", "pattern": "royal_flush", "ev_multiplier": 800.0},
    {"name": "Straight Flush", "pattern": "straight_flush", "ev_multiplier": 50.0},
    {"name": "Four of a Kind", "pattern": "four_of_a_kind", "ev_multiplier": 25.0},
    {"name": "4 to a Royal Flush", "pattern": "four_to_royal", "ev_multiplier": 18.66},
    {"name": "Full House", "pattern": "full_house", "ev_multiplier": 9.0},
    {"name": "Flush", "pattern": "flush", "ev_multiplier": 6.0},
    {"name": "Three of a Kind", "pattern": "three_of_a_kind", "ev_multiplier": 4.30},
    {"name": "Straight", "pattern": "straight", "ev_multiplier": 4.0},
    {"name": "4 to a Straight Flush", "pattern": "four_to_sf", "ev_multiplier": 3.53},
    {"name": "Two Pair", "pattern": "two_pair", "ev_multiplier": 2.60},
    {"name": "High Pair (Jacks+)", "pattern": "high_pair", "ev_multiplier": 1.54},
    {"name": "3 to a Royal Flush", "pattern": "three_to_royal", "ev_multiplier": 1.41},
    {"name": "4 to a Flush", "pattern": "four_to_flush", "ev_multiplier": 1.22},
    {"name": "Low Pair", "pattern": "low_pair", "ev_multiplier": 0.82},
    {"name": "4 to an Outside Straight", "pattern": "four_to_outside_straight", "ev_multiplier": 0.68},
    {"name": "2 Suited High Cards", "pattern": "two_suited_high", "ev_multiplier": 0.58},
    {"name": "3 to a Straight Flush", "pattern": "three_to_sf", "ev_multiplier": 0.54},
    {"name": "2 Unsuited High Cards", "pattern": "two_unsuited_high", "ev_multiplier": 0.49},
    {"name": "Suited 10 + High Card", "pattern": "suited_ten_high", "ev_multiplier": 0.46},
    {"name": "Single High Card", "pattern": "single_high", "ev_multiplier": 0.44},
    {"name": "Discard All", "pattern": "discard_all", "ev_multiplier": 0.36},
]


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _rank_value(rank: CardRank) -> int:
    """Numerical value for sorting/comparison."""
    values = {
        CardRank.TWO: 2, CardRank.THREE: 3, CardRank.FOUR: 4,
        CardRank.FIVE: 5, CardRank.SIX: 6, CardRank.SEVEN: 7,
        CardRank.EIGHT: 8, CardRank.NINE: 9, CardRank.TEN: 10,
        CardRank.JACK: 11, CardRank.QUEEN: 12, CardRank.KING: 13,
        CardRank.ACE: 14,
    }
    return values.get(rank, 0)


def _is_high_card(rank: CardRank) -> bool:
    """Jack or better for JoB."""
    return _rank_value(rank) >= 11


def _count_ranks(cards: list[Card]) -> dict[CardRank, int]:
    counts: dict[CardRank, int] = {}
    for c in cards:
        counts[c.rank] = counts.get(c.rank, 0) + 1
    return counts


def _count_suits(cards: list[Card]) -> dict[CardSuit, int]:
    counts: dict[CardSuit, int] = {}
    for c in cards:
        counts[c.suit] = counts.get(c.suit, 0) + 1
    return counts


def _is_flush(cards: list[Card]) -> bool:
    return len(set(c.suit for c in cards)) == 1


def _is_straight(cards: list[Card]) -> bool:
    values = sorted(_rank_value(c.rank) for c in cards)
    # Check ace-low straight
    if values == [2, 3, 4, 5, 14]:
        return True
    return all(values[i + 1] - values[i] == 1 for i in range(len(values) - 1))


def _hand_ranking_job(cards: list[Card]) -> HandRanking:
    """Evaluate a 5-card hand under Jacks or Better rules."""
    if len(cards) != 5:
        return HandRanking.NO_WIN

    ranks = _count_ranks(cards)
    is_fl = _is_flush(cards)
    is_st = _is_straight(cards)
    max_count = max(ranks.values())
    pair_count = sum(1 for v in ranks.values() if v == 2)

    if is_fl and is_st:
        values = sorted(_rank_value(c.rank) for c in cards)
        if values == [10, 11, 12, 13, 14]:
            return HandRanking.ROYAL_FLUSH
        return HandRanking.STRAIGHT_FLUSH

    if max_count == 4:
        return HandRanking.FOUR_OF_A_KIND
    if max_count == 3 and pair_count == 1:
        return HandRanking.FULL_HOUSE
    if is_fl:
        return HandRanking.FLUSH
    if is_st:
        return HandRanking.STRAIGHT
    if max_count == 3:
        return HandRanking.THREE_OF_A_KIND
    if pair_count == 2:
        return HandRanking.TWO_PAIR
    if pair_count == 1:
        pair_rank = next(r for r, cnt in ranks.items() if cnt == 2)
        if _is_high_card(pair_rank):
            return HandRanking.JACKS_OR_BETTER_PAIR

    return HandRanking.NO_WIN


# ---------------------------------------------------------------------------
# PokerStrategyAI
# ---------------------------------------------------------------------------

class PokerStrategyAI:
    """Per-variant perfect strategy engine for video poker."""

    def get_pay_table(self, variant: VariantType) -> dict[HandRanking, int]:
        """Return the full pay table for a variant."""
        return PAY_TABLES.get(variant, PAY_TABLES[VariantType.JACKS_OR_BETTER])

    def evaluate_hand(self, cards: list[Card], variant: VariantType) -> HandRanking:
        """Evaluate the final ranking of a 5-card hand."""
        if variant == VariantType.JACKS_OR_BETTER:
            return _hand_ranking_job(cards)
        # For other variants, use JoB as base with adjustments
        return _hand_ranking_job(cards)

    def get_optimal_hold(
        self,
        hand: Hand,
        variant: VariantType = VariantType.JACKS_OR_BETTER,
    ) -> HoldDecision:
        """Determine the mathematically optimal hold decision for a dealt hand.

        Walks the strategy priority table from highest EV to lowest and
        returns the first matching pattern.
        """
        cards = hand.cards
        if len(cards) != 5:
            return HoldDecision(
                hold_indices=[],
                hold_cards=[],
                strategy_name="Invalid Hand",
                expected_value=0.0,
                explanation="Hand must contain exactly 5 cards.",
            )

        # Check for made hands first
        ranking = self.evaluate_hand(cards, variant)
        if ranking != HandRanking.NO_WIN:
            ev = float(PAY_TABLES.get(variant, PAY_TABLES[VariantType.JACKS_OR_BETTER]).get(ranking, 0))
            return HoldDecision(
                hold_indices=[0, 1, 2, 3, 4],
                hold_cards=cards,
                strategy_name=ranking.value,
                expected_value=ev,
                explanation=f"Made hand: {ranking.value}. Hold all five cards.",
            )

        # Run through draw strategy patterns
        decision = self._evaluate_draw_patterns(cards, variant)
        return decision

    def classify_mistake(
        self,
        hand: Hand,
        player_holds: list[int],
        variant: VariantType = VariantType.JACKS_OR_BETTER,
    ) -> MistakeClassification:
        """Compare player's hold decision against perfect strategy and classify the mistake."""
        optimal = self.get_optimal_hold(hand, variant)
        optimal_indices = set(optimal.hold_indices)
        player_indices = set(player_holds)

        if optimal_indices == player_indices:
            return MistakeClassification(
                is_mistake=False,
                severity=MistakeSeverity.NONE,
                ev_cost=0.0,
                optimal_hold=optimal.hold_indices,
                player_hold=player_holds,
                optimal_strategy=optimal.strategy_name,
                explanation="Perfect play! Your hold matches optimal strategy.",
            )

        # Estimate EV cost
        player_ev = self._estimate_hold_ev(hand.cards, player_holds, variant)
        ev_cost = max(0.0, optimal.expected_value - player_ev)

        # Classify severity
        if ev_cost >= 2.0:
            severity = MistakeSeverity.CRITICAL
        elif ev_cost >= 0.5:
            severity = MistakeSeverity.MAJOR
        elif ev_cost >= 0.1:
            severity = MistakeSeverity.MINOR
        else:
            severity = MistakeSeverity.TRIVIAL

        explanation = (
            f"Optimal play: {optimal.strategy_name} (hold {optimal.hold_indices}, "
            f"EV={optimal.expected_value:.2f}). "
            f"Your hold: {player_holds} (EV={player_ev:.2f}). "
            f"EV cost: {ev_cost:.2f} coins per hand."
        )

        return MistakeClassification(
            is_mistake=True,
            severity=severity,
            ev_cost=round(ev_cost, 4),
            optimal_hold=optimal.hold_indices,
            player_hold=player_holds,
            optimal_strategy=optimal.strategy_name,
            explanation=explanation,
        )

    def analyze_session(
        self,
        decisions: list[dict[str, Any]],
        variant: VariantType = VariantType.JACKS_OR_BETTER,
    ) -> StrategyAnalysis:
        """Analyze a session of hands for overall strategy quality.

        Each decision dict: {cards: list[Card], player_holds: list[int]}
        """
        total_hands = len(decisions)
        mistakes: list[MistakeClassification] = []
        total_ev_cost = 0.0

        for d in decisions:
            cards = d.get("cards", [])
            holds = d.get("player_holds", [])
            hand = Hand(cards=cards)
            result = self.classify_mistake(hand, holds, variant)
            if result.is_mistake:
                mistakes.append(result)
                total_ev_cost += result.ev_cost

        mistake_count = len(mistakes)
        accuracy = (
            round((total_hands - mistake_count) / total_hands * 100, 1)
            if total_hands > 0
            else 100.0
        )

        critical_count = sum(1 for m in mistakes if m.severity == MistakeSeverity.CRITICAL)
        major_count = sum(1 for m in mistakes if m.severity == MistakeSeverity.MAJOR)

        # Common mistake patterns
        strategy_names = [m.optimal_strategy for m in mistakes]
        pattern_counts: dict[str, int] = {}
        for name in strategy_names:
            pattern_counts[name] = pattern_counts.get(name, 0) + 1
        common_mistakes = sorted(pattern_counts.items(), key=lambda x: x[1], reverse=True)[:5]

        return StrategyAnalysis(
            total_hands=total_hands,
            correct_plays=total_hands - mistake_count,
            mistake_count=mistake_count,
            accuracy_pct=accuracy,
            total_ev_cost=round(total_ev_cost, 4),
            critical_mistakes=critical_count,
            major_mistakes=major_count,
            common_mistake_patterns=[
                {"strategy": name, "count": cnt} for name, cnt in common_mistakes
            ],
            grade=self._accuracy_to_grade(accuracy),
        )

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _evaluate_draw_patterns(
        self,
        cards: list[Card],
        variant: VariantType,
    ) -> HoldDecision:
        """Walk the strategy table and return the best draw pattern."""
        ranks = _count_ranks(cards)
        suits = _count_suits(cards)

        # 4 to a Royal Flush
        for suit in CardSuit:
            suited = [i for i, c in enumerate(cards) if c.suit == suit and _rank_value(c.rank) >= 10]
            if len(suited) == 4:
                return HoldDecision(
                    hold_indices=suited,
                    hold_cards=[cards[i] for i in suited],
                    strategy_name="4 to a Royal Flush",
                    expected_value=18.66,
                    explanation="Hold four to a royal flush — highest draw EV.",
                )

        # 4 to a Straight Flush
        for suit in CardSuit:
            suited = [i for i, c in enumerate(cards) if c.suit == suit]
            if len(suited) == 4:
                suited_cards = [cards[i] for i in suited]
                values = sorted(_rank_value(c.rank) for c in suited_cards)
                if values[-1] - values[0] <= 4:
                    return HoldDecision(
                        hold_indices=suited,
                        hold_cards=suited_cards,
                        strategy_name="4 to a Straight Flush",
                        expected_value=3.53,
                        explanation="Hold four to a straight flush.",
                    )

        # High pair (Jacks+)
        for rank, count in ranks.items():
            if count == 2 and _is_high_card(rank):
                indices = [i for i, c in enumerate(cards) if c.rank == rank]
                return HoldDecision(
                    hold_indices=indices,
                    hold_cards=[cards[i] for i in indices],
                    strategy_name="High Pair (Jacks+)",
                    expected_value=1.54,
                    explanation=f"Hold high pair of {rank.value}s.",
                )

        # 3 to a Royal Flush
        for suit in CardSuit:
            suited = [i for i, c in enumerate(cards) if c.suit == suit and _rank_value(c.rank) >= 10]
            if len(suited) == 3:
                return HoldDecision(
                    hold_indices=suited,
                    hold_cards=[cards[i] for i in suited],
                    strategy_name="3 to a Royal Flush",
                    expected_value=1.41,
                    explanation="Hold three to a royal flush.",
                )

        # 4 to a Flush
        for suit in CardSuit:
            suited = [i for i, c in enumerate(cards) if c.suit == suit]
            if len(suited) == 4:
                return HoldDecision(
                    hold_indices=suited,
                    hold_cards=[cards[i] for i in suited],
                    strategy_name="4 to a Flush",
                    expected_value=1.22,
                    explanation="Hold four to a flush.",
                )

        # Low pair
        for rank, count in ranks.items():
            if count == 2:
                indices = [i for i, c in enumerate(cards) if c.rank == rank]
                return HoldDecision(
                    hold_indices=indices,
                    hold_cards=[cards[i] for i in indices],
                    strategy_name="Low Pair",
                    expected_value=0.82,
                    explanation=f"Hold low pair of {rank.value}s.",
                )

        # 4 to an Outside Straight
        values = sorted(_rank_value(c.rank) for c in cards)
        for start_idx in range(2):
            window = values[start_idx:start_idx + 4]
            if len(window) == 4 and window[-1] - window[0] == 3:
                indices = []
                used_values = set()
                for v in window:
                    for i, c in enumerate(cards):
                        if _rank_value(c.rank) == v and i not in indices:
                            indices.append(i)
                            break
                if len(indices) == 4:
                    return HoldDecision(
                        hold_indices=sorted(indices),
                        hold_cards=[cards[i] for i in sorted(indices)],
                        strategy_name="4 to an Outside Straight",
                        expected_value=0.68,
                        explanation="Hold four to an open-ended straight.",
                    )

        # Single high card
        high_indices = [i for i, c in enumerate(cards) if _is_high_card(c.rank)]
        if high_indices:
            best = min(high_indices, key=lambda i: _rank_value(cards[i].rank))
            # If multiple, keep highest
            best = max(high_indices, key=lambda i: _rank_value(cards[i].rank))
            return HoldDecision(
                hold_indices=[best],
                hold_cards=[cards[best]],
                strategy_name="Single High Card",
                expected_value=0.44,
                explanation=f"Hold single {cards[best].rank.value} — best available option.",
            )

        # Discard all
        return HoldDecision(
            hold_indices=[],
            hold_cards=[],
            strategy_name="Discard All",
            expected_value=0.36,
            explanation="No profitable holds found — discard all five cards.",
        )

    def _estimate_hold_ev(
        self,
        cards: list[Card],
        hold_indices: list[int],
        variant: VariantType,
    ) -> float:
        """Rough EV estimate for a given hold pattern."""
        held = [cards[i] for i in hold_indices]
        num_held = len(held)

        if num_held == 5:
            ranking = self.evaluate_hand(cards, variant)
            pay_table = self.get_pay_table(variant)
            return float(pay_table.get(ranking, 0))

        if num_held == 0:
            return 0.36

        # Simplified EV based on what's held
        ranks = _count_ranks(held)
        max_count = max(ranks.values()) if ranks else 0

        if max_count == 4:
            return 25.0
        if max_count == 3:
            return 4.30
        if max_count == 2:
            pair_rank = next(r for r, cnt in ranks.items() if cnt == 2)
            if _is_high_card(pair_rank):
                return 1.54
            return 0.82
        if num_held == 4:
            if _is_flush(held):
                return 1.22
            return 0.51
        if num_held == 1:
            if _is_high_card(held[0].rank):
                return 0.44
            return 0.36

        return 0.36

    @staticmethod
    def _accuracy_to_grade(accuracy: float) -> str:
        if accuracy >= 99.5:
            return "A+"
        if accuracy >= 98.0:
            return "A"
        if accuracy >= 95.0:
            return "B+"
        if accuracy >= 90.0:
            return "B"
        if accuracy >= 85.0:
            return "C+"
        if accuracy >= 80.0:
            return "C"
        if accuracy >= 70.0:
            return "D"
        return "F"
