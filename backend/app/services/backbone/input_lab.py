"""InputLab — Controller telemetry diagnostics with per-input-type engines.

Three completely separate diagnostic engines (controller, KBM, fight stick),
each with its own drill generators, latency assumptions, and elite benchmarks.
"""

from __future__ import annotations

import uuid as _uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.drill import Drill
from app.models.player_profile import PlayerProfile

from app.schemas.input_lab import (
    DrillSpec,
    EliteBenchmark,
    InputDiagnosis,
    InputEvent,
    InputProfile,
    InputType,
    MechanicalLeak,
)
from app.services.backbone.input_adapters import BaseInputAdapter, get_adapter


class InputLab:
    """Central InputLab engine — delegates to per-input-type adapters."""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    # ------------------------------------------------------------------
    # Data access helpers (backed by DB)
    # ------------------------------------------------------------------

    async def _get_session_history(
        self, user_id: str, input_type: InputType
    ) -> list[dict]:
        """Fetch historical session summaries for a user+input type from DB."""
        try:
            uid = _uuid.UUID(user_id)
            result = await self.db.execute(
                select(Drill)
                .where(Drill.user_id == uid)
                .order_by(Drill.created_at.desc())
                .limit(50)
            )
            drills = result.scalars().all()
            return [
                {
                    "drill_id": str(d.id),
                    "skill_target": d.skill_target,
                    "events": d.drill_config.get("events", []) if d.drill_config else [],
                    "success_rate": d.success_rate,
                }
                for d in drills
            ]
        except (ValueError, Exception):
            return []

    async def _get_elite_pool(
        self, input_type: InputType, skill: str
    ) -> list[dict]:
        """Fetch elite player reference data for benchmarking."""
        return []

    async def _get_user_metric(
        self, user_id: str, input_type: InputType, skill: str
    ) -> float:
        """Fetch the user's current metric value for a skill from DB."""
        try:
            uid = _uuid.UUID(user_id)
            result = await self.db.execute(
                select(PlayerProfile).where(PlayerProfile.user_id == uid)
            )
            profile = result.scalar_one_or_none()
            if profile and profile.execution_ceiling:
                return float(profile.execution_ceiling.get(skill, 0.0))
        except (ValueError, Exception):
            pass
        return 0.0

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    async def diagnose_input(
        self,
        user_id: str,
        input_type: InputType,
        telemetry_data: list[InputEvent],
        session_id: str = "unknown",
    ) -> InputDiagnosis:
        """Run full mechanical diagnosis on a telemetry session.

        Delegates leak detection and drill generation to the correct
        per-input-type adapter.
        """
        adapter = get_adapter(input_type)

        leaks = adapter.analyze_events(telemetry_data)
        drills = [adapter.generate_drill(leak) for leak in leaks]

        total_inputs = len(telemetry_data)
        wasted = self._count_wasted(leaks, telemetry_data)
        efficiency = (total_inputs - wasted) / total_inputs if total_inputs > 0 else 1.0
        avg_reaction = self._avg_reaction_time(telemetry_data, adapter)

        summary = self._build_summary(input_type, efficiency, leaks)

        return InputDiagnosis(
            user_id=user_id,
            input_type=input_type,
            session_id=session_id,
            overall_efficiency=round(efficiency, 3),
            leaks=leaks,
            total_inputs=total_inputs,
            wasted_inputs=wasted,
            avg_reaction_time_ms=round(avg_reaction, 1),
            correction_drills=drills,
            summary=summary,
        )

    def detect_mechanical_leakage(
        self, telemetry: list[InputEvent], input_type: InputType
    ) -> list[MechanicalLeak]:
        """Detect wasted inputs and hesitation windows from raw telemetry."""
        adapter = get_adapter(input_type)
        return adapter.analyze_events(telemetry)

    async def compare_to_elite(
        self, user_id: str, input_type: InputType, skill: str
    ) -> EliteBenchmark:
        """Compare the user's input metrics against elite players."""
        adapter = get_adapter(input_type)
        refs = adapter.elite_benchmarks(skill)

        user_metric = await self._get_user_metric(user_id, input_type, skill)
        elite_avg = refs.get("avg", 0.0)
        elite_top = refs.get("top_10_pct", 0.0)

        # For timing metrics (lower is better), invert percentile logic
        is_timing = "ms" in skill.lower() or "speed" in skill.lower() or "timing" in skill.lower()

        if is_timing:
            percentile = self._timing_percentile(user_metric, elite_avg, elite_top)
            gap = user_metric - elite_avg  # Positive = slower than elite
        else:
            percentile = self._rate_percentile(user_metric, elite_avg, elite_top)
            gap = elite_avg - user_metric  # Positive = worse than elite

        verdict = self._benchmark_verdict(percentile)

        return EliteBenchmark(
            user_id=user_id,
            input_type=input_type,
            skill=skill,
            user_metric=round(user_metric, 3),
            elite_avg=round(elite_avg, 3),
            elite_top_10_pct=round(elite_top, 3),
            percentile=round(percentile, 1),
            gap_to_elite=round(abs(gap), 3),
            verdict=verdict,
        )

    def generate_correction_drill(
        self, leak: MechanicalLeak, input_type: InputType
    ) -> DrillSpec:
        """Generate a drill to fix a specific mechanical leak."""
        adapter = get_adapter(input_type)
        return adapter.generate_drill(leak)

    async def get_input_profile(
        self, user_id: str, input_type: InputType
    ) -> InputProfile:
        """Build a full input profile from historical sessions."""
        history = await self._get_session_history(user_id, input_type)
        adapter = get_adapter(input_type)

        total_sessions = len(history)
        all_leaks: list[MechanicalLeak] = []
        efficiencies: list[float] = []
        reaction_times: list[float] = []

        for session in history:
            events = [InputEvent(**e) for e in session.get("events", [])]
            leaks = adapter.analyze_events(events)
            all_leaks.extend(leaks)

            total = len(events)
            wasted = self._count_wasted(leaks, events)
            if total > 0:
                efficiencies.append((total - wasted) / total)
            reaction_times.append(self._avg_reaction_time(events, adapter))

        avg_eff = sum(efficiencies) / len(efficiencies) if efficiencies else 0.0
        avg_rt = sum(reaction_times) / len(reaction_times) if reaction_times else 0.0

        common_leaks = self._most_common_leaks(all_leaks)
        strengths = self._identify_strengths(avg_eff, avg_rt, common_leaks, adapter)
        weaknesses = self._identify_weaknesses(common_leaks, adapter)
        drills = [adapter.generate_drill(leak) for leak in common_leaks[:3]]

        # Build elite comparisons for default skills
        elite_comparisons: list[EliteBenchmark] = []
        for skill in list(adapter.elite_benchmarks("").keys())[:3] if hasattr(adapter, "_elite_refs") else []:
            benchmark = await self.compare_to_elite(user_id, input_type, skill)
            elite_comparisons.append(benchmark)

        return InputProfile(
            user_id=user_id,
            primary_input_type=input_type,
            total_sessions_analyzed=total_sessions,
            avg_efficiency=round(avg_eff, 3),
            avg_reaction_time_ms=round(avg_rt, 1),
            common_leaks=common_leaks,
            strengths=strengths,
            weaknesses=weaknesses,
            recommended_drills=drills,
            elite_comparison=elite_comparisons,
        )

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _count_wasted(leaks: list[MechanicalLeak], events: list[InputEvent]) -> int:
        """Estimate wasted inputs from detected leaks."""
        if not events or not leaks:
            return 0
        duration_min = (events[-1].timestamp_ms - events[0].timestamp_ms) / 60_000
        if duration_min <= 0:
            return 0
        total_wasted = 0
        for leak in leaks:
            if leak.leak_type in ("wasted_input", "ghost_input"):
                total_wasted += int(leak.frequency_per_minute * duration_min)
        return min(total_wasted, len(events))

    @staticmethod
    def _avg_reaction_time(events: list[InputEvent], adapter: BaseInputAdapter) -> float:
        """Calculate average reaction time accounting for device latency."""
        if not events:
            return 0.0
        press_events = [e for e in events if e.action == "press" and e.duration_ms is not None]
        if not press_events:
            return 0.0
        avg_duration = sum(e.duration_ms for e in press_events if e.duration_ms is not None) / len(press_events)
        return max(avg_duration - adapter.base_latency_ms, 0.0)

    @staticmethod
    def _most_common_leaks(leaks: list[MechanicalLeak], top_n: int = 5) -> list[MechanicalLeak]:
        """Aggregate leaks by type and return the most impactful ones."""
        if not leaks:
            return []
        by_type: dict[str, list[MechanicalLeak]] = {}
        for leak in leaks:
            by_type.setdefault(leak.leak_type, []).append(leak)

        aggregated: list[MechanicalLeak] = []
        for leak_type, instances in by_type.items():
            avg_impact = sum(l.impact_rating for l in instances) / len(instances)
            total_freq = sum(l.frequency_per_minute for l in instances) / len(instances)
            all_inputs = list({inp for l in instances for inp in l.affected_inputs})
            aggregated.append(
                MechanicalLeak(
                    leak_type=leak_type,
                    description=instances[0].description,
                    frequency_per_minute=round(total_freq, 2),
                    impact_rating=round(avg_impact, 3),
                    affected_inputs=all_inputs,
                    example_timestamps_ms=instances[0].example_timestamps_ms[:3],
                )
            )

        aggregated.sort(key=lambda l: l.impact_rating, reverse=True)
        return aggregated[:top_n]

    @staticmethod
    def _identify_strengths(
        avg_eff: float, avg_rt: float, leaks: list[MechanicalLeak], adapter: BaseInputAdapter
    ) -> list[str]:
        strengths: list[str] = []
        if avg_eff >= 0.90:
            strengths.append("High input efficiency — minimal waste")
        if avg_rt > 0 and avg_rt < 50:
            strengths.append("Fast reaction time")
        if not any(l.impact_rating > 0.7 for l in leaks):
            strengths.append("No critical mechanical leaks detected")
        if not strengths:
            strengths.append("Room for improvement across all areas")
        return strengths

    @staticmethod
    def _identify_weaknesses(leaks: list[MechanicalLeak], adapter: BaseInputAdapter) -> list[str]:
        weaknesses: list[str] = []
        for leak in leaks[:3]:
            weaknesses.append(f"{leak.leak_type}: {leak.description}")
        if not weaknesses:
            weaknesses.append("No significant weaknesses detected")
        return weaknesses

    @staticmethod
    def _build_summary(input_type: InputType, efficiency: float, leaks: list[MechanicalLeak]) -> str:
        device = input_type.value.replace("_", " ").title()
        if efficiency >= 0.95 and not leaks:
            return f"{device} inputs are elite-level — clean execution with no detected leaks."
        if efficiency >= 0.80:
            leak_types = ", ".join({l.leak_type for l in leaks}) if leaks else "none"
            return f"{device} inputs are solid ({efficiency:.0%} efficiency). Leaks: {leak_types}."
        leak_summary = "; ".join(f"{l.leak_type} (impact: {l.impact_rating:.0%})" for l in leaks[:3])
        return f"{device} inputs need work ({efficiency:.0%} efficiency). Key issues: {leak_summary}."

    @staticmethod
    def _rate_percentile(user_val: float, elite_avg: float, elite_top: float) -> float:
        """Percentile for rate metrics (higher is better)."""
        if elite_top <= 0:
            return 50.0
        if user_val >= elite_top:
            return min(95.0 + (user_val - elite_top) / elite_top * 50, 99.9)
        if user_val >= elite_avg:
            return 50.0 + (user_val - elite_avg) / (elite_top - elite_avg) * 45
        return max(user_val / elite_avg * 50, 0.0)

    @staticmethod
    def _timing_percentile(user_val: float, elite_avg: float, elite_top: float) -> float:
        """Percentile for timing metrics (lower is better)."""
        if elite_top <= 0:
            return 50.0
        if user_val <= elite_top:
            return min(95.0 + (elite_top - user_val) / elite_top * 50, 99.9)
        if user_val <= elite_avg:
            return 50.0 + (elite_avg - user_val) / (elite_avg - elite_top) * 45
        return max(50.0 - (user_val - elite_avg) / elite_avg * 50, 0.0)

    @staticmethod
    def _benchmark_verdict(percentile: float) -> str:
        if percentile >= 90:
            return "elite"
        if percentile >= 70:
            return "above-average"
        if percentile >= 40:
            return "average"
        if percentile >= 20:
            return "below-average"
        return "needs-work"
