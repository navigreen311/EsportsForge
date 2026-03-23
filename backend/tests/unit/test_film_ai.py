"""Unit tests for FilmAI — replay analysis, mistake classification, pattern detection."""

from __future__ import annotations

import pytest

from app.schemas.film import (
    FilmBreakdown,
    MistakeCategory,
    MistakeClassification,
    PatternDetection,
    ReplayAnalysis,
    TaggedMoment,
)
from app.services.backbone import film_ai


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture(autouse=True)
def _clean_stores():
    """Reset all in-memory stores before each test."""
    film_ai.reset_store()
    yield
    film_ai.reset_store()


def _make_replay_data(
    replay_id: str = "replay-001",
    title: str = "madden26",
    tagged_moments: list | None = None,
) -> dict:
    return {
        "replay_id": replay_id,
        "title": title,
        "tagged_moments": tagged_moments or [],
    }


# ---------------------------------------------------------------------------
# analyze_replay
# ---------------------------------------------------------------------------

class TestAnalyzeReplay:
    """Test analyze_replay produces correct ReplayAnalysis."""

    def test_basic_analysis(self):
        data = _make_replay_data(tagged_moments=[
            {"timestamp": 10.0, "tag": "big_play", "notes": "70-yard TD"},
            {"timestamp": 45.0, "tag": "turnover", "notes": "pick six"},
        ])
        result = film_ai.analyze_replay("user1", data)

        assert isinstance(result, ReplayAnalysis)
        assert result.replay_id == "replay-001"
        assert result.user_id == "user1"
        assert result.title == "madden26"
        assert len(result.tagged_moments) == 2

    def test_empty_replay(self):
        data = _make_replay_data(tagged_moments=[])
        result = film_ai.analyze_replay("user1", data)

        assert len(result.tagged_moments) == 0
        assert result.summary == "No moments tagged."

    def test_generates_replay_id_if_missing(self):
        data = {"title": "madden26", "tagged_moments": []}
        result = film_ai.analyze_replay("user1", data)

        assert result.replay_id  # auto-generated
        assert len(result.replay_id) == 12

    def test_mistakes_extracted_from_tags(self):
        data = _make_replay_data(tagged_moments=[
            {"timestamp": 5.0, "tag": "misread_coverage"},
            {"timestamp": 20.0, "tag": "drop_pass"},
            {"timestamp": 30.0, "tag": "wrong_play_call"},
        ])
        result = film_ai.analyze_replay("user1", data)

        assert len(result.mistakes) == 3
        categories = {m.category for m in result.mistakes}
        assert MistakeCategory.READ_ERROR in categories
        assert MistakeCategory.EXECUTION_ERROR in categories
        assert MistakeCategory.SCHEME_ERROR in categories


# ---------------------------------------------------------------------------
# classify_mistakes
# ---------------------------------------------------------------------------

class TestClassifyMistakes:
    """Test classify_mistakes categorization logic."""

    def test_read_error_keywords(self):
        data = _make_replay_data(tagged_moments=[
            {"timestamp": 1.0, "tag": "misread"},
            {"timestamp": 2.0, "tag": "coverage_read"},
        ])
        analysis = film_ai.analyze_replay("user1", data)
        mistakes = film_ai.classify_mistakes(analysis)

        assert all(m.category == MistakeCategory.READ_ERROR for m in mistakes)

    def test_execution_error_keywords(self):
        data = _make_replay_data(tagged_moments=[
            {"timestamp": 1.0, "tag": "drop"},
            {"timestamp": 2.0, "tag": "timing_miss"},
        ])
        analysis = film_ai.analyze_replay("user1", data)
        mistakes = film_ai.classify_mistakes(analysis)

        assert all(m.category == MistakeCategory.EXECUTION_ERROR for m in mistakes)

    def test_scheme_error_keywords(self):
        data = _make_replay_data(tagged_moments=[
            {"timestamp": 1.0, "tag": "wrong_play_call"},
            {"timestamp": 2.0, "tag": "bad_formation"},
        ])
        analysis = film_ai.analyze_replay("user1", data)
        mistakes = film_ai.classify_mistakes(analysis)

        assert all(m.category == MistakeCategory.SCHEME_ERROR for m in mistakes)

    def test_non_mistake_tags_ignored(self):
        data = _make_replay_data(tagged_moments=[
            {"timestamp": 1.0, "tag": "big_play"},
            {"timestamp": 2.0, "tag": "clutch"},
        ])
        analysis = film_ai.analyze_replay("user1", data)
        mistakes = film_ai.classify_mistakes(analysis)

        assert len(mistakes) == 0


# ---------------------------------------------------------------------------
# detect_patterns
# ---------------------------------------------------------------------------

class TestDetectPatterns:
    """Test cross-replay pattern detection."""

    def test_no_replays_returns_empty(self):
        patterns = film_ai.detect_patterns("user1", "madden26")
        assert patterns == []

    def test_detects_frequent_tag(self):
        """A tag present in >= 30% of sessions should be detected."""
        for i in range(5):
            data = _make_replay_data(
                replay_id=f"r-{i}",
                tagged_moments=[{"timestamp": 10.0, "tag": "turnover"}],
            )
            film_ai.analyze_replay("user1", data)

        patterns = film_ai.detect_patterns("user1", "madden26")
        assert len(patterns) >= 1
        assert any(p.pattern_name == "turnover" for p in patterns)

    def test_infrequent_tag_not_detected(self):
        """A tag in only 1 of 10 sessions should not trigger a pattern."""
        for i in range(10):
            moments = []
            if i == 0:
                moments = [{"timestamp": 10.0, "tag": "rare_event"}]
            else:
                moments = [{"timestamp": 10.0, "tag": "normal_play"}]
            data = _make_replay_data(replay_id=f"r-{i}", tagged_moments=moments)
            film_ai.analyze_replay("user1", data)

        patterns = film_ai.detect_patterns("user1", "madden26")
        pattern_names = {p.pattern_name for p in patterns}
        assert "rare_event" not in pattern_names

    def test_pattern_frequency_is_correct(self):
        for i in range(4):
            tag = "blitz_read" if i < 3 else "other"
            data = _make_replay_data(
                replay_id=f"r-{i}",
                tagged_moments=[{"timestamp": 5.0, "tag": tag}],
            )
            film_ai.analyze_replay("user1", data)

        patterns = film_ai.detect_patterns("user1", "madden26")
        blitz = next((p for p in patterns if p.pattern_name == "blitz_read"), None)
        assert blitz is not None
        assert blitz.frequency == 0.75


# ---------------------------------------------------------------------------
# generate_breakdown
# ---------------------------------------------------------------------------

class TestGenerateBreakdown:
    """Test full film breakdown generation."""

    def test_breakdown_includes_key_moments(self):
        data = _make_replay_data(tagged_moments=[
            {"timestamp": 10.0, "tag": "turnover"},
            {"timestamp": 30.0, "tag": "big_play"},
            {"timestamp": 50.0, "tag": "normal"},
        ])
        film_ai.analyze_replay("user1", data)
        breakdown = film_ai.generate_breakdown("replay-001")

        assert isinstance(breakdown, FilmBreakdown)
        # turnover and big_play are key moments, normal is not
        assert len(breakdown.key_moments) == 2

    def test_breakdown_for_unknown_replay_raises(self):
        with pytest.raises(ValueError, match="No analysis found"):
            film_ai.generate_breakdown("nonexistent")

    def test_breakdown_has_recommendations(self):
        data = _make_replay_data(tagged_moments=[
            {"timestamp": 5.0, "tag": "misread_coverage"},
            {"timestamp": 15.0, "tag": "drop_pass"},
        ])
        film_ai.analyze_replay("user1", data)
        breakdown = film_ai.generate_breakdown("replay-001")

        assert len(breakdown.recommendations) >= 2


# ---------------------------------------------------------------------------
# tag_moment
# ---------------------------------------------------------------------------

class TestTagMoment:
    """Test manual moment tagging."""

    def test_tag_creates_moment(self):
        moment = film_ai.tag_moment("replay-001", 12.5, "clutch", "game-winner")
        assert isinstance(moment, TaggedMoment)
        assert moment.replay_id == "replay-001"
        assert moment.timestamp == 12.5
        assert moment.tag == "clutch"
        assert moment.notes == "game-winner"

    def test_tag_appends_to_existing_analysis(self):
        data = _make_replay_data(tagged_moments=[
            {"timestamp": 5.0, "tag": "normal"},
        ])
        film_ai.analyze_replay("user1", data)

        film_ai.tag_moment("replay-001", 25.0, "turnover", "late int")
        breakdown = film_ai.generate_breakdown("replay-001")
        assert len(breakdown.analysis.tagged_moments) == 2
