"""Defensive-coverage classifier from coach-cam zone-assignment labels (v0.3).

The OCR-of-play-call pivot's coverage leg. Post-snap coverage-from-vision proved a
research arc (by-clip tier numbers did not survive by-game validation), and the
committed coverage is NOT surfaced on the play-call card screen (selection fades all 3
cards uniformly; the field carries no coverage name). The signal that DOES work: the
pre-snap **coach-cam** (play-art ON) draws every defender's zone assignment as a clean
text label on the field — a coverage FINGERPRINT. Validated on 10 real captures
(Cover 0/1/2/2-Man/Tampa2/3/3-Slim/4/6/9); see
`~/madden-recal-refs/digit-campaign/COVERAGE_CONSTELLATIONS.md`.

This module is the PURE CLASSIFIER (CI-tested): given the OCR'd zone-label tokens
(x, y, text) it returns the canonical coverage + man/zone. The coach-cam OCR pass and
view detection live in the adapter/reader (EasyOCR, not CI).

Decision tree (validated):
  1. #DEEP ZONE labels = the deep shell (0-4).
  2. UNDERNEATH-label density (labels excluding the deep zones): sparse (<=2) => MAN
     coverage (man defenders are drawn as LINES, not labels), dense => ZONE.
  3. man family = N-deep + man-under: Cover 0 (0) / Cover 1 (1) / Cover 2-Man (2).
     zone family by shell: <=2 => Cover 2; 3 => Cover 3, unless a QUARTER-flat label
     is present (asymmetric quarter-quarter-half => Cover 6 if it's on the left, Cover 9
     on the right); 4 => Cover 4 (Quarters).

Resolution limit (documented): label-identical variants that differ only by route
GEOMETRY are folded to the canonical family — e.g. Tampa 2 and Cover 2 Invert have the
same constellation and both map to "Cover 2" (matches ADR-0017). BLITZ (red pressure
lines) is an orthogonal pixel signal carried as a separate flag, not a coverage.
"""

from __future__ import annotations

from dataclasses import dataclass, field

# Zone-assignment vocabulary drawn by the coach-cam. Tokens are OCR'd separately
# (two-word labels like "DEEP ZONE" arrive as DEEP + ZONE stacked vertically), so we
# work at the token level and group by 2-D proximity into labels.
_ZONE_WORDS = frozenset({
    "DEEP", "ZONE", "CURL", "HOOK", "FLAT", "CLOUD", "SEAM", "MID", "READ",
    "QUARTER", "SOFT", "SQUAT", "VERT", "3REC", "REC", "HOLE", "BUZZ", "SINK",
})

# Common EasyOCR misreads seen on the captured coach-cam labels -> canonical token.
_TOKEN_FIX = {
    "HURL": "CURL", "BURL": "CURL", "GURL": "CURL",
    "FLATR": "FLAT", "FLAI": "FLAT", "FIAT": "FLAT",
    "ZOME": "ZONE", "ZONE.": "ZONE",
    "QUAT": "SQUAT", "SQUA": "SQUAT", "SQUAT.": "SQUAT",
    "3RECV": "3REC", "3REG": "3REC",
    "READ.": "READ", "MId": "MID",
}

_X_TOL = 0.05   # tokens of one label share x within this
_Y_TOL = 0.07   # ...and stack within this in y


def _clean(text: str) -> str:
    t = text.strip().upper().strip(".,;:~\"'`")
    return _TOKEN_FIX.get(t, t)


@dataclass
class _Label:
    x: float
    y: float
    words: set[str] = field(default_factory=set)

    @property
    def is_deep(self) -> bool:
        return "DEEP" in self.words and "ZONE" in self.words

    @property
    def has_quarter(self) -> bool:
        return "QUARTER" in self.words

    @property
    def has_squat(self) -> bool:
        return "SQUAT" in self.words or "SOFT" in self.words


def _group(tokens: list[tuple[float, float, str]]) -> list[_Label]:
    """Group (x, y, text) tokens into zone labels by 2-D proximity. Only tokens whose
    cleaned text is in the zone vocabulary are kept (drops player names / HUD noise)."""
    labels: list[_Label] = []
    for x, y, raw in tokens:
        w = _clean(raw)
        if w not in _ZONE_WORDS:
            continue
        placed = False
        for lab in labels:
            if abs(lab.x - x) <= _X_TOL and abs(lab.y - y) <= _Y_TOL:
                lab.words.add(w)
                # keep the label anchored near its topmost token
                lab.x = (lab.x + x) / 2
                lab.y = min(lab.y, y)
                placed = True
                break
        if not placed:
            labels.append(_Label(x=x, y=y, words={w}))
    return labels


_MAN_UNDER_MAX = 2   # <= this many underneath labels => man coverage (defenders on lines)


@dataclass(frozen=True)
class CoverageReading:
    coverage: str | None       # canonical, e.g. "Cover 3" / "Cover 2-Man" / "Cover 6"
    man_zone: str | None       # "man" | "zone" | None
    deep_count: int            # number of DEEP ZONE labels (the shell)
    n_labels: int              # total zone labels read (drives confidence)
    confidence: float
    blitz: bool = False        # orthogonal red-pressure signal (from the reader)


# canonical shell -> man-coverage name
_MAN_BY_DEEP = {0: "Cover 0", 1: "Cover 1", 2: "Cover 2-Man"}


def classify_coverage(
    tokens: list[tuple[float, float, str]],
    *,
    is_coach_cam: bool = True,
    blitz: bool = False,
) -> CoverageReading:
    """Classify a coach-cam constellation into a canonical coverage + man/zone.

    tokens: OCR'd (x, y, text) in fractional frame coords (0=left/top .. 1=right/bottom),
    restricted to the play-art band. is_coach_cam: the caller confirmed this is a
    coach-cam view (needed to read the label-less Cover 0). blitz: red-pressure detected.
    """
    labels = _group(tokens)
    deep = [lb for lb in labels if lb.is_deep]
    under = [lb for lb in labels if not lb.is_deep]
    deep_count = len(deep)
    under_count = len(under)
    n = len(labels)

    # Confidence: proportional to how many labels we read (a full coverage draws ~5-7).
    conf = round(min(1.0, 0.35 + 0.11 * n), 3) if n else (0.4 if is_coach_cam else 0.0)

    # Label-less frame: only Cover 0 (all-man, defenders on lines) on a confirmed
    # coach-cam view; otherwise we can't tell it's a coverage at all.
    if n == 0:
        if is_coach_cam:
            return CoverageReading("Cover 0", "man", 0, 0, conf, blitz)
        return CoverageReading(None, None, 0, 0, 0.0, blitz)

    man = under_count <= _MAN_UNDER_MAX
    if man:
        cov = _MAN_BY_DEEP.get(deep_count)
        # A man look with 3+ deep zones is unusual; fall back to the shell name.
        if cov is None:
            cov = f"Cover {deep_count}"
        return CoverageReading(cov, "man", deep_count, n, conf, blitz)

    # Zone family — resolve by deep shell.
    if deep_count <= 2:
        cov = "Cover 2"
    elif deep_count == 3:
        quarters = [lb for lb in under if lb.has_quarter]
        if quarters:
            # asymmetric quarter-quarter-half: QUARTER-flat side is the quarters half.
            qx = sum(lb.x for lb in quarters) / len(quarters)
            cov = "Cover 6" if qx < 0.5 else "Cover 9"
        else:
            cov = "Cover 3"
    else:  # 4+
        cov = "Cover 4 (Quarters)"
    return CoverageReading(cov, "zone", deep_count, n, conf, blitz)
