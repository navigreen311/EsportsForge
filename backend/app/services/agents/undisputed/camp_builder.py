"""CampBuilder — career build path optimizer and punch package builder for Undisputed.

Generates optimal career mode build paths, assembles punch package loadouts,
and recommends training camp priorities based on upcoming opponent.
"""

from __future__ import annotations

import logging
from typing import Any

from app.schemas.undisputed.boxing import (
    BoxingArchetype,
    CareerBuildPath,
    PunchPackage,
    TrainingCampPlan,
)

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Attribute progression trees
# ---------------------------------------------------------------------------

_ATTRIBUTE_TREES: dict[BoxingArchetype, dict[str, list[str]]] = {
    BoxingArchetype.SWARMER: {
        "priority_1": ["stamina", "punch_speed", "head_movement"],
        "priority_2": ["body_power", "footwork", "chin"],
        "priority_3": ["jab_accuracy", "combination_speed", "recovery"],
    },
    BoxingArchetype.OUT_BOXER: {
        "priority_1": ["footwork", "jab_accuracy", "ring_iq"],
        "priority_2": ["hand_speed", "defense", "stamina"],
        "priority_3": ["counter_timing", "reach_utilization", "head_movement"],
    },
    BoxingArchetype.SLUGGER: {
        "priority_1": ["power", "chin", "ko_power"],
        "priority_2": ["body_power", "overhand_accuracy", "timing"],
        "priority_3": ["stamina", "head_movement", "footwork"],
    },
    BoxingArchetype.COUNTER_PUNCHER: {
        "priority_1": ["counter_timing", "defense", "ring_iq"],
        "priority_2": ["hand_speed", "accuracy", "head_movement"],
        "priority_3": ["power", "footwork", "stamina"],
    },
    BoxingArchetype.BOXER_PUNCHER: {
        "priority_1": ["hand_speed", "power", "accuracy"],
        "priority_2": ["footwork", "defense", "stamina"],
        "priority_3": ["ring_iq", "chin", "combination_speed"],
    },
    BoxingArchetype.SWITCH_HITTER: {
        "priority_1": ["footwork", "adaptability", "stance_switching"],
        "priority_2": ["hand_speed", "accuracy", "ring_iq"],
        "priority_3": ["power", "stamina", "defense"],
    },
}

# Punch package loadouts
_PUNCH_PACKAGES: dict[str, dict[str, Any]] = {
    "power_puncher": {
        "lead_punches": ["jab", "lead_hook"],
        "power_punches": ["cross", "overhand", "rear_uppercut"],
        "body_punches": ["body_hook", "body_uppercut"],
        "specialty": "overhand",
        "description": "Heavy-handed package built around the overhand and rear hand power.",
    },
    "volume_fighter": {
        "lead_punches": ["jab", "double_jab", "lead_hook", "lead_uppercut"],
        "power_punches": ["cross", "rear_hook"],
        "body_punches": ["body_jab", "body_hook"],
        "specialty": "double_jab",
        "description": "High-output package with fast combinations and constant pressure.",
    },
    "counter_specialist": {
        "lead_punches": ["jab", "check_hook"],
        "power_punches": ["cross", "rear_uppercut"],
        "body_punches": ["body_cross"],
        "specialty": "check_hook",
        "description": "Reactive package built around counter timing and check hooks.",
    },
    "body_snatcher": {
        "lead_punches": ["jab", "lead_hook"],
        "power_punches": ["cross"],
        "body_punches": ["body_jab", "body_hook", "body_uppercut", "body_cross"],
        "specialty": "body_hook",
        "description": "Body-focused package that breaks down opponents over 12 rounds.",
    },
    "balanced": {
        "lead_punches": ["jab", "lead_hook"],
        "power_punches": ["cross", "rear_hook", "rear_uppercut"],
        "body_punches": ["body_hook", "body_jab"],
        "specialty": "cross",
        "description": "Well-rounded package with options at all ranges and targets.",
    },
}


class CampBuilder:
    """Undisputed career builder and training camp optimizer.

    Generates career build paths based on archetype, assembles punch
    packages, and plans training camps for specific opponents.
    """

    # ------------------------------------------------------------------
    # Career build path
    # ------------------------------------------------------------------

    def generate_build_path(
        self,
        target_archetype: BoxingArchetype,
        current_level: int = 1,
        available_points: int = 50,
    ) -> CareerBuildPath:
        """Generate an optimal career attribute build path for the target archetype.

        Distributes available points across priority tiers to maximize
        effectiveness in the chosen style.
        """
        tree = _ATTRIBUTE_TREES.get(target_archetype, _ATTRIBUTE_TREES[BoxingArchetype.BALANCED])

        # Allocate points: 50% to P1, 30% to P2, 20% to P3
        p1_points = int(available_points * 0.50)
        p2_points = int(available_points * 0.30)
        p3_points = available_points - p1_points - p2_points

        allocations: dict[str, int] = {}
        for attr in tree["priority_1"]:
            per_attr = p1_points // len(tree["priority_1"])
            allocations[attr] = per_attr
        for attr in tree["priority_2"]:
            per_attr = p2_points // len(tree["priority_2"])
            allocations[attr] = per_attr
        for attr in tree["priority_3"]:
            per_attr = p3_points // len(tree["priority_3"])
            allocations[attr] = per_attr

        milestones: list[str] = []
        if current_level < 10:
            milestones.append("Levels 1-10: Focus on priority 1 attributes exclusively.")
        if current_level < 25:
            milestones.append("Levels 10-25: Begin investing in priority 2 attributes.")
        milestones.append("Levels 25+: Round out with priority 3 attributes.")
        milestones.append(f"Target archetype: {target_archetype.value} — specialize, don't generalize.")

        return CareerBuildPath(
            target_archetype=target_archetype,
            current_level=current_level,
            available_points=available_points,
            allocations=allocations,
            priority_1=tree["priority_1"],
            priority_2=tree["priority_2"],
            priority_3=tree["priority_3"],
            milestones=milestones,
        )

    # ------------------------------------------------------------------
    # Punch package optimizer
    # ------------------------------------------------------------------

    def build_punch_package(
        self,
        archetype: BoxingArchetype,
        focus: str = "balanced",
    ) -> PunchPackage:
        """Assemble the optimal punch package for an archetype and focus.

        Returns the recommended loadout of lead, power, body, and specialty punches.
        """
        # Map archetype to default focus
        archetype_focus: dict[BoxingArchetype, str] = {
            BoxingArchetype.SWARMER: "volume_fighter",
            BoxingArchetype.OUT_BOXER: "counter_specialist",
            BoxingArchetype.SLUGGER: "power_puncher",
            BoxingArchetype.COUNTER_PUNCHER: "counter_specialist",
            BoxingArchetype.BOXER_PUNCHER: "balanced",
            BoxingArchetype.SWITCH_HITTER: "balanced",
        }

        package_key = focus if focus in _PUNCH_PACKAGES else archetype_focus.get(archetype, "balanced")
        package_data = _PUNCH_PACKAGES[package_key]

        return PunchPackage(
            name=package_key,
            archetype=archetype,
            lead_punches=package_data["lead_punches"],
            power_punches=package_data["power_punches"],
            body_punches=package_data["body_punches"],
            specialty=package_data["specialty"],
            description=package_data["description"],
        )

    # ------------------------------------------------------------------
    # Training camp plan
    # ------------------------------------------------------------------

    def plan_training_camp(
        self,
        player_archetype: BoxingArchetype,
        opponent_archetype: BoxingArchetype,
        fight_rounds: int = 12,
        weeks_until_fight: int = 8,
    ) -> TrainingCampPlan:
        """Generate a training camp plan tailored to the upcoming opponent.

        Prioritizes drills and sparring that prepare for the opponent's style.
        """
        opponent_data = _ATTRIBUTE_TREES.get(opponent_archetype, {})
        opp_strengths = opponent_data.get("priority_1", [])

        drills: list[str] = []
        sparring_focus: list[str] = []
        conditioning_notes: list[str] = []

        # Counter their strengths
        if "stamina" in opp_strengths or "punch_speed" in opp_strengths:
            drills.append("Clinch drill: Practice tying up to break their rhythm.")
            sparring_focus.append("Spar against high-volume pressure fighters.")
        if "power" in opp_strengths or "ko_power" in opp_strengths:
            drills.append("Head movement drill: Slip and roll under power shots.")
            drills.append("Chin conditioning: Focus on taking shots while maintaining composure.")
            sparring_focus.append("Spar against heavy hitters — get comfortable with power.")
        if "footwork" in opp_strengths or "ring_iq" in opp_strengths:
            drills.append("Cutting the ring: Practice trapping opponent on the ropes.")
            sparring_focus.append("Spar against movers — practice closing distance.")
        if "counter_timing" in opp_strengths:
            drills.append("Feint drill: Use feints to draw and punish the counter.")
            sparring_focus.append("Spar against counter punchers — learn to set traps.")

        # Default drills
        if not drills:
            drills = [
                "Combination drill: 3-4 punch combos on the heavy bag.",
                "Footwork ladder: Improve lateral movement and pivots.",
                "Defense drill: Shoulder roll and head movement against a partner.",
            ]

        # Conditioning based on fight length
        if fight_rounds >= 10:
            conditioning_notes.append("Championship rounds require elite cardio. Run 5+ miles daily.")
            conditioning_notes.append("Include 12-round sparring sessions in weeks 4-6.")
        elif fight_rounds >= 6:
            conditioning_notes.append("Build stamina for 6+ rounds. HIIT training 3x per week.")
        else:
            conditioning_notes.append("Short fight — focus on explosive power over endurance.")

        # Weekly schedule
        week_plan: dict[str, str] = {}
        for week in range(1, min(weeks_until_fight + 1, 9)):
            if week <= 2:
                week_plan[f"Week {week}"] = "Base building — cardio, technique, film study."
            elif week <= 5:
                week_plan[f"Week {week}"] = "Peak training — hard sparring, combo drilling, specific gameplanning."
            elif week <= 7:
                week_plan[f"Week {week}"] = "Sharpening — technical sparring, speed work, mental preparation."
            else:
                week_plan[f"Week {week}"] = "Taper — light work, rest, visualization, weight management."

        return TrainingCampPlan(
            player_archetype=player_archetype,
            opponent_archetype=opponent_archetype,
            fight_rounds=fight_rounds,
            weeks=weeks_until_fight,
            drills=drills,
            sparring_focus=sparring_focus,
            conditioning_notes=conditioning_notes,
            week_plan=week_plan,
        )


# Module-level singleton
camp_builder = CampBuilder()
