"""MomentumGuard — tracks, predicts, and exploits the momentum meter mechanic.

College football's momentum system is unique: crowd noise, big plays, and
game context all feed into a meter that affects player ratings, penalty
likelihood, and overall game feel. MomentumGuard reads this system and
tells the player how to exploit or recover from momentum shifts.
"""

from __future__ import annotations

import logging

from app.schemas.cfb26.momentum import (
    ActionInput,
    GameStateInput,
    MomentumDirection,
    MomentumExploit,
    MomentumPrediction,
    MomentumState,
    MomentumTrigger,
    RecoveryPlan,
)

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Momentum shift weights per trigger
# ---------------------------------------------------------------------------

TRIGGER_WEIGHTS: dict[MomentumTrigger, float] = {
    MomentumTrigger.TURNOVER: 0.25,
    MomentumTrigger.BIG_PLAY: 0.15,
    MomentumTrigger.SACK: 0.08,
    MomentumTrigger.FOURTH_DOWN_STOP: 0.20,
    MomentumTrigger.FOURTH_DOWN_CONVERSION: 0.18,
    MomentumTrigger.SCORING_DRIVE: 0.12,
    MomentumTrigger.THREE_AND_OUT: 0.10,
    MomentumTrigger.PENALTY: 0.05,
    MomentumTrigger.CROWD_NOISE: 0.06,
    MomentumTrigger.TIMEOUT: 0.03,
    MomentumTrigger.TRICK_PLAY: 0.15,
    MomentumTrigger.GOAL_LINE_STAND: 0.22,
}

# Action type to expected momentum shift direction
ACTION_MOMENTUM_MAP: dict[str, float] = {
    "deep_pass": 0.12,
    "trick_play": 0.18,
    "fourth_down_go": 0.20,
    "hurry_up_tempo": 0.05,
    "run_play": 0.02,
    "screen_pass": 0.03,
    "field_goal": 0.04,
    "punt": -0.02,
    "timeout": -0.01,
    "conservative_run": -0.03,
    "kneel": -0.05,
}


class MomentumGuard:
    """Momentum tracking and exploitation engine.

    MVP uses stateless calculations. Production version will maintain
    per-game state and feed into real-time coaching overlays.
    """

    def __init__(self) -> None:
        # In-memory game state cache: game_id -> MomentumState
        self._game_states: dict[str, MomentumState] = {}

    # ------------------------------------------------------------------
    # Track momentum
    # ------------------------------------------------------------------

    def track_momentum(self, game_state: GameStateInput) -> MomentumState:
        """Calculate current momentum meter reading from game state.

        Factors: score differential, recent events, home/away, quarter,
        field position, and crowd noise.
        """
        # Score differential factor
        score_diff = game_state.home_score - game_state.away_score
        score_factor = max(min(score_diff / 28.0, 1.0), -1.0)  # normalize to -1..1

        # Recency factor from events
        event_momentum = 0.0
        recent_triggers: list[MomentumTrigger] = []
        for event in game_state.recent_events[-5:]:  # last 5 events
            try:
                trigger = MomentumTrigger(event)
                weight = TRIGGER_WEIGHTS.get(trigger, 0.0)
                event_momentum += weight
                recent_triggers.append(trigger)
            except ValueError:
                continue

        # Home field advantage
        home_boost = 0.1 if game_state.is_home_game else -0.1
        noise_boost = game_state.stadium_noise_level * 0.15

        # Quarter urgency — momentum matters more late in the game
        quarter_weight = 0.8 + (game_state.quarter * 0.05)

        # Combine factors
        raw_meter = (
            score_factor * 0.3
            + event_momentum * 0.35
            + (home_boost + noise_boost) * 0.2
        ) * quarter_weight

        meter_value = max(min(raw_meter, 1.0), -1.0)

        # Determine direction
        if meter_value > 0.3:
            direction = MomentumDirection.CRITICAL_HIGH
        elif meter_value > 0.1:
            direction = MomentumDirection.RISING
        elif meter_value < -0.3:
            direction = MomentumDirection.CRITICAL_LOW
        elif meter_value < -0.1:
            direction = MomentumDirection.FALLING
        else:
            direction = MomentumDirection.NEUTRAL

        # Velocity: how fast momentum is changing
        velocity = event_momentum * 0.5

        state = MomentumState(
            meter_value=round(meter_value, 4),
            direction=direction,
            velocity=round(velocity, 4),
            home_team=game_state.home_team,
            away_team=game_state.away_team,
            quarter=game_state.quarter,
            game_clock=game_state.game_clock,
            recent_triggers=recent_triggers,
            plays_since_last_shift=len(game_state.recent_events),
        )

        # Cache the state
        game_id = f"{game_state.home_team}_vs_{game_state.away_team}"
        self._game_states[game_id] = state

        logger.info(
            "Tracked momentum: %s meter=%.4f direction=%s",
            game_id, meter_value, direction.value,
        )
        return state

    # ------------------------------------------------------------------
    # Predict momentum shift
    # ------------------------------------------------------------------

    def predict_momentum_shift(
        self,
        game_state: GameStateInput,
        action: ActionInput,
    ) -> MomentumPrediction:
        """Predict how an action will affect momentum.

        Considers the action type, current game state, and risk level
        to project the momentum shift.
        """
        current = self.track_momentum(game_state)

        # Base shift from action type
        base_shift = ACTION_MOMENTUM_MAP.get(action.action_type, 0.0)

        # Aggression amplifies both upside and downside
        amplified_shift = base_shift * (1.0 + action.aggression * 0.5)

        # Success probability depends on current momentum
        if current.direction in (MomentumDirection.RISING, MomentumDirection.CRITICAL_HIGH):
            # Riding momentum — higher success probability
            trigger_prob = min(0.7 + action.aggression * 0.2, 0.95)
        elif current.direction in (MomentumDirection.FALLING, MomentumDirection.CRITICAL_LOW):
            # Against momentum — lower success probability
            trigger_prob = max(0.3 - action.aggression * 0.1, 0.1)
        else:
            trigger_prob = 0.5

        # Weighted prediction
        predicted_shift = amplified_shift * trigger_prob
        new_meter = max(min(current.meter_value + predicted_shift, 1.0), -1.0)

        # Determine new direction
        if new_meter > 0.3:
            new_direction = MomentumDirection.CRITICAL_HIGH
        elif new_meter > 0.1:
            new_direction = MomentumDirection.RISING
        elif new_meter < -0.3:
            new_direction = MomentumDirection.CRITICAL_LOW
        elif new_meter < -0.1:
            new_direction = MomentumDirection.FALLING
        else:
            new_direction = MomentumDirection.NEUTRAL

        # Risk assessment
        risk = "low"
        if action.aggression > 0.7 and current.direction in (
            MomentumDirection.FALLING, MomentumDirection.CRITICAL_LOW
        ):
            risk = "critical"
        elif action.aggression > 0.5:
            risk = "high"
        elif action.aggression > 0.3:
            risk = "medium"

        reasoning = (
            f"Action '{action.action_type}' with aggression {action.aggression:.1f} "
            f"from {current.direction.value} momentum. "
            f"{'Riding the wave amplifies success.' if current.meter_value > 0.1 else ''}"
            f"{'Going against momentum increases risk.' if current.meter_value < -0.1 else ''}"
        )

        return MomentumPrediction(
            predicted_shift=round(predicted_shift, 4),
            new_meter_value=round(new_meter, 4),
            new_direction=new_direction,
            trigger_probability=round(trigger_prob, 3),
            risk_level=risk,
            reasoning=reasoning.strip(),
        )

    # ------------------------------------------------------------------
    # Exploit momentum
    # ------------------------------------------------------------------

    def get_momentum_exploit(self, momentum_state: MomentumState) -> MomentumExploit:
        """How to exploit the current momentum state.

        Generates play recommendations, tempo, and aggression level
        based on the current momentum meter.
        """
        meter = momentum_state.meter_value
        direction = momentum_state.direction

        if direction == MomentumDirection.CRITICAL_HIGH:
            return MomentumExploit(
                strategy="Maximum aggression — ride the momentum wave",
                recommended_plays=[
                    "deep_pass", "trick_play", "fourth_down_go",
                    "hurry_up_tempo", "play_action_shot",
                ],
                tempo_recommendation="hurry_up",
                aggression_level=0.9,
                key_advantages=[
                    "Opponent ratings temporarily reduced",
                    "Your players get confidence boost",
                    "Crowd noise is at maximum — use it",
                    "Higher chance of opponent penalties",
                ],
                window_plays=4,
            )
        elif direction == MomentumDirection.RISING:
            return MomentumExploit(
                strategy="Push the advantage — build on momentum",
                recommended_plays=[
                    "play_action", "RPO", "tempo_run", "screen_pass",
                ],
                tempo_recommendation="hurry_up",
                aggression_level=0.7,
                key_advantages=[
                    "Momentum is building — keep the pressure on",
                    "Opponent may start making mistakes",
                    "Good time for calculated risks",
                ],
                window_plays=6,
            )
        elif direction == MomentumDirection.CRITICAL_LOW:
            return MomentumExploit(
                strategy="Damage control — stop the bleeding immediately",
                recommended_plays=[
                    "safe_run", "short_pass", "timeout", "field_goal",
                ],
                tempo_recommendation="slow_down",
                aggression_level=0.2,
                key_advantages=[
                    "Slowing tempo can break opponent rhythm",
                    "Timeout can reset the momentum meter",
                ],
                window_plays=3,
            )
        elif direction == MomentumDirection.FALLING:
            return MomentumExploit(
                strategy="Stabilize — prevent momentum from snowballing",
                recommended_plays=[
                    "power_run", "screen_pass", "safe_checkdown",
                ],
                tempo_recommendation="normal",
                aggression_level=0.4,
                key_advantages=[
                    "One big play can flip the script",
                    "Methodical drive can reset momentum to neutral",
                ],
                window_plays=5,
            )
        else:
            return MomentumExploit(
                strategy="Neutral state — look for the spark play",
                recommended_plays=[
                    "balanced_attack", "RPO", "play_action",
                    "occasional_deep_shot",
                ],
                tempo_recommendation="normal",
                aggression_level=0.5,
                key_advantages=[
                    "No momentum disadvantage",
                    "Good time to establish your game plan",
                    "A big play here can seize momentum",
                ],
                window_plays=8,
            )

    # ------------------------------------------------------------------
    # Momentum recovery
    # ------------------------------------------------------------------

    def get_momentum_recovery(self, deficit_state: MomentumState) -> RecoveryPlan:
        """Plan to recover from a momentum deficit.

        Analyzes how bad the deficit is and provides actionable steps
        to get back to neutral or positive momentum.
        """
        meter = deficit_state.meter_value

        if meter <= -0.5:
            severity = "dire"
            immediate = [
                "Call timeout IMMEDIATELY to break the run",
                "Switch to a completely different defensive look",
                "Go ultra-conservative on offense — no turnovers",
                "Consider onside kick if late in the game",
            ]
            style_shift = "Ground and pound — eat clock, control tempo, avoid mistakes"
            use_timeout = True
            plays_to_neutral = 12
            risk = "Only take risks if you're down multiple scores in the 4th quarter"
        elif meter <= -0.3:
            severity = "severe"
            immediate = [
                "Consider a timeout to regroup",
                "Make a defensive substitution to change the energy",
                "Run the ball to slow the game down",
            ]
            style_shift = "Ball control offense — short passes and power runs"
            use_timeout = True
            plays_to_neutral = 8
            risk = "One calculated risk per drive — a screen or play-action shot"
        elif meter <= -0.1:
            severity = "moderate"
            immediate = [
                "Stay disciplined — don't panic",
                "Mix in a big play attempt to spark momentum",
                "Focus on winning the next play, not the next drive",
            ]
            style_shift = "Balanced attack with occasional aggression"
            use_timeout = False
            plays_to_neutral = 5
            risk = "Moderate risk acceptable — RPOs and play-action are good choices"
        else:
            severity = "mild"
            immediate = [
                "No major adjustments needed",
                "Stay focused on executing the game plan",
            ]
            style_shift = "Continue current approach with slight urgency"
            use_timeout = False
            plays_to_neutral = 3
            risk = "Normal risk tolerance — play your game"

        return RecoveryPlan(
            severity=severity,
            immediate_actions=immediate,
            play_style_shift=style_shift,
            timeout_recommendation=use_timeout,
            estimated_plays_to_neutral=plays_to_neutral,
            risk_acceptance=risk,
        )


# Module-level singleton
momentum_guard = MomentumGuard()
