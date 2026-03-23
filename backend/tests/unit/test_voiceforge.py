"""Unit tests for VoiceForge integration — client, briefings, tilt, commands, drill, squad.

15+ tests covering all 8 VoiceForge feature modules.
"""

from __future__ import annotations

import pytest

from app.schemas.voiceforge import (
    AvailableCommand,
    BriefingType,
    VoiceBriefing,
    VoiceCheckIn,
    VoiceCheckInRequest,
    VoiceCommand,
    VoiceCommandType,
    VoiceConfig,
    VoiceOutputFormat,
    VoiceSearchQuery,
    VoiceSearchResult,
    VoiceTone,
    VoiceToneLevel,
)
from app.services.integrations.voiceforge.voice_client import VoiceForgeClient
from app.services.integrations.voiceforge.voice_briefing import VoiceBriefingService
from app.services.integrations.voiceforge.voice_tilt import VoiceTiltService
from app.services.integrations.voiceforge.voice_tourna import VoiceTournaService
from app.services.integrations.voiceforge.voice_drill import VoiceDrillService
from app.services.integrations.voiceforge.voice_squad import VoiceSquadService


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

@pytest.fixture
async def connected_client() -> VoiceForgeClient:
    """Return a VoiceForgeClient that has been connected."""
    client = VoiceForgeClient()
    await client.connect(api_key="test_key_123")
    return client


# ---------------------------------------------------------------------------
# 1. VoiceForgeClient tests
# ---------------------------------------------------------------------------


class TestVoiceForgeClient:
    """Tests for the core VoiceForge API client."""

    @pytest.mark.asyncio
    async def test_connect_success(self):
        client = VoiceForgeClient()
        result = await client.connect(api_key="vf_test_key")
        assert result["status"] == "connected"
        assert client.is_connected is True

    @pytest.mark.asyncio
    async def test_connect_empty_key_raises(self):
        client = VoiceForgeClient()
        with pytest.raises(ValueError, match="api_key is required"):
            await client.connect(api_key="")

    @pytest.mark.asyncio
    async def test_text_to_speech_without_connection_raises(self):
        client = VoiceForgeClient()
        with pytest.raises(ConnectionError, match="not connected"):
            await client.text_to_speech("Hello")

    @pytest.mark.asyncio
    async def test_text_to_speech_returns_audio(self, connected_client):
        result = await connected_client.text_to_speech("Test briefing text")
        assert "audio_url" in result
        assert "duration_seconds" in result
        assert result["duration_seconds"] > 0

    @pytest.mark.asyncio
    async def test_speech_to_text_empty_audio_raises(self, connected_client):
        with pytest.raises(ValueError, match="cannot be empty"):
            await connected_client.speech_to_text("")

    @pytest.mark.asyncio
    async def test_analyze_tone_returns_voice_tone(self, connected_client):
        tone = await connected_client.analyze_tone("base64audiodata")
        assert isinstance(tone, VoiceTone)
        assert tone.tone == VoiceToneLevel.NEUTRAL


# ---------------------------------------------------------------------------
# 2. Voice Briefing tests
# ---------------------------------------------------------------------------


class TestVoiceBriefingService:
    """Tests for between-series voice briefings."""

    @pytest.mark.asyncio
    async def test_generate_briefing(self, connected_client):
        service = VoiceBriefingService(connected_client)
        recommendation = {"summary": "Switch to zone defense. Opponent struggles against it."}
        briefing = await service.generate_briefing("user_1", recommendation)

        assert isinstance(briefing, VoiceBriefing)
        assert briefing.user_id == "user_1"
        assert briefing.briefing_type == BriefingType.BETWEEN_SERIES
        assert briefing.duration_seconds <= 15.0
        assert "zone defense" in briefing.text_content

    @pytest.mark.asyncio
    async def test_generate_clock_voice(self, connected_client):
        service = VoiceBriefingService(connected_client)
        game_state = {
            "time_remaining": "1:45",
            "suggested_play": "quick slant",
            "urgency": "critical",
        }
        briefing = await service.generate_clock_voice(game_state)

        assert briefing.briefing_type == BriefingType.CLOCK_DRILL
        assert "1:45" in briefing.text_content
        assert "quick slant" in briefing.text_content

    def test_trim_to_duration(self):
        long_text = " ".join(["word"] * 100)
        trimmed = VoiceBriefingService._trim_to_duration(long_text, 5.0)
        word_count = len(trimmed.split())
        # 5s * 2.5 wps = 12.5 -> 12 words + trailing period
        assert word_count <= 13


# ---------------------------------------------------------------------------
# 3. Voice Tilt (TiltGuard) tests
# ---------------------------------------------------------------------------


class TestVoiceTiltService:
    """Tests for TiltGuard voice check-ins."""

    @pytest.mark.asyncio
    async def test_voice_mood_checkin(self, connected_client):
        service = VoiceTiltService(connected_client)
        checkin = await service.voice_mood_checkin("user_2", "base64audio")

        assert isinstance(checkin, VoiceCheckIn)
        assert checkin.user_id == "user_2"
        assert 0.0 <= checkin.tilt_risk <= 1.0
        assert checkin.mood_label != ""

    @pytest.mark.asyncio
    async def test_get_tone_analysis(self, connected_client):
        service = VoiceTiltService(connected_client)
        tone = await service.get_tone_analysis("base64audio")
        assert isinstance(tone, VoiceTone)

    def test_compute_tilt_risk_calm(self):
        tone = VoiceTone(
            tone=VoiceToneLevel.CALM,
            pace_wpm=100.0,
            energy_level=0.3,
            stress_indicators=[],
            confidence=0.9,
        )
        risk = VoiceTiltService._compute_tilt_risk(tone)
        assert risk < 0.3  # calm = low risk

    def test_compute_tilt_risk_tilted(self):
        tone = VoiceTone(
            tone=VoiceToneLevel.TILTED,
            pace_wpm=180.0,
            energy_level=0.9,
            stress_indicators=["voice_crack", "rapid_speech"],
            confidence=0.85,
        )
        risk = VoiceTiltService._compute_tilt_risk(tone)
        assert risk >= 0.8  # tilted + high energy = high risk


# ---------------------------------------------------------------------------
# 4. Voice TournaOps Command tests
# ---------------------------------------------------------------------------


class TestVoiceTournaService:
    """Tests for TournaOps voice commands."""

    def test_get_available_commands(self):
        commands = VoiceTournaService.get_available_commands()
        assert len(commands) >= 6
        assert all(isinstance(c, AvailableCommand) for c in commands)

    def test_match_intent_next_opponent(self):
        intent, confidence = VoiceTournaService._match_intent("Who is my next opponent")
        assert intent == "next_opponent"
        assert confidence > 0.0

    def test_match_intent_kill_sheet(self):
        intent, _ = VoiceTournaService._match_intent("Show kill sheet stats")
        assert intent == "show_kill_sheet"

    def test_match_intent_unknown(self):
        intent, confidence = VoiceTournaService._match_intent("")
        assert intent == "unknown"
        assert confidence == 0.0


# ---------------------------------------------------------------------------
# 5. Voice Drill (DrillBot) tests
# ---------------------------------------------------------------------------


class TestVoiceDrillService:
    """Tests for DrillBot spoken coaching."""

    @pytest.mark.asyncio
    async def test_speak_rep_count(self, connected_client):
        service = VoiceDrillService(connected_client)
        result = await service.speak_rep_count(5)
        assert result["rep"] == 5
        assert "Rep 5" in result["text"]

    @pytest.mark.asyncio
    async def test_speak_rep_count_milestone(self, connected_client):
        service = VoiceDrillService(connected_client)
        result = await service.speak_rep_count(10)
        assert "milestone" in result["text"].lower()

    @pytest.mark.asyncio
    async def test_speak_rep_count_zero_raises(self, connected_client):
        service = VoiceDrillService(connected_client)
        with pytest.raises(ValueError, match="must be positive"):
            await service.speak_rep_count(0)

    @pytest.mark.asyncio
    async def test_speak_timing_cue(self, connected_client):
        service = VoiceDrillService(connected_client)
        result = await service.speak_timing_cue("3... 2... 1... Go!")
        assert result["text"] == "3... 2... 1... Go!"

    @pytest.mark.asyncio
    async def test_speak_form_feedback(self, connected_client):
        service = VoiceDrillService(connected_client)
        result = await service.speak_form_feedback("Slow down crosshair movement")
        assert "Form check" in result["text"]
        assert result["feedback_type"] == "form_correction"

    @pytest.mark.asyncio
    async def test_speak_timing_cue_empty_raises(self, connected_client):
        service = VoiceDrillService(connected_client)
        with pytest.raises(ValueError, match="cannot be empty"):
            await service.speak_timing_cue("   ")


# ---------------------------------------------------------------------------
# 6. Voice Squad tests
# ---------------------------------------------------------------------------


class TestVoiceSquadService:
    """Tests for SquadOps voice layer."""

    @pytest.mark.asyncio
    async def test_announce_strategy(self, connected_client):
        service = VoiceSquadService(connected_client)
        result = await service.announce_strategy("squad_1", "Push B site")
        assert result["squad_id"] == "squad_1"
        assert "Push B site" in result["text"]

    @pytest.mark.asyncio
    async def test_assign_role_voice(self, connected_client):
        service = VoiceSquadService(connected_client)
        result = await service.assign_role_voice("squad_1", "player_3", "entry fragger")
        assert result["role"] == "entry fragger"
        assert result["player_id"] == "player_3"

    def test_classify_callout_enemy(self):
        assert VoiceSquadService._classify_callout("Enemy spotted on B") == "enemy_spotted"

    def test_classify_callout_push(self):
        assert VoiceSquadService._classify_callout("Let's push A site") == "push_call"

    def test_classify_callout_general(self):
        assert VoiceSquadService._classify_callout("Hello team") == "general"


# ---------------------------------------------------------------------------
# 7. Schema validation tests
# ---------------------------------------------------------------------------


class TestVoiceForgeSchemas:
    """Tests for Pydantic schema validation."""

    def test_voice_config_defaults(self):
        config = VoiceConfig()
        assert config.voice_id == "default"
        assert config.speed == 1.0
        assert config.output_format == VoiceOutputFormat.MP3

    def test_voice_config_speed_bounds(self):
        with pytest.raises(Exception):
            VoiceConfig(speed=3.0)  # max is 2.0

    def test_voice_search_query_max_results_bounds(self):
        with pytest.raises(Exception):
            VoiceSearchQuery(audio_base64="data", max_results=100)  # max is 20

    def test_voice_tone_energy_bounds(self):
        with pytest.raises(Exception):
            VoiceTone(
                tone=VoiceToneLevel.CALM,
                pace_wpm=100.0,
                energy_level=2.0,  # max is 1.0
                confidence=0.9,
            )
