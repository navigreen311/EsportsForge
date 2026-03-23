"""AdaptAI — between-series adjustment intelligence.

Analyzes series performance and produces ONE decisive recommendation
for what to change between series. Designed for the 5-minute break
between competitive sets: fast, focused, high-impact.
"""

from __future__ import annotations

import logging
from datetime import datetime
from uuid import uuid4

from app.schemas.drill import (
    AdaptRecommendation,
    SeriesAnalysis,
)

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

_MIN_GAMES_FOR_ANALYSIS = 1
_HIGH_IMPACT_THRESHOLD = 0.6
_PATTERN_FREQUENCY_THRESHOLD = 0.3

# ---------------------------------------------------------------------------
# In-memory store
# ---------------------------------------------------------------------------

# user_id -> list of past recommendations
_recommendation_history: dict[str, list[AdaptRecommendation]] = {}


class AdaptAI:
    """Between-series adaptation engine.

    Analyzes series data, identifies the highest-impact adjustment,
    and delivers a single, time-compressed recommendation that a
    player can execute in a 5-minute break.
    """

    def __init__(self) -> None:
        pass

    # ------------------------------------------------------------------
    # Core API
    # ------------------------------------------------------------------

    def get_between_series_adjustment(
        self,
        user_id: str,
        series_data: dict,
    ) -> AdaptRecommendation:
        """Produce ONE decisive between-series adjustment.

        Parameters
        ----------
        user_id:
            Player identifier.
        series_data:
            Dict containing game results, plays, tendencies, etc.
            Expected keys: 'games', 'opponent_id', 'title'.

        Returns
        -------
        AdaptRecommendation
            The single highest-impact adjustment to make.
        """
        analysis = self.analyze_series(series_data)
        recommendation = self.generate_quick_adjustment(analysis)
        recommendation.user_id = user_id

        # Store for history
        _recommendation_history.setdefault(user_id, []).append(recommendation)

        logger.info(
            "AdaptAI recommendation for %s: '%s' (impact=%.2f)",
            user_id, recommendation.adjustment, recommendation.expected_impact,
        )
        return recommendation

    # ------------------------------------------------------------------
    # Analysis
    # ------------------------------------------------------------------

    def analyze_series(self, series_data: dict) -> SeriesAnalysis:
        """Analyze what worked and what didn't in a series.

        Parameters
        ----------
        series_data:
            Dict with 'games' list, each game containing 'result',
            'plays', 'score', etc.

        Returns
        -------
        SeriesAnalysis
            Breakdown of strengths, weaknesses, and patterns.
        """
        games = series_data.get("games", [])
        series_id = series_data.get("series_id", "")

        wins = sum(1 for g in games if g.get("result") == "win")
        losses = sum(1 for g in games if g.get("result") == "loss")

        # Extract patterns from games
        strengths: list[str] = []
        weaknesses: list[str] = []
        opponent_patterns: list[str] = []
        momentum_shifts: list[str] = []
        key_moments: list[str] = []

        # Aggregate play data across games
        all_plays = []
        for game in games:
            all_plays.extend(game.get("plays", []))
            # Extract game-level insights
            if game.get("strengths"):
                strengths.extend(game["strengths"])
            if game.get("weaknesses"):
                weaknesses.extend(game["weaknesses"])
            if game.get("opponent_patterns"):
                opponent_patterns.extend(game["opponent_patterns"])
            if game.get("momentum_shifts"):
                momentum_shifts.extend(game["momentum_shifts"])
            if game.get("key_moments"):
                key_moments.extend(game["key_moments"])

        # Auto-detect patterns from play data
        if all_plays:
            play_results = [p.get("result", "neutral") for p in all_plays]
            success_count = sum(1 for r in play_results if r == "success")
            fail_count = sum(1 for r in play_results if r == "fail")

            if fail_count > success_count and not weaknesses:
                weaknesses.append("More failed plays than successful ones")
            if success_count > fail_count and not strengths:
                strengths.append("Positive play success rate")

            # Detect repeated play types
            play_types = [p.get("type", "unknown") for p in all_plays]
            type_counts: dict[str, int] = {}
            for pt in play_types:
                type_counts[pt] = type_counts.get(pt, 0) + 1

            total_plays = len(all_plays)
            for pt, count in type_counts.items():
                if count / total_plays > _PATTERN_FREQUENCY_THRESHOLD:
                    opponent_patterns.append(
                        f"Opponent frequently uses '{pt}' ({count}/{total_plays} plays)"
                    )

        # Fallback analysis if no data provided
        if not weaknesses and losses > 0:
            weaknesses.append("Lost games without identified cause — review film")
        if not strengths and wins > 0:
            strengths.append("Won games — identify repeatable patterns")

        return SeriesAnalysis(
            series_id=series_id,
            games_played=len(games),
            wins=wins,
            losses=losses,
            strengths_exploited=strengths,
            weaknesses_exposed=weaknesses,
            opponent_patterns=opponent_patterns,
            momentum_shifts=momentum_shifts,
            key_moments=key_moments,
        )

    # ------------------------------------------------------------------
    # Quick adjustment generation
    # ------------------------------------------------------------------

    def generate_quick_adjustment(
        self,
        analysis: SeriesAnalysis,
    ) -> AdaptRecommendation:
        """Generate a time-compressed adjustment for a 5-minute break.

        Picks the single highest-impact change based on the analysis and
        delivers it in an immediately actionable format.

        Parameters
        ----------
        analysis:
            Series analysis from :meth:`analyze_series`.

        Returns
        -------
        AdaptRecommendation
            ONE decisive adjustment.
        """
        adjustment = "Maintain current gameplan"
        reasoning = "No significant changes needed"
        implementation = "Continue executing your current strategy"
        expected_impact = 0.1
        time_to_implement = "immediate"

        # Priority 1: Counter opponent patterns
        if analysis.opponent_patterns:
            pattern = analysis.opponent_patterns[0]
            adjustment = f"Counter opponent pattern: {pattern}"
            reasoning = (
                f"Opponent is predictable — exploit this pattern for an advantage."
            )
            implementation = (
                f"Pre-read the opponent's tendency and have your counter ready. "
                f"Identified pattern: {pattern}."
            )
            expected_impact = 0.7
            time_to_implement = "immediate"

        # Priority 2: Fix exposed weakness
        elif analysis.weaknesses_exposed:
            weakness = analysis.weaknesses_exposed[0]
            adjustment = f"Shore up exposed weakness: {weakness}"
            reasoning = (
                f"This weakness cost you games in the series. "
                f"Fixing it is the highest-ROI change."
            )
            implementation = (
                f"Avoid situations that trigger this weakness, or change your "
                f"approach to handle it differently. Weakness: {weakness}."
            )
            expected_impact = 0.6
            time_to_implement = "5 minutes"

        # Priority 3: Double down on strengths
        elif analysis.strengths_exploited:
            strength = analysis.strengths_exploited[0]
            adjustment = f"Double down on what's working: {strength}"
            reasoning = (
                f"This is your edge — lean into it harder."
            )
            implementation = (
                f"Increase usage of this strategy. Look for more opportunities "
                f"to exploit: {strength}."
            )
            expected_impact = 0.4
            time_to_implement = "immediate"

        # Priority 4: Momentum management
        elif analysis.momentum_shifts:
            shift = analysis.momentum_shifts[0]
            adjustment = f"Manage momentum: {shift}"
            reasoning = "Momentum swings are costing you. Stabilize."
            implementation = (
                f"When momentum shifts, slow down and return to your base gameplan. "
                f"Observed shift: {shift}."
            )
            expected_impact = 0.5
            time_to_implement = "immediate"

        return AdaptRecommendation(
            user_id="",  # Set by caller
            adjustment=adjustment,
            reasoning=reasoning,
            implementation=implementation,
            expected_impact=expected_impact,
            time_to_implement=time_to_implement,
            analysis=analysis,
        )
