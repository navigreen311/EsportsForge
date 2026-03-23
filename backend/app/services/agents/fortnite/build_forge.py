"""BuildForge FN — ramp-wall, 90s, waterfall, high-ground retake sequence trainer.

Analyzes build sequence execution times, placement accuracy, material efficiency,
and prescribes targeted drills. Includes anti-cheat verification for inhuman
timing patterns.
"""

from __future__ import annotations

import logging
import statistics
from collections import defaultdict

from app.schemas.fortnite.gameplay import (
    AntiCheatFlag,
    BuildDrillPrescription,
    BuildForgeReport,
    BuildSequenceAnalysis,
    BuildSequenceStep,
    BuildType,
    MaterialType,
    MasteryTier,
)

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Sequence definitions: target times (ms) and steps per build type
# ---------------------------------------------------------------------------

SEQUENCE_TEMPLATES: dict[BuildType, list[dict]] = {
    BuildType.RAMP_WALL: [
        {"step_number": 1, "action": "place wall", "target_time_ms": 80},
        {"step_number": 2, "action": "place ramp", "target_time_ms": 60},
        {"step_number": 3, "action": "jump + place wall", "target_time_ms": 120},
        {"step_number": 4, "action": "place ramp", "target_time_ms": 60},
    ],
    BuildType.NINETIES: [
        {"step_number": 1, "action": "place wall", "target_time_ms": 70},
        {"step_number": 2, "action": "place ramp + jump", "target_time_ms": 90},
        {"step_number": 3, "action": "90 turn + place wall", "target_time_ms": 100},
        {"step_number": 4, "action": "place ramp + jump", "target_time_ms": 90},
        {"step_number": 5, "action": "90 turn + place wall", "target_time_ms": 100},
        {"step_number": 6, "action": "place ramp", "target_time_ms": 80},
    ],
    BuildType.WATERFALL: [
        {"step_number": 1, "action": "jump off height", "target_time_ms": 50},
        {"step_number": 2, "action": "look down + place floor", "target_time_ms": 100},
        {"step_number": 3, "action": "place ramp under", "target_time_ms": 90},
        {"step_number": 4, "action": "continue falling + place floor", "target_time_ms": 110},
        {"step_number": 5, "action": "place ramp under", "target_time_ms": 90},
    ],
    BuildType.HIGH_GROUND_RETAKE: [
        {"step_number": 1, "action": "ramp up toward opponent", "target_time_ms": 80},
        {"step_number": 2, "action": "side jump + place floor", "target_time_ms": 130},
        {"step_number": 3, "action": "place ramp over opponent", "target_time_ms": 110},
        {"step_number": 4, "action": "place wall for cover", "target_time_ms": 80},
        {"step_number": 5, "action": "place cone for protection", "target_time_ms": 90},
        {"step_number": 6, "action": "edit cone + shotgun peek", "target_time_ms": 150},
    ],
    BuildType.DOUBLE_RAMP: [
        {"step_number": 1, "action": "place ramp + floor simultaneously", "target_time_ms": 100},
        {"step_number": 2, "action": "place ramp + floor simultaneously", "target_time_ms": 100},
        {"step_number": 3, "action": "place ramp + floor simultaneously", "target_time_ms": 100},
    ],
    BuildType.SIDE_JUMP: [
        {"step_number": 1, "action": "place ramp", "target_time_ms": 60},
        {"step_number": 2, "action": "jump sideways off ramp", "target_time_ms": 110},
        {"step_number": 3, "action": "place floor mid-air", "target_time_ms": 120},
        {"step_number": 4, "action": "place ramp on landing", "target_time_ms": 90},
    ],
    BuildType.THWIFO_CONE: [
        {"step_number": 1, "action": "place ramp toward opponent", "target_time_ms": 70},
        {"step_number": 2, "action": "jump + place floor above", "target_time_ms": 120},
        {"step_number": 3, "action": "place cone on floor", "target_time_ms": 80},
        {"step_number": 4, "action": "edit cone for peek", "target_time_ms": 140},
    ],
    BuildType.PROTECTED_RAMP_RUSH: [
        {"step_number": 1, "action": "place wall", "target_time_ms": 70},
        {"step_number": 2, "action": "place ramp", "target_time_ms": 60},
        {"step_number": 3, "action": "place floor above", "target_time_ms": 90},
        {"step_number": 4, "action": "place wall + ramp forward", "target_time_ms": 110},
    ],
}

# Target total times per build (ms) — benchmark for mastery tiers
TIER_THRESHOLDS: dict[MasteryTier, float] = {
    MasteryTier.BEGINNER: 2.0,
    MasteryTier.DEVELOPING: 1.6,
    MasteryTier.COMPETENT: 1.3,
    MasteryTier.ADVANCED: 1.1,
    MasteryTier.ELITE: 0.95,
    MasteryTier.PRO: 0.80,
}

# Anti-cheat: minimum humanly possible step time (ms)
ANTI_CHEAT_MIN_STEP_MS = 30
ANTI_CHEAT_MAX_CONSISTENCY = 0.97  # Suspiciously consistent timing


class BuildForgeFN:
    """Build sequence trainer and analyzer for Fortnite.

    Evaluates ramp-wall, 90s, waterfall, high-ground retake sequences.
    Prescribes drills, tracks mastery, and flags anti-cheat anomalies.
    """

    def get_sequence_template(self, build_type: BuildType) -> list[BuildSequenceStep]:
        """Return the reference template for a build sequence."""
        raw = SEQUENCE_TEMPLATES.get(build_type, [])
        return [BuildSequenceStep(**step) for step in raw]

    def get_target_time(self, build_type: BuildType) -> int:
        """Return total target time for a build sequence."""
        return sum(s["target_time_ms"] for s in SEQUENCE_TEMPLATES.get(build_type, []))

    # ------------------------------------------------------------------
    # Anti-cheat verification
    # ------------------------------------------------------------------

    def verify_anti_cheat(self, analysis: BuildSequenceAnalysis) -> AntiCheatFlag:
        """Check for inhuman timing or macro patterns.

        Flags:
        - Steps faster than humanly possible (< 30ms)
        - Inhuman consistency across steps (std dev too low)
        - Input anomalies (identical timings suggesting macros)
        """
        actual_times = [
            s.actual_time_ms for s in analysis.steps if s.actual_time_ms is not None
        ]

        if not actual_times:
            return AntiCheatFlag.CLEAN

        # Check for impossibly fast inputs
        if any(t < ANTI_CHEAT_MIN_STEP_MS for t in actual_times):
            logger.warning(
                "Anti-cheat: timing anomaly for user %s — sub-%dms step detected",
                analysis.user_id, ANTI_CHEAT_MIN_STEP_MS,
            )
            return AntiCheatFlag.TIMING_ANOMALY

        # Check for macro-like identical timings
        unique_times = set(actual_times)
        if len(actual_times) >= 3 and len(unique_times) == 1:
            logger.warning(
                "Anti-cheat: macro detected for user %s — identical step times",
                analysis.user_id,
            )
            return AntiCheatFlag.MACRO_DETECTED

        # Check for inhuman consistency
        if len(actual_times) >= 4:
            mean_t = statistics.mean(actual_times)
            if mean_t > 0:
                cv = statistics.stdev(actual_times) / mean_t
                if cv < 0.03:  # Coefficient of variation < 3%
                    logger.warning(
                        "Anti-cheat: inhuman consistency for user %s (CV=%.4f)",
                        analysis.user_id, cv,
                    )
                    return AntiCheatFlag.INHUMAN_CONSISTENCY

        return AntiCheatFlag.CLEAN

    # ------------------------------------------------------------------
    # Analysis
    # ------------------------------------------------------------------

    def _determine_mastery(self, ratio: float) -> MasteryTier:
        """Determine mastery tier from time ratio (actual / target)."""
        for tier in [
            MasteryTier.PRO,
            MasteryTier.ELITE,
            MasteryTier.ADVANCED,
            MasteryTier.COMPETENT,
            MasteryTier.DEVELOPING,
        ]:
            if ratio <= TIER_THRESHOLDS[tier]:
                return tier
        return MasteryTier.BEGINNER

    def analyze_sequence(
        self,
        user_id: str,
        build_type: BuildType,
        step_times_ms: list[int],
        placement_hits: int,
        placement_total: int,
        materials: dict[str, int] | None = None,
    ) -> BuildSequenceAnalysis:
        """Analyze a single build sequence attempt.

        Args:
            user_id: Player identifier.
            build_type: Which build sequence was attempted.
            step_times_ms: Actual time per step in ms.
            placement_hits: Number of correctly placed pieces.
            placement_total: Total placement attempts.
            materials: Materials used {wood: n, brick: n, metal: n}.
        """
        template = SEQUENCE_TEMPLATES.get(build_type, [])
        steps: list[BuildSequenceStep] = []

        for i, raw in enumerate(template):
            actual = step_times_ms[i] if i < len(step_times_ms) else None
            steps.append(BuildSequenceStep(
                step_number=raw["step_number"],
                action=raw["action"],
                target_time_ms=raw["target_time_ms"],
                actual_time_ms=actual,
            ))

        total_actual = sum(step_times_ms)
        target_total = self.get_target_time(build_type)
        ratio = total_actual / target_total if target_total > 0 else 2.0

        accuracy = placement_hits / placement_total if placement_total > 0 else 0.0
        efficiency = min(1.0, (accuracy * 0.6) + ((1.0 / max(ratio, 0.01)) * 0.4))

        mat_used: dict[MaterialType, int] = {}
        if materials:
            for k, v in materials.items():
                try:
                    mat_used[MaterialType(k)] = v
                except ValueError:
                    pass

        analysis = BuildSequenceAnalysis(
            user_id=user_id,
            build_type=build_type,
            steps=steps,
            total_time_ms=total_actual,
            target_time_ms=target_total,
            efficiency_score=round(efficiency, 3),
            placement_accuracy=round(accuracy, 3),
            material_used=mat_used,
            mastery_tier=self._determine_mastery(ratio),
        )

        # Anti-cheat check
        analysis.anti_cheat = self.verify_anti_cheat(analysis)

        # Generate tips
        analysis.improvement_tips = self._generate_tips(analysis)

        return analysis

    def _generate_tips(self, analysis: BuildSequenceAnalysis) -> list[str]:
        """Generate improvement tips based on analysis."""
        tips: list[str] = []

        if analysis.placement_accuracy < 0.8:
            tips.append(
                "Focus on placement accuracy before speed — misplaced builds "
                "waste materials and create vulnerabilities."
            )

        slow_steps = [
            s for s in analysis.steps
            if s.actual_time_ms is not None
            and s.actual_time_ms > s.target_time_ms * 1.5
        ]
        if slow_steps:
            step_names = ", ".join(s.action for s in slow_steps[:3])
            tips.append(f"Slow steps detected: {step_names}. Isolate and drill these.")

        ratio = analysis.total_time_ms / analysis.target_time_ms if analysis.target_time_ms > 0 else 2.0
        if ratio > 1.5:
            tips.append(
                "Overall speed is well above target — practice the full sequence "
                "in creative mode at half speed, then gradually increase."
            )
        elif ratio > 1.2:
            tips.append(
                "Close to target speed. Focus on smoothing transitions between steps."
            )

        if analysis.build_type == BuildType.NINETIES:
            tips.append(
                "For 90s: keep crosshair at the center-bottom of the wall placement "
                "to minimize mouse movement between wall and ramp."
            )
        elif analysis.build_type == BuildType.WATERFALL:
            tips.append(
                "For waterfalls: look straight down and time floor placements "
                "with your fall velocity. Rhythm > speed."
            )

        return tips

    # ------------------------------------------------------------------
    # Drill prescription
    # ------------------------------------------------------------------

    def prescribe_drills(
        self,
        analyses: list[BuildSequenceAnalysis],
    ) -> list[BuildDrillPrescription]:
        """Generate targeted drill prescriptions from session analyses."""
        type_scores: dict[BuildType, list[float]] = defaultdict(list)

        for a in analyses:
            type_scores[a.build_type].append(a.efficiency_score)

        drills: list[BuildDrillPrescription] = []
        for build_type, scores in type_scores.items():
            avg = statistics.mean(scores) if scores else 0.0

            if avg >= 0.85:
                continue  # No drill needed

            target = self.get_target_time(build_type)
            difficulty = max(1, min(5, int((1.0 - avg) * 5) + 1))

            focus = "placement accuracy" if avg < 0.4 else "transition speed"
            if avg < 0.6:
                focus = "overall sequence fluency"

            drills.append(BuildDrillPrescription(
                build_type=build_type,
                focus_area=focus,
                reps_prescribed=max(5, int((1.0 - avg) * 20)),
                target_time_ms=target,
                difficulty_level=difficulty,
                warm_up_sequence=[
                    f"3x slow-motion {build_type.value}",
                    f"3x medium-speed {build_type.value}",
                    f"Timed attempt x{max(3, int((1.0 - avg) * 10))}",
                ],
            ))

        return drills

    # ------------------------------------------------------------------
    # Full session report
    # ------------------------------------------------------------------

    def generate_report(
        self,
        user_id: str,
        analyses: list[BuildSequenceAnalysis],
    ) -> BuildForgeReport:
        """Generate full BuildForge session report with drills."""
        if not analyses:
            return BuildForgeReport(
                user_id=user_id,
                sequences_analyzed=[],
                overall_mastery=MasteryTier.BEGINNER,
                weakest_sequence=BuildType.RAMP_WALL,
                strongest_sequence=BuildType.RAMP_WALL,
                drills=[],
                material_efficiency=0.0,
            )

        # Find weakest / strongest
        type_efficiency: dict[BuildType, list[float]] = defaultdict(list)
        for a in analyses:
            type_efficiency[a.build_type].append(a.efficiency_score)

        avg_by_type = {
            bt: statistics.mean(scores) for bt, scores in type_efficiency.items()
        }
        weakest = min(avg_by_type, key=avg_by_type.get)  # type: ignore[arg-type]
        strongest = max(avg_by_type, key=avg_by_type.get)  # type: ignore[arg-type]

        # Overall mastery
        overall_avg = statistics.mean(a.efficiency_score for a in analyses)
        overall_mastery = self._determine_mastery(1.0 / max(overall_avg, 0.01))

        # Material efficiency (ratio of accurate placements)
        total_acc = statistics.mean(a.placement_accuracy for a in analyses)

        # Anti-cheat: flag if any analysis is flagged
        ac_flags = [a.anti_cheat for a in analyses if a.anti_cheat != AntiCheatFlag.CLEAN]
        ac_status = ac_flags[0] if ac_flags else AntiCheatFlag.CLEAN

        drills = self.prescribe_drills(analyses)

        return BuildForgeReport(
            user_id=user_id,
            sequences_analyzed=analyses,
            overall_mastery=overall_mastery,
            weakest_sequence=weakest,
            strongest_sequence=strongest,
            drills=drills,
            material_efficiency=round(total_acc, 3),
            anti_cheat_status=ac_status,
        )
