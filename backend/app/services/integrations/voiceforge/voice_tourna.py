"""TournaOps Voice Commands — voice-driven tournament operations.

Enables players to use voice commands during tournaments for quick
access to opponent data, kill sheets, warmup routines, and more.
"""

from __future__ import annotations

import logging
import uuid
from datetime import datetime
from typing import Any

from app.schemas.voiceforge import (
    AvailableCommand,
    VoiceCommand,
    VoiceCommandType,
)
from app.services.integrations.voiceforge.voice_client import VoiceForgeClient

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Command registry
# ---------------------------------------------------------------------------

_COMMANDS: list[AvailableCommand] = [
    AvailableCommand(
        intent="next_opponent",
        phrases=["Next opponent", "Who am I playing next", "Show next match"],
        command_type=VoiceCommandType.TOURNA_OPS,
        description="Display information about the next opponent in the bracket.",
    ),
    AvailableCommand(
        intent="show_kill_sheet",
        phrases=["Show kill sheet", "Pull up kills", "Kill stats"],
        command_type=VoiceCommandType.TOURNA_OPS,
        description="Display the current kill/death statistics sheet.",
    ),
    AvailableCommand(
        intent="start_warmup",
        phrases=["Start warmup", "Begin warmup", "Warmup routine"],
        command_type=VoiceCommandType.TOURNA_OPS,
        description="Launch the pre-match warmup routine.",
    ),
    AvailableCommand(
        intent="bracket_status",
        phrases=["Bracket status", "Where am I in bracket", "Tournament standing"],
        command_type=VoiceCommandType.TOURNA_OPS,
        description="Show current position in the tournament bracket.",
    ),
    AvailableCommand(
        intent="check_schedule",
        phrases=["Check schedule", "When is my next match", "Match time"],
        command_type=VoiceCommandType.TOURNA_OPS,
        description="Check the schedule for upcoming matches.",
    ),
    AvailableCommand(
        intent="report_result",
        phrases=["Report result", "Log score", "Match result"],
        command_type=VoiceCommandType.TOURNA_OPS,
        description="Report a match result to tournament organizers.",
    ),
]

# Intent matching keywords (lowercased)
_INTENT_KEYWORDS: dict[str, list[str]] = {
    "next_opponent": ["next", "opponent", "playing"],
    "show_kill_sheet": ["kill", "kills", "sheet", "stats"],
    "start_warmup": ["warmup", "warm"],
    "bracket_status": ["bracket", "standing", "position"],
    "check_schedule": ["schedule", "when", "time"],
    "report_result": ["report", "result", "score", "log"],
}


# ---------------------------------------------------------------------------
# Service
# ---------------------------------------------------------------------------


class VoiceTournaService:
    """Voice command processing for TournaOps tournament operations."""

    def __init__(self, client: VoiceForgeClient) -> None:
        self._client = client

    async def process_command(self, audio_base64: str) -> VoiceCommand:
        """Transcribe and parse a voice command.

        Args:
            audio_base64: Base64-encoded audio of the spoken command.

        Returns:
            VoiceCommand with detected intent and parameters.
        """
        stt_result = await self._client.speech_to_text(audio_base64)
        transcript = stt_result.get("transcript", "")
        stt_confidence = stt_result.get("confidence", 0.0)

        intent, intent_confidence = self._match_intent(transcript)

        command = VoiceCommand(
            command_id=str(uuid.uuid4()),
            raw_transcript=transcript,
            intent=intent,
            command_type=VoiceCommandType.TOURNA_OPS,
            confidence=min(stt_confidence * intent_confidence, 1.0),
            parameters=self._extract_parameters(intent, transcript),
            processed_at=datetime.utcnow(),
        )

        logger.info(
            "Processed command %s: intent=%s confidence=%.2f",
            command.command_id,
            intent,
            command.confidence,
        )
        return command

    @staticmethod
    def get_available_commands() -> list[AvailableCommand]:
        """Return the list of all supported TournaOps voice commands."""
        return list(_COMMANDS)

    # -- internal helpers ---------------------------------------------------

    @staticmethod
    def _match_intent(transcript: str) -> tuple[str, float]:
        """Match a transcript to a known intent.

        Returns:
            Tuple of (intent_name, confidence).
        """
        lower = transcript.lower()
        best_intent = "unknown"
        best_score = 0.0

        for intent, keywords in _INTENT_KEYWORDS.items():
            matches = sum(1 for kw in keywords if kw in lower)
            if matches > 0:
                score = matches / len(keywords)
                if score > best_score:
                    best_score = score
                    best_intent = intent

        return best_intent, best_score

    @staticmethod
    def _extract_parameters(intent: str, transcript: str) -> dict[str, Any]:
        """Extract parameters from the transcript based on intent."""
        params: dict[str, Any] = {"raw": transcript}

        if intent == "report_result":
            # Try to find numbers in the transcript for score reporting
            words = transcript.split()
            numbers = [w for w in words if w.isdigit()]
            if numbers:
                params["scores"] = numbers

        return params
