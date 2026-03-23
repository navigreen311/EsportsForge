"""GrappleGraph — sequence-level grappling chain model with decision trees and submission awareness.

Models every grapple position as a node in a directed graph with transitions,
available strikes, submissions, and escapes. Provides submission chain awareness
for multi-step finish sequences.
"""

from __future__ import annotations

import logging
from typing import Any

from app.schemas.ufc5.combat import (
    GrapplePosition,
    GrapplePositionType,
    GrappleTransition,
    SubmissionChain,
    SubmissionType,
    StrikeType,
)

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Transition graph — defines all legal transitions between positions
# ---------------------------------------------------------------------------

_TRANSITIONS: list[dict[str, Any]] = [
    # Standing -> Takedowns
    {
        "from": GrapplePositionType.STANDING,
        "to": GrapplePositionType.SINGLE_LEG,
        "input": "L2+Square (shoot single)",
        "cost": 8.0, "rate": 0.65, "denial": 18, "sub": False,
    },
    {
        "from": GrapplePositionType.STANDING,
        "to": GrapplePositionType.DOUBLE_LEG,
        "input": "L2+Triangle (shoot double)",
        "cost": 10.0, "rate": 0.60, "denial": 20, "sub": False,
    },
    {
        "from": GrapplePositionType.STANDING,
        "to": GrapplePositionType.CLINCH,
        "input": "L1+L2 (clinch entry)",
        "cost": 5.0, "rate": 0.75, "denial": 15, "sub": False,
    },
    {
        "from": GrapplePositionType.STANDING,
        "to": GrapplePositionType.THAI_CLINCH,
        "input": "L1+L2+Up (thai clinch)",
        "cost": 6.0, "rate": 0.60, "denial": 18, "sub": False,
    },
    # Single leg chain
    {
        "from": GrapplePositionType.SINGLE_LEG,
        "to": GrapplePositionType.HALF_GUARD_TOP,
        "input": "R2+Forward (finish takedown)",
        "cost": 6.0, "rate": 0.70, "denial": 15, "sub": False,
    },
    {
        "from": GrapplePositionType.SINGLE_LEG,
        "to": GrapplePositionType.BACK_CONTROL,
        "input": "R2+Right (scramble to back)",
        "cost": 8.0, "rate": 0.35, "denial": 20, "sub": False,
    },
    {
        "from": GrapplePositionType.SINGLE_LEG,
        "to": GrapplePositionType.STANDING,
        "input": "L2 (disengage)",
        "cost": 4.0, "rate": 0.80, "denial": 10, "sub": False,
    },
    # Double leg chain
    {
        "from": GrapplePositionType.DOUBLE_LEG,
        "to": GrapplePositionType.FULL_GUARD_TOP,
        "input": "R2+Forward (finish in guard)",
        "cost": 7.0, "rate": 0.70, "denial": 15, "sub": False,
    },
    {
        "from": GrapplePositionType.DOUBLE_LEG,
        "to": GrapplePositionType.SIDE_CONTROL_TOP,
        "input": "R2+Right (finish to side control)",
        "cost": 9.0, "rate": 0.45, "denial": 20, "sub": False,
    },
    # Clinch chains
    {
        "from": GrapplePositionType.CLINCH,
        "to": GrapplePositionType.STANDING,
        "input": "L2 (break clinch)",
        "cost": 3.0, "rate": 0.85, "denial": 10, "sub": False,
    },
    {
        "from": GrapplePositionType.CLINCH,
        "to": GrapplePositionType.DOUBLE_LEG,
        "input": "R2+Down (trip)",
        "cost": 7.0, "rate": 0.55, "denial": 18, "sub": False,
    },
    {
        "from": GrapplePositionType.THAI_CLINCH,
        "to": GrapplePositionType.STANDING,
        "input": "L2 (break)",
        "cost": 3.0, "rate": 0.80, "denial": 12, "sub": False,
    },
    # Guard positions
    {
        "from": GrapplePositionType.FULL_GUARD_TOP,
        "to": GrapplePositionType.HALF_GUARD_TOP,
        "input": "R2+Right (pass to half guard)",
        "cost": 8.0, "rate": 0.55, "denial": 22, "sub": False,
    },
    {
        "from": GrapplePositionType.FULL_GUARD_TOP,
        "to": GrapplePositionType.STANDING,
        "input": "L2 (stand up)",
        "cost": 5.0, "rate": 0.75, "denial": 15, "sub": False,
    },
    {
        "from": GrapplePositionType.FULL_GUARD_BOTTOM,
        "to": GrapplePositionType.STANDING,
        "input": "L2+Up (technical stand up)",
        "cost": 10.0, "rate": 0.40, "denial": 25, "sub": False,
    },
    {
        "from": GrapplePositionType.FULL_GUARD_BOTTOM,
        "to": GrapplePositionType.BUTTERFLY_GUARD,
        "input": "R2+Down (butterfly guard)",
        "cost": 5.0, "rate": 0.65, "denial": 15, "sub": False,
    },
    # Half guard
    {
        "from": GrapplePositionType.HALF_GUARD_TOP,
        "to": GrapplePositionType.SIDE_CONTROL_TOP,
        "input": "R2+Right (pass to side control)",
        "cost": 7.0, "rate": 0.55, "denial": 20, "sub": False,
    },
    {
        "from": GrapplePositionType.HALF_GUARD_TOP,
        "to": GrapplePositionType.MOUNT_TOP,
        "input": "R2+Up (advance to mount)",
        "cost": 10.0, "rate": 0.35, "denial": 25, "sub": False,
    },
    {
        "from": GrapplePositionType.HALF_GUARD_BOTTOM,
        "to": GrapplePositionType.FULL_GUARD_BOTTOM,
        "input": "R2+Down (recover guard)",
        "cost": 7.0, "rate": 0.50, "denial": 20, "sub": False,
    },
    {
        "from": GrapplePositionType.HALF_GUARD_BOTTOM,
        "to": GrapplePositionType.STANDING,
        "input": "L2+Up (stand up)",
        "cost": 12.0, "rate": 0.30, "denial": 28, "sub": False,
    },
    # Side control
    {
        "from": GrapplePositionType.SIDE_CONTROL_TOP,
        "to": GrapplePositionType.MOUNT_TOP,
        "input": "R2+Up (advance to mount)",
        "cost": 8.0, "rate": 0.50, "denial": 22, "sub": False,
    },
    {
        "from": GrapplePositionType.SIDE_CONTROL_TOP,
        "to": GrapplePositionType.BACK_CONTROL,
        "input": "R2+Right (take back)",
        "cost": 10.0, "rate": 0.40, "denial": 25, "sub": False,
    },
    {
        "from": GrapplePositionType.SIDE_CONTROL_BOTTOM,
        "to": GrapplePositionType.HALF_GUARD_BOTTOM,
        "input": "R2+Down (recover half guard)",
        "cost": 8.0, "rate": 0.45, "denial": 22, "sub": False,
    },
    # Mount
    {
        "from": GrapplePositionType.MOUNT_TOP,
        "to": GrapplePositionType.BACK_CONTROL,
        "input": "R2+Right (take back on scramble)",
        "cost": 8.0, "rate": 0.45, "denial": 20, "sub": False,
    },
    {
        "from": GrapplePositionType.MOUNT_BOTTOM,
        "to": GrapplePositionType.HALF_GUARD_BOTTOM,
        "input": "R2+Down (buck to half guard)",
        "cost": 10.0, "rate": 0.35, "denial": 25, "sub": False,
    },
    # Back control
    {
        "from": GrapplePositionType.BACK_CONTROL,
        "to": GrapplePositionType.MOUNT_TOP,
        "input": "R2+Up (roll to mount if they escape hooks)",
        "cost": 6.0, "rate": 0.50, "denial": 18, "sub": False,
    },
    {
        "from": GrapplePositionType.BACK_CONTROL_BOTTOM,
        "to": GrapplePositionType.HALF_GUARD_BOTTOM,
        "input": "R2+Down (escape to half guard)",
        "cost": 12.0, "rate": 0.30, "denial": 30, "sub": False,
    },
    {
        "from": GrapplePositionType.BACK_CONTROL_BOTTOM,
        "to": GrapplePositionType.STANDING,
        "input": "L2+Up (stand up in back control)",
        "cost": 15.0, "rate": 0.20, "denial": 35, "sub": False,
    },
    # Butterfly guard
    {
        "from": GrapplePositionType.BUTTERFLY_GUARD,
        "to": GrapplePositionType.STANDING,
        "input": "L2+Up (sweep to standing)",
        "cost": 8.0, "rate": 0.55, "denial": 18, "sub": False,
    },
    {
        "from": GrapplePositionType.BUTTERFLY_GUARD,
        "to": GrapplePositionType.FULL_GUARD_BOTTOM,
        "input": "R2+Down (return to full guard)",
        "cost": 4.0, "rate": 0.75, "denial": 12, "sub": False,
    },
]

# Submissions available from each position
_POSITION_SUBMISSIONS: dict[GrapplePositionType, list[SubmissionType]] = {
    GrapplePositionType.FULL_GUARD_BOTTOM: [
        SubmissionType.TRIANGLE,
        SubmissionType.ARMBAR,
        SubmissionType.KIMURA,
        SubmissionType.GUILLOTINE,
        SubmissionType.OMOPLATA,
    ],
    GrapplePositionType.HALF_GUARD_BOTTOM: [
        SubmissionType.KIMURA,
        SubmissionType.GUILLOTINE,
    ],
    GrapplePositionType.MOUNT_TOP: [
        SubmissionType.ARMBAR,
        SubmissionType.ARM_TRIANGLE,
        SubmissionType.AMERICANA,
    ] if hasattr(SubmissionType, "AMERICANA") else [
        SubmissionType.ARMBAR,
        SubmissionType.ARM_TRIANGLE,
    ],
    GrapplePositionType.SIDE_CONTROL_TOP: [
        SubmissionType.KIMURA,
        SubmissionType.ARM_TRIANGLE,
    ],
    GrapplePositionType.BACK_CONTROL: [
        SubmissionType.REAR_NAKED_CHOKE,
        SubmissionType.NECK_CRANK,
    ],
    GrapplePositionType.RUBBER_GUARD: [
        SubmissionType.TRIANGLE,
        SubmissionType.GOGOPLATA,
        SubmissionType.OMOPLATA,
    ],
    GrapplePositionType.CLINCH: [
        SubmissionType.GUILLOTINE,
    ],
    GrapplePositionType.THAI_CLINCH: [
        SubmissionType.GUILLOTINE,
    ],
    GrapplePositionType.CRUCIFIX: [
        SubmissionType.NECK_CRANK,
    ],
}

# Ground strikes available per position
_POSITION_STRIKES: dict[GrapplePositionType, list[StrikeType]] = {
    GrapplePositionType.FULL_GUARD_TOP: [
        StrikeType.CROSS, StrikeType.HOOK, StrikeType.ELBOW,
    ],
    GrapplePositionType.HALF_GUARD_TOP: [
        StrikeType.CROSS, StrikeType.ELBOW, StrikeType.HOOK,
    ],
    GrapplePositionType.SIDE_CONTROL_TOP: [
        StrikeType.ELBOW, StrikeType.KNEE, StrikeType.HOOK,
    ],
    GrapplePositionType.MOUNT_TOP: [
        StrikeType.CROSS, StrikeType.HOOK, StrikeType.ELBOW, StrikeType.UPPERCUT,
    ],
    GrapplePositionType.BACK_CONTROL: [
        StrikeType.HOOK,
    ],
    GrapplePositionType.CLINCH: [
        StrikeType.KNEE, StrikeType.UPPERCUT, StrikeType.ELBOW,
    ],
    GrapplePositionType.THAI_CLINCH: [
        StrikeType.KNEE, StrikeType.ELBOW,
    ],
    GrapplePositionType.CRUCIFIX: [
        StrikeType.ELBOW, StrikeType.HOOK,
    ],
}

# Stamina drain per second in each position (top / dominant positions drain less)
_POSITION_DRAIN: dict[GrapplePositionType, float] = {
    GrapplePositionType.STANDING: 0.0,
    GrapplePositionType.CLINCH: 1.0,
    GrapplePositionType.THAI_CLINCH: 1.2,
    GrapplePositionType.SINGLE_LEG: 2.0,
    GrapplePositionType.DOUBLE_LEG: 2.0,
    GrapplePositionType.FULL_GUARD_TOP: 0.5,
    GrapplePositionType.FULL_GUARD_BOTTOM: 1.5,
    GrapplePositionType.HALF_GUARD_TOP: 0.4,
    GrapplePositionType.HALF_GUARD_BOTTOM: 1.8,
    GrapplePositionType.SIDE_CONTROL_TOP: 0.3,
    GrapplePositionType.SIDE_CONTROL_BOTTOM: 2.0,
    GrapplePositionType.MOUNT_TOP: 0.3,
    GrapplePositionType.MOUNT_BOTTOM: 2.5,
    GrapplePositionType.BACK_CONTROL: 0.4,
    GrapplePositionType.BACK_CONTROL_BOTTOM: 2.8,
    GrapplePositionType.RUBBER_GUARD: 1.0,
    GrapplePositionType.BUTTERFLY_GUARD: 1.2,
    GrapplePositionType.CRUCIFIX: 0.2,
}


def _build_transition(t: dict[str, Any]) -> GrappleTransition:
    return GrappleTransition(
        from_position=t["from"],
        to_position=t["to"],
        input_sequence=t["input"],
        stamina_cost=t["cost"],
        success_rate=t["rate"],
        denial_window_frames=t["denial"],
        leads_to_submission=t["sub"],
    )


class GrappleGraph:
    """Sequence-level grappling chain model.

    Every position is a node with a decision tree of transitions,
    available strikes, submissions, and escapes. Provides submission
    chain awareness for multi-step finish sequences.
    """

    def __init__(self) -> None:
        self._transitions = [_build_transition(t) for t in _TRANSITIONS]
        self._graph: dict[GrapplePositionType, list[GrappleTransition]] = {}
        for t in self._transitions:
            self._graph.setdefault(t.from_position, []).append(t)

    def get_position_tree(self, position: GrapplePositionType) -> GrapplePosition:
        """Return the full decision tree for a given grapple position."""
        transitions = self._graph.get(position, [])
        is_dominant = position in {
            GrapplePositionType.MOUNT_TOP,
            GrapplePositionType.SIDE_CONTROL_TOP,
            GrapplePositionType.BACK_CONTROL,
            GrapplePositionType.HALF_GUARD_TOP,
            GrapplePositionType.CRUCIFIX,
        }

        # Separate transitions from escapes
        if "bottom" in position.value or position in {
            GrapplePositionType.FULL_GUARD_BOTTOM,
            GrapplePositionType.BACK_CONTROL_BOTTOM,
        }:
            escapes = transitions
            advances = []
        else:
            advances = transitions
            escapes = []

        submissions = _POSITION_SUBMISSIONS.get(position, [])
        strikes = _POSITION_STRIKES.get(position, [])
        drain = _POSITION_DRAIN.get(position, 1.0)

        priority = self._determine_priority(position, is_dominant, submissions)

        return GrapplePosition(
            position=position,
            is_dominant=is_dominant,
            available_transitions=advances,
            available_strikes=strikes,
            available_submissions=submissions,
            escape_options=escapes,
            priority_action=priority,
            stamina_drain_per_second=drain,
        )

    def get_all_positions(self) -> list[GrapplePosition]:
        """Return decision trees for all known positions."""
        return [self.get_position_tree(p) for p in GrapplePositionType]

    def get_submission_chain(
        self,
        target_sub: SubmissionType,
        start_position: GrapplePositionType = GrapplePositionType.STANDING,
    ) -> SubmissionChain | None:
        """
        Build a submission chain from start position to the target submission.

        Returns None if no valid chain exists.
        """
        # Find which positions offer this submission
        target_positions = [
            pos for pos, subs in _POSITION_SUBMISSIONS.items()
            if target_sub in subs
        ]
        if not target_positions:
            return None

        # BFS to find shortest path from start to a target position
        best_path: list[GrappleTransition] | None = None
        best_target: GrapplePositionType | None = None

        for target_pos in target_positions:
            path = self._bfs_path(start_position, target_pos)
            if path is not None and (best_path is None or len(path) < len(best_path)):
                best_path = path
                best_target = target_pos

        if best_path is None or best_target is None:
            return None

        # Find alternative submissions from the same position
        alternatives = [
            s for s in _POSITION_SUBMISSIONS.get(best_target, [])
            if s != target_sub
        ]

        gate_count = self._estimate_gates(target_sub)
        stamina_threshold = self._stamina_threshold_for_sub(target_sub)

        return SubmissionChain(
            entry_position=best_target,
            submission=target_sub,
            setup_transitions=best_path,
            gate_count=gate_count,
            stamina_threshold=stamina_threshold,
            chain_alternatives=alternatives,
        )

    def get_all_submission_chains(
        self,
        start: GrapplePositionType = GrapplePositionType.STANDING,
    ) -> list[SubmissionChain]:
        """Generate chains for all available submissions from a starting position."""
        chains: list[SubmissionChain] = []
        seen: set[SubmissionType] = set()
        for subs in _POSITION_SUBMISSIONS.values():
            for sub in subs:
                if sub not in seen:
                    seen.add(sub)
                    chain = self.get_submission_chain(sub, start)
                    if chain is not None:
                        chains.append(chain)
        return chains

    def get_optimal_path(
        self,
        start: GrapplePositionType,
        goal: GrapplePositionType,
    ) -> list[GrappleTransition]:
        """Find the optimal transition path between two positions."""
        path = self._bfs_path(start, goal)
        return path if path is not None else []

    # --- private helpers ---

    def _bfs_path(
        self,
        start: GrapplePositionType,
        goal: GrapplePositionType,
    ) -> list[GrappleTransition] | None:
        """Breadth-first search for shortest transition path."""
        if start == goal:
            return []
        visited: set[GrapplePositionType] = {start}
        queue: list[tuple[GrapplePositionType, list[GrappleTransition]]] = [
            (start, [])
        ]
        while queue:
            current, path = queue.pop(0)
            for t in self._graph.get(current, []):
                if t.to_position in visited:
                    continue
                new_path = path + [t]
                if t.to_position == goal:
                    return new_path
                visited.add(t.to_position)
                queue.append((t.to_position, new_path))
        return None

    def _determine_priority(
        self,
        position: GrapplePositionType,
        is_dominant: bool,
        submissions: list[SubmissionType],
    ) -> str:
        if position == GrapplePositionType.STANDING:
            return "Control distance and pick shots"
        if position == GrapplePositionType.BACK_CONTROL:
            return "Lock in rear naked choke"
        if position == GrapplePositionType.MOUNT_TOP:
            return "Ground and pound or advance to armbar"
        if is_dominant:
            return "Advance position or attack with ground strikes"
        if submissions:
            return "Threaten submission to create scramble"
        if "bottom" in position.value:
            return "Work to stand up or sweep"
        return "Advance to dominant position"

    def _estimate_gates(self, sub: SubmissionType) -> int:
        """Estimate the number of submission minigame gates."""
        gate_map = {
            SubmissionType.REAR_NAKED_CHOKE: 3,
            SubmissionType.GUILLOTINE: 2,
            SubmissionType.ARM_TRIANGLE: 3,
            SubmissionType.TRIANGLE: 3,
            SubmissionType.ARMBAR: 2,
            SubmissionType.KIMURA: 2,
            SubmissionType.OMOPLATA: 3,
            SubmissionType.DARCE: 3,
            SubmissionType.ANACONDA: 3,
            SubmissionType.HEEL_HOOK: 2,
            SubmissionType.KNEEBAR: 2,
            SubmissionType.NECK_CRANK: 2,
            SubmissionType.TWISTER: 4,
            SubmissionType.GOGOPLATA: 4,
        }
        return gate_map.get(sub, 3)

    def _stamina_threshold_for_sub(self, sub: SubmissionType) -> float:
        """Opponent stamina below which this submission's chance spikes."""
        high_stamina_subs = {
            SubmissionType.REAR_NAKED_CHOKE,
            SubmissionType.ARM_TRIANGLE,
        }
        if sub in high_stamina_subs:
            return 45.0
        return 35.0
