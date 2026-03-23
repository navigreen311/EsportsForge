"""Tests for ForgeVault — knowledge vault service."""

from __future__ import annotations

import pytest

from app.schemas.vault import VaultEntryType
from app.services.backbone.forge_vault import ForgeVault, _vaults


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture(autouse=True)
def _clear_vaults():
    """Clear in-memory vault before each test."""
    _vaults.clear()
    yield


@pytest.fixture
def vault() -> ForgeVault:
    return ForgeVault()


@pytest.fixture
def populated_vault(vault: ForgeVault) -> ForgeVault:
    """Vault with several entries pre-loaded."""
    vault.store("user1", "blitz-counter", "Cover 2 shell beats the A-gap blitz", ["defense", "blitz"])
    vault.store("user1", "red-zone-plays", "Slant-flat combo in red zone is money", ["offense", "red-zone"])
    vault.store("user1", "opponent-habit", "xGamer always audibles on 3rd and long", ["opponent", "tendencies"], VaultEntryType.MATCHUP)
    vault.store("user1", "meta-patch", "Patch 1.3 nerfed cover 3 AI", ["meta", "patch"], VaultEntryType.META)
    vault.store("user1", "tilt-recovery", "Box breathing after bad loss", ["mental"], VaultEntryType.PERSONAL)
    return vault


# ---------------------------------------------------------------------------
# Store
# ---------------------------------------------------------------------------

class TestStore:
    def test_store_creates_entry(self, vault: ForgeVault):
        entry = vault.store("user1", "test-key", "test content", ["tag1"])
        assert entry.key == "test-key"
        assert entry.content == "test content"
        assert entry.tags == ["tag1"]
        assert entry.entry_id  # has an ID

    def test_store_increments_count(self, vault: ForgeVault):
        vault.store("user1", "a", "a")
        vault.store("user1", "b", "b")
        assert len(_vaults["user1"]) == 2

    def test_store_with_type(self, vault: ForgeVault):
        entry = vault.store("user1", "k", "c", entry_type=VaultEntryType.STRATEGY)
        assert entry.entry_type == VaultEntryType.STRATEGY


# ---------------------------------------------------------------------------
# Query
# ---------------------------------------------------------------------------

class TestQuery:
    def test_query_finds_matching(self, populated_vault: ForgeVault):
        result = populated_vault.query("user1", "blitz counter defense")
        assert result.total_matches >= 1
        assert any("blitz" in e.key for e in result.entries)

    def test_query_no_results(self, populated_vault: ForgeVault):
        result = populated_vault.query("user1", "xyz-nonexistent-thing")
        assert result.total_matches == 0

    def test_query_respects_max_results(self, populated_vault: ForgeVault):
        result = populated_vault.query("user1", "the", max_results=2)
        assert len(result.entries) <= 2

    def test_query_increments_access_count(self, populated_vault: ForgeVault):
        result = populated_vault.query("user1", "blitz")
        for entry in result.entries:
            assert entry.access_count >= 1


# ---------------------------------------------------------------------------
# Tag Retrieval
# ---------------------------------------------------------------------------

class TestGetByTags:
    def test_single_tag(self, populated_vault: ForgeVault):
        entries = populated_vault.get_by_tags("user1", ["defense"])
        assert len(entries) >= 1

    def test_multiple_tags(self, populated_vault: ForgeVault):
        entries = populated_vault.get_by_tags("user1", ["defense", "meta"])
        assert len(entries) >= 2

    def test_no_matching_tags(self, populated_vault: ForgeVault):
        entries = populated_vault.get_by_tags("user1", ["nonexistent"])
        assert entries == []


# ---------------------------------------------------------------------------
# Recent
# ---------------------------------------------------------------------------

class TestGetRecent:
    def test_recent_order(self, populated_vault: ForgeVault):
        entries = populated_vault.get_recent("user1")
        assert len(entries) == 5
        # Most recent should be last stored
        assert entries[0].key == "tilt-recovery"

    def test_recent_limit(self, populated_vault: ForgeVault):
        entries = populated_vault.get_recent("user1", limit=2)
        assert len(entries) == 2

    def test_recent_empty_user(self, vault: ForgeVault):
        entries = vault.get_recent("nobody")
        assert entries == []


# ---------------------------------------------------------------------------
# Stats
# ---------------------------------------------------------------------------

class TestStats:
    def test_stats_populated(self, populated_vault: ForgeVault):
        stats = populated_vault.get_stats("user1")
        assert stats.total_entries == 5
        assert stats.entries_by_type.get("note", 0) >= 1
        assert stats.avg_relevance > 0

    def test_stats_empty_user(self, vault: ForgeVault):
        stats = vault.get_stats("nobody")
        assert stats.total_entries == 0


# ---------------------------------------------------------------------------
# Delete
# ---------------------------------------------------------------------------

class TestDelete:
    def test_delete_existing(self, populated_vault: ForgeVault):
        entries = populated_vault.get_recent("user1", limit=1)
        entry_id = entries[0].entry_id
        assert populated_vault.delete("user1", entry_id) is True
        assert populated_vault.get_stats("user1").total_entries == 4

    def test_delete_nonexistent(self, vault: ForgeVault):
        assert vault.delete("user1", "fake-id") is False
