"""VoiceForge endpoints — voice briefings, tilt check-ins, commands, coaching, squad comms.

Phase 2 integration layer connecting EsportsForge features to
the Green Companies LLC VoiceForge platform.
"""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Body, HTTPException, Query

from app.schemas.voiceforge import (
    AvailableCommand,
    VoiceBriefing,
    VoiceCheckIn,
    VoiceCheckInRequest,
    VoiceCommand,
    VoiceCommandRequest,
    VoiceConfig,
    VoiceSearchQuery,
    VoiceSearchResult,
)

router = APIRouter(prefix="/voiceforge", tags=["VoiceForge"])


# ---------------------------------------------------------------------------
# Briefing endpoints (AdaptAI / ClockAI)
# ---------------------------------------------------------------------------


@router.post("/{user_id}/briefing", response_model=VoiceBriefing)
async def generate_briefing(
    user_id: str,
    adapt_recommendation: dict[str, Any] = Body(
        default={}, description="AdaptAI recommendation payload"
    ),
):
    """Generate a between-series voice briefing from AdaptAI recommendation."""
    return {
        "briefing_id": "stub",
        "user_id": user_id,
        "briefing_type": "between_series",
        "text_content": "No recommendations available.",
        "audio_url": None,
        "duration_seconds": 0,
        "status": "stub - VoiceForge integration pending",
    }


@router.post("/clock/voice", response_model=VoiceBriefing)
async def generate_clock_voice(
    game_state: dict[str, Any] = Body(
        ..., description="Current game/clock state from ClockAI"
    ),
):
    """Generate a ClockAI 2-minute drill voice delivery."""
    return {
        "briefing_id": "stub",
        "user_id": "clock_ai",
        "briefing_type": "clock_drill",
        "text_content": "Clock drill voice pending.",
        "audio_url": None,
        "duration_seconds": 0,
        "status": "stub - VoiceForge integration pending",
    }


# ---------------------------------------------------------------------------
# TiltGuard voice check-in endpoints
# ---------------------------------------------------------------------------


@router.post("/{user_id}/checkin", response_model=VoiceCheckIn)
async def voice_mood_checkin(
    user_id: str,
    request: VoiceCheckInRequest = Body(...),
):
    """Perform a voice-based mood check-in for TiltGuard."""
    return {
        "checkin_id": "stub",
        "user_id": user_id,
        "tone_analysis": {
            "tone": "neutral",
            "pace_wpm": 0.0,
            "energy_level": 0.0,
            "stress_indicators": [],
            "confidence": 0.0,
        },
        "mood_label": "unknown",
        "tilt_risk": 0.0,
        "recommendation": None,
        "status": "stub - VoiceForge integration pending",
    }


@router.post("/tone/analyze")
async def analyze_tone(
    audio_base64: str = Body(..., embed=True, description="Base64-encoded audio"),
):
    """Analyze voice tone, pace, and energy."""
    return {
        "tone": "neutral",
        "pace_wpm": 0.0,
        "energy_level": 0.0,
        "stress_indicators": [],
        "confidence": 0.0,
        "status": "stub - VoiceForge integration pending",
    }


# ---------------------------------------------------------------------------
# TournaOps voice command endpoints
# ---------------------------------------------------------------------------


@router.post("/commands/process", response_model=VoiceCommand)
async def process_voice_command(
    request: VoiceCommandRequest = Body(...),
):
    """Process a voice command for TournaOps."""
    return {
        "command_id": "stub",
        "raw_transcript": "",
        "intent": "unknown",
        "command_type": "tourna_ops",
        "confidence": 0.0,
        "parameters": {},
        "status": "stub - VoiceForge integration pending",
    }


@router.get("/commands/available", response_model=list[AvailableCommand])
async def list_available_commands():
    """List all available voice commands for TournaOps."""
    from app.services.integrations.voiceforge.voice_tourna import VoiceTournaService

    return VoiceTournaService.get_available_commands()


# ---------------------------------------------------------------------------
# DrillBot spoken coaching endpoints
# ---------------------------------------------------------------------------


@router.post("/drill/rep-count")
async def speak_rep_count(
    count: int = Body(..., embed=True, ge=1, description="Current rep number"),
):
    """Speak a rep count during a DrillBot session."""
    return {
        "text": f"Rep {count}.",
        "audio_url": None,
        "rep": count,
        "status": "stub - VoiceForge integration pending",
    }


@router.post("/drill/timing-cue")
async def speak_timing_cue(
    cue: str = Body(..., embed=True, description="Timing cue text"),
):
    """Speak a timing cue during a drill."""
    if not cue.strip():
        raise HTTPException(status_code=400, detail="Timing cue cannot be empty")
    return {
        "text": cue,
        "audio_url": None,
        "status": "stub - VoiceForge integration pending",
    }


@router.post("/drill/form-feedback")
async def speak_form_feedback(
    feedback: str = Body(..., embed=True, description="Form correction feedback"),
):
    """Speak form correction feedback during a drill."""
    if not feedback.strip():
        raise HTTPException(status_code=400, detail="Feedback cannot be empty")
    return {
        "text": f"Form check. {feedback}",
        "audio_url": None,
        "feedback_type": "form_correction",
        "status": "stub - VoiceForge integration pending",
    }


# ---------------------------------------------------------------------------
# SquadOps voice layer endpoints
# ---------------------------------------------------------------------------


@router.post("/squad/{squad_id}/callout")
async def broadcast_callout(
    squad_id: str,
    caller_id: str = Body(..., embed=True),
    audio_base64: str = Body(..., embed=True),
):
    """Broadcast a voice callout to the squad."""
    return {
        "callout_id": "stub",
        "squad_id": squad_id,
        "caller_id": caller_id,
        "transcript": "",
        "callout_type": "general",
        "status": "stub - VoiceForge integration pending",
    }


@router.post("/squad/{squad_id}/strategy")
async def announce_strategy(
    squad_id: str,
    strategy_text: str = Body(..., embed=True, description="Strategy to announce"),
):
    """Announce a strategy to the squad via voice."""
    return {
        "squad_id": squad_id,
        "text": f"Squad update. {strategy_text}",
        "audio_url": None,
        "status": "stub - VoiceForge integration pending",
    }


# ---------------------------------------------------------------------------
# Voice search
# ---------------------------------------------------------------------------


@router.post("/search", response_model=VoiceSearchResult)
async def voice_search(
    query: VoiceSearchQuery = Body(...),
):
    """Perform a voice-initiated search across EsportsForge data."""
    return {
        "query_text": "",
        "results": [],
        "result_count": 0,
        "spoken_summary": None,
        "audio_url": None,
        "status": "stub - VoiceForge integration pending",
    }
