"""Tests for TournaOps Console — tournament operations service."""

from __future__ import annotations

import pytest

from app.schemas.tournament import (
    HydrationLevel,
    PrepStatus,
    ResetType,
)
from app.services.backbone.tourna_ops import TournaOps, _queue_sheets, _memory_cards, _quick_notes, _hydration_log


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture(autouse=True)
def _clear_stores():
    """Clear in-memory stores before each test."""
    _queue_sheets.clear()
    _memory_cards.clear()
    _quick_notes.clear()
    _hydration_log.clear()
    yield


@pytest.fixture
def ops() -> TournaOps:
    return TournaOps()


# ---------------------------------------------------------------------------
# Opponent Queue
# ---------------------------------------------------------------------------

class TestOpponentQueue:
    def test_get_empty_queue(self, ops: TournaOps):
        sheet = ops.get_opponent_queue("user1", "tourney1")
        assert sheet.user_id == "user1"
        assert sheet.tournament_id == "tourney1"
        assert sheet.opponents == []

    def test_get_queue_returns_same_instance(self, ops: TournaOps):
        sheet1 = ops.get_opponent_queue("user1", "tourney1")
        sheet2 = ops.get_opponent_queue("user1", "tourney1")
        assert sheet1 is sheet2

    def test_add_opponent(self, ops: TournaOps):
        sheet = ops.add_opponent_to_queue(
            "user1", "tourney1", "opp1", "ProGamer99", seed=3, estimated_round=2,
        )
        assert len(sheet.opponents) == 1
        assert sheet.opponents[0].opponent_tag == "ProGamer99"
        assert sheet.opponents[0].seed == 3
        assert sheet.total_rounds == 2

    def test_add_multiple_opponents(self, ops: TournaOps):
        ops.add_opponent_to_queue("user1", "t1", "opp1", "Player1", estimated_round=1)
        sheet = ops.add_opponent_to_queue("user1", "t1", "opp2", "Player2", estimated_round=3)
        assert len(sheet.opponents) == 2
        assert sheet.total_rounds == 3


# ---------------------------------------------------------------------------
# Matchup Notes
# ---------------------------------------------------------------------------

class TestMatchupNotes:
    def test_empty_matchup(self, ops: TournaOps):
        notes = ops.get_matchup_notes("user1", "opp1")
        assert notes["total_encounters"] == 0
        assert notes["tendencies"] == []

    def test_matchup_with_memory_card(self, ops: TournaOps):
        ops.add_memory_card(
            "user1", "tourney1", "opp1", "Tag1",
            key_tendencies=["runs left", "blitzes often"],
            exploit_notes="Weak against deep routes",
        )
        notes = ops.get_matchup_notes("user1", "opp1")
        assert notes["total_encounters"] == 1
        assert "runs left" in notes["tendencies"]
        assert "Weak against deep routes" in notes["exploit_notes"]


# ---------------------------------------------------------------------------
# Warmup Checklist
# ---------------------------------------------------------------------------

class TestWarmupChecklist:
    def test_warmup_has_items(self, ops: TournaOps):
        checklist = ops.get_warmup_checklist("user1")
        assert checklist.user_id == "user1"
        assert len(checklist.items) > 0
        assert checklist.estimated_total_minutes > 0

    def test_warmup_items_not_completed(self, ops: TournaOps):
        checklist = ops.get_warmup_checklist("user1")
        assert all(item["completed"] is False for item in checklist.items)


# ---------------------------------------------------------------------------
# Reset Script
# ---------------------------------------------------------------------------

class TestResetScript:
    def test_quick_reset(self, ops: TournaOps):
        script = ops.get_reset_script("user1", ResetType.QUICK)
        assert script.reset_type == ResetType.QUICK
        assert script.duration_seconds == 30
        assert len(script.steps) > 0

    def test_standard_reset(self, ops: TournaOps):
        script = ops.get_reset_script("user1", ResetType.STANDARD)
        assert script.reset_type == ResetType.STANDARD
        assert script.duration_seconds == 120

    def test_deep_reset(self, ops: TournaOps):
        script = ops.get_reset_script("user1", ResetType.DEEP)
        assert script.reset_type == ResetType.DEEP
        assert script.duration_seconds == 300
        assert len(script.steps) > len(
            ops.get_reset_script("user1", ResetType.QUICK).steps
        )

    def test_reset_has_affirmation(self, ops: TournaOps):
        for rt in ResetType:
            script = ops.get_reset_script("user1", rt)
            assert script.affirmation != ""


# ---------------------------------------------------------------------------
# Memory Cards
# ---------------------------------------------------------------------------

class TestMemoryCards:
    def test_empty_cards(self, ops: TournaOps):
        cards = ops.get_memory_cards("user1", "tourney1")
        assert cards == []

    def test_add_and_retrieve(self, ops: TournaOps):
        card = ops.add_memory_card(
            "user1", "tourney1", "opp1", "ProGamer",
            key_tendencies=["aggressive early"],
            danger_plays=["Hail Mary on 4th"],
            confidence_rating=0.8,
        )
        assert card.opponent_tag == "ProGamer"
        assert card.confidence_rating == 0.8
        cards = ops.get_memory_cards("user1", "tourney1")
        assert len(cards) == 1

    def test_update_replaces_card(self, ops: TournaOps):
        ops.add_memory_card("user1", "t1", "opp1", "Tag1", exploit_notes="v1")
        ops.add_memory_card("user1", "t1", "opp1", "Tag1", exploit_notes="v2")
        cards = ops.get_memory_cards("user1", "t1")
        assert len(cards) == 1
        assert cards[0].exploit_notes == "v2"


# ---------------------------------------------------------------------------
# Quick Notes
# ---------------------------------------------------------------------------

class TestQuickNotes:
    def test_log_note(self, ops: TournaOps):
        result = ops.log_quick_note("user1", "They always run on 3rd down")
        assert result["total_notes"] == 1
        assert "3rd down" in result["note"]

    def test_multiple_notes(self, ops: TournaOps):
        ops.log_quick_note("user1", "Note 1")
        result = ops.log_quick_note("user1", "Note 2")
        assert result["total_notes"] == 2
        notes = ops.get_quick_notes("user1")
        assert len(notes) == 2

    def test_get_empty_notes(self, ops: TournaOps):
        assert ops.get_quick_notes("user1") == []


# ---------------------------------------------------------------------------
# Hydration
# ---------------------------------------------------------------------------

class TestHydration:
    def test_no_hydration_logged(self, ops: TournaOps):
        reminder = ops.get_hydration_reminder("user1")
        assert reminder.level == HydrationLevel.OVERDUE

    def test_log_hydration(self, ops: TournaOps):
        reminder = ops.log_hydration("user1")
        assert reminder.level == HydrationLevel.OK
