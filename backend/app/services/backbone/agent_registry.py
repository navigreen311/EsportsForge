"""Agent registry — central catalog of all agents available to ForgeCore."""

from __future__ import annotations

import threading
from dataclasses import dataclass, field
from datetime import datetime
from typing import Sequence

from app.schemas.forgecore import AgentStatus, DecisionContext


@dataclass
class AgentRegistryEntry:
    """Metadata for a single registered agent."""

    name: str
    titles: list[str] = field(default_factory=list)  # game titles this agent supports
    capabilities: list[str] = field(default_factory=list)
    priority: int = 50  # 0 = highest priority, 100 = lowest
    status: AgentStatus = AgentStatus.ACTIVE
    last_heartbeat: datetime = field(default_factory=datetime.utcnow)
    metadata: dict = field(default_factory=dict)


class AgentRegistry:
    """Thread-safe in-memory registry of agents.

    In production this would be backed by Redis or a DB.  For the MVP the
    in-memory dict is sufficient and avoids extra infrastructure.
    """

    def __init__(self) -> None:
        self._agents: dict[str, AgentRegistryEntry] = {}
        self._lock = threading.Lock()

    # -- mutations ----------------------------------------------------------

    def register(self, entry: AgentRegistryEntry) -> None:
        """Register (or re-register) an agent."""
        with self._lock:
            self._agents[entry.name] = entry

    def unregister(self, name: str) -> bool:
        """Remove an agent.  Returns True if the agent existed."""
        with self._lock:
            return self._agents.pop(name, None) is not None

    def update_status(self, name: str, status: AgentStatus) -> None:
        """Update an agent's health status."""
        with self._lock:
            if name in self._agents:
                self._agents[name].status = status
                self._agents[name].last_heartbeat = datetime.utcnow()

    def heartbeat(self, name: str) -> None:
        """Record a heartbeat from an agent."""
        with self._lock:
            if name in self._agents:
                self._agents[name].last_heartbeat = datetime.utcnow()

    # -- queries ------------------------------------------------------------

    def get(self, name: str) -> AgentRegistryEntry | None:
        """Look up a single agent by name."""
        return self._agents.get(name)

    def list_all(self) -> list[AgentRegistryEntry]:
        """Return all registered agents (snapshot)."""
        return list(self._agents.values())

    def query(
        self,
        title: str | None = None,
        capability: str | None = None,
        status: AgentStatus | None = None,
    ) -> list[AgentRegistryEntry]:
        """Return agents matching the given filters, sorted by priority (lowest value = highest)."""
        results: list[AgentRegistryEntry] = []
        for entry in self._agents.values():
            if title and title not in entry.titles:
                continue
            if capability and capability not in entry.capabilities:
                continue
            if status is not None and entry.status != status:
                continue
            results.append(entry)
        results.sort(key=lambda e: e.priority)
        return results

    def get_for_decision(
        self,
        title: str,
        context: DecisionContext,
        requested: Sequence[str] | None = None,
    ) -> list[AgentRegistryEntry]:
        """Return the agents that should participate in a decision cycle.

        Filters by:
        1. Title support
        2. ACTIVE or DEGRADED status (offline agents are excluded)
        3. Optional explicit agent list from the request
        """
        eligible = self.query(title=title)
        eligible = [
            a for a in eligible
            if a.status in (AgentStatus.ACTIVE, AgentStatus.DEGRADED)
        ]
        if requested:
            requested_set = set(requested)
            eligible = [a for a in eligible if a.name in requested_set]
        return eligible

    @property
    def count(self) -> int:
        return len(self._agents)
