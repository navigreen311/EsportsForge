"""LoopAI — the self-improvement engine.

After every game the platform asks: was the recommendation followed?
Did it work?  If not, exactly why?  The answers flow back into every
backbone system so EsportsForge gets measurably smarter with each
session.
"""

from __future__ import annotations

import logging
from collections import defaultdict
from datetime import datetime
from uuid import UUID, uuid4

from app.schemas.loop_ai import (
    DownstreamUpdate,
    FailureAttribution,
    FailureType,
    InterventionType,
    LoopResult,
    Pattern,
    RecommendationOutcome,
)
from app.services.backbone.downstream_updater import DownstreamUpdater
from app.services.backbone.failure_attribution import AttributionEngine

logger = logging.getLogger(__name__)


class LoopAI:
    """Orchestrates the full post-game learning loop.

    Lifecycle for every completed session:

    1. ``process_session`` — run the full pipeline
    2. ``evaluate_recommendations`` — score each recommendation
    3. ``attribute_failure`` — root-cause every miss
    4. ``trigger_downstream_updates`` — push learnings everywhere
    5. ``detect_patterns`` — spot cross-session trends

    The class is stateless; all persistence is handled through the
    ``_store`` dict (in-memory for now, swapped for DB later).
    """

    def __init__(self) -> None:
        self._attribution_engine = AttributionEngine()
        self._downstream_updater = DownstreamUpdater()

        # In-memory store — will be replaced with DB persistence
        self._store: dict[UUID, list[LoopResult]] = defaultdict(list)

    # ------------------------------------------------------------------
    # 1. Full post-game pipeline
    # ------------------------------------------------------------------

    def process_session(
        self,
        user_id: UUID,
        session_id: UUID,
        title: str,
        session_data: dict,
        recommendations_used: list[dict],
    ) -> LoopResult:
        """Run the complete post-game analysis for a single session.

        Parameters
        ----------
        user_id:
            Player identifier.
        session_id:
            The completed session to analyse.
        title:
            Game title (e.g. ``"madden26"``).
        session_data:
            Raw session telemetry — game events, actions, outcomes.
        recommendations_used:
            Recommendations that were active during the session.

        Returns
        -------
        LoopResult containing outcomes, attributions, downstream
        updates, detected patterns, and an improvement score.
        """
        logger.info(
            "LoopAI processing session=%s user=%s title=%s",
            session_id, user_id, title,
        )

        # Step 1 — evaluate every recommendation
        outcomes = self.evaluate_recommendations(
            session_id, session_data, recommendations_used
        )

        # Step 2 — attribute failures
        attributions: list[FailureAttribution] = []
        for outcome in outcomes:
            if outcome.was_successful is False:
                attr = self.attribute_failure(
                    outcome,
                    session_data.get("outcome", {}),
                    session_data.get("context", {}),
                )
                attributions.append(attr)

        # Step 3 — calculate accuracy
        evaluated = [o for o in outcomes if o.was_successful is not None]
        successes = sum(1 for o in evaluated if o.was_successful)
        overall_accuracy = successes / len(evaluated) if evaluated else 0.0

        # Step 4 — compute improvement delta
        net_improvement = self._compute_improvement_delta(
            user_id, title, overall_accuracy
        )

        # Step 5 — detect cross-session patterns
        patterns = self.detect_patterns(user_id, title)

        # Step 6 — build result
        loop_result = LoopResult(
            user_id=user_id,
            session_id=session_id,
            title=title,
            outcomes=outcomes,
            attributions=attributions,
            downstream_updates=[],  # filled by trigger step
            patterns_detected=patterns,
            overall_accuracy=overall_accuracy,
            net_improvement_score=net_improvement,
            summary=self._build_summary(
                outcomes, attributions, overall_accuracy, net_improvement
            ),
        )

        # Step 7 — push downstream
        downstream = self.trigger_downstream_updates(user_id, loop_result)
        loop_result.downstream_updates = downstream

        # Persist
        self._store[user_id].append(loop_result)

        logger.info(
            "LoopAI complete: session=%s accuracy=%.2f delta=%+.2f attributions=%d patterns=%d",
            session_id,
            overall_accuracy,
            net_improvement,
            len(attributions),
            len(patterns),
        )

        return loop_result

    # ------------------------------------------------------------------
    # 2. Evaluate recommendations
    # ------------------------------------------------------------------

    def evaluate_recommendations(
        self,
        session_id: UUID,
        session_data: dict,
        recommendations_used: list[dict],
    ) -> list[RecommendationOutcome]:
        """Score each recommendation that was active during the session.

        Each recommendation dict should include at minimum:
        ``id``, ``description``, ``confidence``.  The session_data
        provides the actual game outcome.
        """
        outcomes: list[RecommendationOutcome] = []
        game_result = session_data.get("outcome", {})
        player_actions = session_data.get("player_actions", [])

        for rec in recommendations_used:
            rec_id = UUID(rec["id"]) if isinstance(rec.get("id"), str) else rec.get("id", uuid4())
            description = rec.get("description", "Unknown recommendation")
            confidence = rec.get("confidence", 0.5)

            was_followed = self._check_if_followed(rec, player_actions)
            was_successful = self._check_if_successful(rec, game_result, was_followed)

            outcome = RecommendationOutcome(
                recommendation_id=rec_id,
                session_id=session_id,
                description=description,
                was_followed=was_followed,
                was_successful=was_successful,
                confidence_at_time=confidence,
                context_snapshot=rec.get("context", {}),
                notes=rec.get("notes", ""),
            )
            outcomes.append(outcome)

        logger.info(
            "Evaluated %d recommendations for session=%s",
            len(outcomes),
            session_id,
        )
        return outcomes

    # ------------------------------------------------------------------
    # 3. Failure attribution (delegates to engine)
    # ------------------------------------------------------------------

    def attribute_failure(
        self,
        recommendation: RecommendationOutcome,
        outcome: dict,
        context: dict,
    ) -> FailureAttribution:
        """Diagnose why a single recommendation failed."""
        return self._attribution_engine.classify_failure(
            recommendation, outcome, context
        )

    # ------------------------------------------------------------------
    # 4. Downstream updates (delegates to updater)
    # ------------------------------------------------------------------

    def trigger_downstream_updates(
        self,
        user_id: UUID,
        loop_result: LoopResult,
    ) -> list[DownstreamUpdate]:
        """Push learnings to PlayerTwin, ImpactRank, TruthEngine, agents."""
        return self._downstream_updater.push_all(user_id, loop_result)

    # ------------------------------------------------------------------
    # 5. Learning history
    # ------------------------------------------------------------------

    def get_learning_history(
        self,
        user_id: UUID,
        title: str,
    ) -> list[LoopResult]:
        """Return all past loop results for a player + title."""
        return [
            r for r in self._store.get(user_id, [])
            if r.title == title
        ]

    # ------------------------------------------------------------------
    # 6. Cross-session pattern detection
    # ------------------------------------------------------------------

    def detect_patterns(
        self,
        user_id: UUID,
        title: str,
    ) -> list[Pattern]:
        """Detect recurring patterns across a player's session history.

        Pattern types:
        - ``failure_cluster``: same failure type keeps recurring
        - ``improvement_trend``: accuracy is consistently rising
        - ``regression``: accuracy is consistently falling
        - ``habit``: player ignores the same category of recs
        """
        history = self.get_learning_history(user_id, title)
        if len(history) < 2:
            return []

        patterns: list[Pattern] = []
        now = datetime.utcnow()

        # --- Failure clusters ---
        failure_counts: dict[FailureType, int] = defaultdict(int)
        failure_first_seen: dict[FailureType, datetime] = {}
        failure_last_seen: dict[FailureType, datetime] = {}

        for result in history:
            for attr in result.attributions:
                ft = attr.failure_type
                failure_counts[ft] += 1
                if ft not in failure_first_seen:
                    failure_first_seen[ft] = result.processed_at
                failure_last_seen[ft] = result.processed_at

        for ft, count in failure_counts.items():
            if count >= 3:
                patterns.append(
                    Pattern(
                        user_id=user_id,
                        title=title,
                        pattern_type="failure_cluster",
                        description=f"Recurring {ft.value} failures ({count} occurrences)",
                        frequency=count,
                        first_seen=failure_first_seen[ft],
                        last_seen=failure_last_seen[ft],
                        related_failure_types=[ft],
                        severity=min(count / 10.0, 1.0),
                        actionable=True,
                        suggested_intervention=self._attribution_engine._map_intervention(ft),
                    )
                )

        # --- Accuracy trend ---
        accuracies = [r.overall_accuracy for r in history]
        if len(accuracies) >= 3:
            recent = accuracies[-3:]
            if all(recent[i] > recent[i - 1] for i in range(1, len(recent))):
                patterns.append(
                    Pattern(
                        user_id=user_id,
                        title=title,
                        pattern_type="improvement_trend",
                        description="Recommendation accuracy improving over recent sessions",
                        frequency=len(recent),
                        first_seen=history[-3].processed_at,
                        last_seen=history[-1].processed_at,
                        severity=0.2,
                        actionable=False,
                    )
                )
            elif all(recent[i] < recent[i - 1] for i in range(1, len(recent))):
                patterns.append(
                    Pattern(
                        user_id=user_id,
                        title=title,
                        pattern_type="regression",
                        description="Recommendation accuracy declining over recent sessions",
                        frequency=len(recent),
                        first_seen=history[-3].processed_at,
                        last_seen=history[-1].processed_at,
                        severity=0.8,
                        actionable=True,
                        suggested_intervention=InterventionType.review_session,
                    )
                )

        # --- Ignored-rec habit ---
        ignored_total = 0
        total_recs = 0
        for result in history:
            for o in result.outcomes:
                total_recs += 1
                if not o.was_followed:
                    ignored_total += 1

        if total_recs >= 5 and ignored_total / total_recs > 0.5:
            patterns.append(
                Pattern(
                    user_id=user_id,
                    title=title,
                    pattern_type="habit",
                    description=f"Player ignores {ignored_total}/{total_recs} recommendations",
                    frequency=ignored_total,
                    first_seen=history[0].processed_at,
                    last_seen=history[-1].processed_at,
                    severity=0.7,
                    actionable=True,
                    suggested_intervention=InterventionType.confidence_recalibration,
                )
            )

        return patterns

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _check_if_followed(self, rec: dict, player_actions: list) -> bool:
        """Determine whether the player acted on a recommendation.

        Simple keyword/tag matching for now — will be upgraded to
        action-sequence alignment.
        """
        rec_tags = set(rec.get("tags", []))
        if not rec_tags:
            return rec.get("was_followed", False)

        action_tags = set()
        for action in player_actions:
            action_tags.update(action.get("tags", []))

        overlap = rec_tags & action_tags
        return len(overlap) / len(rec_tags) >= 0.5 if rec_tags else False

    def _check_if_successful(
        self, rec: dict, game_result: dict, was_followed: bool
    ) -> bool | None:
        """Determine whether following/ignoring the rec led to success.

        Returns ``None`` if we lack enough data to evaluate.
        """
        result_flag = game_result.get("success")
        if result_flag is not None:
            return bool(result_flag)

        score_delta = game_result.get("score_delta")
        if score_delta is not None:
            return score_delta > 0

        return None

    def _compute_improvement_delta(
        self,
        user_id: UUID,
        title: str,
        current_accuracy: float,
    ) -> float:
        """Compare current accuracy against rolling average of past sessions."""
        history = self.get_learning_history(user_id, title)
        if not history:
            return 0.0

        past_accuracies = [r.overall_accuracy for r in history[-10:]]
        rolling_avg = sum(past_accuracies) / len(past_accuracies)
        return current_accuracy - rolling_avg

    def _build_summary(
        self,
        outcomes: list[RecommendationOutcome],
        attributions: list[FailureAttribution],
        accuracy: float,
        delta: float,
    ) -> str:
        """Generate a human-readable summary of the loop result."""
        total = len(outcomes)
        followed = sum(1 for o in outcomes if o.was_followed)
        failures = len(attributions)

        parts = [
            f"{total} recommendations evaluated",
            f"{followed} followed",
            f"{accuracy:.0%} accuracy",
        ]

        if delta > 0:
            parts.append(f"+{delta:.1%} vs average (improving)")
        elif delta < 0:
            parts.append(f"{delta:.1%} vs average (declining)")
        else:
            parts.append("on par with average")

        if failures:
            top_failure = max(
                set(a.failure_type for a in attributions),
                key=lambda ft: sum(1 for a in attributions if a.failure_type == ft),
            )
            parts.append(f"top failure: {top_failure.value}")

        return ". ".join(parts) + "."
