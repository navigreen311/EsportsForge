"""WebSocket wire-protocol shapes.

Agent ↔ core protocol. Capture-agent spec §3 defines the shapes;
this module is the canonical Pydantic representation.
"""

from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict

from .enums import IntegrityMode, TitleEnum


# ---------------------------------------------------------------------------
# Server → Agent
# ---------------------------------------------------------------------------


class SessionOpenMessage(BaseModel):
    """Sent by core after WS handshake; orients the agent on the session."""

    model_config = ConfigDict(extra="forbid")

    type: Literal["session_open"] = "session_open"
    session_id: str
    integrity_mode: IntegrityMode
    active_title: TitleEnum | None = None
    capture_allowed: bool
    frame_format: Literal["jpeg"] = "jpeg"
    max_fps: int = 24


class CapturePauseMessage(BaseModel):
    model_config = ConfigDict(extra="forbid")
    type: Literal["capture_pause"] = "capture_pause"
    reason: str


class CaptureResumeMessage(BaseModel):
    model_config = ConfigDict(extra="forbid")
    type: Literal["capture_resume"] = "capture_resume"


class SetTargetFpsMessage(BaseModel):
    model_config = ConfigDict(extra="forbid")
    type: Literal["set_target_fps"] = "set_target_fps"
    fps: int


class SessionCloseMessage(BaseModel):
    model_config = ConfigDict(extra="forbid")
    type: Literal["session_close"] = "session_close"
    reason: str


# ---------------------------------------------------------------------------
# Agent → Server
# ---------------------------------------------------------------------------


class FrameRef(BaseModel):
    """One frame inside a batch."""

    model_config = ConfigDict(extra="forbid")

    frame_id: int
    captured_at: datetime
    width: int
    height: int
    format: Literal["jpeg"] = "jpeg"
    data_b64: str  # base64-encoded JPEG bytes


class FrameBatchMessage(BaseModel):
    model_config = ConfigDict(extra="forbid")
    type: Literal["frame_batch"] = "frame_batch"
    session_id: str
    batch_seq: int
    frames: list[FrameRef]


class HeartbeatStats(BaseModel):
    model_config = ConfigDict(extra="forbid")
    frames_captured: int
    frames_sent: int
    frames_dropped: int
    current_fps: float
    capture_device_status: Literal["ok", "missing", "degraded"] = "ok"
    uptime_sec: int


class HeartbeatMessage(BaseModel):
    model_config = ConfigDict(extra="forbid")
    type: Literal["heartbeat"] = "heartbeat"
    session_id: str
    stats: HeartbeatStats


class AgentCloseMessage(BaseModel):
    model_config = ConfigDict(extra="forbid")
    type: Literal["session_close"] = "session_close"
    reason: str = "agent_quit"
