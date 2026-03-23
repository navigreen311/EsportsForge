"""ClipExport — clip creation, overlay rendering, and export packaging.

Creates clips from replay data, adds AI-generated overlays with tactical
annotations, and packages clips for sharing or coaching review.
"""

from __future__ import annotations

import logging
import uuid
from datetime import datetime, timezone
from typing import Any

from app.schemas.visionaudio import (
    ClipData,
    ExportPackage,
    OverlayConfig,
    OverlayType,
)

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Export configuration
# ---------------------------------------------------------------------------

_SUPPORTED_FORMATS = ["mp4", "webm", "gif"]
_MAX_CLIP_DURATION_SEC = 120
_DEFAULT_RESOLUTION = "1080p"

_OVERLAY_TEMPLATES: dict[OverlayType, dict[str, Any]] = {
    OverlayType.FORMATION_LABEL: {
        "position": "top_center",
        "font_size": 24,
        "bg_color": "rgba(0,0,0,0.6)",
        "text_color": "#FFFFFF",
        "duration_sec": 3.0,
    },
    OverlayType.COVERAGE_INDICATOR: {
        "position": "top_right",
        "font_size": 20,
        "bg_color": "rgba(0,0,128,0.6)",
        "text_color": "#FFD700",
        "duration_sec": 4.0,
    },
    OverlayType.PLAY_RESULT: {
        "position": "bottom_center",
        "font_size": 28,
        "bg_color": "rgba(0,0,0,0.7)",
        "text_color": "#00FF00",
        "duration_sec": 3.0,
    },
    OverlayType.ARROW: {
        "position": "custom",
        "color": "#FF4444",
        "width": 3,
        "animated": True,
        "duration_sec": 2.0,
    },
    OverlayType.HIGHLIGHT_BOX: {
        "position": "custom",
        "border_color": "#FFD700",
        "border_width": 2,
        "fill_color": "rgba(255,215,0,0.1)",
        "duration_sec": 2.5,
    },
    OverlayType.TELESTRATOR: {
        "position": "custom",
        "color": "#FF0000",
        "width": 4,
        "tool": "freehand",
        "duration_sec": 5.0,
    },
}


class ClipExport:
    """Clip creation and export engine.

    Creates clips from replay timestamps, renders AI overlays,
    and packages clips for export and sharing.
    """

    def __init__(self) -> None:
        self._clip_store: dict[str, ClipData] = {}

    # ------------------------------------------------------------------
    # Create clip
    # ------------------------------------------------------------------

    def create_clip(
        self,
        replay_id: str,
        start_sec: float,
        end_sec: float,
        title: str = "Clip",
        tags: list[str] | None = None,
    ) -> ClipData:
        """Create a clip from a replay with start/end timestamps.

        Validates duration, generates a clip ID, and stores metadata.
        """
        duration = end_sec - start_sec
        if duration <= 0:
            raise ValueError("End time must be after start time.")
        if duration > _MAX_CLIP_DURATION_SEC:
            raise ValueError(f"Clip duration exceeds maximum of {_MAX_CLIP_DURATION_SEC}s.")

        clip_id = f"clip_{uuid.uuid4().hex[:12]}"

        clip = ClipData(
            clip_id=clip_id,
            replay_id=replay_id,
            start_sec=start_sec,
            end_sec=end_sec,
            duration_sec=round(duration, 2),
            title=title,
            tags=tags or [],
            overlays=[],
            created_at=datetime.now(timezone.utc).isoformat(),
            resolution=_DEFAULT_RESOLUTION,
        )

        self._clip_store[clip_id] = clip
        logger.info("Clip created: id=%s duration=%.1fs", clip_id, duration)
        return clip

    # ------------------------------------------------------------------
    # Add overlay
    # ------------------------------------------------------------------

    def add_overlay(
        self,
        clip_id: str,
        overlay_type: OverlayType,
        content: str,
        timestamp_sec: float | None = None,
        position: dict[str, float] | None = None,
    ) -> ClipData:
        """Add an AI-generated overlay to a clip.

        Supports formation labels, coverage indicators, play results,
        arrows, highlight boxes, and telestrator drawings.
        """
        clip = self._clip_store.get(clip_id)
        if not clip:
            raise ValueError(f"Clip '{clip_id}' not found.")

        template = _OVERLAY_TEMPLATES.get(overlay_type, {})
        effective_ts = timestamp_sec if timestamp_sec is not None else clip.start_sec

        if effective_ts < clip.start_sec or effective_ts > clip.end_sec:
            raise ValueError("Overlay timestamp must be within the clip duration.")

        overlay = OverlayConfig(
            overlay_type=overlay_type,
            content=content,
            timestamp_sec=effective_ts,
            duration_sec=template.get("duration_sec", 3.0),
            position=position or {"x": 0.5, "y": 0.1},
            style={
                "font_size": template.get("font_size"),
                "bg_color": template.get("bg_color"),
                "text_color": template.get("text_color"),
                "color": template.get("color"),
                "border_color": template.get("border_color"),
            },
        )

        clip.overlays.append(overlay)
        logger.info(
            "Overlay added to clip %s: type=%s content='%s'",
            clip_id, overlay_type.value, content[:50],
        )
        return clip

    # ------------------------------------------------------------------
    # Export package
    # ------------------------------------------------------------------

    def export_package(
        self,
        clip_id: str,
        format: str = "mp4",
        include_overlays: bool = True,
        include_audio: bool = True,
        quality: str = "high",
    ) -> ExportPackage:
        """Package a clip for export with all overlays rendered.

        Returns export metadata including estimated file size and export URL.
        """
        clip = self._clip_store.get(clip_id)
        if not clip:
            raise ValueError(f"Clip '{clip_id}' not found.")

        if format not in _SUPPORTED_FORMATS:
            raise ValueError(f"Format '{format}' not supported. Use one of {_SUPPORTED_FORMATS}.")

        # Estimate file size
        quality_multipliers = {"low": 0.5, "medium": 1.0, "high": 2.0, "ultra": 4.0}
        base_mb_per_sec = {"mp4": 2.5, "webm": 2.0, "gif": 5.0}.get(format, 2.5)
        quality_mult = quality_multipliers.get(quality, 1.0)
        estimated_size_mb = clip.duration_sec * base_mb_per_sec * quality_mult

        if not include_audio:
            estimated_size_mb *= 0.85  # Audio is ~15% of file size

        overlay_count = len(clip.overlays) if include_overlays else 0
        processing_time_estimate_sec = clip.duration_sec * 0.5 + overlay_count * 0.3

        export_url = f"/exports/{clip_id}.{format}"

        return ExportPackage(
            clip_id=clip_id,
            format=format,
            quality=quality,
            resolution=clip.resolution,
            duration_sec=clip.duration_sec,
            include_overlays=include_overlays,
            overlay_count=overlay_count,
            include_audio=include_audio,
            estimated_size_mb=round(estimated_size_mb, 2),
            processing_time_sec=round(processing_time_estimate_sec, 1),
            export_url=export_url,
            status="ready",
        )

    # ------------------------------------------------------------------
    # Clip retrieval
    # ------------------------------------------------------------------

    def get_clip(self, clip_id: str) -> ClipData | None:
        """Retrieve a clip by ID."""
        return self._clip_store.get(clip_id)

    def list_clips(self, replay_id: str | None = None) -> list[ClipData]:
        """List all clips, optionally filtered by replay ID."""
        clips = list(self._clip_store.values())
        if replay_id:
            clips = [c for c in clips if c.replay_id == replay_id]
        return clips


# Module-level singleton
clip_export = ClipExport()
