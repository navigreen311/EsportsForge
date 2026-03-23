"""VoiceForge API client — core connection and audio processing.

Handles authentication, TTS, STT, and tone analysis against the
Green Companies LLC VoiceForge platform.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any

from app.schemas.voiceforge import VoiceConfig, VoiceTone, VoiceToneLevel

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Defaults
# ---------------------------------------------------------------------------

VOICEFORGE_BASE_URL = "https://api.voiceforge.greencompanies.com/v1"
DEFAULT_TIMEOUT = 10.0


# ---------------------------------------------------------------------------
# Client
# ---------------------------------------------------------------------------


@dataclass
class VoiceForgeClient:
    """Low-level client for the VoiceForge REST API.

    Usage:
        client = VoiceForgeClient()
        await client.connect(api_key="vf_...")
        audio_url = await client.text_to_speech("Take a break.", config)
    """

    base_url: str = VOICEFORGE_BASE_URL
    timeout: float = DEFAULT_TIMEOUT
    _api_key: str | None = field(default=None, repr=False)
    _connected: bool = field(default=False, init=False)

    # -- connection ---------------------------------------------------------

    async def connect(self, api_key: str) -> dict[str, Any]:
        """Authenticate and establish a session with VoiceForge.

        Args:
            api_key: VoiceForge platform API key.

        Returns:
            Connection metadata including session token and capabilities.
        """
        if not api_key:
            raise ValueError("api_key is required to connect to VoiceForge")

        self._api_key = api_key
        self._connected = True
        logger.info("Connected to VoiceForge at %s", self.base_url)

        # Stub — real implementation would POST /auth/connect
        return {
            "status": "connected",
            "platform": "VoiceForge",
            "capabilities": [
                "text_to_speech",
                "speech_to_text",
                "tone_analysis",
                "voice_cloning",
            ],
        }

    # -- core API methods ---------------------------------------------------

    async def text_to_speech(
        self,
        text: str,
        voice_config: VoiceConfig | None = None,
    ) -> dict[str, Any]:
        """Convert text to speech using VoiceForge TTS engine.

        Args:
            text: The text content to synthesise.
            voice_config: Optional voice configuration (speed, pitch, format).

        Returns:
            Dict with ``audio_url`` and ``duration_seconds``.
        """
        self._require_connection()
        config = voice_config or VoiceConfig()

        logger.info(
            "TTS request: %d chars, voice=%s, format=%s",
            len(text),
            config.voice_id,
            config.output_format.value,
        )

        # Stub — real implementation would POST /tts
        estimated_duration = len(text.split()) * 0.4  # ~0.4s per word
        return {
            "audio_url": f"https://cdn.voiceforge.greencompanies.com/tts/{hash(text)}.{config.output_format.value}",
            "duration_seconds": round(estimated_duration, 2),
            "format": config.output_format.value,
            "text_length": len(text),
        }

    async def speech_to_text(self, audio_base64: str) -> dict[str, Any]:
        """Transcribe voice input to text using VoiceForge STT engine.

        Args:
            audio_base64: Base64-encoded audio data.

        Returns:
            Dict with ``transcript``, ``confidence``, and ``words``.
        """
        self._require_connection()

        if not audio_base64:
            raise ValueError("audio_base64 cannot be empty")

        logger.info("STT request: %d bytes", len(audio_base64))

        # Stub — real implementation would POST /stt
        return {
            "transcript": "",
            "confidence": 0.0,
            "words": [],
            "language": "en-US",
        }

    async def analyze_tone(self, audio_base64: str) -> VoiceTone:
        """Analyze voice tone, pace, and energy for TiltGuard integration.

        Args:
            audio_base64: Base64-encoded audio data.

        Returns:
            VoiceTone with tone classification, pace, and energy metrics.
        """
        self._require_connection()

        if not audio_base64:
            raise ValueError("audio_base64 cannot be empty")

        logger.info("Tone analysis request: %d bytes", len(audio_base64))

        # Stub — real implementation would POST /analyze/tone
        return VoiceTone(
            tone=VoiceToneLevel.NEUTRAL,
            pace_wpm=120.0,
            energy_level=0.5,
            stress_indicators=[],
            confidence=0.0,
        )

    # -- helpers ------------------------------------------------------------

    def _require_connection(self) -> None:
        """Raise if the client has not been connected."""
        if not self._connected:
            raise ConnectionError(
                "VoiceForgeClient is not connected. Call connect(api_key) first."
            )

    @property
    def is_connected(self) -> bool:
        """Whether the client has an active connection."""
        return self._connected
