"""RecruitingIQ — dynasty mode recruiting optimizer, multi-year roster roadmap.

Evaluates recruits by scheme fit, position need, and commitment likelihood.
Builds multi-year roster plans that optimize team overall trajectory across
the dynasty timeline.
"""

from __future__ import annotations

import logging
from collections import defaultdict

from app.schemas.cfb26.recruiting import (
    DynastyStateInput,
    PipelineStage,
    Position,
    PositionNeed,
    RecruitData,
    RecruitEvaluation,
    RecruitingBoard,
    RecruitingBoardEntry,
    RecruitPriority,
    RosterInput,
    RosterRoadmap,
    YearPlan,
)

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Position importance weights by scheme
# ---------------------------------------------------------------------------

SCHEME_POSITION_WEIGHTS: dict[str, dict[Position, float]] = {
    "triple_option": {
        Position.QB: 1.0, Position.RB: 0.9, Position.OL: 0.95,
        Position.WR: 0.4, Position.TE: 0.7, Position.DL: 0.8,
        Position.LB: 0.85, Position.CB: 0.6, Position.S: 0.65,
    },
    "air_raid": {
        Position.QB: 1.0, Position.WR: 0.95, Position.OL: 0.85,
        Position.RB: 0.5, Position.TE: 0.6, Position.DL: 0.7,
        Position.LB: 0.7, Position.CB: 0.9, Position.S: 0.8,
    },
    "spread_rpo": {
        Position.QB: 1.0, Position.RB: 0.85, Position.WR: 0.85,
        Position.OL: 0.8, Position.TE: 0.7, Position.DL: 0.75,
        Position.LB: 0.8, Position.CB: 0.85, Position.S: 0.75,
    },
    "flexbone": {
        Position.QB: 1.0, Position.RB: 0.95, Position.OL: 0.9,
        Position.WR: 0.35, Position.TE: 0.6, Position.DL: 0.8,
        Position.LB: 0.85, Position.CB: 0.55, Position.S: 0.6,
    },
    "west_coast": {
        Position.QB: 1.0, Position.WR: 0.9, Position.RB: 0.8,
        Position.OL: 0.85, Position.TE: 0.8, Position.DL: 0.7,
        Position.LB: 0.75, Position.CB: 0.85, Position.S: 0.8,
    },
}

# Ideal depth per position
IDEAL_DEPTH: dict[Position, int] = {
    Position.QB: 3, Position.RB: 4, Position.WR: 6, Position.TE: 3,
    Position.OL: 10, Position.DL: 8, Position.LB: 6, Position.CB: 5,
    Position.S: 4, Position.K: 1, Position.P: 1, Position.ATH: 2,
}


class RecruitingIQ:
    """Dynasty mode recruiting optimizer.

    MVP uses algorithmic evaluation. Production version will integrate
    with AI models trained on historical recruiting data.
    """

    def __init__(self) -> None:
        self._boards: dict[str, RecruitingBoard] = {}

    # ------------------------------------------------------------------
    # Recruiting board optimization
    # ------------------------------------------------------------------

    def optimize_recruiting_board(
        self, dynasty_state: DynastyStateInput,
    ) -> RecruitingBoard:
        """Build a prioritized recruiting board.

        Evaluates all available recruits against position needs, scheme fit,
        and commitment likelihood, then ranks them by priority.
        """
        # Step 1: Analyze position needs
        roster_input = RosterInput(
            players=dynasty_state.current_roster,
            scheme_type=dynasty_state.scheme_type,
        )
        needs = self.get_position_needs(roster_input)
        need_map = {n.position: n for n in needs}

        # Step 2: Evaluate each recruit
        entries: list[RecruitingBoardEntry] = []
        for recruit_dict in dynasty_state.available_recruits:
            recruit = RecruitData(**recruit_dict)
            evaluation = self.evaluate_recruit(
                recruit, dynasty_state.scheme_type, need_map,
            )

            # Determine priority from evaluation
            if evaluation.overall_grade >= 0.85 and evaluation.position_need_match >= 0.7:
                priority = RecruitPriority.MUST_HAVE
            elif evaluation.overall_grade >= 0.7:
                priority = RecruitPriority.HIGH
            elif evaluation.overall_grade >= 0.5:
                priority = RecruitPriority.MEDIUM
            elif evaluation.overall_grade >= 0.3:
                priority = RecruitPriority.LOW
            else:
                priority = RecruitPriority.DEPTH

            action_items = self._generate_action_items(recruit, evaluation, priority)

            entries.append(RecruitingBoardEntry(
                recruit=recruit,
                evaluation=evaluation,
                priority=priority,
                rank_on_board=0,  # assigned after sort
                action_items=action_items,
            ))

        # Step 3: Sort by priority and overall grade
        priority_order = {
            RecruitPriority.MUST_HAVE: 0,
            RecruitPriority.HIGH: 1,
            RecruitPriority.MEDIUM: 2,
            RecruitPriority.LOW: 3,
            RecruitPriority.DEPTH: 4,
        }
        entries.sort(key=lambda e: (
            priority_order[e.priority],
            -e.evaluation.overall_grade,
        ))
        for idx, entry in enumerate(entries, start=1):
            entry.rank_on_board = idx

        # Build position priority map
        position_priorities = {
            n.position.value: n.urgency for n in needs
        }

        board = RecruitingBoard(
            user_id=dynasty_state.user_id,
            school=dynasty_state.school,
            season_year=dynasty_state.season_year,
            entries=entries,
            total_scholarships_available=dynasty_state.scholarships_available,
            scholarships_committed=sum(
                1 for e in entries if e.recruit.pipeline_stage == PipelineStage.COMMITTED
            ),
            position_priorities=position_priorities,
        )

        self._boards[dynasty_state.user_id] = board
        logger.info(
            "Optimized board: user=%s school=%s recruits=%d",
            dynasty_state.user_id, dynasty_state.school, len(entries),
        )
        return board

    # ------------------------------------------------------------------
    # Roster roadmap
    # ------------------------------------------------------------------

    def build_roster_roadmap(
        self,
        current_roster: list[dict],
        years: int,
        user_id: str = "",
        school: str = "",
        scheme_type: str = "spread_rpo",
    ) -> RosterRoadmap:
        """Build multi-year roster plan.

        Projects roster evolution over multiple years, accounting for
        graduations, development, and recruiting targets.
        """
        # Calculate current team overall
        overalls = [p.get("overall", 70) for p in current_roster]
        current_avg = sum(overalls) / len(overalls) if overalls else 70.0

        year_plans: list[YearPlan] = []
        projected_trajectory: list[float] = [round(current_avg, 1)]

        roster_snapshot = list(current_roster)

        for year_offset in range(1, years + 1):
            season = 2026 + year_offset

            # Find departures (seniors graduating)
            departures = [
                p.get("name", f"Player_{i}")
                for i, p in enumerate(roster_snapshot)
                if p.get("year") in ("senior", "redshirt_senior")
            ]

            # Analyze needs after departures
            remaining = [
                p for p in roster_snapshot
                if p.get("year") not in ("senior", "redshirt_senior")
            ]
            roster_input = RosterInput(players=remaining, scheme_type=scheme_type)
            needs = self.get_position_needs(roster_input)

            # Project development — players improve ~2-4 OVR per year
            for p in remaining:
                dev_trait = p.get("development", "normal")
                boost = {"normal": 2, "impact": 3, "star": 4, "elite": 5}.get(dev_trait, 2)
                p["overall"] = min(p.get("overall", 70) + boost, 99)
                # Age up
                year_progression = {
                    "freshman": "sophomore", "redshirt_freshman": "sophomore",
                    "sophomore": "junior", "redshirt_sophomore": "junior",
                    "junior": "senior", "redshirt_junior": "senior",
                    "senior": "graduated", "redshirt_senior": "graduated",
                }
                p["year"] = year_progression.get(p.get("year", "freshman"), "graduated")

            # Project team overall after development
            remaining_overalls = [p.get("overall", 70) for p in remaining]
            projected_avg = sum(remaining_overalls) / len(remaining_overalls) if remaining_overalls else 70.0
            projected_trajectory.append(round(projected_avg, 1))

            year_plans.append(YearPlan(
                year=season,
                target_positions=needs[:5],
                scholarship_budget=25,
                key_departures=departures[:10],
                key_targets=[],
                projected_team_overall=round(projected_avg, 1),
            ))

            roster_snapshot = remaining

        # Determine championship window
        peak_year_idx = projected_trajectory.index(max(projected_trajectory))
        peak_year = 2026 + peak_year_idx
        window = f"Year {peak_year} — projected peak at {max(projected_trajectory):.1f} OVR"

        return RosterRoadmap(
            user_id=user_id,
            school=school,
            starting_overall=round(current_avg, 1),
            target_overall=round(max(projected_trajectory), 1),
            year_plans=year_plans,
            total_years=years,
            philosophy=f"Build through the trenches and {scheme_type} skill positions",
            championship_window=window,
        )

    # ------------------------------------------------------------------
    # Recruit evaluation
    # ------------------------------------------------------------------

    def evaluate_recruit(
        self,
        recruit: RecruitData,
        scheme_type: str = "spread_rpo",
        need_map: dict[Position, PositionNeed] | None = None,
    ) -> RecruitEvaluation:
        """Evaluate whether a recruit is worth pursuing.

        Scores by scheme fit, development ceiling, position need, and
        commitment likelihood.
        """
        need_map = need_map or {}

        # Scheme fit
        weights = SCHEME_POSITION_WEIGHTS.get(scheme_type, {})
        scheme_fit = weights.get(recruit.position, 0.5)

        # Development ceiling based on star rating and attributes
        ceiling_map = {5: 0.95, 4: 0.80, 3: 0.65, 2: 0.45, 1: 0.30}
        ceiling = ceiling_map.get(recruit.star_rating, 0.5)

        # Position need
        need = need_map.get(recruit.position)
        if need:
            need_match = {
                RecruitPriority.MUST_HAVE: 1.0,
                RecruitPriority.HIGH: 0.8,
                RecruitPriority.MEDIUM: 0.5,
                RecruitPriority.LOW: 0.3,
                RecruitPriority.DEPTH: 0.1,
            }.get(need.urgency, 0.3)
        else:
            need_match = 0.3

        # Commitment likelihood
        commitment = recruit.interest_level * 0.7 + (recruit.star_rating / 5.0) * 0.3
        commitment = min(commitment, 1.0)

        # Overall grade: weighted combination
        overall = (
            scheme_fit * 0.25
            + ceiling * 0.25
            + need_match * 0.30
            + commitment * 0.20
        )

        worth = overall >= 0.45

        reasoning = (
            f"{recruit.star_rating}-star {recruit.position.value} — "
            f"Scheme fit: {scheme_fit:.0%}, Ceiling: {ceiling:.0%}, "
            f"Need: {need_match:.0%}, Commit chance: {commitment:.0%}. "
            f"{'Worth pursuing.' if worth else 'Low priority — resources better spent elsewhere.'}"
        )

        return RecruitEvaluation(
            recruit_name=recruit.name,
            position=recruit.position,
            overall_grade=round(overall, 3),
            scheme_fit=round(scheme_fit, 3),
            development_ceiling=round(ceiling, 3),
            position_need_match=round(need_match, 3),
            commitment_likelihood=round(commitment, 3),
            worth_pursuing=worth,
            reasoning=reasoning,
        )

    # ------------------------------------------------------------------
    # Position needs analysis
    # ------------------------------------------------------------------

    def get_position_needs(self, roster: RosterInput) -> list[PositionNeed]:
        """Identify biggest roster holes.

        Analyzes current roster depth vs ideal depth at each position,
        factoring in scheme importance and upcoming departures.
        """
        # Count players at each position
        position_counts: dict[str, list[dict]] = defaultdict(list)
        for player in roster.players:
            pos = player.get("position", "ATH")
            position_counts[pos].append(player)

        needs: list[PositionNeed] = []
        weights = SCHEME_POSITION_WEIGHTS.get(roster.scheme_type, {})

        for position in Position:
            players_at_pos = position_counts.get(position.value, [])
            current_depth = len(players_at_pos)
            ideal = IDEAL_DEPTH.get(position, 2)

            # Average overall
            overalls = [p.get("overall", 70) for p in players_at_pos]
            avg_ovr = sum(overalls) / len(overalls) if overalls else 0.0

            # Count graduating seniors
            graduating = sum(
                1 for p in players_at_pos
                if p.get("year") in ("senior", "redshirt_senior")
            )

            # Calculate urgency
            depth_deficit = ideal - current_depth
            scheme_weight = weights.get(position, 0.5)

            urgency_score = (
                (depth_deficit / max(ideal, 1)) * 0.4
                + (graduating / max(current_depth, 1)) * 0.3
                + scheme_weight * 0.3
            )

            if urgency_score >= 0.7:
                urgency = RecruitPriority.MUST_HAVE
            elif urgency_score >= 0.5:
                urgency = RecruitPriority.HIGH
            elif urgency_score >= 0.35:
                urgency = RecruitPriority.MEDIUM
            elif urgency_score >= 0.2:
                urgency = RecruitPriority.LOW
            else:
                urgency = RecruitPriority.DEPTH

            reasoning = (
                f"{position.value}: {current_depth}/{ideal} depth, "
                f"{graduating} graduating, scheme weight {scheme_weight:.0%}"
            )

            needs.append(PositionNeed(
                position=position,
                urgency=urgency,
                current_depth=current_depth,
                ideal_depth=ideal,
                avg_overall_at_position=round(avg_ovr, 1),
                graduating_count=graduating,
                reasoning=reasoning,
            ))

        # Sort by urgency
        priority_order = {
            RecruitPriority.MUST_HAVE: 0,
            RecruitPriority.HIGH: 1,
            RecruitPriority.MEDIUM: 2,
            RecruitPriority.LOW: 3,
            RecruitPriority.DEPTH: 4,
        }
        needs.sort(key=lambda n: priority_order[n.urgency])
        return needs

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _generate_action_items(
        self,
        recruit: RecruitData,
        evaluation: RecruitEvaluation,
        priority: RecruitPriority,
    ) -> list[str]:
        """Generate action items for a recruit based on their evaluation."""
        items = []
        stage = recruit.pipeline_stage

        if stage == PipelineStage.IDENTIFIED:
            items.append(f"Scout {recruit.name} — get full attribute breakdown")
        if stage in (PipelineStage.IDENTIFIED, PipelineStage.SCOUTED):
            items.append(f"Send initial contact to {recruit.name}")
        if evaluation.commitment_likelihood < 0.4 and priority in (
            RecruitPriority.MUST_HAVE, RecruitPriority.HIGH
        ):
            items.append(f"Schedule campus visit for {recruit.name} — low interest, high priority")
        if evaluation.scheme_fit >= 0.8:
            items.append(f"Highlight scheme fit in pitch to {recruit.name}")
        if recruit.interest_level >= 0.7 and stage != PipelineStage.COMMITTED:
            items.append(f"Push for commitment from {recruit.name} — interest is high")

        return items


# Module-level singleton
recruiting_iq = RecruitingIQ()
