"""Madden 26 Pydantic schemas for SchemeAI and GameplanAI."""

from app.schemas.madden26.scheme import (
    CoverageMatrix,
    CoverageMatrixRequest,
    Concept,
    HotRoute,
    HotRouteRequest,
    SchemeAnalysis,
    SchemeTendency,
    SituationPlay,
)
from app.schemas.madden26.gameplan import (
    AudibleTree,
    Gameplan,
    GameplanGenerateRequest,
    KillSheet,
    KillSheetRequest,
    MetaExploit,
    MetaRating,
    MetaReport,
    Play,
    ValidatedGameplan,
)

__all__ = [
    "CoverageMatrix",
    "CoverageMatrixRequest",
    "Concept",
    "HotRoute",
    "HotRouteRequest",
    "SchemeAnalysis",
    "SchemeTendency",
    "SituationPlay",
    "AudibleTree",
    "Gameplan",
    "GameplanGenerateRequest",
    "KillSheet",
    "KillSheetRequest",
    "MetaExploit",
    "MetaRating",
    "MetaReport",
    "Play",
    "ValidatedGameplan",
]
