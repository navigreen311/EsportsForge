"""Rollback Manager — snapshot and restore agent configurations.

When the Truth Engine detects that an agent is producing worse advice after
a game patch (or any other cause), the rollback manager can restore the
agent to a previously known-good state automatically.
"""

from __future__ import annotations

import logging
from datetime import datetime
from uuid import UUID

from app.schemas.truth_engine import (
    AgentSnapshot,
    RollbackEvent,
    RollbackHistory,
)

logger = logging.getLogger(__name__)


class RollbackManager:
    """In-memory rollback manager.

    Stores snapshots of agent configurations and supports restoring them.
    Swap the internal dicts for a persistence layer in production.
    """

    def __init__(self) -> None:
        # agent_name -> ordered list of snapshots (newest last)
        self._snapshots: dict[str, list[AgentSnapshot]] = {}
        # agent_name -> current active snapshot id
        self._active_snapshot: dict[str, UUID] = {}
        # All rollback events
        self._events: list[RollbackEvent] = []

    # ------------------------------------------------------------------
    # Snapshots
    # ------------------------------------------------------------------

    def snapshot_agent_state(
        self,
        agent_name: str,
        config: dict,
        accuracy: float = 0.0,
        patch_version: str | None = None,
    ) -> AgentSnapshot:
        """Take a point-in-time snapshot of an agent's configuration."""
        snapshot = AgentSnapshot(
            agent_name=agent_name,
            config=config,
            accuracy_at_snapshot=accuracy,
            patch_version=patch_version,
        )
        self._snapshots.setdefault(agent_name, []).append(snapshot)
        self._active_snapshot[agent_name] = snapshot.id
        logger.info(
            "Snapshot %s created for agent=%s accuracy=%.2f",
            snapshot.id,
            agent_name,
            accuracy,
        )
        return snapshot

    def get_snapshots(self, agent_name: str) -> list[AgentSnapshot]:
        """Return all snapshots for an agent, oldest first."""
        return list(self._snapshots.get(agent_name, []))

    def get_active_snapshot(self, agent_name: str) -> AgentSnapshot | None:
        """Return the currently active snapshot for an agent."""
        active_id = self._active_snapshot.get(agent_name)
        if active_id is None:
            return None
        for snap in self._snapshots.get(agent_name, []):
            if snap.id == active_id:
                return snap
        return None

    # ------------------------------------------------------------------
    # Rollback
    # ------------------------------------------------------------------

    def rollback_agent(
        self,
        agent_name: str,
        reason: str,
        to_snapshot_id: UUID | None = None,
        triggered_by: str = "truth_engine",
    ) -> RollbackEvent:
        """Roll back an agent to a previous snapshot.

        If *to_snapshot_id* is ``None``, rolls back to the most recent
        snapshot with accuracy >= the best recorded accuracy minus a
        small tolerance, or simply the previous snapshot.
        """
        snapshots = self._snapshots.get(agent_name, [])
        if not snapshots:
            raise ValueError(f"No snapshots available for agent '{agent_name}'")

        current_id = self._active_snapshot.get(agent_name)

        if to_snapshot_id is not None:
            target = self._find_snapshot(agent_name, to_snapshot_id)
        else:
            target = self._find_best_previous_snapshot(agent_name)

        if target is None:
            raise ValueError(f"No suitable rollback target for agent '{agent_name}'")

        event = RollbackEvent(
            agent_name=agent_name,
            from_snapshot_id=current_id,
            to_snapshot_id=target.id,
            reason=reason,
            triggered_by=triggered_by,
        )
        self._events.append(event)
        self._active_snapshot[agent_name] = target.id

        logger.warning(
            "ROLLBACK agent=%s from=%s to=%s reason='%s'",
            agent_name,
            current_id,
            target.id,
            reason,
        )
        return event

    def get_rollback_history(self, agent_name: str) -> RollbackHistory:
        """Return the full rollback history for an agent."""
        events = [e for e in self._events if e.agent_name == agent_name]
        current_id = self._active_snapshot.get(agent_name)
        return RollbackHistory(
            agent_name=agent_name,
            events=events,
            current_snapshot_id=current_id,
        )

    def get_recent_rollback_count(
        self,
        agent_name: str,
        since: datetime,
    ) -> int:
        """Count rollbacks for an agent since a given timestamp."""
        return sum(
            1
            for e in self._events
            if e.agent_name == agent_name and e.created_at >= since
        )

    # ------------------------------------------------------------------
    # Internals
    # ------------------------------------------------------------------

    def _find_snapshot(self, agent_name: str, snapshot_id: UUID) -> AgentSnapshot | None:
        for snap in self._snapshots.get(agent_name, []):
            if snap.id == snapshot_id:
                return snap
        return None

    def _find_best_previous_snapshot(self, agent_name: str) -> AgentSnapshot | None:
        """Pick the best rollback target — highest accuracy that is not current."""
        snapshots = self._snapshots.get(agent_name, [])
        current_id = self._active_snapshot.get(agent_name)

        candidates = [s for s in snapshots if s.id != current_id]
        if not candidates:
            return None

        # Prefer the one with highest recorded accuracy
        return max(candidates, key=lambda s: s.accuracy_at_snapshot)
