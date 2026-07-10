"""Capture-source dispatch. Source enum is open per ADR — adding a new
source is a new module + registry entry, no agent core changes."""

from .base import CaptureSource, Frame
from .file_playback import FilePlaybackSource
from .hdmi_capture import HdmiCaptureSource
from .test_video import TestVideoSource

__all__ = [
    "CaptureSource",
    "Frame",
    "FilePlaybackSource",
    "HdmiCaptureSource",
    "TestVideoSource",
]
