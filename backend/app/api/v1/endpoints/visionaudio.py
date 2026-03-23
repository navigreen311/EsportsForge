"""API endpoints for VisionAudioForge integration — vision, film, formations, telemetry, clips."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, Query

from app.schemas.visionaudio import (
    AntiCheatResult,
    ClipData,
    ConnectionStatus,
    CoverageShell,
    ExportPackage,
    FormationCounter,
    FormationDetection,
    HesitationWindow,
    LootTierDetection,
    OverlayType,
    ReplayAnalysis,
    ScreenCaptureResult,
    SquadLocation,
    StickMovementAnalysis,
    TelemetryReport,
    VideoReplayResult,
    ZonePositionRead,
)
from app.services.integrations.visionaudio.vision_client import VisionClient
from app.services.integrations.visionaudio.film_visual import FilmVisualAI
from app.services.integrations.visionaudio.formation_recognition import FormationRecognition
from app.services.integrations.visionaudio.visual_telemetry import VisualTelemetry
from app.services.integrations.visionaudio.scene_reader import SceneReader
from app.services.integrations.visionaudio.clip_export import ClipExport

router = APIRouter(prefix="/vision", tags=["VisionAudioForge"])

_vision = VisionClient()
_film = FilmVisualAI()
_formations = FormationRecognition()
_telemetry = VisualTelemetry()
_scene = SceneReader()
_clips = ClipExport()


# ---------------------------------------------------------------------------
# Vision client
# ---------------------------------------------------------------------------

@router.post("/connect", response_model=ConnectionStatus, summary="Connect to vision service")
async def connect(api_key: str = Query(...), user_id: str = Query(...), title: str = Query("generic")) -> ConnectionStatus:
    """Establish connection to VisionAudioForge."""
    return await _vision.connect(api_key, user_id, title)


@router.post("/capture", response_model=ScreenCaptureResult, summary="Process screen capture")
async def process_capture(
    resolution: str = Query("1080p"), title: str = Query("generic"), analysis_type: str = Query("full"),
) -> ScreenCaptureResult:
    """Process a screen capture frame."""
    return await _vision.process_screen_capture(None, resolution, title, analysis_type)


@router.post("/replay", response_model=VideoReplayResult, summary="Process video replay")
async def process_replay(
    duration_sec: float = Query(30, ge=1, le=300), title: str = Query("generic"),
) -> VideoReplayResult:
    """Process a video replay."""
    return await _vision.process_video_replay(None, duration_sec, title)


@router.get("/anti-cheat", response_model=AntiCheatResult, summary="Check anti-cheat compliance")
async def check_anti_cheat(
    title: str = Query("generic"), capture_method: str = Query("game_dvr"),
) -> AntiCheatResult:
    """Verify capture method is anti-cheat compliant."""
    return await _vision.check_anti_cheat_compliance(title, capture_method)


# ---------------------------------------------------------------------------
# Film analysis
# ---------------------------------------------------------------------------

@router.post("/film/analyze", response_model=ReplayAnalysis, summary="Auto-analyze replay")
async def analyze_replay(events: list[dict], title: str = Query("madden26")) -> ReplayAnalysis:
    """Automatically analyze a replay from vision events."""
    return _film.auto_analyze_replay(events, title)


# ---------------------------------------------------------------------------
# Formation recognition
# ---------------------------------------------------------------------------

@router.post("/formation/identify", response_model=FormationDetection, summary="Identify formation")
async def identify_formation(player_positions: list[dict]) -> FormationDetection:
    """Identify offensive formation from player positions."""
    return _formations.identify_formation(player_positions)


@router.post("/formation/coverage", response_model=CoverageShell, summary="Identify coverage")
async def identify_coverage(defender_positions: list[dict]) -> CoverageShell:
    """Identify defensive coverage shell."""
    return _formations.identify_coverage_shell(defender_positions)


@router.get("/formation/counter/{formation}", response_model=FormationCounter, summary="Suggest counter")
async def suggest_counter(formation: str) -> FormationCounter:
    """Suggest counter for an identified formation."""
    return _formations.suggest_counter(formation)


# ---------------------------------------------------------------------------
# Telemetry
# ---------------------------------------------------------------------------

@router.post("/telemetry/stick", response_model=StickMovementAnalysis, summary="Analyze stick movement")
async def analyze_stick(input_samples: list[dict], context: str = Query("general")) -> StickMovementAnalysis:
    """Analyze stick movement patterns."""
    return _telemetry.analyze_stick_movement(input_samples, context)


@router.post("/telemetry/hesitation", response_model=list[HesitationWindow], summary="Detect hesitations")
async def detect_hesitations(input_samples: list[dict], game_events: list[dict] | None = None) -> list[HesitationWindow]:
    """Detect hesitation windows in input data."""
    return _telemetry.detect_hesitation_windows(input_samples, game_events)


@router.post("/telemetry/report", response_model=TelemetryReport, summary="Full telemetry report")
async def telemetry_report(
    input_samples: list[dict], game_events: list[dict] | None = None, context: str = Query("general"),
) -> TelemetryReport:
    """Generate comprehensive telemetry report."""
    return _telemetry.generate_report(input_samples, game_events, context)


# ---------------------------------------------------------------------------
# Scene reading
# ---------------------------------------------------------------------------

@router.post("/scene/zone", response_model=ZonePositionRead, summary="Read zone position")
async def read_zone(position_data: dict, title: str = Query("madden26")) -> ZonePositionRead:
    """Read player's zone position."""
    return _scene.read_zone_position(title, position_data)


@router.post("/scene/squad", response_model=SquadLocation, summary="Detect squad locations")
async def detect_squad(markers: list[dict], title: str = Query("warzone")) -> SquadLocation:
    """Detect squad member positions."""
    return _scene.detect_squad_locations(markers, title)


@router.get("/scene/loot", response_model=LootTierDetection, summary="Identify loot tier")
async def identify_loot(
    color: str = Query(...), title: str = Query("fortnite"), item: str | None = Query(None),
) -> LootTierDetection:
    """Identify loot tier from detected color."""
    return _scene.identify_loot_tier(color, title, item)


# ---------------------------------------------------------------------------
# Clip export
# ---------------------------------------------------------------------------

@router.post("/clips/create", response_model=ClipData, summary="Create clip")
async def create_clip(
    replay_id: str = Query(...), start_sec: float = Query(..., ge=0),
    end_sec: float = Query(..., ge=0), title: str = Query("Clip"),
) -> ClipData:
    """Create a clip from replay timestamps."""
    try:
        return _clips.create_clip(replay_id, start_sec, end_sec, title)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/clips/{clip_id}/overlay", response_model=ClipData, summary="Add overlay")
async def add_overlay(
    clip_id: str, overlay_type: OverlayType = Query(...), content: str = Query(...),
    timestamp_sec: float | None = Query(None),
) -> ClipData:
    """Add an AI overlay to a clip."""
    try:
        return _clips.add_overlay(clip_id, overlay_type, content, timestamp_sec)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/clips/{clip_id}/export", response_model=ExportPackage, summary="Export clip")
async def export_clip(
    clip_id: str, format: str = Query("mp4"), quality: str = Query("high"),
) -> ExportPackage:
    """Export a clip with overlays rendered."""
    try:
        return _clips.export_package(clip_id, format)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
