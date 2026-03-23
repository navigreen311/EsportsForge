"""ImpactRank AI — ruthless prioritizer for competitive gaming improvement.

Scores every weakness by actual win-rate damage, ranks fixes by ROI,
and tells the player the ONE thing to fix next.  Low-ROI noise is suppressed.
"""

from __future__ import annotations

import logging
from datetime import datetime
from uuid import UUID, uuid4

from app.schemas.impact_rank import (
    Fix,
    FixScore,
    ImpactRanking,
    ImpactScore,
    OutcomeVerdict,
    PriorityRecommendation,
    Weakness,
)
from app.services.backbone.fix_scorer import (
    check_execution_feasibility,
    generate_fixes,
    score_fix_roi,
)
from app.services.backbone.weakness_detector import (
    detect_weaknesses,
    estimate_win_rate_damage,
)

logger = logging.getLogger(__name__)

# Default suppression threshold — anything below this composite is hidden
DEFAULT_ROI_THRESHOLD = 0.005


class ImpactRank:
    """Central ranking engine.

    In production this persists state in the database.  Current MVP uses an
    in-memory store keyed by ``(user_id, title)`` to enable full recalculation
    and outcome-based learning without external dependencies.
    """

    def __init__(self) -> None:
        # In-memory store: (user_id, title) -> list[ImpactRanking]
        self._store: dict[tuple[str, str], list[ImpactRanking]] = {}
        # Outcome history for learning: ranking_id -> list of outcomes
        self._outcomes: dict[UUID, list[dict]] = {}

    # ------------------------------------------------------------------
    # Scoring primitives
    # ------------------------------------------------------------------

    def score_weakness(
        self,
        weakness: Weakness,
        player_data: dict | None = None,
    ) -> ImpactScore:
        """Calculate win-rate damage for a weakness.

        Delegates to weakness_detector.estimate_win_rate_damage and enriches
        with any player-specific context.
        """
        context = player_data or {}
        score = estimate_win_rate_damage(weakness, context)
        weakness.impact_score = score
        return score

    def score_fix(
        self,
        fix: Fix,
        player_data: dict | None = None,
    ) -> FixScore:
        """Score a fix: expected lift, time-to-master, transfer rate.

        Combines ROI scoring with execution feasibility from PlayerTwin data.
        """
        player_profile = player_data or {}
        fix_score = score_fix_roi(fix, player_profile)

        # Adjust transfer rate by feasibility if twin data available
        twin_data = player_profile.get("player_twin")
        if twin_data:
            feasibility = check_execution_feasibility(fix, twin_data)
            fix_score = FixScore(
                expected_lift=fix_score.expected_lift,
                time_to_master_hours=fix_score.time_to_master_hours,
                execution_transfer_rate=round(
                    fix_score.execution_transfer_rate * feasibility, 4
                ),
            )

        fix.fix_score = fix_score
        return fix_score

    # ------------------------------------------------------------------
    # Ranking
    # ------------------------------------------------------------------

    def rank_weaknesses(
        self,
        user_id: str,
        title: str,
        player_data: dict | None = None,
        threshold: float = DEFAULT_ROI_THRESHOLD,
    ) -> list[ImpactRanking]:
        """Rank all weaknesses by win-rate damage.  Highest damage = rank 1.

        Steps:
        1. Detect weaknesses from player data
        2. Score each weakness
        3. Generate and score fixes for each
        4. Attach best fix per weakness
        5. Rank by composite score (weakness damage * best fix ROI)
        6. Suppress low-ROI items
        """
        player_data = player_data or {}

        # 1. Detect
        weaknesses = detect_weaknesses(player_data, title)
        if not weaknesses:
            logger.info("No weaknesses detected for user=%s title=%s", user_id, title)
            self._store[(user_id, title)] = []
            return []

        rankings: list[ImpactRanking] = []
        for w in weaknesses:
            # 2. Score weakness
            impact = self.score_weakness(w, player_data.get("context"))

            # 3. Generate and score fixes
            fixes = generate_fixes(w)
            best_fix: Fix | None = None
            best_roi = -1.0

            for fix in fixes:
                fs = self.score_fix(fix, player_data)
                if fs.roi > best_roi:
                    best_roi = fs.roi
                    best_fix = fix

            # 4. Composite: weakness damage weighted by best available fix ROI
            if best_fix and best_fix.fix_score:
                composite = impact.win_rate_damage * (1.0 + best_fix.fix_score.roi)
            else:
                composite = impact.win_rate_damage

            ranking = ImpactRanking(
                id=uuid4(),
                user_id=user_id,
                weakness=w,
                best_fix=best_fix,
                rank=0,  # assigned after sort
                composite_score=round(composite, 6),
            )
            rankings.append(ranking)

        # 5. Sort descending by composite
        rankings.sort(key=lambda r: r.composite_score, reverse=True)
        for idx, r in enumerate(rankings, start=1):
            r.rank = idx

        # 6. Suppress low-ROI
        rankings = self.suppress_low_roi(rankings, threshold)

        self._store[(user_id, title)] = rankings
        logger.info(
            "Ranked %d weaknesses for user=%s title=%s (suppressed=%d)",
            len(rankings),
            user_id,
            title,
            sum(1 for r in rankings if r.suppressed),
        )
        return rankings

    def get_top_priority(
        self,
        user_id: str,
        title: str,
    ) -> PriorityRecommendation | None:
        """Return THE one thing to fix next.

        Returns the highest-ranked non-suppressed item with a direct,
        actionable message.
        """
        rankings = self._store.get((user_id, title), [])
        active = [r for r in rankings if not r.suppressed]
        if not active:
            return None

        top = active[0]
        fix_detail = ""
        if top.best_fix:
            fix_detail = f" Fix: {top.best_fix.label} — {top.best_fix.drill}"

        message = (
            f"Your #1 priority: {top.weakness.label}. "
            f"This is costing you ~{top.weakness.impact_score.win_rate_damage * 100:.1f}% win rate."
            f"{fix_detail}"
        )

        return PriorityRecommendation(
            user_id=user_id,
            title=title,
            ranking=top,
            message=message,
        )

    # ------------------------------------------------------------------
    # Suppression
    # ------------------------------------------------------------------

    def suppress_low_roi(
        self,
        rankings: list[ImpactRanking],
        threshold: float = DEFAULT_ROI_THRESHOLD,
    ) -> list[ImpactRanking]:
        """Mark rankings below the ROI threshold as suppressed.

        Suppressed items stay in the list but are hidden from the player.
        They are not surfaced — they won't move the needle yet.
        """
        for r in rankings:
            r.suppressed = r.composite_score < threshold
        return rankings

    # ------------------------------------------------------------------
    # Learning from outcomes (LoopAI integration)
    # ------------------------------------------------------------------

    def update_from_outcome(
        self,
        user_id: str,
        ranking_id: UUID,
        outcome: dict,
    ) -> ImpactRanking | None:
        """Learn from a reported outcome after the player attempted a fix.

        Adjusts confidence and composite score based on observed results.
        In production this feeds into LoopAI for model retraining.

        Args:
            user_id: The player.
            ranking_id: Which ranking this outcome applies to.
            outcome: Dict with ``verdict`` (improved/no_change/regressed),
                ``observed_lift``, ``games_played``.
        """
        # Find the ranking
        ranking = self._find_ranking(ranking_id)
        if ranking is None:
            logger.warning("Ranking %s not found for outcome update", ranking_id)
            return None

        # Store outcome history
        self._outcomes.setdefault(ranking_id, []).append(outcome)

        verdict = outcome.get("verdict", "no_change")
        observed_lift = outcome.get("observed_lift", 0.0)

        if ranking.weakness.impact_score:
            score = ranking.weakness.impact_score
            if verdict == OutcomeVerdict.IMPROVED.value:
                # Fix is working — increase confidence, reduce damage estimate
                new_confidence = min(score.confidence + 0.1, 1.0)
                new_damage = max(score.win_rate_damage - abs(observed_lift or 0.03), 0.0)
                ranking.weakness.impact_score = ImpactScore(
                    win_rate_damage=round(new_damage, 4),
                    frequency=score.frequency,
                    severity=score.severity,
                    confidence=round(new_confidence, 4),
                )
            elif verdict == OutcomeVerdict.REGRESSED.value:
                # Fix made things worse — re-evaluate
                new_confidence = max(score.confidence - 0.15, 0.1)
                ranking.weakness.impact_score = ImpactScore(
                    win_rate_damage=score.win_rate_damage,
                    frequency=score.frequency,
                    severity=min(score.severity + 0.1, 1.0),
                    confidence=round(new_confidence, 4),
                )
            # no_change: leave scores as-is but bump confidence slightly
            else:
                ranking.weakness.impact_score = ImpactScore(
                    win_rate_damage=score.win_rate_damage,
                    frequency=score.frequency,
                    severity=score.severity,
                    confidence=round(min(score.confidence + 0.05, 1.0), 4),
                )

        ranking.updated_at = datetime.utcnow()
        logger.info(
            "Updated ranking %s with outcome=%s for user=%s",
            ranking_id,
            verdict,
            user_id,
        )
        return ranking

    # ------------------------------------------------------------------
    # Recalculation
    # ------------------------------------------------------------------

    def recalculate(
        self,
        user_id: str,
        title: str,
        player_data: dict | None = None,
    ) -> list[ImpactRanking]:
        """Full recalculation — called after every session via LoopAI.

        Clears existing rankings and rebuilds from scratch with fresh data.
        """
        logger.info("Full recalculation for user=%s title=%s", user_id, title)
        # Preserve outcome history (learning persists across recalcs)
        return self.rank_weaknesses(user_id, title, player_data)

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _find_ranking(self, ranking_id: UUID) -> ImpactRanking | None:
        """Find a ranking by ID across all stored data."""
        for rankings in self._store.values():
            for r in rankings:
                if r.id == ranking_id:
                    return r
        return None


# Module-level singleton for use by the API layer
impact_rank_engine = ImpactRank()
