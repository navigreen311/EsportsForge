"""Defensive play-call parser — maps OCR'd play-call text to the defensive stack.

The OCR-of-play-call pivot (docs/phase-completions/coverage-ocr-playcall-pivot.md): after
post-snap coverage-from-vision proved a research arc (by-clip tier numbers did not survive
by-game validation), the defensive call is read off the **play-call screen**, which shows —
in clean, high-confidence text — the coverage NAME ("Cover 1 Hole", "Tampa 2"), the FRONT
("4-3 Over"), and an explicit MAN/ZONE/BLITZ badge. One screen serves v0.2 (`defensive_formation`),
v0.3 (`defensive_coverage`), and man/zone.

This module is the PURE PARSER (CI-tested): it takes the OCR text of a defensive play-call
card — the coverage-name string, the front string, and the badge — and returns the canonical
front + coverage (ADR 0017 vocabulary) + man/zone. The EasyOCR pass over each card region and
the screen detection live in the adapter (a follow-up wiring step); reading the whole card band
at once splits "Cover 1 Hole" into loose tokens, so the caller OCRs each card region separately.

HARD LIMIT (documented): this reads the coverage the USER calls (on defense / own-defense
analytics). It cannot read the opponent's coverage while on offense — that is the deferred
post-snap-vision arc.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

# Canonical coverage vocabulary (ADR 0017): keyword-in-name -> canonical. Order matters —
# more specific variants first (e.g. "cover 2 man" before "cover 2", "tampa" before "cover 2").
_COVERAGE_RULES: list[tuple[str, str]] = [
    ("cover 0", "Cover 0"),
    ("cover 1 robber", "Cover 1-Robber"),
    ("robber", "Cover 1-Robber"),
    ("cover 1", "Cover 1"),
    ("cover 2 man", "Cover 2-Man"),
    ("tampa", "Cover 2"),          # Tampa 2 is a Cover-2 variant
    ("cover 2", "Cover 2"),
    ("cover 3", "Cover 3"),
    ("cover 6", "Cover 6"),
    ("quarter", "Cover 4 (Quarters)"),
    ("palms", "Cover 4 (Quarters)"),
    ("cover 4", "Cover 4 (Quarters)"),
]

# Defensive front / personnel keywords -> canonical front.
_FRONT_RULES: list[tuple[str, str]] = [
    ("big dime", "Big Dime"),
    ("nickel", "Nickel"),
    ("dime", "Dime"),
    ("dollar", "Dollar"),
    ("quarter", "Quarter"),
    ("3-4", "3-4"),
    ("4-3", "4-3"),
    ("4-4", "4-4"),
    ("46", "46"),
    ("bear", "Bear"),
    ("prevent", "Prevent"),
    ("goal line", "Goal Line"),
]

_MZ = {"man": "man", "zone": "zone", "blitz": "blitz"}


def _norm(s: str) -> str:
    return re.sub(r"\s+", " ", s.strip().lower())


def canonical_coverage(name: str | None) -> str | None:
    """Map a play name (e.g. "Cover 1 Hole", "Tampa 2") to the ADR-0017 canonical
    coverage, or None if it is not a recognisable coverage (e.g. a pure blitz)."""
    if not name:
        return None
    n = _norm(name)
    for kw, canon in _COVERAGE_RULES:
        if kw in n:
            return canon
    return None


def canonical_front(text: str | None) -> str | None:
    """Map a front/formation string (e.g. "4-3 Over", "Nickel") to a canonical front."""
    if not text:
        return None
    n = _norm(text)
    for kw, canon in _FRONT_RULES:
        if kw in n:
            return canon
    return None


def man_zone(badge: str | None, coverage: str | None = None) -> str | None:
    """man / zone from the card badge; falls back to deriving it from the coverage
    number (ADR 0017: Cover 0/1 = man-principle, 2/3/4/6 = zone) when no badge is read."""
    if badge:
        b = _norm(badge)
        for kw, v in _MZ.items():
            if kw in b:
                return "man" if v == "blitz" else v   # a "blitz" badge is a man-pressure look
    if coverage:
        c = _norm(coverage)
        if c.startswith("cover 0") or c.startswith("cover 1"):
            return "man"
        if any(c.startswith(f"cover {n}") for n in ("2", "3", "4", "6")):
            return "zone"
    return None


@dataclass(frozen=True)
class DefensivePlaycallReading:
    """One defensive play-call card, parsed to the canonical stack."""
    front: str | None            # v0.2 defensive_formation, e.g. "4-3"
    coverage: str | None         # v0.3 defensive_coverage, e.g. "Cover 1"
    man_zone: str | None         # "man" | "zone" | None
    raw_name: str | None         # the OCR'd play name, e.g. "Cover 1 Hole"


def parse_card(name: str | None, front_text: str | None = None,
               badge: str | None = None) -> DefensivePlaycallReading:
    """Parse one defensive play-call card's OCR text into the canonical stack."""
    cov = canonical_coverage(name)
    return DefensivePlaycallReading(
        front=canonical_front(front_text),
        coverage=cov,
        man_zone=man_zone(badge, cov),
        raw_name=name.strip() if name else None,
    )
