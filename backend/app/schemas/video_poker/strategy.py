"""Pydantic schemas for video poker strategy analysis."""

from __future__ import annotations

from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------

class VariantType(str, Enum):
    """Supported video poker variants."""
    JACKS_OR_BETTER = "jacks_or_better"
    DEUCES_WILD = "deuces_wild"
    DOUBLE_BONUS = "double_bonus"
    DOUBLE_DOUBLE_BONUS = "double_double_bonus"
    JOKER_POKER = "joker_poker"


class CardRank(str, Enum):
    """Standard card ranks."""
    TWO = "2"
    THREE = "3"
    FOUR = "4"
    FIVE = "5"
    SIX = "6"
    SEVEN = "7"
    EIGHT = "8"
    NINE = "9"
    TEN = "10"
    JACK = "J"
    QUEEN = "Q"
    KING = "K"
    ACE = "A"


class CardSuit(str, Enum):
    """Standard card suits."""
    HEARTS = "hearts"
    DIAMONDS = "diamonds"
    CLUBS = "clubs"
    SPADES = "spades"


class HandRanking(str, Enum):
    """All possible video poker hand rankings across variants."""
    ROYAL_FLUSH = "royal_flush"
    STRAIGHT_FLUSH = "straight_flush"
    FOUR_OF_A_KIND = "four_of_a_kind"
    FULL_HOUSE = "full_house"
    FLUSH = "flush"
    STRAIGHT = "straight"
    THREE_OF_A_KIND = "three_of_a_kind"
    TWO_PAIR = "two_pair"
    JACKS_OR_BETTER_PAIR = "jacks_or_better_pair"
    KINGS_OR_BETTER_PAIR = "kings_or_better_pair"
    NO_WIN = "no_win"
    # Deuces Wild specific
    FOUR_DEUCES = "four_deuces"
    WILD_ROYAL_FLUSH = "wild_royal_flush"
    FIVE_OF_A_KIND = "five_of_a_kind"
    # Double Bonus specific
    FOUR_ACES = "four_aces"
    FOUR_TWOS_THREES_FOURS = "four_2s_3s_4s"
    # Double Double Bonus specific
    FOUR_ACES_WITH_KICKER = "four_aces_with_kicker"
    FOUR_TWOS_THREES_FOURS_WITH_KICKER = "four_2s_3s_4s_with_kicker"


class MistakeSeverity(str, Enum):
    """Classification of strategy mistakes by EV cost."""
    NONE = "none"
    TRIVIAL = "trivial"
    MINOR = "minor"
    MAJOR = "major"
    CRITICAL = "critical"


# ---------------------------------------------------------------------------
# Core Models
# ---------------------------------------------------------------------------

class Card(BaseModel):
    """A single playing card."""
    rank: CardRank
    suit: CardSuit

    def __str__(self) -> str:
        return f"{self.rank.value}{self.suit.value[0].upper()}"


class Hand(BaseModel):
    """A 5-card video poker hand."""
    cards: list[Card] = Field(..., min_length=5, max_length=5)


class HoldDecision(BaseModel):
    """Optimal hold recommendation for a dealt hand."""
    hold_indices: list[int] = Field(..., description="0-indexed positions to hold")
    hold_cards: list[Card]
    strategy_name: str
    expected_value: float = Field(..., description="Expected value in bet units")
    explanation: str


class MistakeClassification(BaseModel):
    """Analysis of a player's hold decision vs. optimal strategy."""
    is_mistake: bool
    severity: MistakeSeverity
    ev_cost: float = Field(..., ge=0.0, description="EV cost in bet units per hand")
    optimal_hold: list[int]
    player_hold: list[int]
    optimal_strategy: str
    explanation: str


class StrategyAnalysis(BaseModel):
    """Session-level strategy analysis."""
    total_hands: int
    correct_plays: int
    mistake_count: int
    accuracy_pct: float = Field(..., ge=0.0, le=100.0)
    total_ev_cost: float = Field(..., ge=0.0)
    critical_mistakes: int
    major_mistakes: int
    common_mistake_patterns: list[dict[str, Any]]
    grade: str


# ---------------------------------------------------------------------------
# Request / Response
# ---------------------------------------------------------------------------

class OptimalHoldRequest(BaseModel):
    """Request for optimal hold analysis."""
    hand: Hand
    variant: VariantType = VariantType.JACKS_OR_BETTER


class OptimalHoldResponse(BaseModel):
    """Response with optimal hold decision."""
    decision: HoldDecision
    variant: VariantType
    pay_table: dict[str, int]


class MistakeCheckRequest(BaseModel):
    """Request to check a player's hold decision."""
    hand: Hand
    player_holds: list[int] = Field(..., description="0-indexed card positions the player held")
    variant: VariantType = VariantType.JACKS_OR_BETTER


class MistakeCheckResponse(BaseModel):
    """Response with mistake classification."""
    classification: MistakeClassification


class SessionAnalysisRequest(BaseModel):
    """Request for session strategy analysis."""
    decisions: list[dict[str, Any]] = Field(
        ..., description="List of {cards, player_holds} dicts"
    )
    variant: VariantType = VariantType.JACKS_OR_BETTER


class SessionAnalysisResponse(BaseModel):
    """Response with session-level strategy analysis."""
    analysis: StrategyAnalysis
