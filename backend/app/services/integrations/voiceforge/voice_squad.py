"""SquadOps Voice Layer — team communication and callouts via VoiceForge.

Provides voice-based team coordination including callouts, role
assignments, and strategy announcements for squad play.
"""

from __future__ import annotations

import logging
import uuid
from datetime import datetime
from typing import Any

from app.schemas.voiceforge import VoiceConfig
from app.services.integrations.voiceforge.voice_client import VoiceForgeClient

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Service
# ---------------------------------------------------------------------------


class VoiceSquadService:
    """Voice layer for SquadOps team communication."""

    def __init__(self, client: VoiceForgeClient) -> None:
        self._client = client

    async def broadcast_callout(
        self,
        squad_id: str,
        caller_id: str,
        audio_base64: str,
    ) -> dict[str, Any]:
        """Transcribe and broadcast a voice callout to the squad.

        Args:
            squad_id: Team/squad identifier.
            caller_id: Player making the callout.
            audio_base64: Base64-encoded voice callout.

        Returns:
            Dict with transcription and broadcast metadata.
        """
        stt = await self._client.speech_to_text(audio_base64)
        transcript = stt.get("transcript", "")

        callout = {
            "callout_id": str(uuid.uuid4()),
            "squad_id": squad_id,
            "caller_id": caller_id,
            "transcript": transcript,
            "callout_type": self._classify_callout(transcript),
            "timestamp": datetime.utcnow().isoformat(),
        }

        logger.info(
            "Callout %s from %s in squad %s: %s",
            callout["callout_id"],
            caller_id,
            squad_id,
            transcript,
        )
        return callout

    async def announce_strategy(
        self,
        squad_id: str,
        strategy_text: str,
        voice_config: VoiceConfig | None = None,
    ) -> dict[str, Any]:
        """Generate a spoken strategy announcement for the squad.

        Args:
            squad_id: Team/squad identifier.
            strategy_text: Strategy description to announce.
            voice_config: Optional TTS configuration.

        Returns:
            Dict with audio URL and announcement metadata.
        """
        spoken = f"Squad update. {strategy_text}"
        tts = await self._client.text_to_speech(spoken, voice_config)

        return {
            "announcement_id": str(uuid.uuid4()),
            "squad_id": squad_id,
            "text": spoken,
            "audio_url": tts.get("audio_url"),
            "timestamp": datetime.utcnow().isoformat(),
        }

    async def assign_role_voice(
        self,
        squad_id: str,
        player_id: str,
        role: str,
        voice_config: VoiceConfig | None = None,
    ) -> dict[str, Any]:
        """Announce a role assignment via voice.

        Args:
            squad_id: Team/squad identifier.
            player_id: Player receiving the role.
            role: Role name (e.g. "entry fragger", "support").
            voice_config: Optional TTS configuration.

        Returns:
            Dict with audio URL and assignment metadata.
        """
        text = f"Role assignment. Player {player_id}, you are {role}."
        tts = await self._client.text_to_speech(text, voice_config)

        return {
            "squad_id": squad_id,
            "player_id": player_id,
            "role": role,
            "audio_url": tts.get("audio_url"),
            "text": text,
        }

    # -- helpers ------------------------------------------------------------

    @staticmethod
    def _classify_callout(transcript: str) -> str:
        """Classify a callout based on keywords."""
        lower = transcript.lower()
        if any(w in lower for w in ["enemy", "contact", "spotted", "see"]):
            return "enemy_spotted"
        if any(w in lower for w in ["push", "go", "rush", "attack"]):
            return "push_call"
        if any(w in lower for w in ["rotate", "fall back", "retreat"]):
            return "rotation"
        if any(w in lower for w in ["help", "need", "assist"]):
            return "assistance"
        return "general"
