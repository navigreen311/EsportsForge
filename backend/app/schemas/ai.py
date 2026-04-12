"""Pydantic schemas for AI agent request/response models."""

from pydantic import BaseModel, Field


# ─── ImpactRank ──────────────────────────────────────────────────────────────

class ImpactRankRequest(BaseModel):
    session_history: list[dict] = Field(default_factory=list, description="Recent session data")
    weaknesses: list[str] = Field(default_factory=list, description="Known weaknesses")
    title_id: str = Field(..., description="Game title identifier")


class PriorityItem(BaseModel):
    rank: int
    area: str
    impact: float
    description: str


class ImpactRankResponse(BaseModel):
    status: str
    data: dict
    source: str


# ─── Gameplan ─────────────────────────────────────────────────────────────────

class GameplanRequest(BaseModel):
    opponent_id: str = Field(..., description="Opponent identifier")
    player_identity: dict = Field(default_factory=dict, description="Player identity profile")
    title_id: str = Field(..., description="Game title identifier")


class GameplanResponse(BaseModel):
    status: str
    data: dict
    source: str


# ─── Scout ────────────────────────────────────────────────────────────────────

class ScoutRequest(BaseModel):
    gamertag: str = Field(..., description="Opponent gamertag to scout")
    title_id: str = Field(..., description="Game title identifier")


class ScoutResponse(BaseModel):
    status: str
    data: dict
    source: str


# ─── DrillBot ─────────────────────────────────────────────────────────────────

class DrillBotRequest(BaseModel):
    weaknesses: list[str] = Field(default_factory=list, description="Weaknesses to address")
    mastery_levels: dict = Field(default_factory=dict, description="Current mastery levels")
    title_id: str = Field(..., description="Game title identifier")


class DrillBotResponse(BaseModel):
    status: str
    data: dict
    source: str


# ─── Adapt ────────────────────────────────────────────────────────────────────

class AdaptRequest(BaseModel):
    what_happened: str = Field(..., description="Description of what just occurred")
    opponent_history: list[dict] = Field(default_factory=list, description="Opponent play history")
    game_state: dict = Field(default_factory=dict, description="Current game state")


class AdaptResponse(BaseModel):
    status: str
    data: dict
    source: str


# ─── Meta ─────────────────────────────────────────────────────────────────────

class MetaRequest(BaseModel):
    title_id: str = Field(..., description="Game title identifier")
    patch_version: str = Field(..., description="Current patch version")


class MetaResponse(BaseModel):
    status: str
    data: dict
    source: str


# ─── TiltGuard ────────────────────────────────────────────────────────────────

class TiltGuardRequest(BaseModel):
    mood_input: str = Field(..., description="Player's described mood or emotional state")
    session_data: dict = Field(default_factory=dict, description="Current session metrics")


class TiltGuardResponse(BaseModel):
    status: str
    data: dict
    source: str


# ─── Clock ────────────────────────────────────────────────────────────────────

class ClockRequest(BaseModel):
    game_state: dict = Field(..., description="Current game state")
    score: dict = Field(..., description="Current score")
    time_remaining: str = Field(..., description="Time remaining in game/quarter")


class ClockResponse(BaseModel):
    status: str
    data: dict
    source: str


# ─── Loop ─────────────────────────────────────────────────────────────────────

class LoopRequest(BaseModel):
    recommendation: str = Field(..., description="The recommendation that was given")
    followed: bool = Field(..., description="Whether the player followed it")
    outcome: str = Field(..., description="What happened as a result")
    session_id: str = Field(..., description="Session identifier")


class LoopResponse(BaseModel):
    status: str
    data: dict
    source: str


# ─── Confidence ───────────────────────────────────────────────────────────────

class ConfidenceRequest(BaseModel):
    recommendation: str = Field(..., description="The recommendation to evaluate")
    data_source: str = Field(..., description="Where the data came from")
    sample_size: int = Field(..., description="Number of data points")


class ConfidenceResponse(BaseModel):
    status: str
    data: dict
    source: str


# ─── Narrative ────────────────────────────────────────────────────────────────

class NarrativeRequest(BaseModel):
    session_history: list[dict] = Field(default_factory=list, description="Recent sessions")
    improvements: list[str] = Field(default_factory=list, description="Noted improvements")


class NarrativeResponse(BaseModel):
    status: str
    data: dict
    source: str
