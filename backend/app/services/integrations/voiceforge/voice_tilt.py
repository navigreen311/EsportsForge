"""TiltGuard Voice Check-Ins — voice-based mood detection and tone analysis.

Integrates VoiceForge tone analysis with TiltGuard to provide
real-time emotional state monitoring through voice.
"""

from __future__ import annotations

import logging
import uuid
from datetime import datetime
from typing import Any

from app.schemas.voiceforge import (
    VoiceCheckIn,
    VoiceTone,
    VoiceToneLevel,
)
from app.services.integrations.voiceforge.voice_client import VoiceForgeClient

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Tilt-risk mapping
# ---------------------------------------------------------------------------

_TONE_TILT_RISK: dict[VoiceToneLevel, float] = {
    VoiceToneLevel.CALM: 0.05,
    VoiceToneLevel.NEUTRAL: 0.15,
    VoiceToneLevel.EXCITED: 0.30,
    VoiceToneLevel.FRUSTRATED: 0.65,
    VoiceToneLevel.TILTED: 0.90,
    VoiceToneLevel.FATIGUED: 0.50,
}

_TILT_RECOMMENDATIONS: dict[str, str] = {
    "low": "You sound steady. Keep up the focus.",
    "moderate": "Energy is rising. Take a breath between plays.",
    "high": "Tilt risk detected. Consider a 2-minute reset break.",
    "critical": "High tilt detected. Recommend pausing and doing a breathing exercise.",
}


# ---------------------------------------------------------------------------
# Service
# ---------------------------------------------------------------------------


class VoiceTiltService:
    """Voice-based mood detection for TiltGuard integration."""

    def __init__(self, client: VoiceForgeClient) -> None:
        self._client = client

    async def voice_mood_checkin(
        self,
        user_id: str,
        audio_base64: str,
        session_id: str | None = None,
    ) -> VoiceCheckIn:
        """Perform a voice-based mood check-in.

        Transcribes and analyses tone to derive a mood label, tilt risk,
        and an actionable recommendation.

        Args:
            user_id: Player identifier.
            audio_base64: Base64-encoded voice sample.
            session_id: Optional game session ID for correlation.

        Returns:
            VoiceCheckIn with mood, tilt risk, and recommendation.
        """
        tone = await self.get_tone_analysis(audio_base64)
        tilt_risk = self._compute_tilt_risk(tone)
        mood_label = self._derive_mood_label(tone)
        recommendation = self._get_recommendation(tilt_risk)

        checkin = VoiceCheckIn(
            checkin_id=str(uuid.uuid4()),
            user_id=user_id,
            tone_analysis=tone,
            mood_label=mood_label,
            tilt_risk=tilt_risk,
            recommendation=recommendation,
            checked_at=datetime.utcnow(),
        )

        logger.info(
            "Voice check-in %s for user %s: mood=%s tilt_risk=%.2f",
            checkin.checkin_id,
            user_id,
            mood_label,
            tilt_risk,
        )
        return checkin

    async def get_tone_analysis(self, audio_base64: str) -> VoiceTone:
        """Analyse voice tone, pace, and energy via VoiceForge.

        Args:
            audio_base64: Base64-encoded audio.

        Returns:
            VoiceTone with tone, pace_wpm, energy_level, and stress indicators.
        """
        return await self._client.analyze_tone(audio_base64)

    # -- internal helpers ---------------------------------------------------

    @staticmethod
    def _compute_tilt_risk(tone: VoiceTone) -> float:
        """Compute tilt risk from tone analysis (0.0–1.0)."""
        base_risk = _TONE_TILT_RISK.get(tone.tone, 0.15)

        # High pace and energy push risk up
        pace_factor = min(tone.pace_wpm / 200.0, 1.0) * 0.15
        energy_factor = tone.energy_level * 0.10
        stress_factor = len(tone.stress_indicators) * 0.05

        return min(base_risk + pace_factor + energy_factor + stress_factor, 1.0)

    @staticmethod
    def _derive_mood_label(tone: VoiceTone) -> str:
        """Map tone to a human-readable mood label."""
        mapping = {
            VoiceToneLevel.CALM: "relaxed",
            VoiceToneLevel.NEUTRAL: "neutral",
            VoiceToneLevel.EXCITED: "hyped",
            VoiceToneLevel.FRUSTRATED: "frustrated",
            VoiceToneLevel.TILTED: "tilted",
            VoiceToneLevel.FATIGUED: "tired",
        }
        return mapping.get(tone.tone, "unknown")

    @staticmethod
    def _get_recommendation(tilt_risk: float) -> str:
        """Get recommendation text based on tilt risk score."""
        if tilt_risk >= 0.8:
            return _TILT_RECOMMENDATIONS["critical"]
        if tilt_risk >= 0.5:
            return _TILT_RECOMMENDATIONS["high"]
        if tilt_risk >= 0.3:
            return _TILT_RECOMMENDATIONS["moderate"]
        return _TILT_RECOMMENDATIONS["low"]
