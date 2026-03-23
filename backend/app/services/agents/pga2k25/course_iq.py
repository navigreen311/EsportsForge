"""CourseIQ — per-hole strategy, safe vs aggressive line EV, hazard risk model.

Win condition focus: bogey avoidance through intelligent course management.
Evaluates every hole for risk/reward and recommends lines that minimize
downside while preserving birdie opportunities.
"""

from __future__ import annotations

import logging
import uuid
from datetime import datetime, timezone
from typing import Any, Optional

from app.schemas.pga2k25.course import (
    CourseAnalysis,
    HazardRisk,
    HazardType,
    HoleStrategy,
    LineEV,
    LineType,
    ShotPlan,
    ShotShape,
)

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Course database — built-in course knowledge
# ---------------------------------------------------------------------------

_COURSE_DB: dict[str, dict[str, Any]] = {
    "east_lake": {
        "par": 72,
        "total_yardage": 7346,
        "holes": [
            {"hole": 1, "par": 4, "yardage": 424, "handicap": 7, "hazards": ["bunker_left", "water_right"]},
            {"hole": 2, "par": 4, "yardage": 463, "handicap": 1, "hazards": ["bunker_both"]},
            {"hole": 3, "par": 3, "yardage": 207, "handicap": 13, "hazards": ["water_front"]},
            {"hole": 4, "par": 4, "yardage": 437, "handicap": 5, "hazards": ["bunker_right"]},
            {"hole": 5, "par": 5, "yardage": 546, "handicap": 11, "hazards": ["water_left", "bunker_greenside"]},
            {"hole": 6, "par": 3, "yardage": 183, "handicap": 15, "hazards": ["bunker_both"]},
            {"hole": 7, "par": 4, "yardage": 458, "handicap": 3, "hazards": ["trees_left", "ob_right"]},
            {"hole": 8, "par": 4, "yardage": 400, "handicap": 9, "hazards": ["bunker_left"]},
            {"hole": 9, "par": 4, "yardage": 448, "handicap": 2, "hazards": ["water_right", "bunker_left"]},
            {"hole": 10, "par": 4, "yardage": 392, "handicap": 10, "hazards": ["bunker_right"]},
            {"hole": 11, "par": 4, "yardage": 437, "handicap": 6, "hazards": ["water_left"]},
            {"hole": 12, "par": 3, "yardage": 180, "handicap": 16, "hazards": ["bunker_both"]},
            {"hole": 13, "par": 5, "yardage": 527, "handicap": 12, "hazards": ["water_crossing"]},
            {"hole": 14, "par": 4, "yardage": 440, "handicap": 4, "hazards": ["ob_left", "bunker_right"]},
            {"hole": 15, "par": 5, "yardage": 525, "handicap": 14, "hazards": ["water_left", "bunker_greenside"]},
            {"hole": 16, "par": 3, "yardage": 200, "handicap": 18, "hazards": ["bunker_front"]},
            {"hole": 17, "par": 4, "yardage": 430, "handicap": 8, "hazards": ["water_right"]},
            {"hole": 18, "par": 4, "yardage": 449, "handicap": 17, "hazards": ["bunker_both", "water_front_green"]},
        ],
    },
    "tpc_sawgrass": {
        "par": 72,
        "total_yardage": 7245,
        "holes": [
            {"hole": 1, "par": 4, "yardage": 423, "handicap": 9, "hazards": ["bunker_left"]},
            {"hole": 2, "par": 5, "yardage": 532, "handicap": 7, "hazards": ["water_right"]},
            {"hole": 3, "par": 3, "yardage": 177, "handicap": 15, "hazards": ["bunker_both"]},
            {"hole": 4, "par": 4, "yardage": 399, "handicap": 11, "hazards": ["bunker_left"]},
            {"hole": 5, "par": 4, "yardage": 466, "handicap": 1, "hazards": ["water_left", "bunker_right"]},
            {"hole": 6, "par": 4, "yardage": 393, "handicap": 13, "hazards": ["bunker_both"]},
            {"hole": 7, "par": 4, "yardage": 442, "handicap": 3, "hazards": ["trees_both"]},
            {"hole": 8, "par": 3, "yardage": 219, "handicap": 5, "hazards": ["bunker_left", "water_right"]},
            {"hole": 9, "par": 5, "yardage": 583, "handicap": 17, "hazards": ["water_right"]},
            {"hole": 10, "par": 4, "yardage": 424, "handicap": 8, "hazards": ["bunker_right"]},
            {"hole": 11, "par": 5, "yardage": 542, "handicap": 6, "hazards": ["water_left"]},
            {"hole": 12, "par": 4, "yardage": 358, "handicap": 14, "hazards": ["bunker_greenside"]},
            {"hole": 13, "par": 3, "yardage": 181, "handicap": 16, "hazards": ["bunker_both"]},
            {"hole": 14, "par": 4, "yardage": 467, "handicap": 2, "hazards": ["water_left", "ob_right"]},
            {"hole": 15, "par": 4, "yardage": 449, "handicap": 4, "hazards": ["bunker_both"]},
            {"hole": 16, "par": 5, "yardage": 523, "handicap": 10, "hazards": ["water_right"]},
            {"hole": 17, "par": 3, "yardage": 137, "handicap": 18, "hazards": ["water_all"]},
            {"hole": 18, "par": 4, "yardage": 462, "handicap": 12, "hazards": ["water_left"]},
        ],
    },
}


class CourseIQ:
    """
    CourseIQ for PGA TOUR 2K25.

    Provides per-hole strategic analysis with safe vs aggressive line expected
    value calculations.  Core objective: minimize bogeys through smart course
    management while identifying the best birdie opportunities.
    """

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    async def analyze_course(
        self,
        user_id: uuid.UUID,
        course_name: str,
        tee_box: str = "championship",
        player_handicap: float = 0.0,
        risk_tolerance: float = 0.5,
    ) -> CourseAnalysis:
        """Generate a full 18-hole course strategy."""
        course_key = course_name.lower().replace(" ", "_")
        course_data = _COURSE_DB.get(course_key, self._generate_default_course(course_name))

        holes: list[HoleStrategy] = []
        bogey_danger: list[int] = []
        birdie_opps: list[int] = []

        for hole_data in course_data["holes"]:
            strategy = self._analyze_hole(hole_data, player_handicap, risk_tolerance)
            holes.append(strategy)

            # Track bogey danger and birdie opportunity holes
            safe_line = next(
                (l for l in strategy.line_options if l.line_type == LineType.SAFE), None
            )
            if safe_line and safe_line.bogey_probability > 0.25:
                bogey_danger.append(strategy.hole_number)
            agg_line = next(
                (l for l in strategy.line_options if l.line_type == LineType.AGGRESSIVE), None
            )
            if agg_line and agg_line.birdie_probability > 0.30:
                birdie_opps.append(strategy.hole_number)

        # Compute target score
        target_score = sum(
            next(
                (l.expected_score for l in h.line_options if l.line_type == h.recommended_line),
                h.par,
            )
            for h in holes
        )

        # Risk management score
        total_bogey_risk = sum(
            min(l.bogey_probability for l in h.line_options if l.line_type == h.recommended_line)
            if any(l.line_type == h.recommended_line for l in h.line_options)
            else 0.2
            for h in holes
        )
        risk_score = max(0.0, min(1.0, 1.0 - (total_bogey_risk / 18)))

        strategy_summary = self._build_round_strategy(
            holes, bogey_danger, birdie_opps, risk_tolerance,
        )

        return CourseAnalysis(
            course_name=course_name,
            tee_box=tee_box,
            total_yardage=course_data["total_yardage"],
            par=course_data["par"],
            holes=holes,
            overall_strategy=strategy_summary,
            target_score=round(target_score, 1),
            bogey_danger_holes=bogey_danger,
            birdie_opportunity_holes=birdie_opps,
            risk_management_score=round(risk_score, 2),
            confidence=0.78,
            generated_at=datetime.now(timezone.utc).isoformat(),
        )

    async def get_hole_strategy(
        self,
        course_name: str,
        hole_number: int,
        risk_tolerance: float = 0.5,
    ) -> HoleStrategy:
        """Get strategy for a single hole."""
        course_key = course_name.lower().replace(" ", "_")
        course_data = _COURSE_DB.get(course_key, self._generate_default_course(course_name))

        hole_data = next(
            (h for h in course_data["holes"] if h["hole"] == hole_number),
            course_data["holes"][0],
        )
        return self._analyze_hole(hole_data, 0.0, risk_tolerance)

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _analyze_hole(
        self,
        hole_data: dict[str, Any],
        handicap: float,
        risk_tolerance: float,
    ) -> HoleStrategy:
        """Build a complete strategy for a single hole."""
        hole_num = hole_data["hole"]
        par = hole_data["par"]
        yardage = hole_data["yardage"]
        handicap_idx = hole_data.get("handicap", 9)

        # Build hazard risks
        hazards = self._assess_hazards(hole_data.get("hazards", []), yardage)

        # Calculate line EVs
        safe_line = self._calculate_safe_line(par, yardage, hazards, handicap)
        agg_line = self._calculate_aggressive_line(par, yardage, hazards, handicap)

        # Recommend based on risk tolerance and EV comparison
        ev_diff = safe_line.expected_score - agg_line.expected_score
        bogey_diff = agg_line.bogey_probability - safe_line.bogey_probability

        # Bogey avoidance: prefer safe when downside is significant
        if risk_tolerance < 0.3:
            recommended = LineType.SAFE
        elif risk_tolerance > 0.7 and ev_diff > 0.15:
            recommended = LineType.AGGRESSIVE
        elif bogey_diff > 0.15:
            # Aggressive line has much higher bogey risk — go safe
            recommended = LineType.SAFE
        elif ev_diff > 0.1:
            recommended = LineType.AGGRESSIVE
        else:
            recommended = LineType.SAFE

        # Mark the recommended line
        safe_line = safe_line.model_copy(
            update={"recommended": recommended == LineType.SAFE},
        )
        agg_line = agg_line.model_copy(
            update={"recommended": recommended == LineType.AGGRESSIVE},
        )

        # Build shot plan
        shot_plan = self._build_shot_plan(par, yardage, recommended)

        # Key miss identification
        key_miss = self._identify_key_miss(hazards)

        return HoleStrategy(
            hole_number=hole_num,
            par=par,
            yardage=yardage,
            handicap_index=handicap_idx,
            hazards=hazards,
            line_options=[safe_line, agg_line],
            recommended_line=recommended,
            shot_plan=shot_plan,
            bogey_avoidance_notes=self._bogey_avoidance_note(par, hazards, recommended),
            key_miss=key_miss,
        )

    def _assess_hazards(
        self, hazard_codes: list[str], yardage: int,
    ) -> list[HazardRisk]:
        """Convert hazard codes to risk assessments."""
        hazards: list[HazardRisk] = []
        for code in hazard_codes:
            hazard_type, location, prob, penalty = self._decode_hazard(code, yardage)
            hazards.append(
                HazardRisk(
                    hazard_type=hazard_type,
                    location=location,
                    probability=prob,
                    penalty_strokes=penalty,
                    avoidance_strategy=self._hazard_avoidance(hazard_type, location),
                )
            )
        return hazards

    @staticmethod
    def _decode_hazard(
        code: str, yardage: int,
    ) -> tuple[HazardType, str, float, float]:
        """Decode a hazard code into type, location, probability, penalty."""
        hazard_map = {
            "water": (HazardType.WATER, 0.12, 1.5),
            "bunker": (HazardType.BUNKER, 0.18, 0.5),
            "ob": (HazardType.OB, 0.08, 1.8),
            "trees": (HazardType.TREES, 0.15, 0.7),
            "waste": (HazardType.WASTE_AREA, 0.10, 0.4),
        }

        parts = code.split("_")
        h_type_key = parts[0]
        location_hint = "_".join(parts[1:]) if len(parts) > 1 else "unknown"

        h_type, base_prob, penalty = hazard_map.get(
            h_type_key, (HazardType.BUNKER, 0.15, 0.5),
        )

        # Longer holes have slightly higher hazard probability
        prob_adj = base_prob * (1 + (yardage - 400) / 2000) if yardage > 400 else base_prob

        location_str = location_hint.replace("_", " ").title()
        return h_type, f"{location_str} at ~{yardage // 2}y" if "greenside" not in code else f"Greenside {location_str}", min(prob_adj, 0.40), penalty

    @staticmethod
    def _hazard_avoidance(h_type: HazardType, location: str) -> str:
        """Generate avoidance strategy."""
        strategies = {
            HazardType.WATER: "Aim away from water edge; take one extra club and miss to dry side",
            HazardType.BUNKER: "Favor the opposite side of the fairway/green",
            HazardType.OB: "Aim well inside the boundary; consider less club off the tee",
            HazardType.TREES: "Prioritize fairway position over distance",
            HazardType.DEEP_ROUGH: "Keep ball on short grass; miss to the safe bail-out area",
            HazardType.WASTE_AREA: "Play to the wide side of the fairway",
            HazardType.FAIRWAY_BUNKER: "Consider laying back short of the bunker",
        }
        return strategies.get(h_type, "Play conservatively away from trouble")

    @staticmethod
    def _calculate_safe_line(
        par: int, yardage: int, hazards: list[HazardRisk], handicap: float,
    ) -> LineEV:
        """Calculate EV for the safe/conservative line."""
        base_score = par + 0.05 + (handicap * 0.01)

        # Safe line reduces hazard risk but limits birdie chances
        hazard_penalty = sum(h.probability * h.penalty_strokes * 0.3 for h in hazards)
        expected = base_score + hazard_penalty

        birdie_p = max(0.05, 0.20 - (yardage / 5000))
        if par == 5:
            birdie_p = min(0.35, birdie_p + 0.15)
        elif par == 3:
            birdie_p = min(0.25, birdie_p + 0.05)

        bogey_p = max(0.05, 0.12 + hazard_penalty * 0.3)
        par_p = 1.0 - birdie_p - bogey_p - 0.02
        double_p = 0.02

        rr_ratio = birdie_p / max(bogey_p + double_p, 0.01)

        return LineEV(
            line_type=LineType.SAFE,
            expected_score=round(expected, 2),
            birdie_probability=round(birdie_p, 3),
            par_probability=round(max(0.0, par_p), 3),
            bogey_probability=round(bogey_p, 3),
            double_or_worse_probability=round(double_p, 3),
            risk_reward_ratio=round(rr_ratio, 2),
        )

    @staticmethod
    def _calculate_aggressive_line(
        par: int, yardage: int, hazards: list[HazardRisk], handicap: float,
    ) -> LineEV:
        """Calculate EV for the aggressive line."""
        base_score = par - 0.05 + (handicap * 0.005)

        hazard_penalty = sum(h.probability * h.penalty_strokes * 0.7 for h in hazards)
        expected = base_score + hazard_penalty

        birdie_p = max(0.10, 0.35 - (yardage / 4000))
        if par == 5:
            birdie_p = min(0.50, birdie_p + 0.20)
        elif par == 3:
            birdie_p = min(0.30, birdie_p + 0.05)

        bogey_p = max(0.10, 0.18 + hazard_penalty * 0.5)
        double_p = max(0.03, hazard_penalty * 0.15)
        par_p = 1.0 - birdie_p - bogey_p - double_p

        rr_ratio = birdie_p / max(bogey_p + double_p, 0.01)

        return LineEV(
            line_type=LineType.AGGRESSIVE,
            expected_score=round(expected, 2),
            birdie_probability=round(birdie_p, 3),
            par_probability=round(max(0.0, par_p), 3),
            bogey_probability=round(bogey_p, 3),
            double_or_worse_probability=round(double_p, 3),
            risk_reward_ratio=round(rr_ratio, 2),
        )

    @staticmethod
    def _build_shot_plan(par: int, yardage: int, line: LineType) -> list[ShotPlan]:
        """Build a basic shot plan for the hole."""
        plans: list[ShotPlan] = []

        if par == 3:
            plans.append(ShotPlan(
                shot_number=1,
                club="iron" if yardage < 200 else "hybrid",
                target_distance=float(yardage),
                aim_point="center green" if line == LineType.SAFE else "pin",
            ))
        elif par == 4:
            drive_dist = min(280.0, float(yardage) * 0.6)
            approach_dist = float(yardage) - drive_dist
            plans.append(ShotPlan(
                shot_number=1,
                club="driver" if yardage > 380 else "3-wood",
                target_distance=drive_dist,
                aim_point="center fairway" if line == LineType.SAFE else "aggressive side",
            ))
            plans.append(ShotPlan(
                shot_number=2,
                club=_approach_club(approach_dist),
                target_distance=approach_dist,
                aim_point="middle of green" if line == LineType.SAFE else "pin high",
            ))
        else:  # par 5
            plans.append(ShotPlan(
                shot_number=1,
                club="driver",
                target_distance=280.0,
                aim_point="center fairway",
            ))
            remaining = float(yardage) - 280
            if line == LineType.AGGRESSIVE and remaining < 260:
                plans.append(ShotPlan(
                    shot_number=2,
                    club="3-wood" if remaining > 220 else "hybrid",
                    target_distance=remaining,
                    aim_point="front edge of green",
                    notes="Go for it in two",
                ))
            else:
                layup_dist = remaining * 0.55
                wedge_dist = remaining - layup_dist
                plans.append(ShotPlan(
                    shot_number=2,
                    club=_approach_club(layup_dist),
                    target_distance=layup_dist,
                    aim_point="100-yard marker",
                    notes="Layup to comfortable wedge distance",
                ))
                plans.append(ShotPlan(
                    shot_number=3,
                    club="wedge",
                    target_distance=wedge_dist,
                    aim_point="center green" if line == LineType.SAFE else "pin",
                ))

        return plans

    @staticmethod
    def _identify_key_miss(hazards: list[HazardRisk]) -> str:
        """Find the single most dangerous miss."""
        if not hazards:
            return "No major hazards — focus on center of fairway/green"
        worst = max(hazards, key=lambda h: h.probability * h.penalty_strokes)
        return f"Avoid {worst.hazard_type.value} at {worst.location}"

    @staticmethod
    def _bogey_avoidance_note(
        par: int, hazards: list[HazardRisk], line: LineType,
    ) -> str:
        """Generate bogey avoidance advice."""
        water_hazards = [h for h in hazards if h.hazard_type == HazardType.WATER]
        ob_hazards = [h for h in hazards if h.hazard_type == HazardType.OB]

        notes: list[str] = []
        if water_hazards:
            notes.append("Water in play — take one extra club and aim for dry side")
        if ob_hazards:
            notes.append("OB risk — tee shot accuracy is paramount")
        if par == 3:
            notes.append("Par 3: aim center green, take your par and move on")
        if not notes:
            notes.append("Fairway off the tee, green in regulation, two putts")

        return "; ".join(notes)

    @staticmethod
    def _build_round_strategy(
        holes: list[HoleStrategy],
        danger: list[int],
        birdies: list[int],
        risk_tolerance: float,
    ) -> str:
        """Build the overall round strategy narrative."""
        parts = []
        if risk_tolerance < 0.3:
            parts.append("Conservative approach: prioritize bogey avoidance on every hole.")
        elif risk_tolerance > 0.7:
            parts.append("Aggressive approach: attack birdie holes and accept calculated risks.")
        else:
            parts.append("Balanced approach: play safe on danger holes, attack birdie opportunities.")

        if danger:
            parts.append(f"Bogey danger holes to manage: {', '.join(str(h) for h in danger)}.")
        if birdies:
            parts.append(f"Best birdie opportunities: {', '.join(str(h) for h in birdies)}.")

        parts.append("Key principle: never compound a mistake — take your medicine and limit damage.")
        return " ".join(parts)

    @staticmethod
    def _generate_default_course(name: str) -> dict[str, Any]:
        """Generate a default course template when not in the database."""
        holes = []
        pars = [4, 4, 3, 4, 5, 4, 4, 3, 4, 4, 4, 3, 5, 4, 5, 3, 4, 4]
        yardages = [420, 440, 185, 410, 540, 395, 450, 200, 430, 400, 445, 175, 530, 460, 520, 195, 435, 455]
        for i in range(18):
            holes.append({
                "hole": i + 1,
                "par": pars[i],
                "yardage": yardages[i],
                "handicap": ((i * 7 + 3) % 18) + 1,
                "hazards": ["bunker_left", "bunker_right"],
            })
        return {"par": 72, "total_yardage": sum(yardages), "holes": holes}


def _approach_club(distance: float) -> str:
    """Select approach club based on distance."""
    if distance > 200:
        return "3-iron"
    if distance > 180:
        return "4-iron"
    if distance > 165:
        return "5-iron"
    if distance > 150:
        return "6-iron"
    if distance > 140:
        return "7-iron"
    if distance > 130:
        return "8-iron"
    if distance > 120:
        return "9-iron"
    if distance > 100:
        return "PW"
    if distance > 80:
        return "GW"
    return "SW"
