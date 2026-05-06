"""AnimaForge service exceptions."""

from __future__ import annotations


class AnimaForgeError(Exception):
    """Base class for AnimaForge errors."""


class AnimaForgeUnavailable(AnimaForgeError):
    """Raised when AnimaForge is unreachable or returns 5xx."""
