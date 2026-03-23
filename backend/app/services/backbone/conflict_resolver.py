"""Conflict resolution engine for ForgeCore.

When multiple agents produce competing recommendations, the resolver
applies a deterministic priority chain to pick a single winner:

1. **PlayerTwin veto** — if the player physically/mentally can't execute it, drop it.
2. **Confidence threshold** — filter outputs below the context-dependent minimum.
3. **Context-aware weighting** — multiply confidence by a mode-specific weight.
4. **Priority-based resolution** — agent with the lowest priority number wins.
5. **ImpactRank tiebreak** — if priorities are equal, highest ImpactRank score wins.
"""

from __future__ import annotations

from app.schemas.forgecore import (
    AgentOutput,
    ConflictResolution,
    DecisionContext,
    GameMode,
    PressureState,
)

# ---------------------------------------------------------------------------
# Configurable thresholds & weights
# ---------------------------------------------------------------------------

#: Minimum confidence required for an agent output to survive filtering.
#: Keyed by (GameMode, PressureState) with a global fallback.
CONFIDENCE_THRESHOLDS: dict[tuple[GameMode, PressureState] | str, float] = {
    (GameMode.TOURNAMENT, PressureState.CRITICAL): 0.70,
    (GameMode.TOURNAMENT, PressureState.HIGH): 0.60,
    (GameMode.RANKED, PressureState.CRITICAL): 0.65,
    (GameMode.RANKED, PressureState.HIGH): 0.55,
    (GameMode.TRAINING, PressureState.LOW): 0.20,
    "default": 0.40,
}

#: Mode-specific multipliers applied to agent confidence before comparison.
MODE_WEIGHTS: dict[GameMode, float] = {
    GameMode.TOURNAMENT: 1.20,
    GameMode.RANKED: 1.00,
    GameMode.SCRIM: 0.90,
    GameMode.CASUAL: 0.70,
    GameMode.TRAINING: 0.60,
}

#: Agents whose priority values are assigned at registration.
#: Lower numbers mean higher trust.  This maps are the *default* priorities
#: used if the registry entry doesn't specify one.
DEFAULT_AGENT_PRIORITIES: dict[str, int] = {
    "player_twin": 10,   # highest — veto power
    "meta_bot": 20,
    "impact_rank": 30,
    "truth_engine": 40,
    "loop_ai": 50,
}


def _get_confidence_threshold(ctx: DecisionContext) -> float:
    """Return the minimum confidence for this mode + pressure combo."""
    key = (ctx.mode, ctx.pressure_state)
    return CONFIDENCE_THRESHOLDS.get(key, CONFIDENCE_THRESHOLDS["default"])  # type: ignore[arg-type]


def _get_mode_weight(ctx: DecisionContext) -> float:
    return MODE_WEIGHTS.get(ctx.mode, 1.0)


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

class ConflictResolver:
    """Stateless resolver — all state flows through method arguments."""

    def __init__(
        self,
        agent_priorities: dict[str, int] | None = None,
    ) -> None:
        self._priorities = agent_priorities or DEFAULT_AGENT_PRIORITIES

    # -- step 1: veto -------------------------------------------------------

    def apply_player_twin_veto(
        self,
        outputs: list[AgentOutput],
    ) -> tuple[list[AgentOutput], list[AgentOutput]]:
        """Separate vetoed outputs from surviving ones.

        The PlayerTwin agent marks outputs it considers non-executable by
        setting ``vetoed=True`` on the AgentOutput.  Any output produced
        *by* the PlayerTwin itself is never vetoed.
        """
        surviving: list[AgentOutput] = []
        vetoed: list[AgentOutput] = []
        for out in outputs:
            if out.vetoed and out.agent_name != "player_twin":
                vetoed.append(out)
            else:
                surviving.append(out)
        return surviving, vetoed

    # -- step 2: confidence threshold ---------------------------------------

    def filter_by_confidence(
        self,
        outputs: list[AgentOutput],
        context: DecisionContext,
    ) -> tuple[list[AgentOutput], list[AgentOutput]]:
        """Drop outputs below the context-dependent confidence threshold."""
        threshold = _get_confidence_threshold(context)
        passing: list[AgentOutput] = []
        filtered: list[AgentOutput] = []
        for out in outputs:
            if out.confidence >= threshold:
                passing.append(out)
            else:
                filtered.append(out)
        return passing, filtered

    # -- step 3: context weighting ------------------------------------------

    def apply_context_weights(
        self,
        outputs: list[AgentOutput],
        context: DecisionContext,
    ) -> list[AgentOutput]:
        """Return *new* AgentOutput instances with weighted confidence.

        The original objects are not mutated.
        """
        weight = _get_mode_weight(context)
        weighted: list[AgentOutput] = []
        for out in outputs:
            new_confidence = min(out.confidence * weight, 1.0)
            weighted.append(out.model_copy(update={"confidence": new_confidence}))
        return weighted

    # -- step 4 + 5: priority + ImpactRank tiebreak -------------------------

    def resolve(
        self,
        outputs: list[AgentOutput],
    ) -> tuple[AgentOutput, list[ConflictResolution]]:
        """Pick the single winning output using priority then ImpactRank.

        Returns ``(winner, list_of_conflict_records)``.
        Raises ``ValueError`` if *outputs* is empty.
        """
        if not outputs:
            raise ValueError("Cannot resolve conflicts with zero agent outputs.")

        if len(outputs) == 1:
            return outputs[0], []

        # Sort: lowest priority number first, then highest ImpactRank, then highest confidence
        def _sort_key(o: AgentOutput) -> tuple[int, float, float]:
            pri = self._priorities.get(o.agent_name, 50)
            return (pri, -o.impact_rank_score, -o.confidence)

        ranked = sorted(outputs, key=_sort_key)
        winner = ranked[0]

        # Build conflict records for every non-winner
        conflicts: list[ConflictResolution] = []
        if len(ranked) > 1:
            losers = ranked[1:]
            winner_pri = self._priorities.get(winner.agent_name, 50)
            for loser in losers:
                loser_pri = self._priorities.get(loser.agent_name, 50)
                if winner_pri < loser_pri:
                    method = "priority"
                elif winner_pri == loser_pri:
                    method = "impact_rank"
                else:
                    method = "confidence"
                conflicts.append(
                    ConflictResolution(
                        conflicting_agents=[winner.agent_name, loser.agent_name],
                        winner=winner.agent_name,
                        resolution_method=method,
                        explanation=(
                            f"{winner.agent_name} (pri={winner_pri}, ir={winner.impact_rank_score:.1f}, "
                            f"conf={winner.confidence:.2f}) beat {loser.agent_name} "
                            f"(pri={loser_pri}, ir={loser.impact_rank_score:.1f}, "
                            f"conf={loser.confidence:.2f}) via {method}."
                        ),
                        discarded_recommendations=[loser.recommendation],
                    )
                )

        return winner, conflicts

    # -- full pipeline (convenience) ----------------------------------------

    def run(
        self,
        outputs: list[AgentOutput],
        context: DecisionContext,
    ) -> tuple[AgentOutput | None, list[ConflictResolution], int]:
        """Execute the full conflict resolution pipeline.

        Returns ``(winner_or_none, conflict_records, filtered_count)``.
        """
        if not outputs:
            return None, [], 0

        filtered_count = 0

        # 1. Veto
        surviving, vetoed = self.apply_player_twin_veto(outputs)
        filtered_count += len(vetoed)

        if not surviving:
            return None, [], filtered_count

        # 2. Confidence threshold
        surviving, low_conf = self.filter_by_confidence(surviving, context)
        filtered_count += len(low_conf)

        if not surviving:
            return None, [], filtered_count

        # 3. Context weighting
        surviving = self.apply_context_weights(surviving, context)

        # 4 + 5. Priority + ImpactRank
        winner, conflicts = self.resolve(surviving)
        return winner, conflicts, filtered_count
