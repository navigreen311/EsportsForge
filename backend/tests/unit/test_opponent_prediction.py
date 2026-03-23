"""Unit tests for Opponent Prediction Engine."""

from __future__ import annotations

import pytest

from app.schemas.opponent import Prediction
from app.services.backbone.opponent_prediction import (
    _reset_store,
    get_prediction_confidence,
    predict_next_call,
    update_model,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture(autouse=True)
def _clear_model():
    """Ensure a clean model store for every test."""
    _reset_store()
    yield
    _reset_store()


def _build_history(actions_per_situation: dict[str, list[str]]) -> list[dict]:
    """Build a history list from {situation: [action, ...]}."""
    history = []
    for sit, actions in actions_per_situation.items():
        for act in actions:
            history.append({"situation": sit, "action": act})
    return history


# ---------------------------------------------------------------------------
# predict_next_call
# ---------------------------------------------------------------------------

class TestPredictNextCall:
    def test_returns_prediction_with_history(self):
        history = _build_history({
            "3rd & 7": ["PA Crossers", "PA Crossers", "HB Dive"],
        })
        pred = predict_next_call("opp-1", "3rd & 7", history)

        assert isinstance(pred, Prediction)
        assert pred.predicted_action == "PA Crossers"
        assert pred.confidence > 0.5

    def test_returns_unknown_with_no_data(self):
        pred = predict_next_call("opp-empty", "3rd & 7")

        assert pred.predicted_action == "unknown"
        assert pred.confidence == 0.0

    def test_alternatives_listed(self):
        history = _build_history({
            "1st & 10": ["HB Dive", "HB Dive", "PA Boot", "Screen"],
        })
        pred = predict_next_call("opp-2", "1st & 10", history)

        assert pred.predicted_action == "HB Dive"
        alt_actions = [a["action"] for a in pred.alternatives]
        assert "PA Boot" in alt_actions
        assert "Screen" in alt_actions

    def test_prediction_uses_stored_model(self):
        # First call seeds the model via history
        history = _build_history({"red zone": ["Fade", "Fade", "Slant"]})
        predict_next_call("opp-3", "red zone", history)

        # Second call should use stored model (no history passed)
        pred = predict_next_call("opp-3", "red zone")
        assert pred.predicted_action == "Fade"

    def test_100_percent_confidence_when_only_one_action(self):
        history = _build_history({"4th & 1": ["QB Sneak", "QB Sneak", "QB Sneak"]})
        pred = predict_next_call("opp-4", "4th & 1", history)

        assert pred.predicted_action == "QB Sneak"
        assert pred.confidence == 1.0
        assert pred.alternatives == []


# ---------------------------------------------------------------------------
# get_prediction_confidence
# ---------------------------------------------------------------------------

class TestGetPredictionConfidence:
    def test_zero_for_unknown(self):
        pred = predict_next_call("opp-x", "any")
        conf = get_prediction_confidence(pred)

        assert conf == 0.0

    def test_penalises_small_sample(self):
        history = _build_history({"3rd & 3": ["Blitz", "Blitz"]})
        pred = predict_next_call("opp-5", "3rd & 3", history)

        raw = pred.confidence
        adjusted = get_prediction_confidence(pred)
        # With 2 observations (< 5), the adjusted confidence should be lower
        assert adjusted < raw

    def test_no_penalty_for_large_sample(self):
        history = _build_history({"3rd & 3": ["Blitz"] * 10})
        pred = predict_next_call("opp-6", "3rd & 3", history)

        adjusted = get_prediction_confidence(pred)
        assert adjusted == pred.confidence


# ---------------------------------------------------------------------------
# update_model
# ---------------------------------------------------------------------------

class TestUpdateModel:
    def test_updates_model_with_new_data(self):
        update_model("opp-7", {"situation": "goal line", "action": "Power Run"})
        update_model("opp-7", {"situation": "goal line", "action": "Power Run"})
        update_model("opp-7", {"situation": "goal line", "action": "PA Pass"})

        pred = predict_next_call("opp-7", "goal line")
        assert pred.predicted_action == "Power Run"
        assert pred.confidence > 0.5

    def test_ignores_incomplete_data(self):
        update_model("opp-8", {"situation": "", "action": "something"})
        update_model("opp-8", {"situation": "3rd", "action": ""})

        # Model should still be empty for this opponent
        pred = predict_next_call("opp-8", "3rd")
        assert pred.predicted_action == "unknown"

    def test_model_accumulates(self):
        for _ in range(5):
            update_model("opp-9", {"situation": "2nd & 5", "action": "Curl"})
        update_model("opp-9", {"situation": "2nd & 5", "action": "Out"})

        pred = predict_next_call("opp-9", "2nd & 5")
        assert pred.predicted_action == "Curl"
        # 5/6 = ~83%
        assert pred.confidence > 0.8
