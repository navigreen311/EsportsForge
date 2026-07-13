"""Defensive play-call parser — the OCR-of-play-call pivot (coverage-ocr-playcall-pivot.md).

Pure-parser tests (no EasyOCR / no CI heavy deps). The inputs are the ACTUAL high-confidence
OCR strings read off a captured Rams defensive play-call screen (Cover 1 Hole / OLB Fire Man /
Tampa 2, front "4-3 Over", MAN/BLITZ/ZONE badges), plus canonical-mapping coverage of the
ADR-0017 vocabulary.
"""

from __future__ import annotations

from app.adapters.madden26.defensive_playcall import (
    canonical_coverage,
    canonical_front,
    man_zone,
    parse_card,
)


def test_parses_the_captured_cards():
    # exactly what EasyOCR read off the captured defensive play-call screen
    c1 = parse_card("Cover 1 Hole", "4-3 Over", "MAN")
    assert c1.coverage == "Cover 1" and c1.front == "4-3" and c1.man_zone == "man"

    c2 = parse_card("Tampa 2", "4-3 Over", "ZONE")
    assert c2.coverage == "Cover 2" and c2.front == "4-3" and c2.man_zone == "zone"

    # a man-pressure blitz card: not a coverage, but man/zone is still "man"
    c3 = parse_card("OLB Fire Man", "4-3 Over", "BLITZ")
    assert c3.coverage is None and c3.man_zone == "man"


def test_canonical_coverage_vocabulary():
    assert canonical_coverage("Cover 0") == "Cover 0"
    assert canonical_coverage("Cover 1 Robber") == "Cover 1-Robber"
    assert canonical_coverage("Cover 3 Sky") == "Cover 3"
    assert canonical_coverage("Cover 2 Man") == "Cover 2-Man"
    assert canonical_coverage("Tampa 2") == "Cover 2"
    assert canonical_coverage("Quarters") == "Cover 4 (Quarters)"
    assert canonical_coverage("Cover 6") == "Cover 6"
    assert canonical_coverage("Zone Blitz") is None   # not a coverage name


def test_canonical_front_vocabulary():
    assert canonical_front("4-3 Over") == "4-3"
    assert canonical_front("3-4 Odd") == "3-4"
    assert canonical_front("4-4 Split") == "4-4"       # real capture read; front was missing pre-v0.2
    assert canonical_front("Nickel Over") == "Nickel"  # personnel + alignment
    assert canonical_front("Big Dime") == "Big Dime"   # more specific than "Dime"
    assert canonical_front("Prevent") == "Prevent"
    assert canonical_front("something else") is None


def test_man_zone_derives_from_coverage_without_badge():
    # ADR 0017: 0/1 = man-principle, 2/3/4/6 = zone
    assert man_zone(None, "Cover 1") == "man"
    assert man_zone(None, "Cover 3") == "zone"
    assert man_zone(None, "Cover 4 (Quarters)") == "zone"
    assert man_zone(None, None) is None
