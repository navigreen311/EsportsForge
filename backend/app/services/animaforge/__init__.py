"""AnimaForge integration service package.

Re-exports the public surface that other modules (Agents #2, #4, #6, #8, #9)
import:

    from app.services.animaforge import AnimaForgeService, AnimaForgeUnavailable
"""

from app.services.animaforge.client import AnimaForgeService
from app.services.animaforge.exceptions import (
    AnimaForgeError,
    AnimaForgeUnavailable,
)

__all__ = [
    "AnimaForgeService",
    "AnimaForgeError",
    "AnimaForgeUnavailable",
]
