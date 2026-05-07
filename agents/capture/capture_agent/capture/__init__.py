"""Capture-source dispatch. Source enum is open per ADR — adding a new
source is a new module + registry entry, no agent core changes."""

from .base import CaptureSource, Frame
from .test_video import TestVideoSource

__all__ = ["CaptureSource", "Frame", "TestVideoSource"]
