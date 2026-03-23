"""EAFC PlayerTwin — rage sub detection, playstyle identity, and tilt analysis.

Builds a digital model of the EA FC 26 player, detecting emotional patterns
like rage substitutions, identifying dominant playstyle, and tracking
decision-making under pressure.
"""

from __future__ import annotations

import logging
from collections import defaultdict
from datetime import datetime, timezone
from typing import Any

from app.schemas.eafc26.squad import (
    EAFCPlaystyle,
    EAFCPlaystyleProfile,
    EAFCTwinProfile,
    RageSubDetection,
    TiltIndicator,
)

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Playstyle classification thresholds
# ---------------------------------------------------------------------------

_PLAYSTYLE_RULES: dict[EAFCPlaystyle, dict[str, Any]] = {
    EAFCPlaystyle.POSSESSION: {
        "pass_accuracy_min": 0.82,
        "avg_possession_min": 55,
        "long_ball_pct_max": 0.15,
        "description": "Patient build-up, high pass accuracy, controls tempo",
    },
    EAFCPlaystyle.COUNTER_ATTACK: {
        "pass_accuracy_min": 0.65,
        "avg_possession_max": 45,
        "through_ball_pct_min": 0.20,
        "description": "Low possession, direct transitions, through-ball heavy",
    },
    EAFCPlaystyle.HIGH_PRESS: {
        "tackles_per_game_min": 15,
        "interceptions_min": 8,
        "avg_possession_min": 48,
        "description": "Aggressive pressing, high tackles, wins ball in opponent half",
    },
    EAFCPlaystyle.SKILL_HEAVY: {
        "skill_moves_per_game_min": 10,
        "dribble_success_min": 0.55,
        "description": "Frequent skill moves, relies on individual dribbling talent",
    },
    EAFCPlaystyle.LONG_BALL: {
        "long_ball_pct_min": 0.30,
        "avg_possession_max": 42,
        "description": "Direct approach, bypasses midfield, targets aerial duels",
    },
}

_RAGE_SUB_THRESHOLDS = {
    "sub_within_minutes": 30,  # substitution before 30th minute = suspicious
    "subs_per_half": 3,  # using all subs in one half
    "goals_conceded_trigger": 2,  # 2+ goals conceded before sub
}


class EAFCPlayerTwin:
    """Digital twin for EA FC 26 players.

    Detects rage substitution patterns, builds a playstyle identity profile,
    and monitors tilt indicators to recommend mental resets.
    """

    def __init__(self) -> None:
        self._match_history: dict[str, list[dict[str, Any]]] = defaultdict(list)
        self._sub_history: dict[str, list[dict[str, Any]]] = defaultdict(list)

    # ------------------------------------------------------------------
    # Rage sub detection
    # ------------------------------------------------------------------

    def detect_rage_subs(
        self,
        user_id: str,
        match_data: dict[str, Any],
    ) -> RageSubDetection:
        """Analyze substitution patterns to detect rage subs.

        A rage sub is characterized by premature substitutions after conceding,
        swapping formation in frustration, or burning all subs early.
        """
        subs = match_data.get("substitutions", [])
        goals_conceded_timeline = match_data.get("goals_conceded_timeline", [])
        self._match_history[user_id].append(match_data)

        rage_subs: list[dict[str, Any]] = []
        total_rage_score = 0.0

        for sub in subs:
            minute = sub.get("minute", 90)
            reason = sub.get("reason", "tactical")
            player_out = sub.get("player_out", "unknown")

            score = 0.0
            indicators: list[str] = []

            # Early sub
            if minute < _RAGE_SUB_THRESHOLDS["sub_within_minutes"]:
                score += 0.3
                indicators.append(f"Sub at minute {minute} (before 30')")

            # Sub after conceding
            recent_goals = [g for g in goals_conceded_timeline if g <= minute and g >= minute - 3]
            if recent_goals:
                score += 0.4
                indicators.append(f"Sub immediately after conceding at minute {recent_goals[0]}")

            # Formation change with sub
            if sub.get("formation_change"):
                score += 0.2
                indicators.append("Formation changed with substitution")

            # Subbing a high-rated player early
            if sub.get("player_overall", 0) >= 85 and minute < 45:
                score += 0.15
                indicators.append(f"High-rated player ({player_out}) subbed before half-time")

            if score > 0.3:
                rage_subs.append({
                    "minute": minute,
                    "player_out": player_out,
                    "rage_score": round(score, 2),
                    "indicators": indicators,
                })
                total_rage_score += score

        # Track sub history for longitudinal analysis
        for rs in rage_subs:
            self._sub_history[user_id].append(rs)

        # Compute frequency across matches
        match_count = len(self._match_history[user_id])
        rage_match_count = sum(
            1 for m in self._match_history[user_id]
            if any(s.get("minute", 90) < 30 for s in m.get("substitutions", []))
        )
        rage_frequency = rage_match_count / max(match_count, 1)

        advice: list[str] = []
        if total_rage_score > 0.5:
            advice.append("Rage sub detected — take a 30-second pause before making subs.")
            advice.append("Ask yourself: is this tactical or emotional?")
        if rage_frequency > 0.3:
            advice.append(
                f"You rage sub in {rage_frequency:.0%} of matches. "
                "Consider committing to your starting lineup for at least 60 minutes."
            )

        return RageSubDetection(
            user_id=user_id,
            rage_subs_detected=len(rage_subs),
            rage_score=round(min(total_rage_score, 1.0), 3),
            details=rage_subs,
            rage_frequency=round(rage_frequency, 3),
            advice=advice,
        )

    # ------------------------------------------------------------------
    # Playstyle identity
    # ------------------------------------------------------------------

    def identify_playstyle(
        self,
        user_id: str,
        stats: dict[str, Any],
    ) -> EAFCPlaystyleProfile:
        """Identify the player's dominant playstyle from aggregated match stats.

        Expected stats keys: pass_accuracy, avg_possession, long_ball_pct,
        through_ball_pct, tackles_per_game, interceptions, skill_moves_per_game,
        dribble_success, goals_per_game, shots_per_game.
        """
        scores: dict[EAFCPlaystyle, float] = {}

        for style, rules in _PLAYSTYLE_RULES.items():
            score = 0.0
            checks = 0
            for key, threshold in rules.items():
                if key == "description":
                    continue
                stat_key = key.replace("_min", "").replace("_max", "").replace("_pct", "_pct")
                # Normalize stat key
                stat_key = stat_key.replace("_min", "").replace("_max", "")
                stat_val = stats.get(stat_key)
                if stat_val is None:
                    continue
                checks += 1
                if key.endswith("_min") and stat_val >= threshold:
                    score += 1.0
                elif key.endswith("_max") and stat_val <= threshold:
                    score += 1.0
                elif not key.endswith("_min") and not key.endswith("_max"):
                    continue

            normalized = score / max(checks, 1)
            scores[style] = round(normalized, 3)

        # Determine dominant style
        if scores:
            dominant = max(scores, key=scores.get)  # type: ignore[arg-type]
        else:
            dominant = EAFCPlaystyle.POSSESSION

        confidence = scores.get(dominant, 0.5)
        secondary_styles = sorted(
            [(s, v) for s, v in scores.items() if s != dominant and v > 0.3],
            key=lambda x: x[1], reverse=True,
        )

        return EAFCPlaystyleProfile(
            user_id=user_id,
            dominant_style=dominant,
            confidence=confidence,
            style_scores=scores,
            secondary_styles=[s[0] for s in secondary_styles[:2]],
            description=_PLAYSTYLE_RULES[dominant]["description"],
            recommendation=(
                f"Your dominant style is {dominant.value}. "
                f"{'Consider mixing in counter-attacks to stay unpredictable.' if dominant == EAFCPlaystyle.POSSESSION else ''}"
                f"{'Add possession phases to control the game tempo.' if dominant == EAFCPlaystyle.COUNTER_ATTACK else ''}"
                f"{'Be careful of stamina drain in later stages.' if dominant == EAFCPlaystyle.HIGH_PRESS else ''}"
            ),
        )

    # ------------------------------------------------------------------
    # Tilt detection
    # ------------------------------------------------------------------

    def detect_tilt(
        self,
        user_id: str,
        recent_results: list[dict[str, Any]],
    ) -> TiltIndicator:
        """Detect if the player is on tilt based on recent match results.

        Analyzes loss streaks, goal differences, and rage sub frequency
        to produce a tilt score and recommendations.
        """
        if not recent_results:
            return TiltIndicator(
                user_id=user_id,
                tilt_score=0.0,
                is_tilted=False,
                indicators=[],
                recommendations=["No recent data to analyze."],
            )

        indicators: list[str] = []
        tilt_score = 0.0

        # Loss streak
        consecutive_losses = 0
        for result in reversed(recent_results):
            if result.get("outcome") == "loss":
                consecutive_losses += 1
            else:
                break

        if consecutive_losses >= 4:
            tilt_score += 0.4
            indicators.append(f"On a {consecutive_losses}-game losing streak")
        elif consecutive_losses >= 2:
            tilt_score += 0.2
            indicators.append(f"{consecutive_losses} consecutive losses")

        # Large goal deficits
        blowouts = sum(
            1 for r in recent_results[-5:]
            if r.get("goals_conceded", 0) - r.get("goals_scored", 0) >= 3
        )
        if blowouts >= 2:
            tilt_score += 0.25
            indicators.append(f"{blowouts} blowout losses in last 5 games")

        # Rage sub frequency in recent matches
        rage_subs = sum(
            1 for r in recent_results[-5:]
            if any(
                s.get("minute", 90) < 30
                for s in r.get("substitutions", [])
            )
        )
        if rage_subs >= 2:
            tilt_score += 0.2
            indicators.append(f"Rage subs in {rage_subs} of last 5 matches")

        # Declining pass accuracy
        recent_acc = [r.get("pass_accuracy", 0.8) for r in recent_results[-5:]]
        if len(recent_acc) >= 3:
            trend = recent_acc[-1] - recent_acc[0]
            if trend < -0.08:
                tilt_score += 0.15
                indicators.append("Pass accuracy declining over recent matches")

        tilt_score = min(tilt_score, 1.0)
        is_tilted = tilt_score >= 0.45

        recommendations: list[str] = []
        if is_tilted:
            recommendations.append("Take a 15-30 minute break before your next match.")
            recommendations.append("Play a friendly or Squad Battles to reset mentally.")
            recommendations.append("Review your last win to remind yourself of your strengths.")
        elif tilt_score > 0.2:
            recommendations.append("Stay mindful — early signs of tilt detected.")
            recommendations.append("Focus on process over results for the next 2-3 games.")

        return TiltIndicator(
            user_id=user_id,
            tilt_score=round(tilt_score, 3),
            is_tilted=is_tilted,
            indicators=indicators,
            recommendations=recommendations,
        )


# Module-level singleton
eafc_player_twin = EAFCPlayerTwin()
