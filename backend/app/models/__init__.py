"""EsportsForge database models — import all models for Alembic discovery."""

from app.models.base import TimestampMixin, UUIDPrimaryKeyMixin
from app.models.user import User, UserRole
from app.models.player_profile import PlayerProfile, InputType
from app.models.game_session import GameSession, GameMode, GameResult
from app.models.recommendation import Recommendation
from app.models.opponent import Opponent
from app.models.gameplan import Gameplan
from app.models.agent_performance import AgentPerformance
from app.models.impact_ranking import ImpactRanking, ImpactStatus
from app.models.drill import Drill
from app.models.integrity_mode import IntegrityMode, GameEnvironment, AntiCheatStatus
from app.models.madden26 import MaddenScheme, MaddenPlay, SchemeType
from app.models.cfb26 import (
    CFBScheme,
    CFBPlay,
    CFBSchemeType,
    CFBRecruitingTarget,
    RecruitingPipeline,
)

__all__ = [
    # Mixins
    "TimestampMixin",
    "UUIDPrimaryKeyMixin",
    # Core models
    "User",
    "PlayerProfile",
    "GameSession",
    "Recommendation",
    "Opponent",
    "Gameplan",
    "AgentPerformance",
    "ImpactRanking",
    "Drill",
    "IntegrityMode",
    # Madden 26
    "MaddenScheme",
    "MaddenPlay",
    # CFB 26
    "CFBScheme",
    "CFBPlay",
    "CFBRecruitingTarget",
    # Enums
    "UserRole",
    "InputType",
    "GameMode",
    "GameResult",
    "ImpactStatus",
    "GameEnvironment",
    "AntiCheatStatus",
    "SchemeType",
    "CFBSchemeType",
    "RecruitingPipeline",
]
