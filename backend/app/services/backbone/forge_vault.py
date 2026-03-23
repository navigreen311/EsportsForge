"""ForgeVault — persistent knowledge vault for esports intelligence.

Stores, retrieves, and searches player knowledge entries with
tag-based organization, natural-language search, and relevance tracking.
"""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

import structlog

from app.schemas.vault import (
    ForgeVaultStats,
    VaultEntry,
    VaultEntryType,
    VaultQuery,
    VaultSearchResult,
)

logger = structlog.get_logger(__name__)

# ---------------------------------------------------------------------------
# In-memory store (replaced by DB in production)
# ---------------------------------------------------------------------------
_vaults: dict[str, list[VaultEntry]] = {}  # key: user_id


class ForgeVault:
    """Knowledge vault service for storing and retrieving player knowledge."""

    # -----------------------------------------------------------------
    # Store
    # -----------------------------------------------------------------
    def store(
        self,
        user_id: str,
        key: str,
        content: str,
        tags: list[str] | None = None,
        entry_type: VaultEntryType = VaultEntryType.NOTE,
    ) -> VaultEntry:
        """Store a new knowledge entry in the vault."""
        entry = VaultEntry(
            entry_id=str(uuid.uuid4()),
            user_id=user_id,
            key=key,
            content=content,
            tags=tags or [],
            entry_type=entry_type,
        )
        if user_id not in _vaults:
            _vaults[user_id] = []
        _vaults[user_id].append(entry)
        logger.info("forge_vault.stored", user_id=user_id, key=key, entry_id=entry.entry_id)
        return entry

    # -----------------------------------------------------------------
    # Query (natural language search)
    # -----------------------------------------------------------------
    def query(self, user_id: str, query_text: str, max_results: int = 10) -> VaultSearchResult:
        """Search vault entries using natural language matching.

        Uses simple keyword matching in this implementation.
        Production would use embeddings / vector search.
        """
        start = datetime.utcnow()
        entries = _vaults.get(user_id, [])
        query_lower = query_text.lower()
        query_terms = query_lower.split()

        scored: list[tuple[float, VaultEntry]] = []
        for entry in entries:
            score = self._score_entry(entry, query_terms)
            if score > 0:
                scored.append((score, entry))

        scored.sort(key=lambda x: x[0], reverse=True)
        results = [entry for _, entry in scored[:max_results]]

        # Update access counts
        for entry in results:
            entry.access_count += 1

        elapsed = (datetime.utcnow() - start).total_seconds() * 1000
        logger.info(
            "forge_vault.query",
            user_id=user_id,
            query=query_text,
            results=len(results),
        )
        return VaultSearchResult(
            entries=results,
            total_matches=len(scored),
            query_text=query_text,
            search_time_ms=elapsed,
        )

    # -----------------------------------------------------------------
    # Tag-based retrieval
    # -----------------------------------------------------------------
    def get_by_tags(
        self, user_id: str, tags: list[str]
    ) -> list[VaultEntry]:
        """Retrieve entries matching any of the given tags."""
        entries = _vaults.get(user_id, [])
        tag_set = set(t.lower() for t in tags)
        matches = [
            e for e in entries
            if tag_set & set(t.lower() for t in e.tags)
        ]
        for entry in matches:
            entry.access_count += 1
        logger.info(
            "forge_vault.get_by_tags",
            user_id=user_id,
            tags=tags,
            results=len(matches),
        )
        return matches

    # -----------------------------------------------------------------
    # Recent entries
    # -----------------------------------------------------------------
    def get_recent(self, user_id: str, limit: int = 10) -> list[VaultEntry]:
        """Return the most recently created entries."""
        entries = _vaults.get(user_id, [])
        sorted_entries = sorted(entries, key=lambda e: e.created_at, reverse=True)
        return sorted_entries[:limit]

    # -----------------------------------------------------------------
    # Stats
    # -----------------------------------------------------------------
    def get_stats(self, user_id: str) -> ForgeVaultStats:
        """Return vault statistics for a user."""
        entries = _vaults.get(user_id, [])
        if not entries:
            return ForgeVaultStats(user_id=user_id)

        by_type: dict[str, int] = {}
        by_tag: dict[str, int] = {}
        total_relevance = 0.0

        for entry in entries:
            by_type[entry.entry_type.value] = by_type.get(entry.entry_type.value, 0) + 1
            for tag in entry.tags:
                by_tag[tag] = by_tag.get(tag, 0) + 1
            total_relevance += entry.relevance_score

        most_accessed = sorted(entries, key=lambda e: e.access_count, reverse=True)[:5]
        dates = [e.created_at for e in entries]

        return ForgeVaultStats(
            user_id=user_id,
            total_entries=len(entries),
            entries_by_type=by_type,
            entries_by_tag=by_tag,
            most_accessed=most_accessed,
            avg_relevance=total_relevance / len(entries),
            oldest_entry=min(dates),
            newest_entry=max(dates),
        )

    # -----------------------------------------------------------------
    # Delete
    # -----------------------------------------------------------------
    def delete(self, user_id: str, entry_id: str) -> bool:
        """Delete an entry from the vault. Returns True if found and deleted."""
        entries = _vaults.get(user_id, [])
        before = len(entries)
        _vaults[user_id] = [e for e in entries if e.entry_id != entry_id]
        deleted = len(_vaults[user_id]) < before
        if deleted:
            logger.info("forge_vault.deleted", user_id=user_id, entry_id=entry_id)
        return deleted

    # -----------------------------------------------------------------
    # Internals
    # -----------------------------------------------------------------
    @staticmethod
    def _score_entry(entry: VaultEntry, query_terms: list[str]) -> float:
        """Score an entry against query terms (simple keyword matching)."""
        searchable = f"{entry.key} {entry.content} {' '.join(entry.tags)}".lower()
        score = 0.0
        for term in query_terms:
            if term in searchable:
                score += 1.0
                # Bonus for key match
                if term in entry.key.lower():
                    score += 0.5
                # Bonus for tag match
                if any(term in t.lower() for t in entry.tags):
                    score += 0.3
        # Weight by relevance
        score *= entry.relevance_score
        return score
