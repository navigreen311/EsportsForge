"""Decision context model and builder for ForgeCore."""

from __future__ import annotations

from typing import Any

from app.schemas.forgecore import DecisionContext, GameMode, PressureState


class ContextBuilder:
    """Fluent builder that constructs a ``DecisionContext`` from session data.

    Usage::

        ctx = (
            ContextBuilder()
            .mode(GameMode.TOURNAMENT)
            .pressure(PressureState.CRITICAL)
            .time("0:42 Q4")
            .opponent({"tendency": "blitz_heavy", "blitz_rate": 0.68})
            .player({"fatigue": 0.3, "tilt": 0.1})
            .session("sess-abc-123")
            .build()
        )
    """

    def __init__(self) -> None:
        self._mode: GameMode = GameMode.RANKED
        self._pressure: PressureState = PressureState.MEDIUM
        self._time_context: str | None = None
        self._opponent_info: dict[str, Any] = {}
        self._player_state: dict[str, Any] = {}
        self._session_id: str | None = None
        self._extra: dict[str, Any] = {}

    # -- fluent setters -----------------------------------------------------

    def mode(self, mode: GameMode) -> ContextBuilder:
        self._mode = mode
        return self

    def pressure(self, pressure: PressureState) -> ContextBuilder:
        self._pressure = pressure
        return self

    def time(self, time_context: str) -> ContextBuilder:
        self._time_context = time_context
        return self

    def opponent(self, info: dict[str, Any]) -> ContextBuilder:
        self._opponent_info = info
        return self

    def player(self, state: dict[str, Any]) -> ContextBuilder:
        self._player_state = state
        return self

    def session(self, session_id: str) -> ContextBuilder:
        self._session_id = session_id
        return self

    def extra(self, data: dict[str, Any]) -> ContextBuilder:
        self._extra = data
        return self

    # -- build --------------------------------------------------------------

    def build(self) -> DecisionContext:
        """Return an immutable ``DecisionContext``."""
        return DecisionContext(
            mode=self._mode,
            pressure_state=self._pressure,
            time_context=self._time_context,
            opponent_info=self._opponent_info,
            player_state=self._player_state,
            session_id=self._session_id,
            extra=self._extra,
        )

    # -- convenience factory ------------------------------------------------

    @classmethod
    def from_session_data(cls, data: dict[str, Any]) -> DecisionContext:
        """Build a context directly from a flat session-data dictionary.

        Expected keys (all optional):
            mode, pressure_state, time_context, opponent_info,
            player_state, session_id, extra
        """
        builder = cls()

        if "mode" in data:
            builder.mode(GameMode(data["mode"]))
        if "pressure_state" in data:
            builder.pressure(PressureState(data["pressure_state"]))
        if "time_context" in data:
            builder.time(data["time_context"])
        if "opponent_info" in data:
            builder.opponent(data["opponent_info"])
        if "player_state" in data:
            builder.player(data["player_state"])
        if "session_id" in data:
            builder.session(data["session_id"])
        if "extra" in data:
            builder.extra(data["extra"])

        return builder.build()
