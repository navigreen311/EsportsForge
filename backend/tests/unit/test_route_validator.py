"""Tests for route_validator — the guard on play-diagram geometry."""

from __future__ import annotations

from app.schemas.madden26.gameplan import RouteSpec
from app.services.agents.madden26.route_validator import validate_routes
from app.services.agents.madden26.template_routes import TEMPLATE_ROUTES, routes_for


def _slant(receiver: str = "X") -> dict:
    return {"receiver": receiver, "points": [[12, 60], [12, 55], [26, 50]]}


# ---------------------------------------------------------------------------
# Happy path
# ---------------------------------------------------------------------------

def test_valid_routes_pass_through():
    result = validate_routes([_slant("X"), _slant("Z")])
    assert result is not None
    assert len(result) == 2
    assert all(isinstance(r, RouteSpec) for r in result)
    assert result[0].receiver == "X"
    assert result[0].points[0] == [12.0, 60.0]


def test_accepts_routespec_objects_not_just_dicts():
    spec = RouteSpec(receiver="TE", points=[[64, 60], [64, 40]])
    result = validate_routes([spec])
    assert result is not None and result[0].receiver == "TE"


def test_out_of_bounds_coords_are_clamped():
    result = validate_routes([{"receiver": "Z", "points": [[130, 60], [-20, 30]]}])
    assert result is not None
    assert result[0].points[0] == [100.0, 60.0]
    assert result[0].points[1] == [0.0, 30.0]


# ---------------------------------------------------------------------------
# Rejections -> None (frontend falls back to template)
# ---------------------------------------------------------------------------

def test_empty_or_wrong_type_rejected():
    assert validate_routes([]) is None
    assert validate_routes(None) is None
    assert validate_routes("nope") is None


def test_route_with_single_point_rejected():
    assert validate_routes([{"receiver": "X", "points": [[12, 60]]}]) is None


def test_missing_receiver_rejected():
    assert validate_routes([{"receiver": "", "points": [[12, 60], [12, 40]]}]) is None
    assert validate_routes([{"points": [[12, 60], [12, 40]]}]) is None


def test_non_numeric_point_rejected():
    assert validate_routes([{"receiver": "X", "points": [[12, 60], ["a", 40]]}]) is None
    assert validate_routes([{"receiver": "X", "points": [[12, 60], [40]]}]) is None


def test_bool_coords_rejected():
    # bool is a subclass of int — must not be accepted as a coordinate.
    assert validate_routes([{"receiver": "X", "points": [[True, 60], [12, 40]]}]) is None


def test_start_downfield_rejected():
    # Receiver starting well above the LOS (y<52) means bad geometry.
    assert validate_routes([{"receiver": "X", "points": [[12, 30], [12, 10]]}]) is None


def test_degenerate_zero_extent_rejected():
    assert validate_routes([{"receiver": "X", "points": [[12, 60], [12.4, 60.3]]}]) is None


def test_one_bad_route_rejects_the_whole_set():
    good = _slant("X")
    bad = {"receiver": "Z", "points": [[12, 60]]}  # single point
    assert validate_routes([good, bad]) is None


# ---------------------------------------------------------------------------
# Template routes are themselves valid geometry
# ---------------------------------------------------------------------------

def test_all_template_routes_are_valid():
    for name, specs in TEMPLATE_ROUTES.items():
        assert validate_routes(specs) is not None, f"{name} has invalid template routes"


def test_routes_for_returns_copies():
    a = routes_for("Mesh Cross")
    b = routes_for("Mesh Cross")
    assert a is not None and b is not None
    a[0].points[0][0] = 999
    assert b[0].points[0][0] != 999  # mutation must not leak into the library


def test_routes_for_unknown_play_is_none():
    assert routes_for("Nonexistent Play") is None
