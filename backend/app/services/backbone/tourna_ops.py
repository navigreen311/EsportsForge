"""TournaOps Console — tournament operations assistant.

Provides opponent queue management, matchup notes, warmup checklists,
mental reset scripts, memory cards, and quick note logging for
tournament day operations.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timedelta
from typing import Any

import structlog

from app.schemas.tournament import (
    HydrationLevel,
    HydrationReminder,
    MemoryCard,
    OpponentQueue,
    PrepStatus,
    QueueSheet,
    ResetScript,
    ResetType,
    TournamentPrep,
    WarmupChecklist,
)

logger = structlog.get_logger(__name__)

# ---------------------------------------------------------------------------
# Default warmup items
# ---------------------------------------------------------------------------
DEFAULT_WARMUP_ITEMS: list[dict[str, Any]] = [
    {"task": "Controller/input warm-up drill", "completed": False, "duration_minutes": 5, "category": "mechanical"},
    {"task": "Reaction time trainer", "completed": False, "duration_minutes": 3, "category": "cognitive"},
    {"task": "Review opponent memory cards", "completed": False, "duration_minutes": 5, "category": "preparation"},
    {"task": "Run favorite play sequence 3x", "completed": False, "duration_minutes": 5, "category": "mechanical"},
    {"task": "Breathing exercise (box breathing)", "completed": False, "duration_minutes": 2, "category": "mental"},
    {"task": "Visualize first 3 plays", "completed": False, "duration_minutes": 3, "category": "mental"},
    {"task": "Check hydration & snacks", "completed": False, "duration_minutes": 1, "category": "physical"},
    {"task": "Test audio/comms setup", "completed": False, "duration_minutes": 2, "category": "equipment"},
]

# ---------------------------------------------------------------------------
# Default reset scripts
# ---------------------------------------------------------------------------
RESET_SCRIPTS: dict[ResetType, dict[str, Any]] = {
    ResetType.QUICK: {
        "steps": [
            "Close eyes, 3 deep breaths (4-4-4 pattern).",
            "Release controller, shake out hands.",
            "One positive self-talk statement.",
            "Refocus: what is the ONE thing to do next round?",
        ],
        "affirmation": "I adapt. I execute. I win.",
        "duration_seconds": 30,
    },
    ResetType.STANDARD: {
        "steps": [
            "Set controller down. Stand up if possible.",
            "Box breathing: 4 counts in, 4 hold, 4 out, 4 hold. Repeat 3x.",
            "Body scan — release tension in jaw, shoulders, hands.",
            "Review: what worked last round? Keep that.",
            "Review: what failed? One adjustment only.",
            "Sip water. Re-grip controller.",
            "Positive statement: state your game plan in one sentence.",
        ],
        "affirmation": "Process over outcome. Execute the plan.",
        "duration_seconds": 120,
    },
    ResetType.DEEP: {
        "steps": [
            "Step away from screen completely.",
            "Walk 10 steps, stretch arms overhead.",
            "Extended breathing: 5 counts in, 7 out. Repeat 5x.",
            "Full body tension release — clench everything, then release.",
            "Mental replay: visualize your BEST moment from today.",
            "Write one sentence: what you will do differently.",
            "Hydrate fully. Eat a small snack if needed.",
            "Return to setup. Adjust seating/posture.",
            "3 practice inputs to confirm feel.",
            "State game plan aloud. Begin.",
        ],
        "affirmation": "I have prepared for this. Trust the process.",
        "duration_seconds": 300,
    },
}


# ---------------------------------------------------------------------------
# In-memory stores (replaced by DB in production)
# ---------------------------------------------------------------------------
_queue_sheets: dict[str, QueueSheet] = {}        # key: f"{user_id}:{tournament_id}"
_memory_cards: dict[str, list[MemoryCard]] = {}  # key: f"{user_id}:{tournament_id}"
_quick_notes: dict[str, list[str]] = {}          # key: user_id
_hydration_log: dict[str, datetime] = {}         # key: user_id


class TournaOps:
    """Tournament operations console service."""

    # -----------------------------------------------------------------
    # Opponent Queue
    # -----------------------------------------------------------------
    def get_opponent_queue(self, user_id: str, tournament_id: str) -> QueueSheet:
        """Return the queue sheet with prep status per opponent.

        If no queue exists yet, returns an empty sheet the player can populate.
        """
        key = f"{user_id}:{tournament_id}"
        if key in _queue_sheets:
            logger.info("tourna_ops.queue_hit", user_id=user_id, tournament_id=tournament_id)
            return _queue_sheets[key]

        sheet = QueueSheet(
            user_id=user_id,
            tournament_id=tournament_id,
        )
        _queue_sheets[key] = sheet
        logger.info("tourna_ops.queue_created", user_id=user_id, tournament_id=tournament_id)
        return sheet

    def add_opponent_to_queue(
        self,
        user_id: str,
        tournament_id: str,
        opponent_id: str,
        opponent_tag: str,
        seed: int | None = None,
        estimated_round: int | None = None,
    ) -> QueueSheet:
        """Add an opponent to the queue sheet."""
        sheet = self.get_opponent_queue(user_id, tournament_id)
        entry = OpponentQueue(
            opponent_id=opponent_id,
            opponent_tag=opponent_tag,
            seed=seed,
            estimated_round=estimated_round,
        )
        sheet.opponents.append(entry)
        sheet.total_rounds = max(sheet.total_rounds, estimated_round or 0)
        logger.info(
            "tourna_ops.opponent_added",
            user_id=user_id,
            opponent_tag=opponent_tag,
        )
        return sheet

    # -----------------------------------------------------------------
    # Matchup Notes
    # -----------------------------------------------------------------
    def get_matchup_notes(self, user_id: str, opponent_id: str) -> dict[str, Any]:
        """Return quick matchup notes for a specific opponent.

        Aggregates across all tournaments where this opponent was faced.
        """
        notes: list[str] = []
        tendencies: list[str] = []

        for key, cards in _memory_cards.items():
            if not key.startswith(f"{user_id}:"):
                continue
            for card in cards:
                if card.opponent_id == opponent_id:
                    tendencies.extend(card.key_tendencies)
                    if card.exploit_notes:
                        notes.append(card.exploit_notes)

        return {
            "user_id": user_id,
            "opponent_id": opponent_id,
            "tendencies": list(set(tendencies)),
            "exploit_notes": notes,
            "total_encounters": len(notes),
        }

    # -----------------------------------------------------------------
    # Warmup Checklist
    # -----------------------------------------------------------------
    def get_warmup_checklist(self, user_id: str) -> WarmupChecklist:
        """Return the pre-tournament warmup routine."""
        total_minutes = sum(item["duration_minutes"] for item in DEFAULT_WARMUP_ITEMS)
        return WarmupChecklist(
            user_id=user_id,
            items=[dict(item) for item in DEFAULT_WARMUP_ITEMS],
            estimated_total_minutes=total_minutes,
            notes="Complete all items before your first match.",
        )

    # -----------------------------------------------------------------
    # Reset Script
    # -----------------------------------------------------------------
    def get_reset_script(
        self, user_id: str, reset_type: ResetType = ResetType.STANDARD
    ) -> ResetScript:
        """Return a between-round mental reset script."""
        template = RESET_SCRIPTS[reset_type]
        return ResetScript(
            user_id=user_id,
            reset_type=reset_type,
            steps=list(template["steps"]),
            affirmation=template["affirmation"],
            duration_seconds=template["duration_seconds"],
        )

    # -----------------------------------------------------------------
    # Memory Cards
    # -----------------------------------------------------------------
    def get_memory_cards(
        self, user_id: str, tournament_id: str
    ) -> list[MemoryCard]:
        """Return quick-reference memory cards for a tournament."""
        key = f"{user_id}:{tournament_id}"
        return _memory_cards.get(key, [])

    def add_memory_card(
        self,
        user_id: str,
        tournament_id: str,
        opponent_id: str,
        opponent_tag: str,
        key_tendencies: list[str] | None = None,
        exploit_notes: str = "",
        danger_plays: list[str] | None = None,
        confidence_rating: float = 0.5,
    ) -> MemoryCard:
        """Create or update a memory card for an opponent."""
        key = f"{user_id}:{tournament_id}"
        card = MemoryCard(
            opponent_id=opponent_id,
            opponent_tag=opponent_tag,
            key_tendencies=key_tendencies or [],
            exploit_notes=exploit_notes,
            danger_plays=danger_plays or [],
            confidence_rating=confidence_rating,
        )
        if key not in _memory_cards:
            _memory_cards[key] = []
        # Replace existing card for same opponent or append
        _memory_cards[key] = [
            c for c in _memory_cards[key] if c.opponent_id != opponent_id
        ]
        _memory_cards[key].append(card)
        logger.info(
            "tourna_ops.memory_card_saved",
            user_id=user_id,
            opponent_tag=opponent_tag,
        )
        return card

    # -----------------------------------------------------------------
    # Quick Notes
    # -----------------------------------------------------------------
    def log_quick_note(self, user_id: str, note: str) -> dict[str, Any]:
        """Log a fast note during a tournament."""
        if user_id not in _quick_notes:
            _quick_notes[user_id] = []
        timestamped = f"[{datetime.utcnow().isoformat()}] {note}"
        _quick_notes[user_id].append(timestamped)
        logger.info("tourna_ops.quick_note", user_id=user_id)
        return {
            "user_id": user_id,
            "note": timestamped,
            "total_notes": len(_quick_notes[user_id]),
        }

    def get_quick_notes(self, user_id: str) -> list[str]:
        """Return all quick notes for a user."""
        return _quick_notes.get(user_id, [])

    # -----------------------------------------------------------------
    # Hydration
    # -----------------------------------------------------------------
    def get_hydration_reminder(self, user_id: str) -> HydrationReminder:
        """Check hydration status and return a reminder."""
        now = datetime.utcnow()
        last = _hydration_log.get(user_id)
        if last is None:
            return HydrationReminder(
                user_id=user_id,
                level=HydrationLevel.OVERDUE,
                minutes_since_last=999,
                message="No hydration logged yet — drink water now!",
            )
        diff = now - last
        minutes = int(diff.total_seconds() / 60)
        if minutes < 20:
            level = HydrationLevel.OK
            msg = "Hydration on track."
        elif minutes < 40:
            level = HydrationLevel.DUE
            msg = f"It's been {minutes} minutes — time to hydrate."
        else:
            level = HydrationLevel.OVERDUE
            msg = f"OVERDUE: {minutes} minutes since last drink. Hydrate immediately!"
        return HydrationReminder(
            user_id=user_id,
            level=level,
            last_hydration=last,
            minutes_since_last=minutes,
            message=msg,
        )

    def log_hydration(self, user_id: str) -> HydrationReminder:
        """Log a hydration event and return updated status."""
        _hydration_log[user_id] = datetime.utcnow()
        return self.get_hydration_reminder(user_id)
