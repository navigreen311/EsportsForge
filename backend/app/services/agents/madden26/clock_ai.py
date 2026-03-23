"""ClockAI — 2-minute drill, 4th down probability, end-game scenario simulator.

Provides real-time clock management intelligence for Madden 26 competitive play.
"""

from __future__ import annotations

import math
import uuid as _uuid
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.game_session import GameSession

from app.schemas.madden26.clock import (
    ClockAction,
    ClockDecision,
    EndGamePlan,
    FourthDownChoice,
    FourthDownDecision,
    GameState,
    PlayCall,
    PlayOutcome,
    PlayType,
    SimulationResult,
    TimeoutAdvice,
    TwoMinutePlan,
)


class ClockAI:
    """Clock management intelligence for Madden 26.

    Evaluates game state and recommends optimal clock decisions including
    two-minute drill sequencing, fourth-down choices, end-game strategy,
    timeout usage, and what-if scenario simulation.
    """

    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def get_game_session(self, session_id: str) -> GameSession | None:
        """Load a GameSession from the database by ID."""
        result = await self.db.execute(
            select(GameSession).where(GameSession.id == _uuid.UUID(session_id))
        )
        return result.scalar_one_or_none()

    # Average seconds consumed per play type in Madden 26
    PLAY_TIME_MAP: dict[PlayType, int] = {
        PlayType.RUN: 40,
        PlayType.PASS_SHORT: 25,
        PlayType.PASS_MEDIUM: 28,
        PlayType.PASS_DEEP: 30,
        PlayType.SCREEN: 26,
        PlayType.DRAW: 38,
        PlayType.QB_SNEAK: 42,
        PlayType.SPIKE: 3,
        PlayType.KNEEL: 42,
    }

    # Average yards per play type
    PLAY_YARDS_MAP: dict[PlayType, float] = {
        PlayType.RUN: 4.0,
        PlayType.PASS_SHORT: 5.5,
        PlayType.PASS_MEDIUM: 9.0,
        PlayType.PASS_DEEP: 16.0,
        PlayType.SCREEN: 4.5,
        PlayType.DRAW: 4.2,
        PlayType.QB_SNEAK: 1.5,
        PlayType.SPIKE: 0.0,
        PlayType.KNEEL: -1.5,
    }

    FG_BASE_PROBABILITY: float = 0.95
    FG_DECAY_PER_YARD: float = 0.012  # Probability drops per yard beyond 20

    # -----------------------------------------------------------------------
    # Public API
    # -----------------------------------------------------------------------

    def get_clock_decision(self, game_state: GameState) -> ClockDecision:
        """Determine the optimal clock action for the current game state."""
        score_diff = game_state.score_user - game_state.score_opponent
        seconds = game_state.time_remaining_seconds
        quarter = game_state.quarter
        is_possession = game_state.is_user_possession

        # Late-game kneel-down scenario
        if (
            is_possession
            and score_diff > 0
            and quarter == 4
            and seconds <= 120
            and self._can_kneel_out(game_state)
        ):
            return ClockDecision(
                action=ClockAction.KNEEL,
                reasoning="Lead is safe and clock can be run out with kneel-downs.",
                urgency=0.1,
                recommended_play_type=PlayType.KNEEL,
                seconds_burned_estimate=float(seconds),
            )

        # Trailing late — hurry up
        if score_diff < 0 and quarter == 4 and seconds <= 240:
            urgency = min(1.0, 1.0 - (seconds / 240))
            play_type = PlayType.PASS_MEDIUM if game_state.yards_to_go > 5 else PlayType.PASS_SHORT
            return ClockDecision(
                action=ClockAction.HURRY_UP,
                reasoning=f"Trailing by {abs(score_diff)} with {seconds}s left. Must move quickly.",
                urgency=urgency,
                recommended_play_type=play_type,
                seconds_burned_estimate=float(self.PLAY_TIME_MAP.get(play_type, 25)),
            )

        # Winning and want to milk
        if score_diff > 0 and quarter >= 3 and is_possession:
            return ClockDecision(
                action=ClockAction.MILK_CLOCK,
                reasoning=f"Leading by {score_diff}. Run the clock with safe plays.",
                urgency=0.3,
                recommended_play_type=PlayType.RUN,
                seconds_burned_estimate=float(self.PLAY_TIME_MAP[PlayType.RUN]),
            )

        # Default normal tempo
        play_type = self._suggest_play_type(game_state)
        return ClockDecision(
            action=ClockAction.NORMAL,
            reasoning="Standard game situation. Play at normal tempo.",
            urgency=0.5,
            recommended_play_type=play_type,
            seconds_burned_estimate=float(self.PLAY_TIME_MAP.get(play_type, 30)),
        )

    def two_minute_drill(self, game_state: GameState) -> TwoMinutePlan:
        """Generate a full 2-minute drill play call sequence."""
        plays: list[PlayCall] = []
        sim_state = game_state.model_copy()
        yards_to_endzone = 100 - sim_state.yard_line
        seconds_left = sim_state.time_remaining_seconds

        while seconds_left > 0 and yards_to_endzone > 0 and len(plays) < 15:
            # Pick play type based on remaining distance / time
            if yards_to_endzone <= 5:
                ptype = PlayType.PASS_SHORT
                clock_act = ClockAction.HURRY_UP
            elif seconds_left < 10:
                ptype = PlayType.PASS_DEEP
                clock_act = ClockAction.HURRY_UP
            elif seconds_left < 30 and sim_state.timeouts_user == 0:
                ptype = PlayType.PASS_SHORT
                clock_act = ClockAction.SPIKE
            else:
                ptype = PlayType.PASS_MEDIUM
                clock_act = ClockAction.HURRY_UP

            avg_yards = self.PLAY_YARDS_MAP[ptype]
            time_cost = self.PLAY_TIME_MAP[ptype]

            plays.append(
                PlayCall(
                    play_name=f"2min_{ptype.value}_{len(plays) + 1}",
                    play_type=ptype,
                    clock_action=clock_act,
                    target_yards=int(avg_yards),
                    rationale=f"{yards_to_endzone}yd to go, {seconds_left}s left",
                )
            )

            yards_to_endzone -= int(avg_yards)
            seconds_left -= time_cost

        score_prob = self._estimate_drive_score_probability(game_state, len(plays))

        return TwoMinutePlan(
            game_state_snapshot=game_state,
            total_plays_planned=len(plays),
            estimated_score_probability=score_prob,
            play_sequence=plays,
            notes=f"Plan generated for {game_state.time_remaining_seconds}s remaining.",
        )

    def fourth_down_decision(self, game_state: GameState) -> FourthDownDecision:
        """Recommend go / punt / FG with probability analysis."""
        ytg = game_state.yards_to_go
        yard_line = game_state.yard_line
        distance_to_endzone = 100 - yard_line
        score_diff = game_state.score_user - game_state.score_opponent

        # Conversion probability — decreases with distance
        go_prob = max(0.05, min(0.85, 0.75 - (ytg - 1) * 0.07))

        # FG probability — based on distance
        fg_distance = distance_to_endzone + 17  # LOS + 17 yards
        fg_prob: float | None = None
        if fg_distance <= 60:
            fg_prob = max(0.05, self.FG_BASE_PROBABILITY - max(0, fg_distance - 20) * self.FG_DECAY_PER_YARD)

        # Expected points from punting (opponent starts ~45 yards back)
        punt_value = -(3.0 - (distance_to_endzone / 100) * 2.5)  # Rough EP model

        # Break-even yards
        break_even = self._break_even_yards(yard_line, score_diff)

        # Decision logic
        if game_state.quarter == 4 and score_diff < 0 and game_state.time_remaining_seconds < 300:
            # Desperation — must go for it
            recommendation = FourthDownChoice.GO_FOR_IT
            reasoning = f"Trailing by {abs(score_diff)} in Q4 with {game_state.time_remaining_seconds}s. Must convert."
        elif fg_prob is not None and fg_prob >= 0.65 and fg_distance <= 50:
            recommendation = FourthDownChoice.FIELD_GOAL
            reasoning = f"FG from {fg_distance} yards has {fg_prob:.0%} probability. Take the points."
        elif ytg <= break_even and go_prob >= 0.45:
            recommendation = FourthDownChoice.GO_FOR_IT
            reasoning = f"{ytg} yards to go is within break-even ({break_even:.1f}yd). Conversion probability {go_prob:.0%}."
        else:
            recommendation = FourthDownChoice.PUNT
            reasoning = f"Yards to go ({ytg}) exceeds break-even ({break_even:.1f}yd). Punt for field position."

        return FourthDownDecision(
            recommendation=recommendation,
            go_probability=go_prob,
            punt_value=punt_value,
            fg_probability=fg_prob,
            reasoning=reasoning,
            break_even_yards=break_even,
        )

    def end_game_scenario(self, game_state: GameState) -> EndGamePlan:
        """Build an end-game management plan."""
        score_diff = game_state.score_user - game_state.score_opponent
        seconds = game_state.time_remaining_seconds
        is_poss = game_state.is_user_possession

        # Label the scenario
        if score_diff > 0:
            label = f"leading by {score_diff}, {seconds}s left"
            strategy = "Protect the lead. Milk clock, run the ball, force opponent to burn timeouts."
        elif score_diff == 0:
            label = f"tied, {seconds}s left"
            strategy = "Score efficiently. Use middle-of-field passes and take a shot if opportunity arises."
        else:
            label = f"trailing by {abs(score_diff)}, {seconds}s left"
            scores_needed = math.ceil(abs(score_diff) / 7)
            strategy = f"Need ~{scores_needed} score(s). Hurry-up offense, target sidelines, manage timeouts."

        # Build play sequence
        plays = self._build_endgame_sequence(game_state, score_diff, is_poss)

        # Win probability estimation
        win_prob = self._estimate_win_probability(game_state)

        critical = []
        if seconds <= 30:
            critical.append("Under 30 seconds — every play critical")
        if game_state.timeouts_user == 0:
            critical.append("No timeouts — must manage sideline plays")
        if abs(score_diff) > 14:
            critical.append(f"Large deficit ({abs(score_diff)} pts) — need big plays and stops")

        return EndGamePlan(
            scenario_label=label,
            win_probability=win_prob,
            strategy=strategy,
            play_sequence=plays,
            critical_moments=critical,
        )

    def evaluate_timeout_usage(self, game_state: GameState) -> TimeoutAdvice:
        """Advise on whether to use a timeout right now."""
        seconds = game_state.time_remaining_seconds
        quarter = game_state.quarter
        timeouts = game_state.timeouts_user
        score_diff = game_state.score_user - game_state.score_opponent

        if timeouts == 0:
            return TimeoutAdvice(
                should_use_timeout=False,
                reasoning="No timeouts remaining.",
                optimal_time_to_use=None,
                timeouts_after=0,
            )

        # On defense, trailing, Q4 — use timeouts to save time
        if not game_state.is_user_possession and score_diff < 0 and quarter == 4 and seconds <= 180:
            return TimeoutAdvice(
                should_use_timeout=True,
                reasoning=f"On defense, trailing by {abs(score_diff)} with {seconds}s. Stop the clock to preserve time.",
                optimal_time_to_use=seconds,
                timeouts_after=timeouts - 1,
            )

        # On offense, need to stop clock but can't spike
        if game_state.is_user_possession and score_diff < 0 and quarter == 4 and seconds <= 60:
            return TimeoutAdvice(
                should_use_timeout=True,
                reasoning=f"Under 60s trailing. Use timeout to regroup and call optimal play.",
                optimal_time_to_use=seconds,
                timeouts_after=timeouts - 1,
            )

        # General — save them
        return TimeoutAdvice(
            should_use_timeout=False,
            reasoning="No immediate need. Preserve timeouts for a critical late-game situation.",
            optimal_time_to_use=None,
            timeouts_after=timeouts,
        )

    def simulate_scenario(self, initial_state: GameState, plays: list[str]) -> SimulationResult:
        """Run a what-if simulation given a sequence of play names."""
        outcomes: list[PlayOutcome] = []
        state = initial_state.model_copy()
        score_user = state.score_user
        score_opp = state.score_opponent
        time_left = state.time_remaining_seconds
        yard_line = state.yard_line
        down = state.down
        ytg = state.yards_to_go

        for play_name in plays:
            if time_left <= 0:
                break

            ptype = self._infer_play_type(play_name)
            yards = int(self.PLAY_YARDS_MAP.get(ptype, 4.0))
            elapsed = self.PLAY_TIME_MAP.get(ptype, 30)
            turnover = False
            score_change = 0

            new_yard_line = min(99, max(1, yard_line + yards))

            # Touchdown
            if new_yard_line >= 99:
                score_change = 7
                score_user += 7
                new_yard_line = 25  # Kickoff result approximation
                down = 1
                ytg = 10
            elif yards >= ytg:
                # First down
                down = 1
                ytg = 10
            else:
                down += 1
                ytg -= yards
                if down > 4:
                    # Turnover on downs
                    turnover = True
                    down = 1
                    ytg = 10
                    new_yard_line = 100 - new_yard_line

            time_left = max(0, time_left - elapsed)

            outcomes.append(
                PlayOutcome(
                    play_name=play_name,
                    yards_gained=yards,
                    time_elapsed_seconds=elapsed,
                    new_down=down,
                    new_yards_to_go=ytg,
                    new_yard_line=new_yard_line,
                    turnover=turnover,
                    score_change=score_change,
                )
            )

            yard_line = new_yard_line

        final_diff = score_user - score_opp
        win_prob = 0.5 + min(0.45, max(-0.45, final_diff * 0.03))

        return SimulationResult(
            initial_state=initial_state,
            play_outcomes=outcomes,
            final_score_user=score_user,
            final_score_opponent=score_opp,
            final_time_remaining=time_left,
            win_probability=round(win_prob, 3),
            summary=f"Simulated {len(outcomes)} plays. Score: {score_user}-{score_opp}, {time_left}s remaining.",
        )

    # -----------------------------------------------------------------------
    # Private helpers
    # -----------------------------------------------------------------------

    def _can_kneel_out(self, gs: GameState) -> bool:
        """Check if kneeling can run out the remaining clock."""
        kneels_available = gs.down + (4 - gs.down)  # Remaining downs
        time_per_kneel = self.PLAY_TIME_MAP[PlayType.KNEEL]
        return kneels_available * time_per_kneel >= gs.time_remaining_seconds

    def _suggest_play_type(self, gs: GameState) -> PlayType:
        """Suggest a generic play type based on down and distance."""
        if gs.yards_to_go <= 2:
            return PlayType.QB_SNEAK
        if gs.yards_to_go <= 5:
            return PlayType.RUN
        if gs.yards_to_go <= 8:
            return PlayType.PASS_SHORT
        return PlayType.PASS_MEDIUM

    def _estimate_drive_score_probability(self, gs: GameState, num_plays: int) -> float:
        """Rough probability of scoring on this drive."""
        distance = 100 - gs.yard_line
        time_factor = min(1.0, gs.time_remaining_seconds / 120)
        distance_factor = max(0.1, 1.0 - distance / 100)
        return round(min(0.95, time_factor * distance_factor * 0.85), 3)

    def _break_even_yards(self, yard_line: int, score_diff: int) -> float:
        """Yards-to-go where going for it breaks even vs. punting."""
        base = 3.0
        # More aggressive deeper in opponent territory
        position_bonus = max(0, (yard_line - 50)) * 0.06
        # More aggressive when trailing
        trail_bonus = 1.5 if score_diff < 0 else 0.0
        return base + position_bonus + trail_bonus

    def _build_endgame_sequence(
        self, gs: GameState, score_diff: int, is_possession: bool
    ) -> list[PlayCall]:
        """Build a short play sequence for end-of-game."""
        plays: list[PlayCall] = []
        if not is_possession:
            return plays  # Defensive — no play calls

        if score_diff > 0:
            # Protect lead
            for i in range(3):
                plays.append(
                    PlayCall(
                        play_name=f"endgame_run_{i + 1}",
                        play_type=PlayType.RUN,
                        clock_action=ClockAction.MILK_CLOCK,
                        target_yards=3,
                        rationale="Burn clock with safe run.",
                    )
                )
        else:
            # Need to score
            for i in range(4):
                ptype = PlayType.PASS_MEDIUM if i < 3 else PlayType.PASS_DEEP
                plays.append(
                    PlayCall(
                        play_name=f"endgame_pass_{i + 1}",
                        play_type=ptype,
                        clock_action=ClockAction.HURRY_UP,
                        target_yards=int(self.PLAY_YARDS_MAP[ptype]),
                        rationale=f"Quick score attempt, play {i + 1}.",
                    )
                )

        return plays

    def _estimate_win_probability(self, gs: GameState) -> float:
        """Estimate win probability from game state."""
        diff = gs.score_user - gs.score_opponent
        time_factor = gs.time_remaining_seconds / 900  # Full quarter
        # Logistic-ish model
        raw = 0.5 + diff * 0.04 * (1 - time_factor * 0.5)
        possession_bonus = 0.05 if gs.is_user_possession else -0.05
        return round(min(0.99, max(0.01, raw + possession_bonus)), 3)

    def _infer_play_type(self, play_name: str) -> PlayType:
        """Infer play type from play name string."""
        name = play_name.lower()
        if "kneel" in name:
            return PlayType.KNEEL
        if "spike" in name:
            return PlayType.SPIKE
        if "deep" in name:
            return PlayType.PASS_DEEP
        if "screen" in name:
            return PlayType.SCREEN
        if "draw" in name:
            return PlayType.DRAW
        if "sneak" in name:
            return PlayType.QB_SNEAK
        if "short" in name or "quick" in name:
            return PlayType.PASS_SHORT
        if "pass" in name or "medium" in name:
            return PlayType.PASS_MEDIUM
        if "run" in name or "rush" in name:
            return PlayType.RUN
        return PlayType.PASS_SHORT
