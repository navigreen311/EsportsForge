"""Tests for LoopAI — session processing, failure attribution, downstream updates."""

from __future__ import annotations

from uuid import uuid4

import pytest

from app.schemas.loop_ai import (
    DownstreamTarget,
    FailureType,
    InterventionType,
    RecommendationOutcome,
)
from app.services.backbone.downstream_updater import DownstreamUpdater
from app.services.backbone.failure_attribution import AttributionEngine
from app.services.backbone.loop_ai import LoopAI


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def loop_ai() -> LoopAI:
    return LoopAI()


@pytest.fixture
def attribution_engine() -> AttributionEngine:
    return AttributionEngine()


@pytest.fixture
def downstream_updater() -> DownstreamUpdater:
    return DownstreamUpdater()


@pytest.fixture
def user_id():
    return uuid4()


@pytest.fixture
def session_id():
    return uuid4()


def _make_rec(
    *,
    description: str = "Run play X",
    confidence: float = 0.75,
    was_followed: bool = True,
    tags: list[str] | None = None,
    success: bool | None = True,
) -> dict:
    """Helper to build a recommendation dict for testing."""
    return {
        "id": str(uuid4()),
        "description": description,
        "confidence": confidence,
        "was_followed": was_followed,
        "tags": tags or [],
        "notes": "",
        "context": {},
    }


def _make_session_data(
    *,
    success: bool | None = True,
    score_delta: int = 7,
    performance_delta: float = 0.0,
    tags: list[str] | None = None,
    meta_age_days: int = 0,
    predicted_opponent_action: str | None = None,
    actual_opponent_action: str | None = None,
) -> dict:
    """Helper to build session_data for testing."""
    return {
        "outcome": {
            "success": success,
            "score_delta": score_delta,
        },
        "context": {
            "game_state": {"tags": tags or []},
            "meta_age_days": meta_age_days,
            "predicted_opponent_action": predicted_opponent_action,
        },
        "player_actions": [],
    }


# ---------------------------------------------------------------------------
# LoopAI — process_session
# ---------------------------------------------------------------------------


class TestProcessSession:
    """Tests for the full post-game pipeline."""

    def test_process_session_returns_loop_result(self, loop_ai, user_id, session_id):
        recs = [_make_rec()]
        session_data = _make_session_data()

        result = loop_ai.process_session(
            user_id=user_id,
            session_id=session_id,
            title="madden26",
            session_data=session_data,
            recommendations_used=recs,
        )

        assert result.user_id == user_id
        assert result.session_id == session_id
        assert result.title == "madden26"
        assert 0.0 <= result.overall_accuracy <= 1.0
        assert isinstance(result.summary, str)

    def test_process_session_with_failures_produces_attributions(
        self, loop_ai, user_id, session_id
    ):
        recs = [
            _make_rec(description="Blitz heavy", confidence=0.9),
            _make_rec(description="Play safe", confidence=0.6),
        ]
        session_data = _make_session_data(success=False, score_delta=-7)

        result = loop_ai.process_session(
            user_id=user_id,
            session_id=session_id,
            title="madden26",
            session_data=session_data,
            recommendations_used=recs,
        )

        assert result.overall_accuracy == 0.0
        assert len(result.attributions) > 0

    def test_process_session_persists_to_history(self, loop_ai, user_id, session_id):
        recs = [_make_rec()]
        session_data = _make_session_data()

        loop_ai.process_session(
            user_id=user_id,
            session_id=session_id,
            title="madden26",
            session_data=session_data,
            recommendations_used=recs,
        )

        history = loop_ai.get_learning_history(user_id, "madden26")
        assert len(history) == 1
        assert history[0].session_id == session_id

    def test_process_session_generates_downstream_updates(
        self, loop_ai, user_id, session_id
    ):
        recs = [_make_rec()]
        session_data = _make_session_data()

        result = loop_ai.process_session(
            user_id=user_id,
            session_id=session_id,
            title="madden26",
            session_data=session_data,
            recommendations_used=recs,
        )

        # At minimum: player_twin + impact_rank + truth_engine
        assert len(result.downstream_updates) >= 3

    def test_improvement_delta_calculated_across_sessions(
        self, loop_ai, user_id
    ):
        """Second session should have a non-zero delta."""
        session_data = _make_session_data(success=True)
        recs = [_make_rec()]

        # Session 1
        loop_ai.process_session(
            user_id=user_id,
            session_id=uuid4(),
            title="madden26",
            session_data=session_data,
            recommendations_used=recs,
        )

        # Session 2 — same accuracy, delta should be ~0
        result2 = loop_ai.process_session(
            user_id=user_id,
            session_id=uuid4(),
            title="madden26",
            session_data=session_data,
            recommendations_used=recs,
        )

        # Delta should be 0 since both sessions had same accuracy
        assert result2.net_improvement_score == pytest.approx(0.0, abs=0.01)

    def test_empty_recommendations_handled(self, loop_ai, user_id, session_id):
        session_data = _make_session_data()

        result = loop_ai.process_session(
            user_id=user_id,
            session_id=session_id,
            title="madden26",
            session_data=session_data,
            recommendations_used=[],
        )

        assert result.overall_accuracy == 0.0
        assert len(result.outcomes) == 0
        assert len(result.attributions) == 0


# ---------------------------------------------------------------------------
# Failure Attribution
# ---------------------------------------------------------------------------


class TestFailureAttribution:
    """Tests for the AttributionEngine."""

    def _make_outcome(
        self,
        *,
        was_followed: bool = True,
        was_successful: bool = False,
        confidence: float = 0.75,
    ) -> RecommendationOutcome:
        return RecommendationOutcome(
            recommendation_id=uuid4(),
            session_id=uuid4(),
            description="Test recommendation",
            was_followed=was_followed,
            was_successful=was_successful,
            confidence_at_time=confidence,
        )

    def test_pressure_collapse_detected(self, attribution_engine):
        rec = self._make_outcome(was_followed=True, was_successful=False)
        outcome = {"performance_delta": -0.25}
        context = {"game_state": {"tags": ["overtime", "clutch"]}}

        result = attribution_engine.classify_failure(rec, outcome, context)

        assert result.failure_type == FailureType.pressure_collapse
        assert result.confidence >= 0.8

    def test_stale_meta_detected(self, attribution_engine):
        rec = self._make_outcome()
        outcome = {}
        context = {"meta_age_days": 30, "game_state": {"tags": []}}

        result = attribution_engine.classify_failure(rec, outcome, context)

        assert result.failure_type == FailureType.stale_meta

    def test_wrong_opponent_model_detected(self, attribution_engine):
        rec = self._make_outcome()
        outcome = {"actual_opponent_action": "zone_blitz"}
        context = {
            "predicted_opponent_action": "cover_3",
            "game_state": {"tags": []},
            "meta_age_days": 0,
        }

        result = attribution_engine.classify_failure(rec, outcome, context)

        assert result.failure_type == FailureType.wrong_opponent_model

    def test_wrong_confidence_high_conf_failure(self, attribution_engine):
        rec = self._make_outcome(confidence=0.95, was_successful=False)
        outcome = {}
        context = {"game_state": {"tags": []}, "meta_age_days": 0}

        result = attribution_engine.classify_failure(rec, outcome, context)

        assert result.failure_type == FailureType.wrong_confidence

    def test_bad_execution_when_followed_but_failed(self, attribution_engine):
        rec = self._make_outcome(
            was_followed=True, was_successful=False, confidence=0.5
        )
        outcome = {}
        context = {"game_state": {"tags": []}, "meta_age_days": 0}

        result = attribution_engine.classify_failure(rec, outcome, context)

        assert result.failure_type == FailureType.bad_execution

    def test_bad_read_when_not_followed(self, attribution_engine):
        rec = self._make_outcome(
            was_followed=False, was_successful=False, confidence=0.5
        )
        outcome = {}
        context = {"game_state": {"tags": []}, "meta_age_days": 0}

        result = attribution_engine.classify_failure(rec, outcome, context)

        assert result.failure_type == FailureType.bad_read

    def test_attribution_always_has_evidence(self, attribution_engine):
        rec = self._make_outcome()
        result = attribution_engine.classify_failure(rec, {}, {"game_state": {"tags": []}, "meta_age_days": 0})

        assert len(result.evidence) > 0

    def test_suggest_intervention_returns_structured_result(self, attribution_engine):
        result = attribution_engine.suggest_intervention(
            FailureType.bad_execution,
            {"weakest_skill": "pass_rush"},
        )

        assert result["intervention_type"] == InterventionType.drill_assignment.value
        assert "priority" in result
        assert "description" in result
        assert result["parameters"]["drill_focus"] == "pass_rush"

    def test_attribution_distribution(self, attribution_engine):
        from app.schemas.loop_ai import FailureAttribution

        user_id = uuid4()
        attributions = [
            FailureAttribution(
                recommendation_id=uuid4(),
                failure_type=FailureType.bad_execution,
                confidence=0.7,
            ),
            FailureAttribution(
                recommendation_id=uuid4(),
                failure_type=FailureType.bad_execution,
                confidence=0.65,
            ),
            FailureAttribution(
                recommendation_id=uuid4(),
                failure_type=FailureType.stale_meta,
                confidence=0.8,
            ),
        ]

        dist = attribution_engine.get_attribution_distribution(
            user_id, "madden26", attributions
        )

        assert dist.total_failures == 3
        assert dist.most_common == FailureType.bad_execution
        assert dist.distribution[FailureType.bad_execution] == 2
        assert dist.distribution[FailureType.stale_meta] == 1


# ---------------------------------------------------------------------------
# Downstream Updater
# ---------------------------------------------------------------------------


class TestDownstreamUpdater:
    """Tests for the DownstreamUpdater."""

    def _make_loop_result(self, user_id, failure_types: list[FailureType] | None = None):
        from app.schemas.loop_ai import (
            FailureAttribution,
            LoopResult,
            RecommendationOutcome,
        )

        session_id = uuid4()
        outcomes = [
            RecommendationOutcome(
                recommendation_id=uuid4(),
                session_id=session_id,
                description="Test rec",
                was_followed=True,
                was_successful=True,
                confidence_at_time=0.8,
            )
        ]
        attributions = [
            FailureAttribution(
                recommendation_id=uuid4(),
                failure_type=ft,
                confidence=0.7,
            )
            for ft in (failure_types or [])
        ]

        return LoopResult(
            user_id=user_id,
            session_id=session_id,
            title="madden26",
            outcomes=outcomes,
            attributions=attributions,
            overall_accuracy=0.75,
            net_improvement_score=0.05,
            summary="Test summary.",
        )

    def test_update_player_twin(self, downstream_updater, user_id):
        result = self._make_loop_result(user_id)
        update = downstream_updater.update_player_twin(user_id, result)

        assert update.target == DownstreamTarget.player_twin
        assert update.status == "sent"

    def test_update_impact_rank(self, downstream_updater, user_id):
        result = self._make_loop_result(user_id)
        update = downstream_updater.update_impact_rank(user_id, result)

        assert update.target == DownstreamTarget.impact_rank
        assert update.status == "sent"

    def test_update_truth_engine(self, downstream_updater, user_id):
        result = self._make_loop_result(user_id)
        update = downstream_updater.update_truth_engine(result)

        assert update.target == DownstreamTarget.truth_engine
        assert update.status == "sent"

    def test_notify_agents_gameplan_on_bad_read(self, downstream_updater, user_id):
        result = self._make_loop_result(user_id, [FailureType.bad_read])
        updates = downstream_updater.notify_agents(result)

        targets = [u.target for u in updates]
        assert DownstreamTarget.gameplan_ai in targets

    def test_notify_agents_drillbot_on_bad_execution(self, downstream_updater, user_id):
        result = self._make_loop_result(user_id, [FailureType.bad_execution])
        updates = downstream_updater.notify_agents(result)

        targets = [u.target for u in updates]
        assert DownstreamTarget.drill_bot in targets

    def test_notify_agents_antimeta_on_stale_meta(self, downstream_updater, user_id):
        result = self._make_loop_result(user_id, [FailureType.stale_meta])
        updates = downstream_updater.notify_agents(result)

        targets = [u.target for u in updates]
        assert DownstreamTarget.anti_meta_lab in targets

    def test_notify_agents_confidence_on_pressure_collapse(
        self, downstream_updater, user_id
    ):
        result = self._make_loop_result(user_id, [FailureType.pressure_collapse])
        updates = downstream_updater.notify_agents(result)

        targets = [u.target for u in updates]
        assert DownstreamTarget.confidence_ai in targets

    def test_push_all_returns_at_least_three_updates(
        self, downstream_updater, user_id
    ):
        result = self._make_loop_result(user_id)
        updates = downstream_updater.push_all(user_id, result)

        # player_twin + impact_rank + truth_engine = 3 minimum
        assert len(updates) >= 3

    def test_push_all_with_failures_triggers_agent_notifications(
        self, downstream_updater, user_id
    ):
        result = self._make_loop_result(
            user_id,
            [FailureType.bad_execution, FailureType.stale_meta],
        )
        updates = downstream_updater.push_all(user_id, result)

        # 3 core + drill_bot + anti_meta_lab = 5
        assert len(updates) >= 5


# ---------------------------------------------------------------------------
# Pattern Detection
# ---------------------------------------------------------------------------


class TestPatternDetection:
    """Tests for cross-session pattern detection."""

    def test_no_patterns_with_single_session(self, loop_ai, user_id):
        session_data = _make_session_data()
        recs = [_make_rec()]

        loop_ai.process_session(
            user_id=user_id,
            session_id=uuid4(),
            title="madden26",
            session_data=session_data,
            recommendations_used=recs,
        )

        patterns = loop_ai.detect_patterns(user_id, "madden26")
        assert len(patterns) == 0

    def test_failure_cluster_detected_after_repeated_failures(
        self, loop_ai, user_id
    ):
        """Feed 4 sessions with stale-meta failures to trigger cluster."""
        for _ in range(4):
            recs = [_make_rec(confidence=0.5)]
            session_data = _make_session_data(
                success=False,
                score_delta=-3,
                meta_age_days=20,
            )
            loop_ai.process_session(
                user_id=user_id,
                session_id=uuid4(),
                title="madden26",
                session_data=session_data,
                recommendations_used=recs,
            )

        patterns = loop_ai.detect_patterns(user_id, "madden26")
        cluster_patterns = [p for p in patterns if p.pattern_type == "failure_cluster"]
        assert len(cluster_patterns) >= 1

    def test_patterns_scoped_to_title(self, loop_ai, user_id):
        """Patterns for madden26 should not appear in cfb26 queries."""
        session_data = _make_session_data()
        recs = [_make_rec()]

        for _ in range(3):
            loop_ai.process_session(
                user_id=user_id,
                session_id=uuid4(),
                title="madden26",
                session_data=session_data,
                recommendations_used=recs,
            )

        patterns = loop_ai.detect_patterns(user_id, "cfb26")
        assert len(patterns) == 0
