"""Shared Pydantic schemas used across the EsportsForge platform."""

from __future__ import annotations

import math
from datetime import datetime
from typing import Any, Generic, TypeVar

from pydantic import BaseModel, Field

T = TypeVar("T")


# ---------------------------------------------------------------------------
# Pagination
# ---------------------------------------------------------------------------
class PaginatedResponse(BaseModel, Generic[T]):
    """Generic paginated response wrapper."""

    items: list[T]
    total: int = Field(..., description="Total number of records matching the query")
    page: int = Field(..., ge=1, description="Current page number (1-indexed)")
    per_page: int = Field(..., ge=1, le=100, description="Items per page")
    pages: int = Field(..., ge=0, description="Total number of pages")

    @classmethod
    def create(cls, items: list[T], total: int, page: int, per_page: int) -> PaginatedResponse[T]:
        """Factory that auto-computes *pages*."""
        return cls(
            items=items,
            total=total,
            page=page,
            per_page=per_page,
            pages=math.ceil(total / per_page) if per_page else 0,
        )


# ---------------------------------------------------------------------------
# Standard API responses
# ---------------------------------------------------------------------------
class ErrorResponse(BaseModel):
    """Consistent error shape returned by all endpoints."""

    detail: str = Field(..., description="Human-readable error description")
    code: str = Field(..., description="Machine-readable error code (e.g. 'NOT_FOUND')")
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    request_id: str | None = Field(default=None, description="Trace ID for debugging")


class SuccessResponse(BaseModel):
    """Generic success wrapper."""

    message: str = Field("ok", description="Human-readable status message")
    data: Any | None = Field(default=None, description="Optional payload")


# ---------------------------------------------------------------------------
# Agent / AI shared shapes
# ---------------------------------------------------------------------------
class ConfidenceScore(BaseModel):
    """Confidence with breakdown of contributing factors."""

    score: float = Field(..., ge=0, le=100, description="Overall confidence 0-100")
    factors: list[str] = Field(default_factory=list, description="Factors that influenced the score")
    calibrated: bool = Field(False, description="Whether the score has been calibrated against historical accuracy")


class AgentOutput(BaseModel):
    """Standard output envelope produced by every backbone agent."""

    agent_name: str = Field(..., description="Canonical agent identifier (e.g. 'gameplan', 'scout')")
    title: str = Field(..., description="Short human-readable title for this output")
    output: dict[str, Any] = Field(default_factory=dict, description="Agent-specific payload")
    confidence: ConfidenceScore
    timestamp: datetime = Field(default_factory=datetime.utcnow)


# ---------------------------------------------------------------------------
# Data quality
# ---------------------------------------------------------------------------
class DataQualityReport(BaseModel):
    """Quality metrics attached to any data pipeline output."""

    completeness: float = Field(..., ge=0, le=1, description="Fraction of expected fields present")
    freshness: float = Field(..., ge=0, le=1, description="1.0 = just ingested, decays over time")
    confidence: float = Field(..., ge=0, le=1, description="Aggregate data trustworthiness")
    issues: list[str] = Field(default_factory=list, description="Human-readable quality warnings")


# ---------------------------------------------------------------------------
# Utility / filter types
# ---------------------------------------------------------------------------
class TimeRange(BaseModel):
    """Start/end datetime filter for queries."""

    start: datetime = Field(..., description="Inclusive lower bound")
    end: datetime = Field(..., description="Exclusive upper bound")


class PatchContext(BaseModel):
    """Game patch metadata attached to sessions and analyses."""

    version: str = Field(..., description="Patch version string (e.g. '1.14.2')")
    release_date: datetime
    meta_state: str = Field(
        "stable",
        description="Current meta classification: 'fresh', 'evolving', 'stable', 'stale'",
    )
