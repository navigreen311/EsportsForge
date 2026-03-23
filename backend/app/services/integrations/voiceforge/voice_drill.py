"""DrillBot Spoken Coaching — verbal rep counts, timing cues, and form feedback.

Provides real-time spoken coaching during training drills via VoiceForge TTS.
"""

from __future__ import annotations

import logging
from typing import Any

from app.schemas.voiceforge import VoiceConfig
from app.services.integrations.voiceforge.voice_client import VoiceForgeClient

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Coaching voice defaults
# ---------------------------------------------------------------------------

_COACHING_VOICE = VoiceConfig(
    voice_id="coach_energetic",
    speed=1.1,
    pitch=1.05,
    output_format="mp3",  # type: ignore[arg-type]
    language="en-US",
)


# ---------------------------------------------------------------------------
# Service
# ---------------------------------------------------------------------------


class VoiceDrillService:
    """Spoken coaching integration for DrillBot training sessions."""

    def __init__(
        self,
        client: VoiceForgeClient,
        voice_config: VoiceConfig | None = None,
    ) -> None:
        self._client = client
        self._voice_config = voice_config or _COACHING_VOICE

    async def speak_rep_count(self, count: int) -> dict[str, Any]:
        """Speak a rep count during a drill.

        Args:
            count: Current rep number.

        Returns:
            Dict with ``audio_url`` and ``text``.
        """
        if count <= 0:
            raise ValueError("Rep count must be positive")

        text = self._format_rep_text(count)
        tts = await self._client.text_to_speech(text, self._voice_config)

        logger.info("Spoke rep count: %d", count)
        return {"audio_url": tts.get("audio_url"), "text": text, "rep": count}

    async def speak_timing_cue(self, cue: str) -> dict[str, Any]:
        """Speak a timing cue during a drill.

        Args:
            cue: Timing cue text (e.g. "3... 2... 1... Go!").

        Returns:
            Dict with ``audio_url`` and ``text``.
        """
        if not cue or not cue.strip():
            raise ValueError("Timing cue cannot be empty")

        tts = await self._client.text_to_speech(cue, self._voice_config)

        logger.info("Spoke timing cue: %s", cue)
        return {"audio_url": tts.get("audio_url"), "text": cue}

    async def speak_form_feedback(self, feedback: str) -> dict[str, Any]:
        """Speak form correction feedback during a drill.

        Args:
            feedback: Form feedback text (e.g. "Slow down your crosshair placement").

        Returns:
            Dict with ``audio_url``, ``text``, and ``feedback_type``.
        """
        if not feedback or not feedback.strip():
            raise ValueError("Feedback cannot be empty")

        # Prefix with attention word for clarity
        spoken = f"Form check. {feedback}"
        tts = await self._client.text_to_speech(spoken, self._voice_config)

        logger.info("Spoke form feedback: %s", feedback)
        return {
            "audio_url": tts.get("audio_url"),
            "text": spoken,
            "original_feedback": feedback,
            "feedback_type": "form_correction",
        }

    # -- helpers ------------------------------------------------------------

    @staticmethod
    def _format_rep_text(count: int) -> str:
        """Format a rep count into coach-style spoken text."""
        if count % 10 == 0:
            return f"Rep {count}. Great milestone! Keep pushing."
        if count % 5 == 0:
            return f"Rep {count}. Halfway checkpoint. Stay sharp."
        return f"Rep {count}."
