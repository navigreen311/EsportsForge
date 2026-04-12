"""LoopAI Service — AI-powered session analysis and learning loop.

Provides higher-level AI analysis on top of the backbone LoopAI engine.
Handles session-end processing with mock AI logic that evaluates
win/loss outcomes against whether recommendations were followed.
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

logger = logging.getLogger(__name__)


class LoopAIService:
    """AI layer for the learning loop.

    After every session, ``process_session_end`` evaluates:
    - Win + followed advice -> reinforce PlayerTwin beliefs
    - Win + ignored advice  -> question twin accuracy
    - Loss + followed advice -> flag bad advice, recalibrate
    - Loss + ignored advice  -> reinforce that advice was correct

    Returns structured updates for PlayerTwin and a human-readable debrief.
    """

    def __init__(self) -> None:
        self._history: dict[str, list[dict[str, Any]]] = {}

    def process_session_end(self, session_data: dict[str, Any]) -> dict[str, Any]:
        """Process a completed session and generate AI insights.

        Parameters
        ----------
        session_data : dict
            Must include at minimum:
            - user_id: str
            - title: str
            - outcome: "win" | "loss" | "draw"
            - recommendations_followed: list[dict] with {id, name, followed: bool}
            - stats: dict with session performance metrics

        Returns
        -------
        dict with keys:
            - player_twin_updates: list of updates to push to PlayerTwin
            - debrief_text: human-readable session debrief
            - confidence_adjustments: per-recommendation confidence deltas
            - patterns_flagged: any new patterns detected
            - session_id: unique id for this analysis
        """
        user_id = session_data.get("user_id", "unknown")
        title = session_data.get("title", "unknown")
        outcome = session_data.get("outcome", "unknown")
        recs = session_data.get("recommendations_followed", [])
        stats = session_data.get("stats", {})

        session_id = str(uuid4())
        is_win = outcome == "win"

        twin_updates: list[dict[str, Any]] = []
        confidence_adjustments: list[dict[str, Any]] = []
        debrief_parts: list[str] = []
        patterns_flagged: list[dict[str, Any]] = []

        # ------------------------------------------------------------------
        # Evaluate each recommendation
        # ------------------------------------------------------------------
        followed_count = 0
        ignored_count = 0

        for rec in recs:
            rec_id = rec.get("id", str(uuid4()))
            rec_name = rec.get("name", "Unknown recommendation")
            was_followed = rec.get("followed", False)

            if was_followed:
                followed_count += 1
            else:
                ignored_count += 1

            if is_win and was_followed:
                # Reinforce — twin was right, player executed
                twin_updates.append({
                    "type": "reinforce",
                    "recommendation_id": rec_id,
                    "recommendation_name": rec_name,
                    "weight_delta": +0.05,
                    "reason": "Win while following recommendation — reinforcing twin belief.",
                })
                confidence_adjustments.append({
                    "recommendation_id": rec_id,
                    "delta": +0.03,
                    "new_confidence": min(1.0, rec.get("confidence", 0.7) + 0.03),
                })
                debrief_parts.append(
                    f"You followed \"{rec_name}\" and it paid off. "
                    f"Your twin model confidence in this strategy increases."
                )

            elif is_win and not was_followed:
                # Question twin accuracy — player won despite ignoring advice
                twin_updates.append({
                    "type": "question_accuracy",
                    "recommendation_id": rec_id,
                    "recommendation_name": rec_name,
                    "weight_delta": -0.02,
                    "reason": "Win despite ignoring recommendation — twin accuracy questioned.",
                })
                confidence_adjustments.append({
                    "recommendation_id": rec_id,
                    "delta": -0.02,
                    "new_confidence": max(0.0, rec.get("confidence", 0.7) - 0.02),
                })
                debrief_parts.append(
                    f"You ignored \"{rec_name}\" but still won. "
                    f"Your twin model is reviewing whether this advice was necessary."
                )

            elif not is_win and was_followed:
                # Flag bad advice — player followed but lost
                twin_updates.append({
                    "type": "flag_bad_advice",
                    "recommendation_id": rec_id,
                    "recommendation_name": rec_name,
                    "weight_delta": -0.08,
                    "reason": "Loss despite following recommendation — flagged for recalibration.",
                })
                confidence_adjustments.append({
                    "recommendation_id": rec_id,
                    "delta": -0.06,
                    "new_confidence": max(0.0, rec.get("confidence", 0.7) - 0.06),
                })
                debrief_parts.append(
                    f"You followed \"{rec_name}\" but lost. "
                    f"This advice is being flagged for review. Your twin will recalibrate."
                )
                patterns_flagged.append({
                    "type": "bad_advice",
                    "recommendation_id": rec_id,
                    "recommendation_name": rec_name,
                    "severity": 0.7,
                    "suggestion": "Review recommendation context and situational applicability.",
                })

            else:
                # Loss + ignored — reinforce that advice was correct
                twin_updates.append({
                    "type": "reinforce_missed",
                    "recommendation_id": rec_id,
                    "recommendation_name": rec_name,
                    "weight_delta": +0.03,
                    "reason": "Loss after ignoring recommendation — advice was likely correct.",
                })
                confidence_adjustments.append({
                    "recommendation_id": rec_id,
                    "delta": +0.02,
                    "new_confidence": min(1.0, rec.get("confidence", 0.7) + 0.02),
                })
                debrief_parts.append(
                    f"You ignored \"{rec_name}\" and lost. "
                    f"Next time, consider following this recommendation."
                )

        # ------------------------------------------------------------------
        # Build debrief text
        # ------------------------------------------------------------------
        outcome_label = "Victory" if is_win else ("Draw" if outcome == "draw" else "Defeat")
        header = f"Session Debrief — {outcome_label}"

        summary_line = (
            f"You followed {followed_count}/{followed_count + ignored_count} "
            f"recommendations this session."
        )

        win_rate = stats.get("win_rate")
        stat_line = ""
        if win_rate is not None:
            stat_line = f" Your rolling win rate is now {win_rate}%."

        debrief_text = (
            f"## {header}\n\n"
            f"{summary_line}{stat_line}\n\n"
            + "\n\n".join(debrief_parts)
        )

        # ------------------------------------------------------------------
        # Store in history
        # ------------------------------------------------------------------
        result = {
            "session_id": session_id,
            "user_id": user_id,
            "title": title,
            "outcome": outcome,
            "player_twin_updates": twin_updates,
            "debrief_text": debrief_text,
            "confidence_adjustments": confidence_adjustments,
            "patterns_flagged": patterns_flagged,
            "processed_at": datetime.now(timezone.utc).isoformat(),
        }

        self._history.setdefault(user_id, []).append(result)

        logger.info(
            "LoopAI processed session=%s user=%s title=%s outcome=%s "
            "followed=%d ignored=%d updates=%d",
            session_id, user_id, title, outcome,
            followed_count, ignored_count, len(twin_updates),
        )

        return result

    def get_history(self, user_id: str, limit: int = 20) -> list[dict[str, Any]]:
        """Return recent session analysis history for a user."""
        entries = self._history.get(user_id, [])
        return entries[-limit:]
