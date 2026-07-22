"""
route_validator — guard LLM-produced play-diagram geometry before it reaches a
Play. Mirrors the frontend `validateExplicitRoutes` (lib/gameplan/playDiagram.ts).

Coordinate space: 0–100 × 0–100, line of scrimmage at y=60, offense below,
routes run up (decreasing y). Bad or degenerate geometry is rejected wholesale
(returns None) so the frontend falls back to its concept template rather than
rendering nonsense.
"""

from __future__ import annotations

from typing import Any, Optional

from app.schemas.madden26.gameplan import RouteSpec

LOS = 60.0
# A receiver starting well above the LOS almost certainly means bad coordinates.
_START_Y_MIN = LOS - 8.0


def _clamp(n: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, n))


def _clean_point(p: Any) -> Optional[list[float]]:
    """Return a clamped [x, y] or None if the point is malformed."""
    if not isinstance(p, (list, tuple)) or len(p) < 2:
        return None
    x, y = p[0], p[1]
    if not isinstance(x, (int, float)) or not isinstance(y, (int, float)):
        return None
    if isinstance(x, bool) or isinstance(y, bool):  # bool is a subclass of int
        return None
    return [_clamp(float(x), 0.0, 100.0), _clamp(float(y), 0.0, 100.0)]


def validate_routes(raw: Any) -> Optional[list[RouteSpec]]:
    """
    Validate + clean a raw routes payload (list of {receiver, points}).

    Returns a list of clamped RouteSpec when every route is structurally sound,
    or None to trigger the frontend template fallback. The whole set is rejected
    if any single route is bad — partial geometry is worse than a clean template.
    """
    if not isinstance(raw, list) or len(raw) == 0:
        return None

    cleaned: list[RouteSpec] = []
    for route in raw:
        receiver: Any
        pts_raw: Any
        if isinstance(route, RouteSpec):
            receiver, pts_raw = route.receiver, route.points
        elif isinstance(route, dict):
            receiver, pts_raw = route.get("receiver"), route.get("points")
        else:
            return None

        if not isinstance(receiver, str) or not receiver.strip():
            return None
        if not isinstance(pts_raw, list) or len(pts_raw) < 2:
            return None

        points: list[list[float]] = []
        for p in pts_raw:
            cp = _clean_point(p)
            if cp is None:
                return None
            points.append(cp)

        # Receiver must start at/near the LOS or in the backfield (offense side).
        if points[0][1] < _START_Y_MIN:
            return None

        # Reject a zero-extent (nothing to animate) path.
        moved = any(
            abs(p[0] - points[0][0]) > 1.0 or abs(p[1] - points[0][1]) > 1.0
            for p in points
        )
        if not moved:
            return None

        cleaned.append(RouteSpec(receiver=receiver.strip(), points=points))

    return cleaned
