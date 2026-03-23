"""EditForge — edit speed trainer per shape, pressure edit trainer, Dynamic Calibration.

Measures edit speed across all tile shapes (triangle, arch, door, window, etc.),
tracks performance under pressure, and dynamically calibrates difficulty.
Anti-cheat verification for inhuman edit speeds.
"""

from __future__ import annotations

import logging
import statistics
from collections import defaultdict

from app.schemas.fortnite.gameplay import (
    AntiCheatFlag,
    EditAttempt,
    EditDrillResult,
    EditShape,
    EditSpeedProfile,
    MasteryTier,
)

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Benchmark targets per shape (ms) — pro-level reference
# ---------------------------------------------------------------------------

SHAPE_BENCHMARKS: dict[EditShape, int] = {
    EditShape.TRIANGLE: 180,
    EditShape.ARCH: 200,
    EditShape.DOOR: 220,
    EditShape.WINDOW: 190,
    EditShape.HALF_WALL: 160,
    EditShape.CORNER: 210,
    EditShape.PEANUT: 250,
    EditShape.STAIRS_EDIT: 230,
}

# Mastery tier thresholds — ratio of actual speed to benchmark
MASTERY_RATIO_THRESHOLDS: dict[MasteryTier, float] = {
    MasteryTier.PRO: 0.85,
    MasteryTier.ELITE: 1.0,
    MasteryTier.ADVANCED: 1.2,
    MasteryTier.COMPETENT: 1.5,
    MasteryTier.DEVELOPING: 2.0,
    MasteryTier.BEGINNER: float("inf"),
}

# Anti-cheat
ANTI_CHEAT_MIN_EDIT_MS = 50  # Sub-50ms edits are physically impossible
ANTI_CHEAT_PRESSURE_BOOST_LIMIT = 0.15  # Cannot be >15% FASTER under pressure

# Dynamic calibration
CALIBRATION_INCREASE_THRESHOLD = 0.85  # accuracy above this -> harder
CALIBRATION_DECREASE_THRESHOLD = 0.50  # accuracy below this -> easier


class EditForge:
    """Edit speed trainer with dynamic calibration and anti-cheat.

    Tracks per-shape edit times, measures pressure impact, calibrates
    drill difficulty dynamically, and flags suspicious input patterns.
    """

    def __init__(self) -> None:
        self._calibration_state: dict[str, dict[str, float]] = defaultdict(
            lambda: {"speed_multiplier": 1.0, "pressure_level": 0.5, "version": 1}
        )

    # ------------------------------------------------------------------
    # Anti-cheat
    # ------------------------------------------------------------------

    def verify_anti_cheat(self, attempts: list[EditAttempt]) -> AntiCheatFlag:
        """Verify edit attempts for anti-cheat anomalies.

        Checks:
        - Edits faster than physically possible
        - Being faster under pressure (unnatural)
        - Impossibly consistent timing across shapes
        """
        if not attempts:
            return AntiCheatFlag.CLEAN

        times = [a.time_ms for a in attempts if a.successful]
        if not times:
            return AntiCheatFlag.CLEAN

        # Sub-minimum speed
        if any(t < ANTI_CHEAT_MIN_EDIT_MS for t in times):
            logger.warning("Anti-cheat: edit time below %dms detected", ANTI_CHEAT_MIN_EDIT_MS)
            return AntiCheatFlag.TIMING_ANOMALY

        # Pressure comparison — cannot be significantly faster under pressure
        pressure_times = [a.time_ms for a in attempts if a.under_pressure and a.successful]
        no_pressure_times = [a.time_ms for a in attempts if not a.under_pressure and a.successful]

        if pressure_times and no_pressure_times:
            avg_pressure = statistics.mean(pressure_times)
            avg_calm = statistics.mean(no_pressure_times)
            if avg_calm > 0 and (avg_calm - avg_pressure) / avg_calm > ANTI_CHEAT_PRESSURE_BOOST_LIMIT:
                logger.warning("Anti-cheat: suspiciously faster under pressure")
                return AntiCheatFlag.INPUT_ANOMALY

        # Identical timings (macro detection)
        if len(times) >= 5:
            unique = set(times)
            if len(unique) <= 2:
                logger.warning("Anti-cheat: near-identical edit timings suggest macro")
                return AntiCheatFlag.MACRO_DETECTED

        return AntiCheatFlag.CLEAN

    # ------------------------------------------------------------------
    # Speed profiling
    # ------------------------------------------------------------------

    def build_speed_profile(
        self,
        user_id: str,
        attempts: list[EditAttempt],
    ) -> EditSpeedProfile:
        """Build a speed profile from a set of edit attempts."""
        shape_times: dict[EditShape, list[int]] = defaultdict(list)
        shape_hits: dict[EditShape, list[bool]] = defaultdict(list)
        pressure_hits: list[bool] = []
        calm_hits: list[bool] = []

        for a in attempts:
            if a.successful:
                shape_times[a.shape].append(a.time_ms)
            shape_hits[a.shape].append(a.successful)
            if a.under_pressure:
                pressure_hits.append(a.successful)
            else:
                calm_hits.append(a.successful)

        shape_speeds = {
            shape: round(statistics.mean(times), 1)
            for shape, times in shape_times.items()
            if times
        }
        shape_accuracy = {
            shape: round(sum(hits) / len(hits), 3)
            for shape, hits in shape_hits.items()
            if hits
        }

        # Pressure penalty
        pressure_acc = sum(pressure_hits) / len(pressure_hits) if pressure_hits else 1.0
        calm_acc = sum(calm_hits) / len(calm_hits) if calm_hits else 1.0
        pressure_penalty = max(0.0, calm_acc - pressure_acc)

        # Overall mastery
        all_ratios: list[float] = []
        for shape, avg_ms in shape_speeds.items():
            benchmark = SHAPE_BENCHMARKS.get(shape, 200)
            all_ratios.append(avg_ms / benchmark)
        avg_ratio = statistics.mean(all_ratios) if all_ratios else 3.0
        mastery = self._ratio_to_mastery(avg_ratio)

        ac_flag = self.verify_anti_cheat(attempts)

        return EditSpeedProfile(
            user_id=user_id,
            shape_speeds=shape_speeds,
            shape_accuracy=shape_accuracy,
            pressure_penalty=round(pressure_penalty, 3),
            mastery_tier=mastery,
            anti_cheat=ac_flag,
            calibration_version=int(self._calibration_state[user_id].get("version", 1)),
        )

    def _ratio_to_mastery(self, ratio: float) -> MasteryTier:
        """Convert speed ratio to mastery tier."""
        for tier in [
            MasteryTier.PRO,
            MasteryTier.ELITE,
            MasteryTier.ADVANCED,
            MasteryTier.COMPETENT,
            MasteryTier.DEVELOPING,
        ]:
            if ratio <= MASTERY_RATIO_THRESHOLDS[tier]:
                return tier
        return MasteryTier.BEGINNER

    # ------------------------------------------------------------------
    # Dynamic Calibration
    # ------------------------------------------------------------------

    def get_calibration(self, user_id: str) -> dict[str, float]:
        """Return current dynamic calibration state for a user."""
        return dict(self._calibration_state[user_id])

    def update_calibration(self, user_id: str, accuracy: float) -> dict[str, float]:
        """Update dynamic calibration based on drill accuracy.

        If accuracy is high, increase difficulty (faster targets, more pressure).
        If accuracy is low, decrease difficulty.
        """
        state = self._calibration_state[user_id]

        if accuracy >= CALIBRATION_INCREASE_THRESHOLD:
            state["speed_multiplier"] = max(0.5, state["speed_multiplier"] - 0.05)
            state["pressure_level"] = min(1.0, state["pressure_level"] + 0.1)
        elif accuracy <= CALIBRATION_DECREASE_THRESHOLD:
            state["speed_multiplier"] = min(2.0, state["speed_multiplier"] + 0.05)
            state["pressure_level"] = max(0.0, state["pressure_level"] - 0.1)

        state["version"] = state.get("version", 1) + 1
        return dict(state)

    # ------------------------------------------------------------------
    # Drill execution
    # ------------------------------------------------------------------

    def evaluate_drill(
        self,
        user_id: str,
        attempts: list[EditAttempt],
    ) -> EditDrillResult:
        """Evaluate an edit drill session and update calibration."""
        successful = [a for a in attempts if a.successful]
        accuracy = len(successful) / len(attempts) if attempts else 0.0

        pressure_attempts = [a for a in attempts if a.under_pressure]
        pressure_successes = [a for a in pressure_attempts if a.successful]
        pressure_accuracy = (
            len(pressure_successes) / len(pressure_attempts)
            if pressure_attempts
            else 0.0
        )

        avg_speed = (
            statistics.mean(a.time_ms for a in successful) if successful else 0.0
        )

        shapes_drilled = list({a.shape for a in attempts})

        # Anti-cheat
        ac_flag = self.verify_anti_cheat(attempts)

        # Dynamic calibration update
        calibration = self.update_calibration(user_id, accuracy)

        # Mastery
        all_ratios = []
        for a in successful:
            benchmark = SHAPE_BENCHMARKS.get(a.shape, 200)
            all_ratios.append(a.time_ms / benchmark)
        mastery = self._ratio_to_mastery(
            statistics.mean(all_ratios) if all_ratios else 3.0
        )

        # Improvement notes
        notes = self._generate_improvement_notes(attempts, accuracy, pressure_accuracy)

        return EditDrillResult(
            user_id=user_id,
            attempts=attempts,
            avg_speed_ms=round(avg_speed, 1),
            accuracy=round(accuracy, 3),
            pressure_accuracy=round(pressure_accuracy, 3),
            shapes_drilled=shapes_drilled,
            mastery_tier=mastery,
            anti_cheat=ac_flag,
            dynamic_calibration=calibration,
            improvement_notes=notes,
        )

    def _generate_improvement_notes(
        self,
        attempts: list[EditAttempt],
        accuracy: float,
        pressure_accuracy: float,
    ) -> list[str]:
        """Generate improvement notes based on drill results."""
        notes: list[str] = []

        if accuracy < 0.6:
            notes.append(
                "Accuracy is below 60% — slow down and focus on completing "
                "each edit cleanly before increasing speed."
            )

        if pressure_accuracy < accuracy * 0.7 and accuracy > 0.5:
            notes.append(
                "Significant pressure drop-off detected. Practice edits while "
                "taking simulated damage to build composure."
            )

        # Find slowest shapes
        shape_times: dict[EditShape, list[int]] = defaultdict(list)
        for a in attempts:
            if a.successful:
                shape_times[a.shape].append(a.time_ms)

        if shape_times:
            shape_avgs = {
                s: statistics.mean(t) for s, t in shape_times.items() if t
            }
            if shape_avgs:
                slowest = max(shape_avgs, key=shape_avgs.get)  # type: ignore[arg-type]
                notes.append(
                    f"Slowest shape: {slowest.value} (avg {shape_avgs[slowest]:.0f}ms). "
                    f"Isolate this shape in practice."
                )

        reset_fails = [a for a in attempts if not a.reset_clean]
        if len(reset_fails) > len(attempts) * 0.2:
            notes.append(
                "Over 20% of edits had unclean resets. Practice the full "
                "edit-reset cycle — a failed reset wastes more time than a slow edit."
            )

        return notes
