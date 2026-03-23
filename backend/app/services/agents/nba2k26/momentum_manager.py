"""2K Momentum Manager — run detection, comeback protocol, timeout decision engine.

Monitors game flow in NBA 2K26, detects scoring runs, recommends timeouts,
and generates comeback strategies based on deficit and time remaining.
"""

from __future__ import annotations

import logging

from app.schemas.nba2k26.gameplay import (
    ComebackProtocol,
    MomentumPhase,
    MomentumState,
    PlayCallType,
    RunDetection,
    TimeoutDecision,
)

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Run detection thresholds
# ---------------------------------------------------------------------------

RUN_THRESHOLD = 7           # Points scored unanswered to detect a run
BLOWOUT_THRESHOLD = 15      # Point diff to enter blowout/collapsing phase
FIRE_THRESHOLD = 0.7        # Momentum value to trigger "on_fire" phase
COMEBACK_WINDOW_SECONDS = 300  # 5 minutes of game time for comeback viability

# ---------------------------------------------------------------------------
# Timeout decision rules
# ---------------------------------------------------------------------------

TIMEOUT_RULES: list[dict] = [
    {
        "condition": "Opponent on 8-0+ run",
        "urgency": 0.9,
        "reasoning": "Stop the bleeding — opponent has momentum and your defense is breaking down.",
    },
    {
        "condition": "Opponent on 5-0 run in 4th quarter",
        "urgency": 0.95,
        "reasoning": "Critical moment — every possession matters in the clutch.",
    },
    {
        "condition": "3 consecutive turnovers",
        "urgency": 0.85,
        "reasoning": "Reset mentally — turnovers feed opponent transition offense.",
    },
    {
        "condition": "Blown 10+ point lead",
        "urgency": 0.88,
        "reasoning": "Momentum fully shifted — need to regroup before deficit grows.",
    },
]

# ---------------------------------------------------------------------------
# Comeback pace tables
# ---------------------------------------------------------------------------

PACE_TABLE: dict[str, dict] = {
    "frantic": {
        "max_deficit": 20,
        "time_range_seconds": (0, 120),
        "strategy": "Full-court press, quick shots, intentional fouls if needed",
        "plays": [PlayCallType.FAST_BREAK, PlayCallType.PICK_AND_ROLL, PlayCallType.ISOLATION],
    },
    "push": {
        "max_deficit": 15,
        "time_range_seconds": (120, 300),
        "strategy": "Push tempo, attack early in shot clock, aggressive defense",
        "plays": [PlayCallType.FAST_BREAK, PlayCallType.PICK_AND_ROLL, PlayCallType.GIVE_AND_GO],
    },
    "normal": {
        "max_deficit": 10,
        "time_range_seconds": (300, 600),
        "strategy": "Play smart basketball, get stops, execute in half court",
        "plays": [PlayCallType.PICK_AND_ROLL, PlayCallType.MOTION, PlayCallType.OFF_BALL_SCREEN],
    },
    "slow": {
        "max_deficit": 5,
        "time_range_seconds": (600, 999),
        "strategy": "Control pace, grind it out, win the possession battle",
        "plays": [PlayCallType.MOTION, PlayCallType.POST_UP, PlayCallType.PICK_AND_POP],
    },
}


class MomentumManager:
    """NBA 2K26 game momentum engine.

    Tracks momentum swings, detects scoring runs, recommends timeouts,
    and generates comeback strategies for deficit situations.
    """

    def __init__(self) -> None:
        self._game_states: dict[str, list[MomentumState]] = {}
        self._timeout_count: dict[str, int] = {}

    # ------------------------------------------------------------------
    # Momentum tracking
    # ------------------------------------------------------------------

    def update_momentum(
        self,
        game_id: str,
        quarter: int,
        game_clock: str,
        user_score: int,
        opponent_score: int,
        consecutive_stops: int = 0,
        consecutive_scores: int = 0,
    ) -> MomentumState:
        """Update and return the current momentum state.

        Computes momentum value based on score differential, recent scoring
        patterns, and game situation context.
        """
        # Calculate raw momentum value
        score_diff = user_score - opponent_score
        score_momentum = max(-1.0, min(1.0, score_diff / 20.0))

        # Scoring streak bonus
        streak_bonus = consecutive_scores * 0.1 - consecutive_stops * 0.05
        streak_bonus = max(-0.3, min(0.3, streak_bonus))

        # Quarter pressure multiplier — momentum matters more late
        pressure = 1.0 + (quarter - 1) * 0.15
        clock_mins = self._parse_clock(game_clock)
        if quarter == 4 and clock_mins <= 2.0:
            pressure = 1.8  # Clutch time

        raw_momentum = (score_momentum + streak_bonus) * min(pressure, 2.0)
        momentum_value = max(-1.0, min(1.0, raw_momentum))

        # Detect run
        run_active = consecutive_scores >= 3 or consecutive_stops >= 3
        run_diff = consecutive_scores * 2 - consecutive_stops * 2  # rough approx

        # Determine phase
        phase = self._determine_phase(momentum_value, score_diff, run_active, quarter, clock_mins)

        state = MomentumState(
            game_id=game_id,
            quarter=quarter,
            game_clock=game_clock,
            user_score=user_score,
            opponent_score=opponent_score,
            phase=phase,
            momentum_value=round(momentum_value, 3),
            run_active=run_active,
            run_score_diff=run_diff,
            consecutive_stops=consecutive_stops,
            consecutive_scores=consecutive_scores,
        )

        # Store history
        if game_id not in self._game_states:
            self._game_states[game_id] = []
        self._game_states[game_id].append(state)

        logger.info(
            "Momentum updated: game=%s Q%d %s score=%d-%d momentum=%.3f phase=%s",
            game_id, quarter, game_clock, user_score, opponent_score,
            momentum_value, phase.value,
        )
        return state

    def _determine_phase(
        self,
        momentum: float,
        score_diff: int,
        run_active: bool,
        quarter: int,
        clock_mins: float,
    ) -> MomentumPhase:
        """Classify the current momentum phase."""
        if momentum >= FIRE_THRESHOLD:
            return MomentumPhase.ON_FIRE
        if momentum >= 0.3 and run_active:
            return MomentumPhase.BUILDING
        if momentum <= -FIRE_THRESHOLD:
            return MomentumPhase.COLLAPSING
        if score_diff < -BLOWOUT_THRESHOLD:
            return MomentumPhase.COLLAPSING
        if score_diff < -5 and momentum > -0.3:
            return MomentumPhase.COMEBACK
        if momentum <= -0.3:
            return MomentumPhase.LOSING
        return MomentumPhase.NEUTRAL

    def _parse_clock(self, game_clock: str) -> float:
        """Parse game clock string to minutes remaining."""
        try:
            parts = game_clock.split(":")
            minutes = int(parts[0])
            seconds = int(parts[1]) if len(parts) > 1 else 0
            return minutes + seconds / 60.0
        except (ValueError, IndexError):
            return 6.0  # default to mid-quarter

    # ------------------------------------------------------------------
    # Run detection
    # ------------------------------------------------------------------

    def detect_run(self, game_id: str) -> RunDetection:
        """Detect if a scoring run is currently in progress.

        Analyzes recent momentum states to identify unanswered scoring streaks.
        """
        history = self._game_states.get(game_id, [])
        if len(history) < 2:
            return RunDetection(run_detected=False)

        current = history[-1]
        previous = history[-2]

        # Check for user run
        if current.consecutive_scores >= 3:
            run_length = current.consecutive_scores * 2  # approximate points
            return RunDetection(
                run_detected=True,
                run_type="user_run",
                run_length=run_length,
                run_duration_seconds=current.consecutive_scores * 24.0,  # ~24 sec per possession
                trigger_event="Consecutive baskets",
            )

        # Check for opponent run
        if current.consecutive_stops == 0 and current.momentum_value < -0.4:
            score_swing = previous.user_score - previous.opponent_score - (
                current.user_score - current.opponent_score
            )
            if score_swing >= RUN_THRESHOLD:
                return RunDetection(
                    run_detected=True,
                    run_type="opponent_run",
                    run_length=score_swing,
                    run_duration_seconds=score_swing / 2 * 24.0,
                    trigger_event="Opponent unanswered scoring",
                )

        return RunDetection(run_detected=False)

    # ------------------------------------------------------------------
    # Timeout decision engine
    # ------------------------------------------------------------------

    def should_call_timeout(self, game_id: str) -> TimeoutDecision:
        """Decide whether to call a timeout based on current game state.

        Evaluates momentum, run status, and game situation to recommend
        timeout usage with urgency rating and post-timeout play call.
        """
        history = self._game_states.get(game_id, [])
        if not history:
            return TimeoutDecision(should_call_timeout=False, reasoning="No game data available.")

        current = history[-1]
        timeouts_used = self._timeout_count.get(game_id, 0)

        # Max timeouts per half (NBA 2K typically allows 7 per game)
        max_timeouts = 7
        if timeouts_used >= max_timeouts:
            return TimeoutDecision(
                should_call_timeout=False,
                urgency=0.0,
                reasoning="No timeouts remaining.",
            )

        urgency = 0.0
        reasons: list[str] = []

        # Opponent run detection
        run = self.detect_run(game_id)
        if run.run_detected and run.run_type == "opponent_run":
            if run.run_length >= 8:
                urgency = max(urgency, 0.9)
                reasons.append(f"Opponent on {run.run_length}-0 run")
            elif run.run_length >= 5:
                urgency = max(urgency, 0.7)
                reasons.append(f"Opponent on {run.run_length}-0 run")

        # Momentum collapse
        if current.phase == MomentumPhase.COLLAPSING:
            urgency = max(urgency, 0.85)
            reasons.append("Momentum collapsing — team needs a reset")

        # Clutch time management
        if current.quarter == 4:
            clock_mins = self._parse_clock(current.game_clock)
            score_diff = current.user_score - current.opponent_score
            if clock_mins <= 2.0 and abs(score_diff) <= 5:
                urgency = max(urgency, 0.75)
                reasons.append("Clutch time — manage the clock")

        should_call = urgency >= 0.6
        reasoning = "; ".join(reasons) if reasons else "No timeout needed — momentum is stable."

        # Recommend play after timeout
        recommended_play = PlayCallType.PICK_AND_ROLL  # default
        if current.phase == MomentumPhase.COLLAPSING:
            recommended_play = PlayCallType.ISOLATION  # get bucket from best player
        elif current.quarter == 4 and self._parse_clock(current.game_clock) <= 1.0:
            recommended_play = PlayCallType.ISOLATION  # clutch ISO

        if should_call:
            self._timeout_count[game_id] = timeouts_used + 1

        return TimeoutDecision(
            should_call_timeout=should_call,
            urgency=round(urgency, 3),
            reasoning=reasoning,
            recommended_play_after=recommended_play,
        )

    # ------------------------------------------------------------------
    # Comeback protocol
    # ------------------------------------------------------------------

    def generate_comeback_protocol(
        self,
        deficit: int,
        time_remaining_seconds: float,
        quarter: int = 4,
    ) -> ComebackProtocol:
        """Generate a comeback strategy for a given deficit and time remaining.

        Produces phased strategy with play recommendations, defensive adjustments,
        and win probability estimation.
        """
        # Determine pace
        pace = "normal"
        for pace_name, pace_info in PACE_TABLE.items():
            time_range = pace_info["time_range_seconds"]
            if (time_range[0] <= time_remaining_seconds <= time_range[1]
                    and deficit <= pace_info["max_deficit"]):
                pace = pace_name
                break
        else:
            # If deficit is too large for time, go frantic
            if deficit > 15 and time_remaining_seconds < 300:
                pace = "frantic"
            elif deficit > 10:
                pace = "push"

        pace_info = PACE_TABLE.get(pace, PACE_TABLE["normal"])
        plays = pace_info["plays"]

        # Strategy phases
        phases: list[str] = []
        if deficit >= 15:
            phases = [
                "Phase 1: Get stops — switch to full-court press",
                "Phase 2: Attack in transition — push pace after every defensive rebound",
                "Phase 3: Cut deficit to single digits — then reassess",
                "Phase 4: Close it out with execution in the half court",
            ]
        elif deficit >= 8:
            phases = [
                "Phase 1: Get two consecutive stops",
                "Phase 2: Attack the paint — draw fouls, get to the line",
                "Phase 3: Shift to execution mode once within 5",
            ]
        else:
            phases = [
                "Phase 1: Play your game — don't force it",
                "Phase 2: One stop at a time, one bucket at a time",
            ]

        # Defensive adjustments
        defensive_adj: list[str] = []
        if deficit >= 10:
            defensive_adj = [
                "Switch to full-court press to speed up tempo",
                "Trap the ball handler on inbounds",
                "Contest every shot aggressively — force tough looks",
            ]
        elif deficit >= 5:
            defensive_adj = [
                "Tighten up on-ball defense — no easy buckets",
                "Switch to aggressive help defense",
                "Force turnovers without gambling",
            ]
        else:
            defensive_adj = [
                "Stay disciplined — don't foul",
                "Contest shots without leaving your feet",
            ]

        # Win probability estimation
        # Simple model: based on deficit and time remaining
        possessions_left = time_remaining_seconds / 24.0  # ~24 sec per possession
        points_per_possession = 1.1  # average
        expected_swing = possessions_left * points_per_possession * 0.1  # net advantage
        win_prob = max(0.01, min(0.95, 0.5 - (deficit / (2 * max(possessions_left, 1)))))

        # Key time/score thresholds
        thresholds: list[str] = []
        if time_remaining_seconds > 300:
            thresholds.append(f"Be within {deficit // 2} by the 5:00 mark")
        if time_remaining_seconds > 120:
            thresholds.append(f"Be within {max(deficit // 3, 3)} by the 2:00 mark")
        thresholds.append("Within 3 points entering the final minute")

        return ComebackProtocol(
            deficit=deficit,
            time_remaining_seconds=time_remaining_seconds,
            strategy_phases=phases,
            recommended_plays=plays,
            defensive_adjustments=defensive_adj,
            pace_recommendation=pace,
            win_probability=round(win_prob, 3),
            key_thresholds=thresholds,
        )

    # ------------------------------------------------------------------
    # Game momentum summary
    # ------------------------------------------------------------------

    def get_game_summary(self, game_id: str) -> dict:
        """Get a summary of momentum swings throughout the game."""
        history = self._game_states.get(game_id, [])
        if not history:
            return {"game_id": game_id, "status": "no_data"}

        phases_seen = [s.phase.value for s in history]
        momentum_values = [s.momentum_value for s in history]
        max_lead = max(s.user_score - s.opponent_score for s in history)
        max_deficit = min(s.user_score - s.opponent_score for s in history)

        return {
            "game_id": game_id,
            "total_updates": len(history),
            "current_phase": history[-1].phase.value,
            "current_momentum": history[-1].momentum_value,
            "max_momentum": max(momentum_values),
            "min_momentum": min(momentum_values),
            "max_lead": max_lead,
            "max_deficit": abs(max_deficit) if max_deficit < 0 else 0,
            "phases_experienced": list(set(phases_seen)),
            "final_score": f"{history[-1].user_score}-{history[-1].opponent_score}",
        }


# Module-level singleton
momentum_manager = MomentumManager()
