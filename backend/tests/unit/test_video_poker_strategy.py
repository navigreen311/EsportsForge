"""Unit tests for PokerStrategyAI — video poker perfect strategy engine."""

from __future__ import annotations

import pytest

from app.schemas.video_poker.strategy import (
    Card,
    CardRank,
    CardSuit,
    Hand,
    HandRanking,
    MistakeSeverity,
    VariantType,
)
from app.services.agents.video_poker.poker_strategy import PokerStrategyAI


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

def _card(rank: str, suit: str) -> Card:
    """Shorthand card factory. rank='A','K',etc. suit='h','d','c','s'."""
    suit_map = {"h": CardSuit.HEARTS, "d": CardSuit.DIAMONDS, "c": CardSuit.CLUBS, "s": CardSuit.SPADES}
    return Card(rank=CardRank(rank), suit=suit_map[suit])


@pytest.fixture
def ai() -> PokerStrategyAI:
    return PokerStrategyAI()


# ---------------------------------------------------------------------------
# Hand Evaluation
# ---------------------------------------------------------------------------

class TestHandEvaluation:
    def test_royal_flush(self, ai: PokerStrategyAI) -> None:
        cards = [_card("10", "h"), _card("J", "h"), _card("Q", "h"), _card("K", "h"), _card("A", "h")]
        assert ai.evaluate_hand(cards, VariantType.JACKS_OR_BETTER) == HandRanking.ROYAL_FLUSH

    def test_straight_flush(self, ai: PokerStrategyAI) -> None:
        cards = [_card("5", "s"), _card("6", "s"), _card("7", "s"), _card("8", "s"), _card("9", "s")]
        assert ai.evaluate_hand(cards, VariantType.JACKS_OR_BETTER) == HandRanking.STRAIGHT_FLUSH

    def test_four_of_a_kind(self, ai: PokerStrategyAI) -> None:
        cards = [_card("K", "h"), _card("K", "d"), _card("K", "c"), _card("K", "s"), _card("3", "h")]
        assert ai.evaluate_hand(cards, VariantType.JACKS_OR_BETTER) == HandRanking.FOUR_OF_A_KIND

    def test_full_house(self, ai: PokerStrategyAI) -> None:
        cards = [_card("J", "h"), _card("J", "d"), _card("J", "c"), _card("8", "s"), _card("8", "h")]
        assert ai.evaluate_hand(cards, VariantType.JACKS_OR_BETTER) == HandRanking.FULL_HOUSE

    def test_flush(self, ai: PokerStrategyAI) -> None:
        cards = [_card("2", "d"), _card("5", "d"), _card("8", "d"), _card("J", "d"), _card("A", "d")]
        assert ai.evaluate_hand(cards, VariantType.JACKS_OR_BETTER) == HandRanking.FLUSH

    def test_straight(self, ai: PokerStrategyAI) -> None:
        cards = [_card("4", "h"), _card("5", "d"), _card("6", "c"), _card("7", "s"), _card("8", "h")]
        assert ai.evaluate_hand(cards, VariantType.JACKS_OR_BETTER) == HandRanking.STRAIGHT

    def test_ace_low_straight(self, ai: PokerStrategyAI) -> None:
        cards = [_card("A", "h"), _card("2", "d"), _card("3", "c"), _card("4", "s"), _card("5", "h")]
        assert ai.evaluate_hand(cards, VariantType.JACKS_OR_BETTER) == HandRanking.STRAIGHT

    def test_three_of_a_kind(self, ai: PokerStrategyAI) -> None:
        cards = [_card("9", "h"), _card("9", "d"), _card("9", "c"), _card("3", "s"), _card("7", "h")]
        assert ai.evaluate_hand(cards, VariantType.JACKS_OR_BETTER) == HandRanking.THREE_OF_A_KIND

    def test_two_pair(self, ai: PokerStrategyAI) -> None:
        cards = [_card("J", "h"), _card("J", "d"), _card("5", "c"), _card("5", "s"), _card("A", "h")]
        assert ai.evaluate_hand(cards, VariantType.JACKS_OR_BETTER) == HandRanking.TWO_PAIR

    def test_jacks_or_better_pair(self, ai: PokerStrategyAI) -> None:
        cards = [_card("Q", "h"), _card("Q", "d"), _card("3", "c"), _card("7", "s"), _card("9", "h")]
        assert ai.evaluate_hand(cards, VariantType.JACKS_OR_BETTER) == HandRanking.JACKS_OR_BETTER_PAIR

    def test_low_pair_no_win(self, ai: PokerStrategyAI) -> None:
        cards = [_card("5", "h"), _card("5", "d"), _card("3", "c"), _card("7", "s"), _card("9", "h")]
        assert ai.evaluate_hand(cards, VariantType.JACKS_OR_BETTER) == HandRanking.NO_WIN

    def test_no_win_junk(self, ai: PokerStrategyAI) -> None:
        cards = [_card("2", "h"), _card("5", "d"), _card("8", "c"), _card("J", "s"), _card("3", "h")]
        assert ai.evaluate_hand(cards, VariantType.JACKS_OR_BETTER) == HandRanking.NO_WIN


# ---------------------------------------------------------------------------
# Optimal Hold
# ---------------------------------------------------------------------------

class TestOptimalHold:
    def test_hold_all_for_made_hand(self, ai: PokerStrategyAI) -> None:
        """Made flush should hold all 5 cards."""
        hand = Hand(cards=[
            _card("2", "d"), _card("5", "d"), _card("8", "d"),
            _card("J", "d"), _card("A", "d"),
        ])
        decision = ai.get_optimal_hold(hand)
        assert decision.hold_indices == [0, 1, 2, 3, 4]
        assert decision.expected_value == 6.0

    def test_hold_high_pair(self, ai: PokerStrategyAI) -> None:
        """Pair of Queens should be held."""
        hand = Hand(cards=[
            _card("Q", "h"), _card("Q", "d"), _card("3", "c"),
            _card("7", "s"), _card("9", "h"),
        ])
        decision = ai.get_optimal_hold(hand)
        assert set(decision.hold_indices) == {0, 1}
        assert decision.strategy_name == "jacks_or_better_pair"

    def test_hold_low_pair(self, ai: PokerStrategyAI) -> None:
        """Low pair of 5s should be held over nothing."""
        hand = Hand(cards=[
            _card("5", "h"), _card("5", "d"), _card("3", "c"),
            _card("9", "s"), _card("2", "h"),
        ])
        decision = ai.get_optimal_hold(hand)
        assert set(decision.hold_indices) == {0, 1}
        assert decision.strategy_name == "Low Pair"

    def test_discard_all_junk(self, ai: PokerStrategyAI) -> None:
        """Complete junk with no high cards should discard all."""
        hand = Hand(cards=[
            _card("2", "h"), _card("4", "d"), _card("6", "c"),
            _card("8", "s"), _card("10", "h"),
        ])
        decision = ai.get_optimal_hold(hand)
        # Should either discard all or hold a single card
        assert len(decision.hold_indices) <= 1

    def test_four_to_flush(self, ai: PokerStrategyAI) -> None:
        """Four cards of same suit — hold the four suited cards."""
        hand = Hand(cards=[
            _card("3", "h"), _card("7", "h"), _card("J", "h"),
            _card("A", "h"), _card("5", "d"),
        ])
        decision = ai.get_optimal_hold(hand)
        assert len(decision.hold_indices) == 4
        assert 4 not in decision.hold_indices  # The diamond should be discarded


# ---------------------------------------------------------------------------
# Mistake Classification
# ---------------------------------------------------------------------------

class TestMistakeClassification:
    def test_perfect_play_no_mistake(self, ai: PokerStrategyAI) -> None:
        hand = Hand(cards=[
            _card("Q", "h"), _card("Q", "d"), _card("3", "c"),
            _card("7", "s"), _card("9", "h"),
        ])
        optimal = ai.get_optimal_hold(hand)
        result = ai.classify_mistake(hand, optimal.hold_indices)
        assert result.is_mistake is False
        assert result.severity == MistakeSeverity.NONE
        assert result.ev_cost == 0.0

    def test_holding_junk_is_mistake(self, ai: PokerStrategyAI) -> None:
        """Holding random cards instead of the pair is a mistake."""
        hand = Hand(cards=[
            _card("Q", "h"), _card("Q", "d"), _card("3", "c"),
            _card("7", "s"), _card("9", "h"),
        ])
        result = ai.classify_mistake(hand, [2, 3, 4])
        assert result.is_mistake is True
        assert result.ev_cost > 0


# ---------------------------------------------------------------------------
# Session Analysis
# ---------------------------------------------------------------------------

class TestSessionAnalysis:
    def test_perfect_session(self, ai: PokerStrategyAI) -> None:
        """Session with all correct plays should get A+ grade."""
        # Create simple decisions with pair of Jacks (optimal: hold the pair)
        cards = [
            _card("J", "h"), _card("J", "d"), _card("3", "c"),
            _card("7", "s"), _card("9", "h"),
        ]
        decisions = [{"cards": cards, "player_holds": [0, 1]} for _ in range(10)]
        analysis = ai.analyze_session(decisions)
        assert analysis.mistake_count == 0
        assert analysis.accuracy_pct == 100.0
        assert analysis.grade == "A+"

    def test_session_with_mistakes(self, ai: PokerStrategyAI) -> None:
        cards = [
            _card("J", "h"), _card("J", "d"), _card("3", "c"),
            _card("7", "s"), _card("9", "h"),
        ]
        # 8 correct, 2 wrong (holding junk instead of pair)
        good = [{"cards": cards, "player_holds": [0, 1]} for _ in range(8)]
        bad = [{"cards": cards, "player_holds": [2, 3, 4]} for _ in range(2)]
        analysis = ai.analyze_session(good + bad)
        assert analysis.mistake_count == 2
        assert analysis.total_hands == 10
        assert analysis.accuracy_pct == 80.0


# ---------------------------------------------------------------------------
# Pay Table
# ---------------------------------------------------------------------------

class TestPayTable:
    def test_jacks_or_better_pay_table(self, ai: PokerStrategyAI) -> None:
        pay_table = ai.get_pay_table(VariantType.JACKS_OR_BETTER)
        assert pay_table[HandRanking.ROYAL_FLUSH] == 800
        assert pay_table[HandRanking.FULL_HOUSE] == 9
        assert pay_table[HandRanking.FLUSH] == 6

    def test_deuces_wild_pay_table(self, ai: PokerStrategyAI) -> None:
        pay_table = ai.get_pay_table(VariantType.DEUCES_WILD)
        assert pay_table[HandRanking.FOUR_DEUCES] == 200
