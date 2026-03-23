"""Pydantic schemas for ForgeVault — the knowledge vault."""

from __future__ import annotations

from datetime import datetime
from enum import Enum

from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------

class VaultEntryType(str, Enum):
    """Type classification for vault entries."""

    STRATEGY = "strategy"
    MATCHUP = "matchup"
    TECHNIQUE = "technique"
    META = "meta"
    PERSONAL = "personal"
    NOTE = "note"


# ---------------------------------------------------------------------------
# Core Models
# ---------------------------------------------------------------------------

class VaultEntry(BaseModel):
    """A single knowledge entry stored in ForgeVault."""

    entry_id: str = Field(description="Unique identifier for this entry.")
    user_id: str
    key: str = Field(description="Short key/title for quick lookup.")
    content: str = Field(description="Full content of the knowledge entry.")
    tags: list[str] = Field(default_factory=list)
    entry_type: VaultEntryType = VaultEntryType.NOTE
    relevance_score: float = Field(
        default=1.0,
        ge=0.0,
        le=1.0,
        description="How relevant this entry currently is (decays over time).",
    )
    access_count: int = Field(default=0, description="Number of times retrieved.")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class VaultQuery(BaseModel):
    """Query payload for natural language search."""

    user_id: str
    query_text: str = Field(description="Natural language search query.")
    max_results: int = Field(default=10, ge=1, le=100)
    tags_filter: list[str] = Field(
        default_factory=list,
        description="Optional tags to narrow search.",
    )


class VaultSearchResult(BaseModel):
    """Result from a vault search operation."""

    entries: list[VaultEntry] = Field(default_factory=list)
    total_matches: int = 0
    query_text: str = ""
    search_time_ms: float = 0.0


class ForgeVaultStats(BaseModel):
    """Statistics about a user's vault."""

    user_id: str
    total_entries: int = 0
    entries_by_type: dict[str, int] = Field(default_factory=dict)
    entries_by_tag: dict[str, int] = Field(default_factory=dict)
    most_accessed: list[VaultEntry] = Field(default_factory=list)
    avg_relevance: float = Field(default=0.0, ge=0.0, le=1.0)
    oldest_entry: datetime | None = None
    newest_entry: datetime | None = None
