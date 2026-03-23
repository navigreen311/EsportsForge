"""ProgressionOS — ImpactRank-driven weekly install roadmap with overload throttling.

Phased mastery: Base -> Pressure -> Anti-Meta -> Tournament.
Actively throttles to prevent information overload.
"""

from __future__ import annotations

import logging
from datetime import datetime
from uuid import uuid4

from app.schemas.install import (
    InstallStatus,
    MasteryPhase,
    OverloadCheck,
    PhaseProgress,
    ProgressionStep,
    WeeklyRoadmap,
)

logger = logging.getLogger(__name__)

# Phase ordering for progression
PHASE_ORDER: list[MasteryPhase] = [
    MasteryPhase.BASE,
    MasteryPhase.PRESSURE,
    MasteryPhase.ANTI_META,
    MasteryPhase.TOURNAMENT,
]

# Default throttle limits
DEFAULT_MAX_HOURS_PER_WEEK = 10.0
DEFAULT_MAX_ACTIVE_INSTALLS = 5
MASTERY_THRESHOLD_PCT = 80.0  # % required to advance phase


class ProgressionOS:
    """Manages phased mastery progression driven by ImpactRank scores.

    In production this persists to the database.  Current MVP uses an
    in-memory store keyed by ``(user_id, title)`` to enable full roadmap
    generation, phase tracking, and overload detection.
    """

    def __init__(self) -> None:
        # In-memory store: (user_id, title) -> list[ProgressionStep]
        self._steps: dict[tuple[str, str], list[ProgressionStep]] = {}
        # Current phase per (user_id, title)
        self._phases: dict[tuple[str, str], MasteryPhase] = {}
        # Week counter per (user_id, title)
        self._week: dict[tuple[str, str], int] = {}
        # Config overrides per user
        self._config: dict[str, dict] = {}

    # ------------------------------------------------------------------
    # Weekly roadmap
    # ------------------------------------------------------------------

    def generate_weekly_roadmap(
        self,
        user_id: str,
        title: str,
        impact_rankings: list[dict] | None = None,
    ) -> WeeklyRoadmap:
        """Generate an ImpactRank-driven weekly install plan.

        Steps are drawn from the current mastery phase and ordered by
        ImpactRank composite score.  Overload throttling is applied
        automatically.

        Args:
            user_id: The player.
            title: Game title (e.g. 'madden26').
            impact_rankings: Optional ImpactRank data to drive step priority.

        Returns:
            WeeklyRoadmap for the current week.
        """
        key = (user_id, title)
        impact_rankings = impact_rankings or []

        # Ensure phase is initialised
        if key not in self._phases:
            self._phases[key] = MasteryPhase.BASE

        current_phase = self._phases[key]
        week_num = self._week.get(key, 0) + 1
        self._week[key] = week_num

        config = self._config.get(user_id, {})
        max_hours = config.get("max_hours_per_week", DEFAULT_MAX_HOURS_PER_WEEK)
        max_installs = config.get("max_active_installs", DEFAULT_MAX_ACTIVE_INSTALLS)

        # Build steps from impact rankings for the current phase
        steps: list[ProgressionStep] = []
        for i, ranking in enumerate(impact_rankings[:max_installs], start=1):
            label = ranking.get("label", f"Step {i}")
            description = ranking.get("description", "")
            score = ranking.get("composite_score", 0.0)
            hours = ranking.get("estimated_hours", 2.0)

            step = ProgressionStep(
                label=label,
                description=description,
                phase=current_phase,
                impact_rank_score=min(score, 1.0),
                estimated_hours=max(hours, 0.5),
                order=i,
            )
            steps.append(step)

        # If no rankings provided, generate default steps for the phase
        if not steps:
            steps = self._generate_default_steps(current_phase)

        # Apply overload throttling
        steps, is_overloaded, total_hours = self._throttle_steps(steps, max_hours)

        # Store steps
        existing = self._steps.get(key, [])
        self._steps[key] = existing + steps

        roadmap = WeeklyRoadmap(
            user_id=user_id,
            title=title,
            week_number=week_num,
            current_phase=current_phase,
            steps=steps,
            total_estimated_hours=total_hours,
            max_hours_per_week=max_hours,
            is_overloaded=is_overloaded,
        )
        logger.info(
            "Generated week %d roadmap for user=%s title=%s phase=%s "
            "steps=%d hours=%.1f overloaded=%s",
            week_num, user_id, title, current_phase.value,
            len(steps), total_hours, is_overloaded,
        )
        return roadmap

    # ------------------------------------------------------------------
    # Phase management
    # ------------------------------------------------------------------

    def get_current_phase(
        self,
        user_id: str,
        title: str,
    ) -> MasteryPhase:
        """Return which mastery phase the player is currently in.

        Args:
            user_id: The player.
            title: Game title.

        Returns:
            Current MasteryPhase (defaults to BASE if not set).
        """
        return self._phases.get((user_id, title), MasteryPhase.BASE)

    def advance_phase(
        self,
        user_id: str,
        title: str,
    ) -> MasteryPhase:
        """Move to the next mastery phase when the player is ready.

        Progression: Base -> Pressure -> Anti-Meta -> Tournament.
        If already at Tournament, stays at Tournament.

        Args:
            user_id: The player.
            title: Game title.

        Returns:
            The new MasteryPhase after advancement.
        """
        key = (user_id, title)
        current = self._phases.get(key, MasteryPhase.BASE)
        current_idx = PHASE_ORDER.index(current)

        if current_idx < len(PHASE_ORDER) - 1:
            new_phase = PHASE_ORDER[current_idx + 1]
            self._phases[key] = new_phase
            logger.info(
                "Advanced user=%s title=%s from %s to %s",
                user_id, title, current.value, new_phase.value,
            )
            return new_phase

        logger.info(
            "User=%s title=%s already at final phase %s",
            user_id, title, current.value,
        )
        return current

    # ------------------------------------------------------------------
    # Next steps
    # ------------------------------------------------------------------

    def get_next_steps(
        self,
        user_id: str,
        title: str,
        count: int = 3,
    ) -> list[ProgressionStep]:
        """Return the next N things to learn or practice.

        Filters to pending steps in the current phase, ordered by
        ImpactRank score (highest priority first).

        Args:
            user_id: The player.
            title: Game title.
            count: Number of steps to return.

        Returns:
            List of up to ``count`` ProgressionSteps.
        """
        key = (user_id, title)
        all_steps = self._steps.get(key, [])
        current_phase = self.get_current_phase(user_id, title)

        # Filter to pending steps in current phase
        pending = [
            s for s in all_steps
            if s.phase == current_phase and s.status == InstallStatus.PENDING
        ]

        # Sort by impact rank score descending
        pending.sort(key=lambda s: s.impact_rank_score, reverse=True)

        return pending[:count]

    # ------------------------------------------------------------------
    # Overload detection
    # ------------------------------------------------------------------

    def check_overload(
        self,
        user_id: str,
    ) -> OverloadCheck:
        """Check whether a player is being asked to install too much.

        Looks across all titles for the user and checks total active
        installs and hours against thresholds.

        Args:
            user_id: The player.

        Returns:
            OverloadCheck with status and recommendation.
        """
        config = self._config.get(user_id, {})
        max_hours = config.get("max_hours_per_week", DEFAULT_MAX_HOURS_PER_WEEK)
        max_installs = config.get("max_active_installs", DEFAULT_MAX_ACTIVE_INSTALLS)

        # Count active installs across all titles
        active_count = 0
        active_hours = 0.0
        for key, steps in self._steps.items():
            if key[0] != user_id:
                continue
            for step in steps:
                if step.status in (InstallStatus.PENDING, InstallStatus.IN_PROGRESS):
                    active_count += 1
                    active_hours += step.estimated_hours

        is_overloaded = active_count > max_installs or active_hours > max_hours

        recommendation = ""
        if is_overloaded:
            if active_hours > max_hours:
                recommendation = (
                    f"Throttle: {active_hours:.1f}h active exceeds {max_hours:.1f}h limit. "
                    "Complete or skip existing installs before adding more."
                )
            else:
                recommendation = (
                    f"Throttle: {active_count} active installs exceeds {max_installs} limit. "
                    "Focus on mastering current items first."
                )

        result = OverloadCheck(
            user_id=user_id,
            is_overloaded=is_overloaded,
            active_installs=active_count,
            active_hours=active_hours,
            max_hours=max_hours,
            recommendation=recommendation,
        )
        logger.info(
            "Overload check for user=%s: overloaded=%s installs=%d hours=%.1f",
            user_id, is_overloaded, active_count, active_hours,
        )
        return result

    # ------------------------------------------------------------------
    # Mastery progress
    # ------------------------------------------------------------------

    def get_mastery_progress(
        self,
        user_id: str,
        title: str,
    ) -> list[PhaseProgress]:
        """Return percent complete per mastery phase.

        Args:
            user_id: The player.
            title: Game title.

        Returns:
            List of PhaseProgress for all four phases.
        """
        key = (user_id, title)
        all_steps = self._steps.get(key, [])
        current_phase = self.get_current_phase(user_id, title)

        progress_list: list[PhaseProgress] = []
        for phase in PHASE_ORDER:
            phase_steps = [s for s in all_steps if s.phase == phase]
            total = len(phase_steps)
            completed = sum(
                1 for s in phase_steps if s.status == InstallStatus.MASTERED
            )
            pct = (completed / total * 100.0) if total > 0 else 0.0

            # A phase is unlocked if it's the current phase or any previous phase
            phase_idx = PHASE_ORDER.index(phase)
            current_idx = PHASE_ORDER.index(current_phase)

            progress = PhaseProgress(
                phase=phase,
                total_steps=total,
                completed_steps=completed,
                mastery_pct=round(pct, 1),
                is_current=(phase == current_phase),
                is_unlocked=(phase_idx <= current_idx),
            )
            progress_list.append(progress)

        return progress_list

    # ------------------------------------------------------------------
    # Configuration
    # ------------------------------------------------------------------

    def configure(
        self,
        user_id: str,
        max_hours_per_week: float | None = None,
        max_active_installs: int | None = None,
    ) -> None:
        """Update throttle configuration for a user.

        Args:
            user_id: The player.
            max_hours_per_week: Override max weekly hours.
            max_active_installs: Override max concurrent installs.
        """
        config = self._config.setdefault(user_id, {})
        if max_hours_per_week is not None:
            config["max_hours_per_week"] = max_hours_per_week
        if max_active_installs is not None:
            config["max_active_installs"] = max_active_installs

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _generate_default_steps(
        self,
        phase: MasteryPhase,
    ) -> list[ProgressionStep]:
        """Generate default progression steps for a phase.

        Used when no ImpactRank data is available to drive step creation.
        """
        defaults: dict[MasteryPhase, list[dict]] = {
            MasteryPhase.BASE: [
                {"label": "Learn base formations", "hours": 2.0},
                {"label": "Master core play calls", "hours": 3.0},
                {"label": "Understand base reads", "hours": 2.0},
            ],
            MasteryPhase.PRESSURE: [
                {"label": "Identify blitz packages", "hours": 2.0},
                {"label": "Practice hot routes under pressure", "hours": 3.0},
                {"label": "Master protection adjustments", "hours": 2.5},
            ],
            MasteryPhase.ANTI_META: [
                {"label": "Scout opponent meta tendencies", "hours": 2.0},
                {"label": "Install counter-meta packages", "hours": 3.0},
                {"label": "Practice anti-meta audibles", "hours": 2.5},
            ],
            MasteryPhase.TOURNAMENT: [
                {"label": "Full gameplan integration", "hours": 3.0},
                {"label": "Situational mastery drills", "hours": 3.0},
                {"label": "Pressure simulation practice", "hours": 2.0},
            ],
        }

        steps: list[ProgressionStep] = []
        for i, step_data in enumerate(defaults.get(phase, []), start=1):
            step = ProgressionStep(
                label=step_data["label"],
                description=f"Phase: {phase.value} — {step_data['label']}",
                phase=phase,
                estimated_hours=step_data["hours"],
                order=i,
            )
            steps.append(step)

        return steps

    def _throttle_steps(
        self,
        steps: list[ProgressionStep],
        max_hours: float,
    ) -> tuple[list[ProgressionStep], bool, float]:
        """Apply overload throttling to a list of steps.

        Keeps adding steps until the hour budget is exhausted.

        Returns:
            Tuple of (throttled steps, was_overloaded, total_hours).
        """
        total_hours = sum(s.estimated_hours for s in steps)

        if total_hours <= max_hours:
            return steps, False, total_hours

        # Throttle: keep steps until we hit the budget
        throttled: list[ProgressionStep] = []
        running_hours = 0.0
        for step in steps:
            if running_hours + step.estimated_hours > max_hours:
                break
            throttled.append(step)
            running_hours += step.estimated_hours

        # Always include at least one step
        if not throttled and steps:
            throttled.append(steps[0])
            running_hours = steps[0].estimated_hours

        logger.info(
            "Throttled %d -> %d steps (%.1fh -> %.1fh, max=%.1fh)",
            len(steps), len(throttled), total_hours, running_hours, max_hours,
        )
        return throttled, True, running_hours


# Module-level singleton for use by the API layer
progression_os_engine = ProgressionOS()
