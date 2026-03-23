"""ForgeVault API endpoints — knowledge vault operations."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, Query

from app.schemas.vault import (
    ForgeVaultStats,
    VaultEntry,
    VaultEntryType,
    VaultSearchResult,
)
from app.services.backbone.forge_vault import ForgeVault

router = APIRouter(prefix="/vault", tags=["ForgeVault"])

# ---------------------------------------------------------------------------
# Singleton (replaced by DI in production)
# ---------------------------------------------------------------------------
_vault = ForgeVault()


def get_vault() -> ForgeVault:
    """Accessor for the global ForgeVault instance (test-friendly)."""
    return _vault


# ---------------------------------------------------------------------------
# Store
# ---------------------------------------------------------------------------

@router.post("/store/{user_id}", response_model=VaultEntry)
async def store_entry(
    user_id: str,
    key: str = Query(..., description="Short key/title for the entry."),
    content: str = Query(..., description="Full content of the entry."),
    tags: list[str] = Query(default=[]),
    entry_type: VaultEntryType = Query(default=VaultEntryType.NOTE),
) -> VaultEntry:
    """Store a new knowledge entry in the vault."""
    return _vault.store(user_id, key, content, tags, entry_type)


# ---------------------------------------------------------------------------
# Search
# ---------------------------------------------------------------------------

@router.get("/search/{user_id}", response_model=VaultSearchResult)
async def search_vault(
    user_id: str,
    query_text: str = Query(..., description="Natural language search query."),
    max_results: int = Query(default=10, ge=1, le=100),
) -> VaultSearchResult:
    """Search vault entries using natural language."""
    return _vault.query(user_id, query_text, max_results)


# ---------------------------------------------------------------------------
# Tag retrieval
# ---------------------------------------------------------------------------

@router.get("/tags/{user_id}", response_model=list[VaultEntry])
async def get_by_tags(
    user_id: str,
    tags: list[str] = Query(..., description="Tags to filter by."),
) -> list[VaultEntry]:
    """Retrieve entries matching any of the given tags."""
    return _vault.get_by_tags(user_id, tags)


# ---------------------------------------------------------------------------
# Recent
# ---------------------------------------------------------------------------

@router.get("/recent/{user_id}", response_model=list[VaultEntry])
async def get_recent(
    user_id: str,
    limit: int = Query(default=10, ge=1, le=100),
) -> list[VaultEntry]:
    """Get the most recently created vault entries."""
    return _vault.get_recent(user_id, limit)


# ---------------------------------------------------------------------------
# Stats
# ---------------------------------------------------------------------------

@router.get("/stats/{user_id}", response_model=ForgeVaultStats)
async def get_stats(user_id: str) -> ForgeVaultStats:
    """Get vault statistics for a user."""
    return _vault.get_stats(user_id)


# ---------------------------------------------------------------------------
# Delete
# ---------------------------------------------------------------------------

@router.delete("/entry/{user_id}/{entry_id}")
async def delete_entry(user_id: str, entry_id: str) -> dict:
    """Delete a vault entry."""
    deleted = _vault.delete(user_id, entry_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Entry not found.")
    return {"deleted": True, "entry_id": entry_id}
