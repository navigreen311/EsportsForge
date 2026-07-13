"""Coverage classifier tests — the OCR-of-play-call coverage leg (v0.3).

Inputs are the ACTUAL coach-cam zone-label constellations OCR'd off 10 real captures
(Cover 0/1/2/2-Man/Tampa2/3/3-Slim/4/6/9), including the real OCR noise (HURL for CURL)
and the far-edge labels EasyOCR missed (SOFT SQUAT on Cover 6) — so the classifier is
verified to be robust to exactly what the reader will feed it. Tokens are (x, y, text)
in fractional frame coords. See ~/madden-recal-refs/digit-campaign/COVERAGE_CONSTELLATIONS.md.
"""

from __future__ import annotations

from app.adapters.madden26.coverage_classifier import classify_coverage

# --- Real captured constellations (deep zones ~y0.37, underneath ~y0.50) ---

COVER_0: list[tuple[float, float, str]] = []  # all man, defenders on lines, no labels

COVER_1 = [(0.50, 0.36, "DEEP"), (0.50, 0.39, "ZONE"),
           (0.50, 0.48, "3REC"), (0.50, 0.52, "HOOK")]

COVER_2_MAN = [(0.32, 0.36, "DEEP"), (0.32, 0.39, "ZONE"),
               (0.68, 0.36, "DEEP"), (0.68, 0.39, "ZONE")]

COVER_2_INVERT = [(0.32, 0.36, "DEEP"), (0.32, 0.39, "ZONE"),
                  (0.68, 0.36, "DEEP"), (0.68, 0.39, "ZONE"),
                  (0.50, 0.43, "MID"), (0.50, 0.46, "READ"),
                  (0.16, 0.51, "CLOUD"), (0.16, 0.55, "FLAT"),
                  (0.84, 0.51, "CLOUD"), (0.84, 0.55, "FLAT"),
                  (0.34, 0.50, "CURL"), (0.66, 0.50, "HURL")]  # HURL = OCR'd CURL

TAMPA_2 = [(0.32, 0.36, "DEEP"), (0.32, 0.39, "ZONE"),
           (0.68, 0.36, "DEEP"), (0.68, 0.39, "ZONE"),
           (0.50, 0.46, "READ"),
           (0.15, 0.51, "CLOUD"), (0.16, 0.55, "FLAT"),
           (0.84, 0.51, "CLOUD"), (0.85, 0.55, "FLATR"),  # FLATR = OCR'd FLAT
           (0.34, 0.50, "CURL"), (0.66, 0.50, "CURL")]

COVER_3 = [(0.24, 0.36, "DEEP"), (0.24, 0.39, "ZONE"),
           (0.50, 0.36, "DEEP"), (0.50, 0.39, "ZONE"),
           (0.76, 0.36, "DEEP"), (0.76, 0.39, "ZONE"),
           (0.18, 0.50, "SEAM"), (0.81, 0.50, "SEAM"),
           (0.40, 0.50, "CURL"), (0.40, 0.53, "HOOK"),
           (0.60, 0.50, "CURL"), (0.60, 0.53, "HOOK")]

COVER_3_SLIM = [(0.24, 0.36, "DEEP"), (0.24, 0.39, "ZONE"),
                (0.50, 0.36, "DEEP"), (0.50, 0.39, "ZONE"),
                (0.76, 0.36, "DEEP"), (0.76, 0.39, "ZONE"),
                (0.18, 0.50, "CURL"), (0.81, 0.50, "CURL"),
                (0.40, 0.50, "CURL"), (0.40, 0.53, "HOOK"),
                (0.60, 0.50, "CURL"), (0.60, 0.53, "HOOK")]

COVER_4 = [(0.23, 0.36, "DEEP"), (0.23, 0.39, "ZONE"),
           (0.40, 0.36, "DEEP"), (0.40, 0.39, "ZONE"),
           (0.60, 0.36, "DEEP"), (0.60, 0.39, "ZONE"),
           (0.76, 0.36, "DEEP"), (0.77, 0.39, "ZONE"),
           (0.50, 0.48, "3REC"), (0.50, 0.52, "HOOK"),
           (0.18, 0.50, "QUARTER"), (0.81, 0.50, "FLAT"), (0.81, 0.53, "QUARTER")]

# Cover 6 as ACTUALLY OCR'd — the SOFT SQUAT far-right label was MISSED by EasyOCR;
# the classifier must still get Cover 6 from the QUARTER-flat side alone.
COVER_6 = [(0.23, 0.36, "DEEP"), (0.23, 0.39, "ZONE"),
           (0.40, 0.36, "DEEP"), (0.40, 0.39, "ZONE"),
           (0.68, 0.36, "DEEP"), (0.68, 0.39, "ZONE"),
           (0.18, 0.50, "QUARTER"), (0.19, 0.55, "FLAT"),
           (0.50, 0.48, "3REC"), (0.50, 0.52, "HOOK"),
           (0.66, 0.50, "VERT"), (0.66, 0.53, "HOOK")]

COVER_9 = [(0.32, 0.36, "DEEP"), (0.32, 0.39, "ZONE"),
           (0.60, 0.36, "DEEP"), (0.60, 0.39, "ZONE"),
           (0.76, 0.36, "DEEP"), (0.77, 0.39, "ZONE"),
           (0.15, 0.55, "SOFT"),
           (0.34, 0.50, "VERT"), (0.34, 0.53, "HOOK"),
           (0.50, 0.48, "3REC"), (0.50, 0.52, "HOOK"),
           (0.81, 0.50, "QUARTER"), (0.81, 0.53, "FLAT")]


def test_full_ladder_shell_and_coverage():
    cases = [
        (COVER_0, "Cover 0", "man", 0),
        (COVER_1, "Cover 1", "man", 1),
        (COVER_2_MAN, "Cover 2-Man", "man", 2),
        (COVER_2_INVERT, "Cover 2", "zone", 2),
        (TAMPA_2, "Cover 2", "zone", 2),          # folds to Cover 2 (same constellation)
        (COVER_3, "Cover 3", "zone", 3),
        (COVER_3_SLIM, "Cover 3", "zone", 3),
        (COVER_4, "Cover 4 (Quarters)", "zone", 4),
        (COVER_6, "Cover 6", "zone", 3),
        (COVER_9, "Cover 9", "zone", 3),
    ]
    for tokens, cov, mz, deep in cases:
        r = classify_coverage(tokens)
        assert r.coverage == cov, f"{cov}: got {r.coverage}"
        assert r.man_zone == mz, f"{cov}: man/zone got {r.man_zone}"
        assert r.deep_count == deep, f"{cov}: deep got {r.deep_count}"


def test_deep_count_reads_the_shell_monotonically():
    assert classify_coverage(COVER_0).deep_count == 0
    assert classify_coverage(COVER_1).deep_count == 1
    assert classify_coverage(COVER_2_INVERT).deep_count == 2
    assert classify_coverage(COVER_3).deep_count == 3
    assert classify_coverage(COVER_4).deep_count == 4


def test_man_family_is_sparse_underneath():
    # Cover 0/1/2-Man share the man structure, differing only by deep count.
    for tokens in (COVER_0, COVER_1, COVER_2_MAN):
        assert classify_coverage(tokens).man_zone == "man"
    for tokens in (COVER_2_INVERT, COVER_3, COVER_4, COVER_6, COVER_9):
        assert classify_coverage(tokens).man_zone == "zone"


def test_cover6_vs_cover9_by_quarter_side():
    # Same 3-deep asymmetric shell; QUARTER-flat side flips 6 <-> 9.
    assert classify_coverage(COVER_6).coverage == "Cover 6"   # quarter left
    assert classify_coverage(COVER_9).coverage == "Cover 9"   # quarter right


def test_cover6_survives_missed_squat_label():
    # The real capture MISSED the SOFT SQUAT edge label; Cover 6 still resolves.
    assert not any("SQUAT" in t[2] for t in COVER_6)
    assert classify_coverage(COVER_6).coverage == "Cover 6"


def test_blitz_flag_is_orthogonal():
    r = classify_coverage(COVER_3_SLIM, blitz=True)
    assert r.coverage == "Cover 3" and r.blitz is True


def test_label_less_frame_needs_coach_cam_confirmation():
    # 0 labels = Cover 0 only when the caller confirms a coach-cam view; else null.
    assert classify_coverage([], is_coach_cam=True).coverage == "Cover 0"
    assert classify_coverage([], is_coach_cam=False).coverage is None
