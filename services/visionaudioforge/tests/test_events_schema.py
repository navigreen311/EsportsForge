"""Contract pin: COVERAGE_LOCKED carries its coverage on `defensive_coverage`.

ADR 0017 — pins the v0.3 COVERAGE_LOCKED payload contract AHEAD of the producer.
Nothing emits coverage (the Madden `detect_coverage` is a v0.3 stub; no model
exists). So this asserts the CONTRACT only — the field accepts a coverage string
and None, defaults None (back-compat with today's FORMATION_LOCKED payloads),
and stays distinct from the v0.2 `defensive_formation` front. There is NO
live/model verification: the coverage value is a domain-grounded vocabulary
(ADR 0017), not a validated model output.
"""

from __future__ import annotations

import pytest
from pydantic import ValidationError

# conftest.py puts the service root on sys.path.
from app.schemas.events import Madden26Payload

BASE = dict(score_home=0, score_away=0, quarter=1, clock="0:00")


def test_defensive_coverage_accepts_a_coverage_string():
    p = Madden26Payload(**BASE, defensive_coverage="Cover 3")
    assert p.defensive_coverage == "Cover 3"


def test_defensive_coverage_accepts_none_explicitly():
    p = Madden26Payload(**BASE, defensive_coverage=None)
    assert p.defensive_coverage is None


def test_defensive_coverage_defaults_none_and_is_distinct_from_front():
    """Omitted → None (back-compat), and separate from the v0.2 front field."""
    p = Madden26Payload(**BASE)
    assert p.defensive_coverage is None       # v0.3 coverage — inert until v0.3
    assert p.defensive_formation is None       # v0.2 pre-snap front — distinct signal


def test_extra_forbid_still_rejects_undeclared_keys():
    """`extra="forbid"` holds: a coverage value can ONLY ride on the declared
    field. An ad-hoc / typo'd key is rejected — so the pin is load-bearing."""
    with pytest.raises(ValidationError):
        Madden26Payload(**BASE, defensive_covrage="Cover 3")  # typo'd/undeclared
