"""TOML config loader.

Per docs/specs/01-capture-agent.md §6, config lives at
%LOCALAPPDATA%\\EsportsForge\\CaptureAgent\\config.toml on Windows.

Phase 0: also accepts CONFIG_PATH env var override for cross-platform
dev. Real Windows-only resolution lands in M1 final.
"""

from __future__ import annotations

import os
import sys
import tomllib
from dataclasses import dataclass
from pathlib import Path


@dataclass
class CaptureConfig:
    source: str  # "capture-card" | "pc-monitor" | "test-video" | "file"
    device_index: int = 0
    monitor_index: int = 0
    crop: tuple[int, int, int, int] = (0, 0, 1920, 1080)
    test_video: str = ""
    # File-mode ingestion (Phase 1a Day 0, source="file").
    file: str = ""
    playback_mode: str = "realtime"  # "realtime" (live cadence) | "max" (throughput)
    normalize_1080p: bool = True


@dataclass
class TransportConfig:
    target_fps: int = 12
    adaptive: bool = True
    adaptive_max_fps: int = 24
    jpeg_quality: int = 75
    batch_size: int = 4
    ring_buffer_seconds: int = 30


@dataclass
class AuthConfig:
    api_key: str
    user_id: str


@dataclass
class CoreConfig:
    endpoint: str
    fallback_endpoint: str = "ws://localhost:8100/ws/ingest"


@dataclass
class AgentConfig:
    auth: AuthConfig
    core: CoreConfig
    capture: CaptureConfig
    transport: TransportConfig
    log_level: str = "INFO"


def default_config_path() -> Path:
    """Resolve the default config path.

    Windows production: %LOCALAPPDATA%\\EsportsForge\\CaptureAgent\\config.toml.
    Other platforms (dev): ~/.config/esportsforge/capture-agent.toml.
    """
    if sys.platform == "win32":
        base = os.environ.get("LOCALAPPDATA", os.path.expanduser("~"))
        return Path(base) / "EsportsForge" / "CaptureAgent" / "config.toml"
    return Path.home() / ".config" / "esportsforge" / "capture-agent.toml"


def load_config(path: str | Path | None = None) -> AgentConfig:
    """Load config from TOML. CONFIG_PATH env var overrides if set."""
    if path is None:
        env_override = os.environ.get("ESF_CAPTURE_AGENT_CONFIG")
        path = env_override if env_override else default_config_path()

    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(
            f"Capture Agent config not found at {p}. "
            "Open EsportsForge → Settings → Game Settings → Capture Source to set it up."
        )

    with p.open("rb") as f:
        raw = tomllib.load(f)

    return AgentConfig(
        auth=AuthConfig(
            api_key=raw["auth"]["api_key"],
            user_id=raw["auth"]["user_id"],
        ),
        core=CoreConfig(
            endpoint=raw["core"]["endpoint"],
            fallback_endpoint=raw["core"].get(
                "fallback_endpoint", "ws://localhost:8100/ws/ingest"
            ),
        ),
        capture=CaptureConfig(
            source=raw["capture"]["source"],
            device_index=raw["capture"].get("device_index", 0),
            monitor_index=raw["capture"].get("monitor_index", 0),
            crop=tuple(raw["capture"].get("crop", [0, 0, 1920, 1080])),  # type: ignore[arg-type]
            test_video=raw["capture"].get("test_video", ""),
            file=raw["capture"].get("file", ""),
            playback_mode=raw["capture"].get("playback_mode", "realtime"),
            normalize_1080p=raw["capture"].get("normalize_1080p", True),
        ),
        transport=TransportConfig(
            target_fps=raw["transport"].get("target_fps", 12),
            adaptive=raw["transport"].get("adaptive", True),
            adaptive_max_fps=raw["transport"].get("adaptive_max_fps", 24),
            jpeg_quality=raw["transport"].get("jpeg_quality", 75),
            batch_size=raw["transport"].get("batch_size", 4),
            ring_buffer_seconds=raw["transport"].get("ring_buffer_seconds", 30),
        ),
        log_level=raw.get("diagnostics", {}).get("log_level", "INFO"),
    )
