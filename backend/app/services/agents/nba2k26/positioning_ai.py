"""PositioningAI — pick-and-roll defense, help-side rotation, user defender path optimizer.

Analyzes defensive positioning in NBA 2K26, provides real-time rotation recommendations,
evaluates PnR coverage quality, and tracks positioning discipline over time.
"""

from __future__ import annotations

import logging
import math
from collections import defaultdict

from app.schemas.nba2k26.gameplay import (
    CourtPosition,
    DefensivePosition,
    DefensiveRole,
    PickAndRollCoverage,
    RotationAnalysis,
)

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Court geometry constants
# ---------------------------------------------------------------------------

COURT_LENGTH_FT = 94.0
COURT_WIDTH_FT = 50.0
THREE_POINT_ARC_FT = 23.75
PAINT_WIDTH_FT = 16.0
PAINT_DEPTH_FT = 19.0
FREE_THROW_LINE_FT = 19.0
BASKET_X = 5.25  # from baseline
BASKET_Y = 25.0  # center of court

# Optimal help-side positions relative to ball and man
HELP_DISTANCE_FT = 8.0
CLOSEOUT_DISTANCE_FT = 6.0

# ---------------------------------------------------------------------------
# PnR coverage type definitions
# ---------------------------------------------------------------------------

PNR_COVERAGES: dict[str, dict] = {
    "drop": {
        "description": "Big drops to free-throw line, guards ball handler",
        "best_against": ["poor shooting bigs", "drive-first PGs"],
        "weak_against": ["shooting bigs", "mid-range pullup"],
        "screener_depth_ft": FREE_THROW_LINE_FT,
    },
    "hedge": {
        "description": "Big steps out to slow ball handler, recovers to man",
        "best_against": ["fast guards", "downhill attackers"],
        "weak_against": ["quick passing PGs", "lob threats"],
        "screener_depth_ft": THREE_POINT_ARC_FT - 3,
    },
    "switch": {
        "description": "Defenders switch assignments on screen",
        "best_against": ["frequent screeners", "two-man actions"],
        "weak_against": ["size mismatches", "post-up bigs"],
        "screener_depth_ft": 0,  # stays with new man
    },
    "blitz": {
        "description": "Both defenders trap the ball handler",
        "best_against": ["poor passers", "turnover-prone guards"],
        "weak_against": ["good passing teams", "3-point shooters"],
        "screener_depth_ft": THREE_POINT_ARC_FT,
    },
    "ice": {
        "description": "Force ball handler away from screen (baseline side)",
        "best_against": ["PnR-heavy offenses", "side pick and rolls"],
        "weak_against": ["wing shooters", "quick reversal offenses"],
        "screener_depth_ft": PAINT_DEPTH_FT,
    },
}


def _distance(a: CourtPosition, b: CourtPosition) -> float:
    """Euclidean distance between two court positions."""
    return math.sqrt((a.x - b.x) ** 2 + (a.y - b.y) ** 2)


def _midpoint(a: CourtPosition, b: CourtPosition) -> CourtPosition:
    """Midpoint between two positions."""
    return CourtPosition(x=(a.x + b.x) / 2, y=(a.y + b.y) / 2)


class PositioningAI:
    """NBA 2K26 defensive positioning engine.

    Evaluates defensive positioning, provides PnR coverage recommendations,
    tracks help-side rotation accuracy, and optimizes defender paths.
    """

    def __init__(self) -> None:
        self._rotation_history: dict[str, list[dict]] = defaultdict(list)

    # ------------------------------------------------------------------
    # Defensive position evaluation
    # ------------------------------------------------------------------

    def evaluate_position(
        self,
        user_id: str,
        role: DefensiveRole,
        current: CourtPosition,
        ball_position: CourtPosition,
        man_position: CourtPosition,
    ) -> DefensivePosition:
        """Evaluate a defender's current position and recommend optimal placement.

        Takes into account the defensive role, ball location, and assignment
        to compute the ideal position and distance from optimal.
        """
        optimal = self._compute_optimal_position(role, ball_position, man_position)
        dist_off = round(_distance(current, optimal), 2)

        # Grade rotation quality (1.0 = perfect, 0.0 = terrible)
        max_acceptable_dist = 12.0  # feet
        grade = max(0.0, 1.0 - (dist_off / max_acceptable_dist))

        # Check help-ready stance (within passing-lane gap)
        help_ready = self._is_help_ready(current, ball_position, man_position)

        # Check gap closure
        gap_closed = dist_off <= 4.0

        recommendations = self._generate_position_recommendations(
            role, current, optimal, dist_off, help_ready,
        )

        result = DefensivePosition(
            user_id=user_id,
            role=role,
            current_position=current,
            optimal_position=optimal,
            distance_off_optimal_ft=dist_off,
            rotation_grade=round(grade, 3),
            help_ready=help_ready,
            gap_closed=gap_closed,
            recommendations=recommendations,
        )

        logger.info(
            "Position evaluated: user=%s role=%s dist_off=%.1fft grade=%.3f",
            user_id, role.value, dist_off, grade,
        )
        return result

    def _compute_optimal_position(
        self,
        role: DefensiveRole,
        ball: CourtPosition,
        man: CourtPosition,
    ) -> CourtPosition:
        """Compute the optimal defensive position given role and context."""
        if role == DefensiveRole.ON_BALL:
            # Stay between man and basket, one arm's length away
            return CourtPosition(
                x=max(0, man.x - 2.0),
                y=man.y,
            )

        if role == DefensiveRole.HELP_SIDE:
            # Split the distance between man and ball, shaded toward paint
            mid = _midpoint(ball, man)
            # Shade toward basket
            return CourtPosition(
                x=min(mid.x, PAINT_DEPTH_FT),
                y=max(PAINT_WIDTH_FT, min(mid.y, COURT_WIDTH_FT - PAINT_WIDTH_FT)),
            )

        if role == DefensiveRole.WEAK_SIDE:
            # Tag the paint, be ready to help
            return CourtPosition(
                x=min(man.x, PAINT_DEPTH_FT + 2),
                y=BASKET_Y + (3.0 if man.y > BASKET_Y else -3.0),
            )

        if role == DefensiveRole.CLOSEOUT:
            # Close out to shooter — between shooter and basket
            return CourtPosition(
                x=max(man.x - CLOSEOUT_DISTANCE_FT, BASKET_X),
                y=man.y,
            )

        if role in (DefensiveRole.PICK_AND_ROLL_BALL, DefensiveRole.PICK_AND_ROLL_SCREENER):
            # Handled by PnR-specific methods
            return CourtPosition(x=man.x - 2.0, y=man.y)

        if role == DefensiveRole.POST_DEFENSE:
            # Three-quarter denial on the low block
            return CourtPosition(
                x=BASKET_X + 3.0,
                y=BASKET_Y + (6.0 if man.y > BASKET_Y else -6.0),
            )

        # Default: stay near your man
        return CourtPosition(x=man.x - 1.5, y=man.y)

    def _is_help_ready(
        self,
        current: CourtPosition,
        ball: CourtPosition,
        man: CourtPosition,
    ) -> bool:
        """Check if a defender is in help-ready position (in the passing lane gap)."""
        # Help ready = can see both ball and man, positioned in gap
        dist_to_ball = _distance(current, ball)
        dist_to_man = _distance(current, man)
        ball_to_man = _distance(ball, man)

        # Should be closer to painting than man is, and not too far from either
        return (
            dist_to_ball < ball_to_man
            and dist_to_man < ball_to_man
            and current.x <= PAINT_DEPTH_FT + 5
        )

    def _generate_position_recommendations(
        self,
        role: DefensiveRole,
        current: CourtPosition,
        optimal: CourtPosition,
        dist_off: float,
        help_ready: bool,
    ) -> list[str]:
        """Generate actionable positioning recommendations."""
        recs: list[str] = []

        if dist_off > 8.0:
            recs.append(f"Major positioning gap — {dist_off:.1f}ft from optimal. Sprint to correct spot.")
        elif dist_off > 4.0:
            recs.append(f"Slightly out of position — {dist_off:.1f}ft off. Slide to tighten up.")

        if role == DefensiveRole.HELP_SIDE and not help_ready:
            recs.append("Not in help-ready stance — open up to see ball and man simultaneously.")

        if role == DefensiveRole.ON_BALL and current.x > optimal.x + 3:
            recs.append("Too far off your man — close the gap to take away the open jumper.")

        if role == DefensiveRole.WEAK_SIDE and current.x > PAINT_DEPTH_FT + 5:
            recs.append("Too far from paint — tag the paint and be ready to rotate on drive.")

        if not recs:
            recs.append("Good positioning — maintain stance and stay active.")

        return recs

    # ------------------------------------------------------------------
    # Pick-and-roll coverage analysis
    # ------------------------------------------------------------------

    def analyze_pnr_coverage(
        self,
        coverage_type: str,
        ball_handler: CourtPosition,
        screener: CourtPosition,
        defender_on_ball: CourtPosition,
        defender_on_screener: CourtPosition,
    ) -> PickAndRollCoverage:
        """Analyze pick-and-roll defensive coverage quality.

        Evaluates whether defenders are positioned correctly for the chosen
        coverage scheme and identifies breakdown risks.
        """
        coverage_info = PNR_COVERAGES.get(coverage_type, PNR_COVERAGES["drop"])

        # Grade the ball handler defender position
        ball_def_dist = _distance(defender_on_ball, ball_handler)
        ball_grade = max(0.0, 1.0 - (ball_def_dist / 10.0))

        # Grade the screener defender position
        expected_depth = coverage_info["screener_depth_ft"]
        if coverage_type == "switch":
            # On switch, screener defender should be near ball handler
            scr_grade = max(0.0, 1.0 - (_distance(defender_on_screener, ball_handler) / 10.0))
        else:
            depth_error = abs(defender_on_screener.x - expected_depth)
            scr_grade = max(0.0, 1.0 - (depth_error / 15.0))

        overall_grade = round((ball_grade * 0.6 + scr_grade * 0.4), 3)

        # Breakdown risk calculation
        gap_between_defenders = _distance(defender_on_ball, defender_on_screener)
        breakdown_risk = min(1.0, gap_between_defenders / 25.0)
        if coverage_type == "blitz" and gap_between_defenders > 15.0:
            breakdown_risk = min(1.0, breakdown_risk + 0.3)

        # Should switch?
        recommend_switch = (
            coverage_type != "switch"
            and ball_def_dist > 8.0
            and gap_between_defenders > 12.0
        )

        tips = self._generate_pnr_tips(coverage_type, ball_grade, scr_grade, breakdown_risk)

        return PickAndRollCoverage(
            coverage_type=coverage_type,
            ball_handler_position=ball_handler,
            screener_position=screener,
            defender_on_ball=defender_on_ball,
            defender_on_screener=defender_on_screener,
            coverage_grade=overall_grade,
            breakdown_risk=round(breakdown_risk, 3),
            recommended_switch=recommend_switch,
            coaching_tips=tips,
        )

    def _generate_pnr_tips(
        self,
        coverage_type: str,
        ball_grade: float,
        scr_grade: float,
        breakdown_risk: float,
    ) -> list[str]:
        """Generate coaching tips for PnR coverage."""
        tips: list[str] = []

        if coverage_type == "drop":
            if scr_grade < 0.5:
                tips.append("Big is dropping too deep — stay at the free-throw line level.")
            tips.append("Guard: fight over the screen, don't go under against shooters.")

        elif coverage_type == "hedge":
            if ball_grade < 0.5:
                tips.append("Hedge isn't aggressive enough — step out higher to slow the ball handler.")
            tips.append("Big: after hedging, sprint back to your man — don't linger.")

        elif coverage_type == "switch":
            tips.append("Communicate the switch early — call it before the screen arrives.")
            if breakdown_risk > 0.5:
                tips.append("Mismatch alert — consider helping on the post-up if switched onto a big.")

        elif coverage_type == "blitz":
            tips.append("Trap aggressively — both defenders sprint to ball handler.")
            tips.append("Weak-side defenders must rotate to cover the roll man.")

        elif coverage_type == "ice":
            tips.append("Force the ball handler baseline — take away the middle of the floor.")
            tips.append("Big: position yourself to wall off the paint, don't jump to the ball.")

        if breakdown_risk > 0.6:
            tips.append("HIGH BREAKDOWN RISK — tighten coverage or consider switching scheme.")

        return tips

    # ------------------------------------------------------------------
    # Help-side rotation tracking
    # ------------------------------------------------------------------

    def record_rotation(
        self,
        user_id: str,
        was_correct: bool,
        reaction_time_ms: float,
        role: DefensiveRole,
    ) -> RotationAnalysis:
        """Record a help-side rotation and return updated analysis.

        Tracks rotation correctness, reaction time, and generates
        improvement recommendations.
        """
        self._rotation_history[user_id].append({
            "correct": was_correct,
            "reaction_ms": reaction_time_ms,
            "role": role.value,
        })

        history = self._rotation_history[user_id]
        total = len(history)
        correct = sum(1 for r in history if r["correct"])
        accuracy = correct / max(total, 1)
        avg_reaction = sum(r["reaction_ms"] for r in history) / max(total, 1)

        mistakes = self._identify_rotation_mistakes(history)
        drills = self._suggest_rotation_drills(accuracy, avg_reaction, mistakes)

        return RotationAnalysis(
            user_id=user_id,
            rotations_analyzed=total,
            correct_rotations=correct,
            rotation_accuracy=round(accuracy, 3),
            avg_reaction_time_ms=round(avg_reaction, 1),
            common_mistakes=mistakes,
            improvement_drills=drills,
        )

    def _identify_rotation_mistakes(self, history: list[dict]) -> list[str]:
        """Identify common rotation mistakes from history."""
        mistakes: list[str] = []
        incorrect = [r for r in history if not r["correct"]]

        if not incorrect:
            return ["No common mistakes detected — keep it up!"]

        # Check for slow reactions
        slow_reactions = [r for r in incorrect if r["reaction_ms"] > 800]
        if len(slow_reactions) > len(incorrect) * 0.5:
            mistakes.append("Late rotations — reacting too slowly to drives")

        # Check for role-specific issues
        help_misses = [r for r in incorrect if r["role"] == DefensiveRole.HELP_SIDE.value]
        if len(help_misses) > 2:
            mistakes.append("Help-side breakdowns — not rotating on ball-side drives")

        weak_misses = [r for r in incorrect if r["role"] == DefensiveRole.WEAK_SIDE.value]
        if len(weak_misses) > 2:
            mistakes.append("Weak-side lapses — losing sight of man or ball")

        if not mistakes:
            mistakes.append("Inconsistent rotation angles — over-helping or under-helping")

        return mistakes

    def _suggest_rotation_drills(
        self,
        accuracy: float,
        avg_reaction: float,
        mistakes: list[str],
    ) -> list[str]:
        """Suggest drills to improve rotation quality."""
        drills: list[str] = []

        if accuracy < 0.5:
            drills.append("Shell drill basics — 4-on-4 half court, focus on gap positioning")
            drills.append("Closeout drill — practice sprinting to shooters from help position")

        if avg_reaction > 700:
            drills.append("Reaction time drill — practice reading ball handler's eyes and hips")
            drills.append("Ball-watching fix — glance at ball, eyes on man, repeat the cycle")

        if "Help-side" in str(mistakes):
            drills.append("Help rotation drill — practice baseline drive rotations")

        if not drills:
            drills.append("Advanced shell drill — 5-on-5 with screening actions")
            drills.append("PnR rotation drill — practice tag-and-recover sequences")

        return drills

    # ------------------------------------------------------------------
    # Defender path optimization
    # ------------------------------------------------------------------

    def optimize_defender_path(
        self,
        start: CourtPosition,
        target: CourtPosition,
        obstacles: list[CourtPosition] | None = None,
    ) -> list[CourtPosition]:
        """Compute the optimal path for a defender to reach a target position.

        Avoids screen obstacles and minimizes travel distance while maintaining
        defensive stance angles.
        """
        obstacles = obstacles or []

        # Direct path if no obstacles
        if not obstacles:
            return [start, target]

        # Simple obstacle avoidance — go around screens
        path = [start]
        current = start

        for obs in sorted(obstacles, key=lambda o: _distance(current, o)):
            dist_to_obs = _distance(current, obs)
            if dist_to_obs < 5.0:  # Screen is in the way
                # Go around — pick the side with more space
                if obs.y > current.y:
                    detour = CourtPosition(x=obs.x, y=max(0, obs.y - 4.0))
                else:
                    detour = CourtPosition(x=obs.x, y=min(COURT_WIDTH_FT, obs.y + 4.0))
                path.append(detour)
                current = detour

        path.append(target)
        return path


# Module-level singleton
positioning_ai = PositioningAI()
