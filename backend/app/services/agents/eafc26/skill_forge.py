"""SkillForge — skill move efficiency trainer and input timing trainer for EA FC 26.

Evaluates skill move effectiveness, tracks user execution timing,
recommends optimal skill chains, and generates personalized training drills.
"""

from __future__ import annotations

import logging
from collections import defaultdict
from typing import Any

from app.schemas.eafc26.tactics import (
    InputTimingResult,
    SkillChain,
    SkillMoveAnalysis,
    SkillMoveData,
    SkillRating,
    SkillTrainingPlan,
    TimingGrade,
)

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Skill move database
# ---------------------------------------------------------------------------

_SKILL_MOVES: dict[str, dict[str, Any]] = {
    "Ball Roll": {
        "star_rating": 2, "input_window_ms": 200, "recovery_frames": 12,
        "effectiveness": {"vs_standing": 0.65, "vs_jockey": 0.40, "vs_press": 0.55},
        "best_situations": ["1v1 isolation", "Wing play", "Creating space in the box"],
        "input_sequence": "Hold RS left/right",
    },
    "Heel to Heel": {
        "star_rating": 4, "input_window_ms": 150, "recovery_frames": 18,
        "effectiveness": {"vs_standing": 0.50, "vs_jockey": 0.70, "vs_press": 0.45},
        "best_situations": ["Central areas", "Breaking press", "Through the middle"],
        "input_sequence": "Flick RS up then down",
    },
    "Elastico": {
        "star_rating": 5, "input_window_ms": 120, "recovery_frames": 22,
        "effectiveness": {"vs_standing": 0.75, "vs_jockey": 0.55, "vs_press": 0.35},
        "best_situations": ["Edge of the box", "1v1 before shooting", "Tight spaces"],
        "input_sequence": "Rotate RS from outside to inside",
    },
    "La Croqueta": {
        "star_rating": 4, "input_window_ms": 140, "recovery_frames": 14,
        "effectiveness": {"vs_standing": 0.70, "vs_jockey": 0.60, "vs_press": 0.50},
        "best_situations": ["Central play", "Quick direction change", "Avoiding tackles"],
        "input_sequence": "Hold L1/LB + RS left/right",
    },
    "Stepovers": {
        "star_rating": 2, "input_window_ms": 180, "recovery_frames": 15,
        "effectiveness": {"vs_standing": 0.55, "vs_jockey": 0.45, "vs_press": 0.60},
        "best_situations": ["Wing play", "Running at defenders", "Creating space"],
        "input_sequence": "Rotate RS forward-side repeatedly",
    },
    "Berba Spin": {
        "star_rating": 4, "input_window_ms": 160, "recovery_frames": 20,
        "effectiveness": {"vs_standing": 0.60, "vs_jockey": 0.65, "vs_press": 0.40},
        "best_situations": ["Changing direction", "Wing to middle cut", "1v1 on the flank"],
        "input_sequence": "Flick RS back then left/right",
    },
    "Fake Shot": {
        "star_rating": 1, "input_window_ms": 250, "recovery_frames": 10,
        "effectiveness": {"vs_standing": 0.60, "vs_jockey": 0.55, "vs_press": 0.65},
        "best_situations": ["Any 1v1 situation", "Creating shooting space", "Inside the box"],
        "input_sequence": "Shoot then pass immediately",
    },
    "McGeady Spin": {
        "star_rating": 5, "input_window_ms": 130, "recovery_frames": 19,
        "effectiveness": {"vs_standing": 0.70, "vs_jockey": 0.50, "vs_press": 0.40},
        "best_situations": ["Wing play", "Beating fullbacks", "Quick direction change"],
        "input_sequence": "Flick RS diagonally then opposite direction",
    },
}

# Optimal skill chains (two-move combos)
_SKILL_CHAINS: list[dict[str, Any]] = [
    {
        "name": "Ball Roll → Fake Shot",
        "moves": ["Ball Roll", "Fake Shot"],
        "combined_effectiveness": 0.72,
        "situation": "Edge of the box, create shooting angle",
        "difficulty": 0.35,
    },
    {
        "name": "La Croqueta → Elastico",
        "moves": ["La Croqueta", "Elastico"],
        "combined_effectiveness": 0.78,
        "situation": "Central 1v1, beat defender and shoot",
        "difficulty": 0.75,
    },
    {
        "name": "Stepovers → Heel to Heel",
        "moves": ["Stepovers", "Heel to Heel"],
        "combined_effectiveness": 0.68,
        "situation": "Wing play, accelerate past defender",
        "difficulty": 0.55,
    },
    {
        "name": "Berba Spin → Ball Roll",
        "moves": ["Berba Spin", "Ball Roll"],
        "combined_effectiveness": 0.65,
        "situation": "Cutting inside from the wing",
        "difficulty": 0.50,
    },
]

# Timing grade boundaries (ms offset from optimal)
_TIMING_GRADES: list[tuple[float, TimingGrade]] = [
    (20.0, TimingGrade.PERFECT),
    (50.0, TimingGrade.GOOD),
    (100.0, TimingGrade.OKAY),
    (999.0, TimingGrade.MISTIMED),
]


class SkillForge:
    """EA FC 26 skill move efficiency trainer and timing coach.

    Analyzes skill move effectiveness, tracks input timing accuracy,
    recommends skill chains, and generates training plans.
    """

    def __init__(self) -> None:
        self._timing_history: dict[str, list[InputTimingResult]] = defaultdict(list)
        self._attempt_history: dict[str, dict[str, int]] = defaultdict(lambda: defaultdict(int))

    # ------------------------------------------------------------------
    # Skill move efficiency analysis
    # ------------------------------------------------------------------

    def analyze_skill_efficiency(
        self,
        skill_name: str,
        defender_stance: str = "standing",
        user_star_rating: int = 5,
    ) -> SkillMoveAnalysis:
        """Analyze the effectiveness of a skill move given the defensive context.

        Considers defender stance, user's skill star rating, and move-specific data.
        """
        move = _SKILL_MOVES.get(skill_name)
        if not move:
            return SkillMoveAnalysis(
                skill_name=skill_name,
                available=False,
                effectiveness=0.0,
                rating=SkillRating.AVOID,
                reason=f"'{skill_name}' not found in the move database.",
                alternatives=[],
            )

        # Check star requirement
        if move["star_rating"] > user_star_rating:
            return SkillMoveAnalysis(
                skill_name=skill_name,
                available=False,
                effectiveness=0.0,
                rating=SkillRating.AVOID,
                reason=f"Requires {move['star_rating']}-star skills but player has {user_star_rating}-star.",
                alternatives=self._find_alternatives(user_star_rating, defender_stance),
            )

        stance_key = f"vs_{defender_stance}"
        effectiveness = move["effectiveness"].get(stance_key, 0.4)

        # Rate the move
        if effectiveness >= 0.70:
            rating = SkillRating.OPTIMAL
        elif effectiveness >= 0.55:
            rating = SkillRating.EFFECTIVE
        elif effectiveness >= 0.40:
            rating = SkillRating.SITUATIONAL
        else:
            rating = SkillRating.AVOID

        reason = (
            f"{skill_name} has {effectiveness:.0%} effectiveness vs {defender_stance} defenders. "
            f"Best used in: {', '.join(move['best_situations'][:2])}."
        )

        alternatives = []
        if rating in (SkillRating.SITUATIONAL, SkillRating.AVOID):
            alternatives = self._find_alternatives(user_star_rating, defender_stance)

        return SkillMoveAnalysis(
            skill_name=skill_name,
            available=True,
            effectiveness=round(effectiveness, 3),
            rating=rating,
            reason=reason,
            input_sequence=move["input_sequence"],
            recovery_frames=move["recovery_frames"],
            alternatives=alternatives,
        )

    # ------------------------------------------------------------------
    # Input timing trainer
    # ------------------------------------------------------------------

    def evaluate_timing(
        self,
        user_id: str,
        skill_name: str,
        input_ms: float,
    ) -> InputTimingResult:
        """Evaluate the timing accuracy of a skill move input.

        Compares actual input timing against the optimal window and assigns a grade.
        """
        move = _SKILL_MOVES.get(skill_name, {"input_window_ms": 150})
        optimal = move["input_window_ms"]
        offset = abs(input_ms - optimal)

        grade = TimingGrade.MISTIMED
        for threshold, g in _TIMING_GRADES:
            if offset <= threshold:
                grade = g
                break

        # Compute improvement tips
        tips: list[str] = []
        if input_ms < optimal:
            tips.append(f"Input was {offset:.0f}ms too early — slow down slightly.")
        elif input_ms > optimal:
            tips.append(f"Input was {offset:.0f}ms too late — speed up the input.")
        if grade == TimingGrade.MISTIMED:
            tips.append("Practice the input sequence in the skill games arena first.")
            tips.append(f"Optimal window for {skill_name}: {optimal}ms from move initiation.")

        result = InputTimingResult(
            user_id=user_id,
            skill_name=skill_name,
            input_ms=input_ms,
            optimal_ms=optimal,
            offset_ms=round(offset, 1),
            grade=grade,
            tips=tips,
        )
        self._timing_history[user_id].append(result)
        self._attempt_history[user_id][skill_name] += 1
        return result

    # ------------------------------------------------------------------
    # Skill chain recommender
    # ------------------------------------------------------------------

    def recommend_chains(
        self,
        user_star_rating: int = 5,
        max_difficulty: float = 1.0,
    ) -> list[SkillChain]:
        """Recommend skill move chains within the user's star rating and difficulty threshold."""
        chains: list[SkillChain] = []
        for chain_data in _SKILL_CHAINS:
            moves = chain_data["moves"]
            all_available = all(
                _SKILL_MOVES.get(m, {}).get("star_rating", 99) <= user_star_rating
                for m in moves
            )
            if not all_available:
                continue
            if chain_data["difficulty"] > max_difficulty:
                continue

            chains.append(SkillChain(
                name=chain_data["name"],
                moves=moves,
                combined_effectiveness=chain_data["combined_effectiveness"],
                situation=chain_data["situation"],
                difficulty=chain_data["difficulty"],
            ))

        chains.sort(key=lambda c: c.combined_effectiveness, reverse=True)
        return chains

    # ------------------------------------------------------------------
    # Training plan generator
    # ------------------------------------------------------------------

    def generate_training_plan(
        self,
        user_id: str,
        focus_skills: list[str] | None = None,
    ) -> SkillTrainingPlan:
        """Generate a personalized skill training plan based on timing history.

        Analyzes past attempts to identify weak areas and create targeted drills.
        """
        history = self._timing_history.get(user_id, [])
        attempts = self._attempt_history.get(user_id, {})

        # Identify weak skills
        skill_grades: dict[str, list[TimingGrade]] = defaultdict(list)
        for result in history:
            skill_grades[result.skill_name].append(result.grade)

        weak_skills: list[str] = []
        strong_skills: list[str] = []
        drills: list[str] = []

        for skill_name, grades in skill_grades.items():
            perfect_rate = sum(1 for g in grades if g == TimingGrade.PERFECT) / max(len(grades), 1)
            mistimed_rate = sum(1 for g in grades if g == TimingGrade.MISTIMED) / max(len(grades), 1)

            if mistimed_rate > 0.4:
                weak_skills.append(skill_name)
                move = _SKILL_MOVES.get(skill_name, {})
                drills.append(
                    f"Drill: {skill_name} — 20 reps in Skill Arena. "
                    f"Input: {move.get('input_sequence', 'unknown')}. "
                    f"Target window: {move.get('input_window_ms', 150)}ms."
                )
            elif perfect_rate > 0.5:
                strong_skills.append(skill_name)

        # Add default drills for new users
        if not drills:
            if focus_skills:
                for skill in focus_skills:
                    move = _SKILL_MOVES.get(skill, {})
                    drills.append(
                        f"Drill: {skill} — 15 reps against AI defender. "
                        f"Focus on {move.get('input_sequence', 'the input sequence')}."
                    )
            else:
                drills = [
                    "Drill: Ball Roll — 20 reps in the box. Focus on direction control.",
                    "Drill: Fake Shot — 15 reps in 1v1 situations. Vary the exit angle.",
                    "Drill: La Croqueta — 10 reps in central areas. Chain with a shot.",
                ]

        return SkillTrainingPlan(
            user_id=user_id,
            total_attempts=sum(attempts.values()),
            weak_skills=weak_skills,
            strong_skills=strong_skills,
            drills=drills,
            estimated_sessions=max(3, len(weak_skills) * 2),
            focus_tip=(
                f"Focus on {weak_skills[0]} — your timing is off by a significant margin."
                if weak_skills
                else "Your timing is solid. Practice chains to combine your strong moves."
            ),
        )

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _find_alternatives(star_rating: int, defender_stance: str) -> list[str]:
        stance_key = f"vs_{defender_stance}"
        alternatives: list[tuple[str, float]] = []
        for name, data in _SKILL_MOVES.items():
            if data["star_rating"] <= star_rating:
                eff = data["effectiveness"].get(stance_key, 0.3)
                if eff >= 0.55:
                    alternatives.append((name, eff))
        alternatives.sort(key=lambda x: x[1], reverse=True)
        return [a[0] for a in alternatives[:3]]


# Module-level singleton
skill_forge = SkillForge()
