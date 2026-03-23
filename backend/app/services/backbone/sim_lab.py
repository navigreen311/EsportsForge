"""SimLab AI — scenario sandbox for testing any game state before facing it live.

Builds best-response decision trees so players can explore what-if situations,
understand optimal responses, and prepare for high-pressure moments without
risking a live match.
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

from app.schemas.simulation import (
    DecisionNode,
    DecisionTree,
    GameState,
    Scenario,
    ScenarioType,
    SimRequest,
    SimulationResult,
)

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# In-memory stores
# ---------------------------------------------------------------------------

# user_id -> list of saved scenarios
_user_scenarios: dict[str, list[Scenario]] = {}

# title -> list of pre-built library scenarios
_scenario_library: dict[str, list[Scenario]] = {}

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _make_id() -> str:
    return uuid4().hex[:12]


def _evaluate_state_advantage(state: GameState) -> float:
    """Heuristic win-probability estimate from raw game state.

    Returns a value between 0.0 (certain loss) and 1.0 (certain win)
    from the perspective of the *possessing* team.
    """
    score_diff = (
        (state.score_home - state.score_away)
        if state.possession == "home"
        else (state.score_away - state.score_home)
    )
    # Normalize score diff to a sigmoid-ish 0-1 value
    score_factor = max(0.0, min(1.0, 0.5 + score_diff / 42.0))

    # Time pressure: less time = more volatile
    total_seconds = state.time_remaining + (4 - state.quarter) * 900
    time_factor = min(1.0, total_seconds / 3600.0)

    # Field position advantage (closer to endzone = better)
    field_factor = (state.field_position or 50) / 100.0

    return round(
        0.50 * score_factor + 0.25 * field_factor + 0.25 * time_factor, 4
    )


def _generate_node(
    label: str,
    depth: int,
    max_depth: int,
    branch_factor: int = 2,
) -> DecisionNode:
    """Recursively generate a decision node with children.

    Uses deterministic heuristics; a real implementation would plug into
    a Monte-Carlo tree search or game-engine replay.
    """
    node_id = _make_id()
    # Deeper nodes carry more risk but also more potential reward
    risk = round(min(1.0, 0.2 + 0.15 * depth), 2)
    success = round(max(0.0, 0.85 - 0.12 * depth), 2)

    children: list[DecisionNode] = []
    if depth < max_depth:
        for i in range(branch_factor):
            child_label = f"{label} → option-{i + 1}"
            children.append(
                _generate_node(child_label, depth + 1, max_depth, branch_factor)
            )

    return DecisionNode(
        id=node_id,
        label=label,
        success_rate=success,
        risk=risk,
        children=children,
    )


def _pick_best_path(node: DecisionNode) -> list[str]:
    """Walk the tree greedily, always choosing the highest success-rate child."""
    path = [node.id]
    current = node
    while current.children:
        best = max(current.children, key=lambda n: n.success_rate - n.risk)
        path.append(best.id)
        current = best
    return path


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def create_scenario(game_state: GameState, what_if: str = "") -> Scenario:
    """Create a what-if scenario from a game state snapshot.

    Parameters
    ----------
    game_state:
        Current game state to branch from.
    what_if:
        Natural-language modifier, e.g. "opponent switches to prevent defense".

    Returns
    -------
    Scenario
        Ready to be fed into :func:`simulate`.
    """
    scenario = Scenario(
        id=_make_id(),
        name=what_if or "Unnamed scenario",
        scenario_type=ScenarioType.CUSTOM,
        base_state=game_state,
        what_if=what_if,
        created_at=_now(),
    )
    logger.info("Created scenario %s: '%s'", scenario.id, scenario.what_if)
    return scenario


def simulate(scenario: Scenario, depth: int = 3) -> SimulationResult:
    """Run the simulation and return a decision tree with analysis.

    Parameters
    ----------
    scenario:
        The what-if scenario to simulate.
    depth:
        How deep the decision tree should be (1-6).

    Returns
    -------
    SimulationResult
    """
    tree = build_decision_tree(scenario.what_if or scenario.name, depth=depth)
    tree.scenario_id = scenario.id
    best_path = tree.best_path

    win_prob = _evaluate_state_advantage(scenario.base_state)
    risk = tree.root.risk

    best_response = get_best_response(scenario)

    result = SimulationResult(
        scenario_id=scenario.id,
        decision_tree=tree,
        best_response=best_response,
        win_probability=win_prob,
        risk_assessment=risk,
        analysis=(
            f"Scenario '{scenario.what_if}' analyzed to depth {depth}. "
            f"Win probability: {win_prob:.0%}. "
            f"Best path traverses {len(best_path)} nodes."
        ),
        timestamp=_now(),
    )
    logger.info("Simulation complete for scenario %s", scenario.id)
    return result


def get_best_response(scenario: Scenario) -> str:
    """Return the optimal response summary for a scenario.

    In production this would consult a trained policy network or Monte-Carlo
    search.  For now it returns a heuristic recommendation.
    """
    state = scenario.base_state
    advantage = _evaluate_state_advantage(state)

    if advantage >= 0.65:
        return "Maintain advantage — run the clock, low-risk plays."
    if advantage >= 0.45:
        return "Balanced approach — mix aggression with safe options."
    if advantage >= 0.25:
        return "Aggressive catch-up — high-reward plays, manage risk."
    return "Desperation mode — maximize big-play potential."


def build_decision_tree(situation: str, depth: int = 3) -> DecisionTree:
    """Build an if-then decision tree for the given situation.

    Parameters
    ----------
    situation:
        Description of the game situation.
    depth:
        Levels of branching (1-6).

    Returns
    -------
    DecisionTree
    """
    depth = max(1, min(depth, 6))
    root = _generate_node(label=situation, depth=0, max_depth=depth)
    best_path = _pick_best_path(root)

    return DecisionTree(
        scenario_id="pending",
        root=root,
        depth=depth,
        best_path=best_path,
    )


def get_scenario_library(title: str) -> list[Scenario]:
    """Return pre-built scenario library for a given game title.

    If no library exists yet, generate sensible defaults.
    """
    if title in _scenario_library:
        return _scenario_library[title]

    # Generate starter library for the title
    defaults = _build_default_library(title)
    _scenario_library[title] = defaults
    logger.info("Generated default scenario library for '%s' (%d scenarios)", title, len(defaults))
    return defaults


def save_scenario(user_id: str, scenario: Scenario) -> Scenario:
    """Persist a custom scenario for a user."""
    user_list = _user_scenarios.setdefault(user_id, [])
    # Avoid duplicates by id
    user_list = [s for s in user_list if s.id != scenario.id]
    user_list.append(scenario)
    _user_scenarios[user_id] = user_list
    logger.info("Saved scenario %s for user %s", scenario.id, user_id)
    return scenario


# ---------------------------------------------------------------------------
# Default library builder
# ---------------------------------------------------------------------------

_DEFAULT_SITUATIONS: list[dict[str, Any]] = [
    {
        "name": "4th & Goal, down by 3",
        "type": ScenarioType.CLUTCH,
        "what_if": "4th and goal from the 2-yard line, trailing by 3 in Q4",
        "state": {"quarter": 4, "time_remaining": 120, "score_home": 21, "score_away": 24,
                  "down": 4, "yards_to_go": 2, "field_position": 98},
    },
    {
        "name": "2-Minute Drill, tied game",
        "type": ScenarioType.TWO_MINUTE,
        "what_if": "2-minute warning, tied, own 25-yard line",
        "state": {"quarter": 4, "time_remaining": 120, "score_home": 17, "score_away": 17,
                  "down": 1, "yards_to_go": 10, "field_position": 25},
    },
    {
        "name": "3rd & Long, prevent defense",
        "type": ScenarioType.OFFENSIVE,
        "what_if": "3rd and 12 against prevent defense, up by 4",
        "state": {"quarter": 3, "time_remaining": 450, "score_home": 21, "score_away": 17,
                  "down": 3, "yards_to_go": 12, "field_position": 45},
    },
    {
        "name": "Opponent hurry-up, stop the bleed",
        "type": ScenarioType.DEFENSIVE,
        "what_if": "Opponent in hurry-up, scored last 14 points, your defense is gassed",
        "state": {"quarter": 3, "time_remaining": 300, "score_home": 21, "score_away": 28,
                  "down": 1, "yards_to_go": 10, "field_position": 35},
    },
    {
        "name": "Opening drive, set the tone",
        "type": ScenarioType.OFFENSIVE,
        "what_if": "First drive of the game, establish tempo",
        "state": {"quarter": 1, "time_remaining": 900, "score_home": 0, "score_away": 0,
                  "down": 1, "yards_to_go": 10, "field_position": 25},
    },
]


def _build_default_library(title: str) -> list[Scenario]:
    """Generate starter scenarios for a title."""
    scenarios: list[Scenario] = []
    for cfg in _DEFAULT_SITUATIONS:
        state_data = {"title": title, **cfg["state"]}
        state_data.setdefault("possession", "home")
        scenario = Scenario(
            id=_make_id(),
            name=cfg["name"],
            scenario_type=cfg["type"],
            base_state=GameState(**state_data),
            what_if=cfg["what_if"],
            tags=[title, cfg["type"].value],
            created_at=_now(),
        )
        scenarios.append(scenario)
    return scenarios
