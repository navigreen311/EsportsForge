"""Downstream Updater — propagates LoopAI insights to all backbone systems.

After every post-game analysis, LoopAI must push updates so that
PlayerTwin, ImpactRank, TruthEngine, and every agent reflects the
latest learnings.  This module coordinates those fan-out updates.
"""

from __future__ import annotations

import logging
from uuid import UUID

from app.schemas.loop_ai import (
    DownstreamTarget,
    DownstreamUpdate,
    FailureType,
    LoopResult,
)

logger = logging.getLogger(__name__)


class DownstreamUpdater:
    """Coordinates fan-out updates from LoopAI to downstream systems.

    Each ``update_*`` method builds a typed payload and records the
    update.  In production these will dispatch to message queues or
    direct service calls; for now they are in-process stubs that
    return ``DownstreamUpdate`` records so the rest of the pipeline
    is fully wired.
    """

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def update_player_twin(
        self, user_id: UUID, loop_result: LoopResult
    ) -> DownstreamUpdate:
        """Feed new performance data to the PlayerTwin.

        Sends accuracy metrics, failure attributions, and detected
        patterns so the digital twin stays current.
        """
        payload = {
            "user_id": str(user_id),
            "session_id": str(loop_result.session_id),
            "title": loop_result.title,
            "overall_accuracy": loop_result.overall_accuracy,
            "net_improvement_score": loop_result.net_improvement_score,
            "failure_types": [
                a.failure_type.value for a in loop_result.attributions
            ],
            "patterns": [
                {"type": p.pattern_type, "severity": p.severity}
                for p in loop_result.patterns_detected
            ],
        }

        update = DownstreamUpdate(
            target=DownstreamTarget.player_twin,
            payload_summary=f"Session {loop_result.session_id} — accuracy {loop_result.overall_accuracy:.0%}",
            status="sent",
        )
        logger.info(
            "PlayerTwin updated for user=%s session=%s",
            user_id,
            loop_result.session_id,
        )
        return update

    def update_impact_rank(
        self, user_id: UUID, loop_result: LoopResult
    ) -> DownstreamUpdate:
        """Recalculate priority rankings based on latest loop data.

        ImpactRank uses failure attributions and improvement scores
        to re-prioritise what the player should work on next.
        """
        failure_counts: dict[str, int] = {}
        for attr in loop_result.attributions:
            key = attr.failure_type.value
            failure_counts[key] = failure_counts.get(key, 0) + 1

        payload = {
            "user_id": str(user_id),
            "title": loop_result.title,
            "net_improvement_score": loop_result.net_improvement_score,
            "failure_distribution": failure_counts,
            "outcomes_count": len(loop_result.outcomes),
        }

        update = DownstreamUpdate(
            target=DownstreamTarget.impact_rank,
            payload_summary=f"Recalculate priorities — improvement delta {loop_result.net_improvement_score:+.2f}",
            status="sent",
        )
        logger.info(
            "ImpactRank updated for user=%s delta=%+.2f",
            user_id,
            loop_result.net_improvement_score,
        )
        return update

    def update_truth_engine(self, loop_result: LoopResult) -> DownstreamUpdate:
        """Feed prediction-accuracy data to the Truth Engine.

        The Truth Engine audits all AI outputs for drift.  LoopAI
        provides the ground-truth signal: did our predictions hold up?
        """
        accuracy_records = [
            {
                "recommendation_id": str(o.recommendation_id),
                "predicted_confidence": o.confidence_at_time,
                "actual_success": o.was_successful,
                "was_followed": o.was_followed,
            }
            for o in loop_result.outcomes
        ]

        payload = {
            "session_id": str(loop_result.session_id),
            "title": loop_result.title,
            "overall_accuracy": loop_result.overall_accuracy,
            "records": accuracy_records,
        }

        update = DownstreamUpdate(
            target=DownstreamTarget.truth_engine,
            payload_summary=f"Accuracy audit — {loop_result.overall_accuracy:.0%} across {len(accuracy_records)} recs",
            status="sent",
        )
        logger.info(
            "TruthEngine updated — session=%s accuracy=%.2f",
            loop_result.session_id,
            loop_result.overall_accuracy,
        )
        return update

    def notify_agents(self, loop_result: LoopResult) -> list[DownstreamUpdate]:
        """Inform title-specific agents (GameplanAI, DrillBot, etc.) of new data.

        Which agents are notified depends on the failure types found.
        """
        updates: list[DownstreamUpdate] = []
        failure_types = {a.failure_type for a in loop_result.attributions}

        # GameplanAI — bad reads or wrong opponent models mean the plan needs work
        if failure_types & {FailureType.bad_read, FailureType.wrong_opponent_model}:
            updates.append(
                DownstreamUpdate(
                    target=DownstreamTarget.gameplan_ai,
                    payload_summary="Gameplan revision needed — read/opponent-model failures",
                    status="sent",
                )
            )
            logger.info("GameplanAI notified for session=%s", loop_result.session_id)

        # DrillBot — execution failures require new drills
        if FailureType.bad_execution in failure_types:
            updates.append(
                DownstreamUpdate(
                    target=DownstreamTarget.drill_bot,
                    payload_summary="New drills needed — execution failures detected",
                    status="sent",
                )
            )
            logger.info("DrillBot notified for session=%s", loop_result.session_id)

        # AntiMeta Lab — stale meta means the meta model is outdated
        if FailureType.stale_meta in failure_types:
            updates.append(
                DownstreamUpdate(
                    target=DownstreamTarget.anti_meta_lab,
                    payload_summary="Meta refresh needed — stale meta detected",
                    status="sent",
                )
            )
            logger.info("AntiMetaLab notified for session=%s", loop_result.session_id)

        # ConfidenceAI — wrong confidence or pressure collapse
        if failure_types & {FailureType.wrong_confidence, FailureType.pressure_collapse}:
            updates.append(
                DownstreamUpdate(
                    target=DownstreamTarget.confidence_ai,
                    payload_summary="Confidence recalibration — confidence/pressure issues",
                    status="sent",
                )
            )
            logger.info("ConfidenceAI notified for session=%s", loop_result.session_id)

        return updates

    # ------------------------------------------------------------------
    # Convenience: run all updates for a loop result
    # ------------------------------------------------------------------

    def push_all(
        self, user_id: UUID, loop_result: LoopResult
    ) -> list[DownstreamUpdate]:
        """Execute every downstream update and return the full list."""
        updates: list[DownstreamUpdate] = []

        updates.append(self.update_player_twin(user_id, loop_result))
        updates.append(self.update_impact_rank(user_id, loop_result))
        updates.append(self.update_truth_engine(loop_result))
        updates.extend(self.notify_agents(loop_result))

        logger.info(
            "All downstream updates pushed: %d total for session=%s",
            len(updates),
            loop_result.session_id,
        )
        return updates
