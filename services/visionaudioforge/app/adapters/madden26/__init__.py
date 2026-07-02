"""Madden 26 adapter — first reference adapter.

v0.1 (this file): offensive formation top-8 only. OCR + CNN inference
stubbed; the architecture (state machine, event assembly, integrity
policy declaration) is real.

v0.2 (Phase 1.1): adds pre-snap defensive front. Budget bumps to 100 ms
(ADR 0006).

v0.3 (Phase 1.1): adds post-snap coverage detection. Budget bumps to
120 ms. Phase 1c cutover is gated on v0.3 shipping (ADR 0010).
"""

from .adapter import Madden26Adapter

__all__ = ["Madden26Adapter"]
