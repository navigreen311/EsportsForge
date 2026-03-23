"""FortniteTwin — build style, edit confidence, zone discipline, material management.

Aggregates data from BuildForge, EditForge, and ZoneForge to construct a
complete digital twin profile for a Fortnite player. Anti-cheat verified.
"""

from __future__ import annotations

import logging
import statistics
from collections import defaultdict

from app.schemas.fortnite.gameplay import (
    AntiCheatFlag,
    BuildForgeReport,
    BuildStyleProfile,
    BuildType,
    EditConfidence,
    EditDrillResult,
    EditShape,
    EditSpeedProfile,
    FortniteTwinProfile,
    MaterialManagement,
    MaterialType,
    MasteryTier,
    RotationPlan,
    ZoneDiscipline,
)

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Build style classification
# ---------------------------------------------------------------------------

BUILD_STYLE_LABELS: dict[str, dict[str, float]] = {
    "cranker": {"speed_weight": 0.8, "accuracy_weight": 0.2, "mat_efficiency": 0.3},
    "boxer": {"speed_weight": 0.3, "accuracy_weight": 0.7, "mat_efficiency": 0.6},
    "piece_controller": {"speed_weight": 0.6, "accuracy_weight": 0.8, "mat_efficiency": 0.5},
    "w_keyer": {"speed_weight": 0.9, "accuracy_weight": 0.4, "mat_efficiency": 0.2},
    "defensive_builder": {"speed_weight": 0.4, "accuracy_weight": 0.9, "mat_efficiency": 0.8},
}

MASTERY_ORDER = [
    MasteryTier.BEGINNER,
    MasteryTier.DEVELOPING,
    MasteryTier.COMPETENT,
    MasteryTier.ADVANCED,
    MasteryTier.ELITE,
    MasteryTier.PRO,
]


class FortniteTwin:
    """Digital twin builder for Fortnite players.

    Aggregates build, edit, zone, and material data into a unified profile
    with strengths, weaknesses, and recommended focus areas.
    """

    # ------------------------------------------------------------------
    # Build style analysis
    # ------------------------------------------------------------------

    def analyze_build_style(
        self,
        build_report: BuildForgeReport,
    ) -> BuildStyleProfile:
        """Classify player's build style from BuildForge data."""
        if not build_report.sequences_analyzed:
            return BuildStyleProfile(primary_style="unknown")

        analyses = build_report.sequences_analyzed

        # Speed: ratio of actual to target (lower = faster)
        speed_ratios = [
            a.total_time_ms / a.target_time_ms
            for a in analyses if a.target_time_ms > 0
        ]
        avg_speed_ratio = statistics.mean(speed_ratios) if speed_ratios else 2.0

        # Accuracy
        avg_accuracy = statistics.mean(a.placement_accuracy for a in analyses)

        # Material efficiency (inverse of overbuilding)
        total_mats = sum(
            sum(a.material_used.values()) for a in analyses
        )
        expected_mats = len(analyses) * 50  # rough baseline
        mat_efficiency = min(1.0, expected_mats / max(total_mats, 1))

        # Classify style
        speed_score = max(0.0, 1.0 - avg_speed_ratio)
        best_style = "piece_controller"
        best_fit = -1.0

        for style, weights in BUILD_STYLE_LABELS.items():
            fit = (
                speed_score * weights["speed_weight"]
                + avg_accuracy * weights["accuracy_weight"]
                + mat_efficiency * weights["mat_efficiency"]
            )
            if fit > best_fit:
                best_fit = fit
                best_style = style

        # Preferred sequences (most practiced)
        seq_counts: dict[BuildType, int] = defaultdict(int)
        for a in analyses:
            seq_counts[a.build_type] += 1
        preferred = sorted(seq_counts, key=seq_counts.get, reverse=True)[:3]  # type: ignore[arg-type]

        # Material preference
        mat_totals: dict[MaterialType, int] = defaultdict(int)
        for a in analyses:
            for mat, count in a.material_used.items():
                mat_totals[mat] += count
        mat_pref = max(mat_totals, key=mat_totals.get) if mat_totals else MaterialType.WOOD  # type: ignore[arg-type]

        overbuilding = round(1.0 - mat_efficiency, 3)

        return BuildStyleProfile(
            primary_style=best_style,
            build_speed_tier=build_report.overall_mastery,
            preferred_sequences=preferred,
            material_preference=mat_pref,
            overbuilding_index=overbuilding,
        )

    # ------------------------------------------------------------------
    # Edit confidence
    # ------------------------------------------------------------------

    def analyze_edit_confidence(
        self,
        speed_profile: EditSpeedProfile,
        drill_results: list[EditDrillResult] | None = None,
    ) -> EditConfidence:
        """Build edit confidence profile from EditForge data."""
        if not speed_profile.shape_speeds:
            return EditConfidence()

        fastest = min(speed_profile.shape_speeds, key=speed_profile.shape_speeds.get)  # type: ignore[arg-type]
        slowest = max(speed_profile.shape_speeds, key=speed_profile.shape_speeds.get)  # type: ignore[arg-type]
        avg_speed = statistics.mean(speed_profile.shape_speeds.values())

        # Pressure reliability from drill results
        pressure_rel = 1.0 - speed_profile.pressure_penalty

        # Edit-to-shoot speed (estimate from drill data)
        edit_to_shoot = 0.0
        if drill_results:
            shoot_times = [
                d.avg_speed_ms * 0.3  # rough estimate: 30% of edit time
                for d in drill_results if d.avg_speed_ms > 0
            ]
            edit_to_shoot = statistics.mean(shoot_times) if shoot_times else 0.0

        return EditConfidence(
            fastest_shape=fastest,
            slowest_shape=slowest,
            avg_speed_ms=round(avg_speed, 1),
            pressure_reliability=round(pressure_rel, 3),
            edit_to_shoot_speed_ms=round(edit_to_shoot, 1),
        )

    # ------------------------------------------------------------------
    # Zone discipline
    # ------------------------------------------------------------------

    def analyze_zone_discipline(
        self,
        rotation_plans: list[RotationPlan],
    ) -> ZoneDiscipline:
        """Analyze zone discipline from rotation history."""
        if not rotation_plans:
            return ZoneDiscipline()

        # Timing classification based on zone tax time pressure
        timing_scores: list[float] = [p.zone_tax.time_pressure for p in rotation_plans]
        avg_timing = statistics.mean(timing_scores)

        if avg_timing < 0.2:
            timing_label = "early"
        elif avg_timing < 0.4:
            timing_label = "on_time"
        elif avg_timing < 0.7:
            timing_label = "late"
        else:
            timing_label = "storm_surfer"

        # Zone death rate (confidence < 0.2 suggests storm death)
        zone_deaths = sum(1 for p in rotation_plans if p.confidence < 0.2)
        death_rate = zone_deaths / len(rotation_plans)

        # Positioning score (inverse of zone tax)
        positioning = statistics.mean(
            1.0 - p.zone_tax.total_tax_score for p in rotation_plans
        )

        # Rotation fight win rate (plans with low fight prob and high confidence)
        fight_situations = [
            p for p in rotation_plans if p.zone_tax.fight_probability > 0.3
        ]
        fight_wins = sum(1 for p in fight_situations if p.confidence > 0.5)
        fight_win_rate = fight_wins / len(fight_situations) if fight_situations else 0.0

        return ZoneDiscipline(
            avg_rotation_timing=timing_label,
            zone_death_rate=round(death_rate, 3),
            positioning_score=round(positioning, 3),
            rotation_fight_win_rate=round(fight_win_rate, 3),
        )

    # ------------------------------------------------------------------
    # Material management
    # ------------------------------------------------------------------

    def analyze_material_management(
        self,
        build_report: BuildForgeReport,
        rotation_plans: list[RotationPlan] | None = None,
    ) -> MaterialManagement:
        """Analyze material management patterns."""
        if not build_report.sequences_analyzed:
            return MaterialManagement()

        analyses = build_report.sequences_analyzed

        # Average mats used per sequence
        mat_totals: dict[MaterialType, list[int]] = defaultdict(list)
        for a in analyses:
            for mat, count in a.material_used.items():
                mat_totals[mat].append(count)

        avg_mats = {
            mat: int(statistics.mean(counts)) if counts else 0
            for mat, counts in mat_totals.items()
        }

        # Farming efficiency (estimated from rotation data)
        farming_eff = 0.5  # default
        if rotation_plans:
            # Players with good mats in late game have good farming
            late_plans = [
                p for p in rotation_plans
                if p.storm_state.zone_phase.value in ("moving_zone", "half_half", "endgame")
            ]
            if late_plans:
                avg_late_mats = statistics.mean(
                    sum(p.player_position.materials.values()) for p in late_plans
                )
                farming_eff = min(1.0, avg_late_mats / 1500)  # 1500 = ideal late mats

        # Waste index (inverse of placement accuracy)
        waste = 1.0 - statistics.mean(a.placement_accuracy for a in analyses)

        # Material split balance
        all_counts = list(avg_mats.values())
        if all_counts and max(all_counts) > 0:
            total = sum(all_counts)
            expected_each = total / max(len(all_counts), 1)
            deviations = [abs(c - expected_each) for c in all_counts]
            max_deviation = max(total, 1)
            balance = 1.0 - (sum(deviations) / max_deviation)
        else:
            balance = 0.0

        return MaterialManagement(
            avg_mats_at_endgame=avg_mats,
            farming_efficiency=round(farming_eff, 3),
            waste_index=round(waste, 3),
            material_split_balance=round(max(0.0, balance), 3),
        )

    # ------------------------------------------------------------------
    # Anti-cheat aggregation
    # ------------------------------------------------------------------

    def aggregate_anti_cheat(
        self,
        build_report: BuildForgeReport | None = None,
        edit_profile: EditSpeedProfile | None = None,
        drill_results: list[EditDrillResult] | None = None,
    ) -> AntiCheatFlag:
        """Aggregate anti-cheat flags from all sources."""
        flags: list[AntiCheatFlag] = []

        if build_report:
            flags.append(build_report.anti_cheat_status)
        if edit_profile:
            flags.append(edit_profile.anti_cheat)
        if drill_results:
            flags.extend(d.anti_cheat for d in drill_results)

        # Return most severe flag
        severity = [
            AntiCheatFlag.MACRO_DETECTED,
            AntiCheatFlag.INHUMAN_CONSISTENCY,
            AntiCheatFlag.INPUT_ANOMALY,
            AntiCheatFlag.TIMING_ANOMALY,
            AntiCheatFlag.REVIEW_REQUIRED,
        ]
        for flag in severity:
            if flag in flags:
                return flag

        return AntiCheatFlag.CLEAN

    # ------------------------------------------------------------------
    # Full twin profile
    # ------------------------------------------------------------------

    def build_twin(
        self,
        user_id: str,
        build_report: BuildForgeReport | None = None,
        edit_profile: EditSpeedProfile | None = None,
        edit_drills: list[EditDrillResult] | None = None,
        rotation_plans: list[RotationPlan] | None = None,
    ) -> FortniteTwinProfile:
        """Build complete digital twin profile from all agent data."""
        # Build style
        build_style = (
            self.analyze_build_style(build_report)
            if build_report else BuildStyleProfile(primary_style="unknown")
        )

        # Edit confidence
        edit_confidence = (
            self.analyze_edit_confidence(edit_profile, edit_drills)
            if edit_profile else EditConfidence()
        )

        # Zone discipline
        zone_discipline = (
            self.analyze_zone_discipline(rotation_plans)
            if rotation_plans else ZoneDiscipline()
        )

        # Material management
        material_mgmt = (
            self.analyze_material_management(build_report, rotation_plans)
            if build_report else MaterialManagement()
        )

        # Anti-cheat
        ac_status = self.aggregate_anti_cheat(build_report, edit_profile, edit_drills)

        # Overall rating (weighted composite)
        rating = self._compute_overall_rating(
            build_style, edit_confidence, zone_discipline, material_mgmt
        )

        # Strengths and weaknesses
        strengths, weaknesses = self._identify_strengths_weaknesses(
            build_style, edit_confidence, zone_discipline, material_mgmt
        )

        # Recommended focus
        focus = self._recommend_focus(weaknesses)

        return FortniteTwinProfile(
            user_id=user_id,
            build_style=build_style,
            edit_confidence=edit_confidence,
            zone_discipline=zone_discipline,
            material_management=material_mgmt,
            overall_rating=round(rating, 1),
            anti_cheat_status=ac_status,
            strengths=strengths,
            weaknesses=weaknesses,
            recommended_focus=focus,
        )

    def _compute_overall_rating(
        self,
        build: BuildStyleProfile,
        edit: EditConfidence,
        zone: ZoneDiscipline,
        mats: MaterialManagement,
    ) -> float:
        """Compute overall rating (0-100) from component profiles."""
        build_score = MASTERY_ORDER.index(build.build_speed_tier) / (len(MASTERY_ORDER) - 1) * 100

        # Edit score from speed (lower = better, benchmark ~200ms)
        edit_score = max(0, min(100, (1.0 - (edit.avg_speed_ms / 500)) * 100)) if edit.avg_speed_ms > 0 else 0

        zone_score = zone.positioning_score * 100

        mat_score = (mats.farming_efficiency * 50 + (1.0 - mats.waste_index) * 50)

        return (
            build_score * 0.30
            + edit_score * 0.25
            + zone_score * 0.25
            + mat_score * 0.20
        )

    def _identify_strengths_weaknesses(
        self,
        build: BuildStyleProfile,
        edit: EditConfidence,
        zone: ZoneDiscipline,
        mats: MaterialManagement,
    ) -> tuple[list[str], list[str]]:
        """Identify player strengths and weaknesses."""
        strengths: list[str] = []
        weaknesses: list[str] = []

        # Build
        tier_idx = MASTERY_ORDER.index(build.build_speed_tier)
        if tier_idx >= 4:
            strengths.append(f"Elite build speed ({build.primary_style} style)")
        elif tier_idx >= 3:
            strengths.append(f"Strong building ({build.primary_style})")
        elif tier_idx <= 1:
            weaknesses.append("Building speed needs significant improvement")

        if build.overbuilding_index > 0.6:
            weaknesses.append("Overbuilding — wasting materials on unnecessary builds")
        elif build.overbuilding_index < 0.2:
            strengths.append("Efficient builder — minimal material waste")

        # Edit
        if edit.avg_speed_ms > 0:
            if edit.avg_speed_ms < 200:
                strengths.append("Fast editor — sub-200ms average")
            elif edit.avg_speed_ms > 350:
                weaknesses.append("Edit speed is slow — above 350ms average")

        if edit.pressure_reliability > 0.8:
            strengths.append("Clutch editor — maintains speed under pressure")
        elif edit.pressure_reliability < 0.5 and edit.avg_speed_ms > 0:
            weaknesses.append("Edit accuracy drops significantly under pressure")

        # Zone
        if zone.positioning_score > 0.7:
            strengths.append("Excellent zone positioning and rotation timing")
        elif zone.positioning_score < 0.4 and zone.positioning_score > 0:
            weaknesses.append("Poor zone discipline — frequently out of position")

        if zone.zone_death_rate > 0.15:
            weaknesses.append(f"High storm death rate ({zone.zone_death_rate:.0%})")

        # Materials
        if mats.farming_efficiency > 0.7:
            strengths.append("Strong material farming and management")
        elif mats.farming_efficiency < 0.3 and mats.farming_efficiency > 0:
            weaknesses.append("Low material farming efficiency")

        return strengths, weaknesses

    def _recommend_focus(self, weaknesses: list[str]) -> list[str]:
        """Generate recommended focus areas from weaknesses."""
        focus: list[str] = []
        for w in weaknesses[:3]:
            if "build" in w.lower():
                focus.append("Practice build sequences in creative mode — 15min daily")
            elif "edit" in w.lower() and "pressure" in w.lower():
                focus.append("Run pressure edit drills with EditForge — focus on composure")
            elif "edit" in w.lower():
                focus.append("Isolate slowest edit shapes and drill 50 reps each")
            elif "zone" in w.lower() or "storm" in w.lower():
                focus.append("Review rotation VODs — practice early rotates in arena")
            elif "material" in w.lower() or "farm" in w.lower():
                focus.append("Farm to 1500 mats before second zone — prioritize metal")
            elif "overbuild" in w.lower():
                focus.append("Practice minimal-build box fights to reduce waste")
        return focus
