"""Score parsing — `_parse_score` / `_parse_scores_pair`.

These glyph-substitution parsers had zero coverage; they back the score read on both
the offline (`read_frame`) and combined-box paths. Pure functions — no OCR / no frame.
(The live patch-NCC score read, `_read_score`, is validated offline on game_hud_1:
19/20 frames read KC 0 / LV 6; 2-digit values await a scoring>9 capture.)
"""

from app.adapters.madden26.ocr_pipeline import _parse_score, _parse_scores_pair


def test_parse_score_plain_digits():
    assert _parse_score("0") == 0
    assert _parse_score("6") == 6
    assert _parse_score("14") == 14
    assert _parse_score("21") == 21


def test_parse_score_stylised_glyph_substitutions():
    # The italic scorebug's stable single-glyph confusions (ADR 0013).
    assert _parse_score("O") == 0          # ring "0" reads as O/U/Q/D
    assert _parse_score("U") == 0
    assert _parse_score("Q") == 0
    assert _parse_score("D") == 0
    assert _parse_score("I") == 1          # I/L -> 1
    assert _parse_score("L") == 1
    assert _parse_score("Z") == 2
    assert _parse_score("S") == 5
    assert _parse_score("G") == 6
    assert _parse_score("T") == 7
    assert _parse_score("B") == 8
    assert _parse_score("A") == 4
    assert _parse_score("IB") == 18        # multi-glyph: I,B -> 1,8
    assert _parse_score("so") == 50        # lower-cased first (S,O -> 5,0)


def test_parse_score_abstains_on_garbage_and_out_of_range():
    assert _parse_score("") is None
    assert _parse_score("--") is None      # no digits survive
    assert _parse_score("1234") is None    # > 3 digits
    assert _parse_score("200") is None     # > 199 (parser ceiling)
    assert _parse_score("199") == 199


def test_parse_scores_pair_splits_the_combined_box():
    assert _parse_scores_pair("7 x 7") == (7, 7)
    assert _parse_scores_pair("14 x 10") == (14, 10)
    assert _parse_scores_pair("14  10") == (14, 10)   # no separator, two numbers
    assert _parse_scores_pair("T x G") == (7, 6)      # glyph-subbed on both sides


def test_parse_scores_pair_abstains_when_under_two_numbers_or_out_of_range():
    assert _parse_scores_pair("") == (None, None)
    assert _parse_scores_pair("7") == (None, None)    # only one number
    assert _parse_scores_pair("200 x 5") == (None, None)  # home out of range
