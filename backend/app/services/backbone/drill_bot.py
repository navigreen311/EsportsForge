"""DrillBot — targeted practice drill generation and tracking.

Converts ImpactRank weaknesses into structured, personalized drills.
Tracks completion, adjusts difficulty via Dynamic Calibration, and
maintains a priority-ordered drill queue per player per title.
"""

from __future__ import annotations

import logging
from collections import defaultdict
from datetime import datetime
from uuid import UUID, uuid4

from app.schemas.drill import (
    DrillQueue,
    DrillResult,
    DrillSession,
    DrillSpec,
    DrillStatus,
    DrillType,
    PersonalizedDrill,
)
from app.services.backbone.dynamic_calibration import (
    adjust_after_rep,
    get_calibration_level,
)

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

_TARGET_SUCCESS_RATE = 0.70
_DEFAULT_REPS = 10
_MIN_REPS_FOR_PROGRESS = 3

# Weakness category -> drill type mapping
_WEAKNESS_TO_DRILL: dict[str, DrillType] = {
    "mechanical": DrillType.MECHANICAL,
    "decision": DrillType.DECISION,
    "knowledge": DrillType.KNOWLEDGE,
    "tactical": DrillType.TACTICAL,
    "mental": DrillType.COMPOSURE,
    "reaction": DrillType.REACTION,
}

# Drill templates by type
_DRILL_TEMPLATES: dict[DrillType, list[dict]] = {
    DrillType.MECHANICAL: [
        {
            "name": "Precision Rep Trainer",
            "description": "Repeat the exact mechanical input until muscle memory locks in.",
            "instructions": [
                "Load the specific scenario targeting your weakness.",
                "Execute the correct input with full focus on timing.",
                "Repeat until the motion feels automatic.",
            ],
        },
    ],
    DrillType.DECISION: [
        {
            "name": "Rapid Read Drill",
            "description": "Practice reading the situation and making the right call under time pressure.",
            "instructions": [
                "Observe the defensive/offensive setup.",
                "Identify the optimal play within 3 seconds.",
                "Execute and review whether the read was correct.",
            ],
        },
    ],
    DrillType.KNOWLEDGE: [
        {
            "name": "Playbook Mastery Quiz",
            "description": "Test and reinforce knowledge of formations, coverages, and counters.",
            "instructions": [
                "Review the relevant section of the playbook.",
                "Identify the correct counter for each presented scenario.",
                "Explain why the counter works.",
            ],
        },
    ],
    DrillType.TACTICAL: [
        {
            "name": "Situational Awareness Drill",
            "description": "Practice making the right strategic decision based on game state.",
            "instructions": [
                "Assess the game situation (score, time, field position).",
                "Choose the optimal strategy.",
                "Execute and evaluate the outcome.",
            ],
        },
    ],
    DrillType.REACTION: [
        {
            "name": "Stimulus Response Trainer",
            "description": "React to visual/audio cues as fast as possible with the correct input.",
            "instructions": [
                "Watch for the trigger cue.",
                "Execute the correct response immediately.",
                "Track your reaction time improvement.",
            ],
        },
    ],
    DrillType.COMPOSURE: [
        {
            "name": "Pressure Scenario Drill",
            "description": "Practice maintaining performance under high-pressure game situations.",
            "instructions": [
                "Enter a high-stakes scenario (close game, late clock).",
                "Focus on process over outcome.",
                "Execute your gameplan despite the pressure.",
            ],
        },
    ],
}

# ---------------------------------------------------------------------------
# In-memory stores
# ---------------------------------------------------------------------------

# (user_id, title) -> list[DrillSession]
_drill_queues: dict[tuple[str, str], list[DrillSession]] = {}

# drill_id -> DrillSession
_drill_sessions: dict[UUID, DrillSession] = {}

# (user_id, title) -> list[DrillResult]
_drill_results: dict[tuple[str, str], list[DrillResult]] = {}


class DrillBot:
    """Generates, queues, and tracks personalized training drills.

    MVP uses in-memory state. Production will persist to DB via
    ForgeDataFabric.
    """

    def __init__(self) -> None:
        pass

    # ------------------------------------------------------------------
    # Drill generation
    # ------------------------------------------------------------------

    def generate_drill(
        self,
        user_id: str,
        title: str,
        weakness: dict,
    ) -> PersonalizedDrill:
        """Generate a personalized drill from an ImpactRank weakness.

        Parameters
        ----------
        user_id:
            Player identifier.
        title:
            Game title (e.g. 'madden26').
        weakness:
            Weakness dict with at least 'label' and 'category' keys.

        Returns
        -------
        PersonalizedDrill
            A drill tailored to the player's weakness and current skill level.
        """
        weakness_label = weakness.get("label", "Unknown weakness")
        category = weakness.get("category", "decision")
        drill_type = _WEAKNESS_TO_DRILL.get(category, DrillType.DECISION)

        # Get current calibration for difficulty
        cal = get_calibration_level(user_id, weakness_label)
        difficulty = cal.difficulty_value

        # Pick template
        templates = _DRILL_TEMPLATES.get(drill_type, _DRILL_TEMPLATES[DrillType.DECISION])
        template = templates[0]

        # Build drill spec
        spec = DrillSpec(
            title=title,
            weakness_label=weakness_label,
            drill_type=drill_type,
            name=f"{template['name']}: {weakness_label}",
            description=template["description"],
            instructions=template["instructions"],
            reps_required=_DEFAULT_REPS,
            difficulty=round(difficulty, 4),
            estimated_minutes=max(3, int(10 * difficulty)),
        )

        # Create session and add to queue
        session = DrillSession(
            user_id=user_id,
            drill_id=spec.id,
            drill_spec=spec,
            status=DrillStatus.PENDING,
            current_difficulty=difficulty,
        )

        key = (user_id, title)
        _drill_queues.setdefault(key, []).append(session)
        _drill_sessions[session.id] = session

        # Compute priority from weakness impact
        impact = weakness.get("impact_score", 0.5)
        if isinstance(impact, dict):
            impact = impact.get("composite", 0.5)
        priority = max(1, len(_drill_queues[key]))

        personalized = PersonalizedDrill(
            user_id=user_id,
            drill_spec=spec,
            reason=f"Targets your '{weakness_label}' weakness (category: {category}).",
            priority=priority,
            expected_improvement=min(1.0, impact * 0.3),
        )

        logger.info(
            "Generated drill '%s' for %s (difficulty=%.2f, type=%s)",
            spec.name, user_id, difficulty, drill_type.value,
        )
        return personalized

    # ------------------------------------------------------------------
    # Drill queue
    # ------------------------------------------------------------------

    def get_drill_queue(self, user_id: str, title: str) -> DrillQueue:
        """Return a priority-ordered drill list for the player.

        Pending drills first, sorted by creation time. Completed drills
        are moved to the end.
        """
        key = (user_id, title)
        sessions = _drill_queues.get(key, [])

        # Sort: pending first, then in_progress, then completed/skipped
        status_order = {
            DrillStatus.IN_PROGRESS: 0,
            DrillStatus.PENDING: 1,
            DrillStatus.COMPLETED: 2,
            DrillStatus.SKIPPED: 3,
        }
        sorted_sessions = sorted(sessions, key=lambda s: status_order.get(s.status, 99))

        total_minutes = sum(
            s.drill_spec.estimated_minutes
            for s in sorted_sessions
            if s.status in (DrillStatus.PENDING, DrillStatus.IN_PROGRESS)
        )

        return DrillQueue(
            user_id=user_id,
            title=title,
            drills=sorted_sessions,
            total_estimated_minutes=total_minutes,
        )

    # ------------------------------------------------------------------
    # Rep tracking
    # ------------------------------------------------------------------

    def complete_rep(
        self,
        user_id: str,
        drill_id: UUID,
        success: bool,
    ) -> DrillSession:
        """Track completion of a single drill rep.

        Updates the session state and triggers difficulty adjustment via
        Dynamic Calibration.

        Parameters
        ----------
        user_id:
            Player identifier.
        drill_id:
            The drill session ID (not the spec ID).
        success:
            Whether the rep was successful.

        Returns
        -------
        DrillSession
            Updated session with new rep count and difficulty.
        """
        session = _drill_sessions.get(drill_id)
        if session is None:
            raise ValueError(f"Drill session {drill_id} not found.")
        if session.user_id != user_id:
            raise ValueError(f"Drill session {drill_id} does not belong to user {user_id}.")

        # Start session on first rep
        if session.status == DrillStatus.PENDING:
            session.status = DrillStatus.IN_PROGRESS
            session.started_at = datetime.utcnow()

        # Record rep
        session.reps_completed += 1
        if success:
            session.reps_successful += 1

        # Dynamic calibration adjustment
        adjustment = adjust_after_rep(
            user_id, session.drill_spec.weakness_label, success
        )
        session.current_difficulty = adjustment.new_difficulty

        # Check completion
        if session.is_complete:
            session.status = DrillStatus.COMPLETED
            session.completed_at = datetime.utcnow()

            # Record result
            result = DrillResult(
                drill_id=drill_id,
                user_id=user_id,
                weakness_label=session.drill_spec.weakness_label,
                reps_completed=session.reps_completed,
                reps_successful=session.reps_successful,
                success_rate=session.success_rate,
                difficulty_at_end=session.current_difficulty,
                improvement_signal=session.success_rate - _TARGET_SUCCESS_RATE,
            )
            key = (user_id, session.drill_spec.title)
            _drill_results.setdefault(key, []).append(result)

            logger.info(
                "Drill %s completed: %d/%d reps successful (%.0f%%)",
                drill_id, session.reps_successful, session.reps_completed,
                session.success_rate * 100,
            )

        return session

    # ------------------------------------------------------------------
    # Progress tracking
    # ------------------------------------------------------------------

    def get_drill_progress(self, user_id: str, title: str) -> dict:
        """Return per-skill progress summary for the player.

        Returns
        -------
        dict
            Keyed by weakness_label with stats for each skill.
        """
        key = (user_id, title)
        results = _drill_results.get(key, [])
        sessions = _drill_queues.get(key, [])

        progress: dict[str, dict] = {}
        for result in results:
            label = result.weakness_label
            if label not in progress:
                progress[label] = {
                    "total_drills_completed": 0,
                    "total_reps": 0,
                    "total_successful": 0,
                    "avg_success_rate": 0.0,
                    "latest_difficulty": 0.0,
                    "improvement_trend": [],
                }
            p = progress[label]
            p["total_drills_completed"] += 1
            p["total_reps"] += result.reps_completed
            p["total_successful"] += result.reps_successful
            p["improvement_trend"].append(result.improvement_signal)
            p["latest_difficulty"] = result.difficulty_at_end

        # Calculate averages
        for label, p in progress.items():
            if p["total_reps"] > 0:
                p["avg_success_rate"] = round(
                    p["total_successful"] / p["total_reps"], 4
                )

        # Include active drills
        for session in sessions:
            label = session.drill_spec.weakness_label
            if label not in progress:
                progress[label] = {
                    "total_drills_completed": 0,
                    "total_reps": 0,
                    "total_successful": 0,
                    "avg_success_rate": 0.0,
                    "latest_difficulty": session.current_difficulty,
                    "improvement_trend": [],
                    "active_drill": True,
                }

        return progress

    # ------------------------------------------------------------------
    # Difficulty calibration
    # ------------------------------------------------------------------

    def calibrate_drill_difficulty(
        self,
        user_id: str,
        drill_id: UUID,
    ) -> DrillSession:
        """Auto-adjust drill difficulty via Dynamic Calibration.

        Reads the session's success rate and adjusts difficulty to keep
        the player in the optimal challenge zone (~70% success rate).

        Returns
        -------
        DrillSession
            Updated session with recalibrated difficulty.
        """
        session = _drill_sessions.get(drill_id)
        if session is None:
            raise ValueError(f"Drill session {drill_id} not found.")

        if session.reps_completed < _MIN_REPS_FOR_PROGRESS:
            logger.info(
                "Not enough reps (%d/%d) to calibrate drill %s",
                session.reps_completed, _MIN_REPS_FOR_PROGRESS, drill_id,
            )
            return session

        success_rate = session.success_rate
        current_diff = session.current_difficulty

        # Adjust based on success rate vs target
        if success_rate > 0.85:
            # Too easy — bump up
            new_diff = min(1.0, current_diff + 0.10)
            logger.info("Drill %s too easy (%.0f%%) — bumping to %.2f", drill_id, success_rate * 100, new_diff)
        elif success_rate < 0.50:
            # Too hard — dial back
            new_diff = max(0.0, current_diff - 0.10)
            logger.info("Drill %s too hard (%.0f%%) — dialing to %.2f", drill_id, success_rate * 100, new_diff)
        else:
            # In the zone — micro-adjust toward target
            delta = (_TARGET_SUCCESS_RATE - success_rate) * 0.05
            new_diff = max(0.0, min(1.0, current_diff - delta))
            logger.info("Drill %s in zone (%.0f%%) — micro-adjust to %.2f", drill_id, success_rate * 100, new_diff)

        session.current_difficulty = round(new_diff, 4)
        return session
