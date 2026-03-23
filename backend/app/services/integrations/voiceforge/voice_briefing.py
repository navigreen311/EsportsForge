"""Between-Series Voice Briefing — spoken summaries from AdaptAI and ClockAI.

Generates short (≤15 s) spoken briefings between game series and
ClockAI 2-minute drill voice delivery.
"""

from __future__ import annotations

import logging
import uuid
from datetime import datetime
from typing import Any

from app.schemas.voiceforge import (
    BriefingType,
    VoiceBriefing,
    VoiceConfig,
)
from app.services.integrations.voiceforge.voice_client import VoiceForgeClient

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

MAX_BRIEFING_SECONDS = 15.0
CLOCK_DRILL_SECONDS = 10.0
WORDS_PER_SECOND = 2.5  # average spoken pace


# ---------------------------------------------------------------------------
# Service
# ---------------------------------------------------------------------------


class VoiceBriefingService:
    """Generates spoken briefings from AI recommendation engines."""

    def __init__(self, client: VoiceForgeClient) -> None:
        self._client = client

    async def generate_briefing(
        self,
        user_id: str,
        adapt_recommendation: dict[str, Any],
        voice_config: VoiceConfig | None = None,
    ) -> VoiceBriefing:
        """Generate a ≤15-second spoken briefing from an AdaptAI recommendation.

        Args:
            user_id: Player identifier.
            adapt_recommendation: Recommendation payload from AdaptAI engine.
            voice_config: Optional TTS configuration.

        Returns:
            VoiceBriefing with text and audio URL.
        """
        text = self._build_briefing_text(adapt_recommendation)
        text = self._trim_to_duration(text, MAX_BRIEFING_SECONDS)

        tts_result = await self._client.text_to_speech(text, voice_config)

        briefing = VoiceBriefing(
            briefing_id=str(uuid.uuid4()),
            user_id=user_id,
            briefing_type=BriefingType.BETWEEN_SERIES,
            text_content=text,
            audio_url=tts_result.get("audio_url"),
            duration_seconds=min(tts_result.get("duration_seconds", 0), MAX_BRIEFING_SECONDS),
            generated_at=datetime.utcnow(),
        )

        logger.info(
            "Generated briefing %s for user %s (%.1fs)",
            briefing.briefing_id,
            user_id,
            briefing.duration_seconds,
        )
        return briefing

    async def generate_clock_voice(
        self,
        game_state: dict[str, Any],
        voice_config: VoiceConfig | None = None,
    ) -> VoiceBriefing:
        """Generate a ClockAI 2-minute drill voice delivery.

        Args:
            game_state: Current clock/game state from ClockAI.
            voice_config: Optional TTS configuration.

        Returns:
            VoiceBriefing with clock drill audio.
        """
        time_remaining = game_state.get("time_remaining", "2:00")
        play_call = game_state.get("suggested_play", "quick pass")
        urgency = game_state.get("urgency", "high")

        text = (
            f"Clock at {time_remaining}. "
            f"Urgency is {urgency}. "
            f"Recommended play: {play_call}. "
            "Execute now."
        )
        text = self._trim_to_duration(text, CLOCK_DRILL_SECONDS)

        tts_result = await self._client.text_to_speech(text, voice_config)

        return VoiceBriefing(
            briefing_id=str(uuid.uuid4()),
            user_id="clock_ai",
            briefing_type=BriefingType.CLOCK_DRILL,
            text_content=text,
            audio_url=tts_result.get("audio_url"),
            duration_seconds=min(tts_result.get("duration_seconds", 0), CLOCK_DRILL_SECONDS),
            generated_at=datetime.utcnow(),
        )

    # -- helpers ------------------------------------------------------------

    @staticmethod
    def _build_briefing_text(recommendation: dict[str, Any]) -> str:
        """Build human-friendly briefing text from an AdaptAI recommendation."""
        summary = recommendation.get("summary", "No new recommendations.")
        adjustments = recommendation.get("adjustments", [])

        parts = [summary]
        for adj in adjustments[:2]:  # max 2 adjustments to keep it short
            parts.append(adj if isinstance(adj, str) else str(adj))

        return " ".join(parts)

    @staticmethod
    def _trim_to_duration(text: str, max_seconds: float) -> str:
        """Trim text to approximately fit within *max_seconds* of speech."""
        max_words = int(max_seconds * WORDS_PER_SECOND)
        words = text.split()
        if len(words) <= max_words:
            return text
        return " ".join(words[:max_words]) + "."
