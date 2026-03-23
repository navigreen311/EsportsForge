"""NBA 2K26 gameplay schemas — shooting, positioning, dribbling, momentum."""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from uuid import UUID, uuid4

from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# Enumerations
# ---------------------------------------------------------------------------

class ShotType(str, Enum):
    """Shot classification."""

    JUMPER = "jumper"
    LAYUP = "layup"
    DUNK = "dunk"
    FLOATER = "floater"
    POST_FADE = "post_fade"
    POST_HOOK = "post_hook"
    FREE_THROW = "free_throw"
    THREE_POINTER = "three_pointer"
    MID_RANGE = "mid_range"


class TimingGrade(str, Enum):
    """Shot timing grade."""

    VERY_EARLY = "very_early"
    EARLY = "early"
    SLIGHTLY_EARLY = "slightly_early"
    EXCELLENT = "excellent"
    SLIGHTLY_LATE = "slightly_late"
    LATE = "late"
    VERY_LATE = "very_late"


class DefensiveRole(str, Enum):
    """Defensive assignment role."""

    ON_BALL = "on_ball"
    HELP_SIDE = "help_side"
    WEAK_SIDE = "weak_side"
    PICK_AND_ROLL_BALL = "pnr_ball_handler"
    PICK_AND_ROLL_SCREENER = "pnr_screener"
    POST_DEFENSE = "post_defense"
    CLOSEOUT = "closeout"
    ZONE_ASSIGNMENT = "zone_assignment"


class DribbleMoveType(str, Enum):
    """Dribble move classification."""

    CROSSOVER = "crossover"
    BEHIND_BACK = "behind_back"
    SPIN_MOVE = "spin_move"
    HESITATION = "hesitation"
    STEPBACK = "stepback"
    IN_AND_OUT = "in_and_out"
    SNATCH_BACK = "snatch_back"
    ESCAPE_DRIBBLE = "escape_dribble"
    SIZE_UP = "size_up"
    BETWEEN_LEGS = "between_legs"


class MomentumPhase(str, Enum):
    """Game momentum phase."""

    NEUTRAL = "neutral"
    BUILDING = "building"
    ON_FIRE = "on_fire"
    LOSING = "losing"
    COLLAPSING = "collapsing"
    COMEBACK = "comeback"


class PlayCallType(str, Enum):
    """Offensive play call type."""

    PICK_AND_ROLL = "pick_and_roll"
    PICK_AND_POP = "pick_and_pop"
    ISOLATION = "isolation"
    POST_UP = "post_up"
    OFF_BALL_SCREEN = "off_ball_screen"
    FAST_BREAK = "fast_break"
    GIVE_AND_GO = "give_and_go"
    MOTION = "motion"


# ---------------------------------------------------------------------------
# Shot timing schemas
# ---------------------------------------------------------------------------

class ShotTiming(BaseModel):
    """Shot timing analysis for a specific jump shot base/release combo."""

    id: UUID = Field(default_factory=uuid4)
    user_id: str
    jump_shot_base: str = Field(..., description="Jump shot base name (e.g. 'Base 98').")
    jump_shot_release_1: str = Field(default="", description="Release 1 name.")
    jump_shot_release_2: str = Field(default="", description="Release 2 name.")
    release_blend: int = Field(
        default=50, ge=0, le=100,
        description="Blend percentage between release 1 and 2.",
    )
    release_speed: str = Field(default="normal", description="Release speed setting.")
    green_window_ms: float = Field(
        default=0.0, ge=0.0,
        description="Green window duration in milliseconds.",
    )
    optimal_release_ms: float = Field(
        default=0.0, ge=0.0,
        description="Optimal release point in ms from shot start.",
    )
    timing_grade: TimingGrade = Field(default=TimingGrade.EXCELLENT)
    make_percentage: float = Field(
        default=0.0, ge=0.0, le=1.0,
        description="Make percentage with current timing.",
    )
    green_percentage: float = Field(
        default=0.0, ge=0.0, le=1.0,
        description="Green release percentage.",
    )
    shot_type: ShotType = Field(default=ShotType.JUMPER)
    samples: int = Field(default=0, ge=0, description="Number of shots analyzed.")


class ShotTrainingPlan(BaseModel):
    """Personalized shot training plan."""

    user_id: str
    current_timing: ShotTiming
    target_green_pct: float = Field(default=0.6, ge=0.0, le=1.0)
    drills: list[str] = Field(default_factory=list)
    focus_areas: list[str] = Field(default_factory=list)
    estimated_sessions_to_target: int = Field(default=10, ge=1)
    recommended_shot_base: str = Field(default="")
    recommended_release: str = Field(default="")


class ShotFeedback(BaseModel):
    """Real-time shot feedback entry."""

    shot_type: ShotType
    timing_grade: TimingGrade
    release_ms: float = Field(ge=0.0)
    was_green: bool = False
    was_make: bool = False
    contest_level: float = Field(default=0.0, ge=0.0, le=1.0)
    shot_distance_ft: float = Field(default=0.0, ge=0.0)


# ---------------------------------------------------------------------------
# Positioning schemas
# ---------------------------------------------------------------------------

class CourtPosition(BaseModel):
    """Position on the court."""

    x: float = Field(..., ge=0.0, le=94.0, description="Court X (0-94 ft).")
    y: float = Field(..., ge=0.0, le=50.0, description="Court Y (0-50 ft).")


class DefensivePosition(BaseModel):
    """Defensive positioning analysis for a single play."""

    id: UUID = Field(default_factory=uuid4)
    user_id: str
    role: DefensiveRole
    current_position: CourtPosition
    optimal_position: CourtPosition
    distance_off_optimal_ft: float = Field(
        default=0.0, ge=0.0,
        description="Distance from optimal position in feet.",
    )
    rotation_grade: float = Field(
        default=0.0, ge=0.0, le=1.0,
        description="Rotation quality grade (0-1).",
    )
    help_ready: bool = Field(
        default=False, description="Whether player is in help-ready stance.",
    )
    gap_closed: bool = Field(
        default=False, description="Whether passing lane or gap is closed.",
    )
    recommendations: list[str] = Field(default_factory=list)


class PickAndRollCoverage(BaseModel):
    """Pick and roll defensive coverage analysis."""

    coverage_type: str = Field(
        ..., description="Coverage type (e.g. 'drop', 'hedge', 'switch', 'blitz', 'ice').",
    )
    ball_handler_position: CourtPosition
    screener_position: CourtPosition
    defender_on_ball: CourtPosition
    defender_on_screener: CourtPosition
    coverage_grade: float = Field(default=0.0, ge=0.0, le=1.0)
    breakdown_risk: float = Field(
        default=0.0, ge=0.0, le=1.0,
        description="Probability of defensive breakdown.",
    )
    recommended_switch: bool = False
    coaching_tips: list[str] = Field(default_factory=list)


class RotationAnalysis(BaseModel):
    """Help-side rotation analysis."""

    user_id: str
    rotations_analyzed: int = Field(default=0, ge=0)
    correct_rotations: int = Field(default=0, ge=0)
    rotation_accuracy: float = Field(default=0.0, ge=0.0, le=1.0)
    avg_reaction_time_ms: float = Field(default=0.0, ge=0.0)
    common_mistakes: list[str] = Field(default_factory=list)
    improvement_drills: list[str] = Field(default_factory=list)


# ---------------------------------------------------------------------------
# Dribble combo schemas
# ---------------------------------------------------------------------------

class DribbleMove(BaseModel):
    """A single dribble move input."""

    move_type: DribbleMoveType
    direction: str = Field(default="left", description="Direction: left, right, forward.")
    speed: float = Field(default=0.5, ge=0.0, le=1.0, description="Execution speed.")
    success: bool = True


class DribbleCombo(BaseModel):
    """A dribble combo chain."""

    id: UUID = Field(default_factory=uuid4)
    name: str = Field(..., description="Combo name (e.g. 'Hesi-Cross-Stepback').")
    moves: list[DribbleMove] = Field(..., min_length=2, max_length=8)
    difficulty: float = Field(
        default=0.5, ge=0.0, le=1.0, description="Execution difficulty (0-1).",
    )
    effectiveness: float = Field(
        default=0.5, ge=0.0, le=1.0,
        description="How effective at creating separation (0-1).",
    )
    best_against: list[str] = Field(
        default_factory=list,
        description="Defensive styles this combo is best against.",
    )
    min_ball_handle: int = Field(
        default=75, ge=25, le=99,
        description="Minimum ball handle attribute required.",
    )


class DribbleMastery(BaseModel):
    """User's dribble mastery profile."""

    user_id: str
    combos_mastered: list[DribbleCombo] = Field(default_factory=list)
    isolation_win_rate: float = Field(default=0.0, ge=0.0, le=1.0)
    avg_separation_created_ft: float = Field(default=0.0, ge=0.0)
    most_effective_move: DribbleMoveType | None = None
    weakest_move: DribbleMoveType | None = None
    pro_comparison: str = Field(default="", description="NBA player comp for dribble style.")


class IsolationCounter(BaseModel):
    """Counter move recommendation against a defender."""

    defender_tendency: str = Field(
        ..., description="How the defender plays (e.g. 'reaches', 'sags off', 'jumps right').",
    )
    counter_combo: DribbleCombo
    success_rate: float = Field(default=0.0, ge=0.0, le=1.0)
    explanation: str = Field(default="")


# ---------------------------------------------------------------------------
# Momentum schemas
# ---------------------------------------------------------------------------

class MomentumState(BaseModel):
    """Current game momentum state."""

    id: UUID = Field(default_factory=uuid4)
    game_id: str
    quarter: int = Field(..., ge=1, le=4)
    game_clock: str = Field(..., description="Game clock (e.g. '5:30').")
    user_score: int = Field(default=0, ge=0)
    opponent_score: int = Field(default=0, ge=0)
    phase: MomentumPhase = Field(default=MomentumPhase.NEUTRAL)
    momentum_value: float = Field(
        default=0.0, ge=-1.0, le=1.0,
        description="Momentum meter (-1=opponent, 0=neutral, 1=user).",
    )
    run_active: bool = Field(default=False, description="Whether a scoring run is in progress.")
    run_score_diff: int = Field(
        default=0,
        description="Point differential during current run.",
    )
    consecutive_stops: int = Field(default=0, ge=0)
    consecutive_scores: int = Field(default=0, ge=0)


class RunDetection(BaseModel):
    """Detection of a scoring run."""

    run_detected: bool = False
    run_type: str = Field(default="", description="'user_run' or 'opponent_run'.")
    run_length: int = Field(default=0, ge=0, description="Points scored in the run.")
    run_duration_seconds: float = Field(default=0.0, ge=0.0)
    trigger_event: str = Field(
        default="", description="Event that triggered the run.",
    )


class TimeoutDecision(BaseModel):
    """Whether to call a timeout."""

    should_call_timeout: bool = False
    urgency: float = Field(
        default=0.0, ge=0.0, le=1.0, description="How urgently a timeout is needed.",
    )
    reasoning: str = Field(default="")
    recommended_play_after: PlayCallType | None = None


class ComebackProtocol(BaseModel):
    """Comeback strategy when trailing."""

    deficit: int = Field(..., ge=0, description="Point deficit.")
    time_remaining_seconds: float = Field(..., ge=0.0)
    strategy_phases: list[str] = Field(default_factory=list)
    recommended_plays: list[PlayCallType] = Field(default_factory=list)
    defensive_adjustments: list[str] = Field(default_factory=list)
    pace_recommendation: str = Field(
        default="normal", description="Pace: slow, normal, push, frantic.",
    )
    win_probability: float = Field(default=0.0, ge=0.0, le=1.0)
    key_thresholds: list[str] = Field(
        default_factory=list,
        description="Score thresholds to hit at specific times.",
    )


# ---------------------------------------------------------------------------
# MyTeam schemas
# ---------------------------------------------------------------------------

class MyTeamCard(BaseModel):
    """MyTeam card entry."""

    card_id: str
    player_name: str
    overall_rating: int = Field(..., ge=70, le=99)
    position: str
    tier: str = Field(default="ruby", description="Card tier: emerald, sapphire, ruby, etc.")
    auction_value: int = Field(default=0, ge=0, description="Current auction house value in MT.")
    badges: list[str] = Field(default_factory=list)


class LineupSlot(BaseModel):
    """A slot in a MyTeam lineup."""

    position: str
    card: MyTeamCard
    chemistry_boost: float = Field(default=0.0, ge=0.0, le=1.0)


class MyTeamLineup(BaseModel):
    """A full MyTeam lineup."""

    id: UUID = Field(default_factory=uuid4)
    name: str
    starters: list[LineupSlot] = Field(default_factory=list, max_length=5)
    bench: list[LineupSlot] = Field(default_factory=list, max_length=8)
    total_chemistry: float = Field(default=0.0, ge=0.0, le=1.0)
    estimated_overall: int = Field(default=80, ge=60, le=99)
    meta_score: float = Field(
        default=0.0, ge=0.0, le=1.0,
        description="How well this lineup fits the current meta.",
    )


class AuctionSnipe(BaseModel):
    """Auction house snipe recommendation."""

    card: MyTeamCard
    current_price: int = Field(ge=0)
    market_value: int = Field(ge=0)
    profit_margin: int = Field(default=0)
    confidence: float = Field(default=0.5, ge=0.0, le=1.0)
    reason: str = Field(default="")
