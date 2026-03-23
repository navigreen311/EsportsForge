"""ScoutBot — Opponent scouting and dossier generation.

Builds full opponent dossiers from game history: play frequency,
situational tendencies, and exploitable weaknesses.
"""

from __future__ import annotations

import logging
from collections import Counter
from datetime import datetime
from typing import Any

from app.schemas.opponent import (
    ExploitableWeakness,
    GameSummary,
    OpponentDossier,
    PlayFrequencyReport,
    Tendency,
    TendencyType,
)

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# In-memory store (will be replaced with DB / cache later)
# ---------------------------------------------------------------------------
_opponent_store: dict[str, list[dict[str, Any]]] = {}


def _load_opponent_games(opponent_id: str, title: str) -> list[dict[str, Any]]:
    """Load raw game data for an opponent.

    Returns the last 20 games from the store. In production this hits
    ForgeDataFabric / external APIs.
    """
    key = f"{opponent_id}:{title}"
    games = _opponent_store.get(key, [])
    return games[-20:]


def _seed_opponent_data(opponent_id: str, title: str, games: list[dict[str, Any]]) -> None:
    """Seed raw game data (used by tests and bootstrap scripts)."""
    key = f"{opponent_id}:{title}"
    _opponent_store[key] = games


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def scout_opponent(opponent_id: str, title: str) -> OpponentDossier:
    """Build a full scouting dossier for *opponent_id* in *title*.

    Pulls the last 20 games, analyses play frequency, detects tendencies,
    and maps weaknesses into an ``OpponentDossier``.
    """
    raw_games = _load_opponent_games(opponent_id, title)

    recent_games = [
        GameSummary(
            game_id=g.get("game_id", ""),
            opponent_id=opponent_id,
            title=title,
            result=g.get("result", "unknown"),
            score=g.get("score", ""),
            key_plays=g.get("key_plays", []),
            timestamp=g.get("timestamp", datetime.utcnow()),
        )
        for g in raw_games
    ]

    wins = sum(1 for g in recent_games if g.result == "win")
    losses = sum(1 for g in recent_games if g.result == "loss")
    draws = len(recent_games) - wins - losses

    play_freq = analyze_play_frequency(raw_games, opponent_id)
    tendencies = detect_tendencies(raw_games)
    weaknesses = get_weakness_map(raw_games)

    threat = _compute_threat_level(wins, losses, draws, weaknesses)

    return OpponentDossier(
        opponent_id=opponent_id,
        title=title,
        recent_games=recent_games,
        record={"wins": wins, "losses": losses, "draws": draws},
        play_frequency=play_freq,
        tendencies=tendencies,
        weaknesses=weaknesses,
        overall_threat_level=threat,
    )


def analyze_play_frequency(
    opponent_data: list[dict[str, Any]],
    opponent_id: str = "",
) -> PlayFrequencyReport:
    """Analyse what an opponent runs most often.

    Returns a ``PlayFrequencyReport`` with top plays, formation distribution,
    and per-situation breakdowns.
    """
    all_plays: list[str] = []
    formations: list[str] = []
    situation_plays: dict[str, list[str]] = {}

    for game in opponent_data:
        for play in game.get("plays", []):
            play_name = play.get("name", "unknown")
            all_plays.append(play_name)

            formation = play.get("formation", "")
            if formation:
                formations.append(formation)

            situation = play.get("situation", "general")
            situation_plays.setdefault(situation, []).append(play_name)

    total = len(all_plays)
    play_counts = Counter(all_plays)
    top_plays = [
        {"play": name, "count": count, "frequency": round(count / max(total, 1), 3)}
        for name, count in play_counts.most_common(10)
    ]

    formation_counts = Counter(formations)
    formation_total = max(len(formations), 1)
    formation_dist = {
        f: round(c / formation_total, 3) for f, c in formation_counts.most_common()
    }

    situation_breakdown: dict[str, list[dict[str, Any]]] = {}
    for sit, plays in situation_plays.items():
        sit_counts = Counter(plays)
        sit_total = max(len(plays), 1)
        situation_breakdown[sit] = [
            {"play": n, "count": c, "frequency": round(c / sit_total, 3)}
            for n, c in sit_counts.most_common(5)
        ]

    return PlayFrequencyReport(
        opponent_id=opponent_id,
        total_plays=total,
        top_plays=top_plays,
        formation_distribution=formation_dist,
        situation_breakdown=situation_breakdown,
    )


def detect_tendencies(opponent_data: list[dict[str, Any]]) -> list[Tendency]:
    """Detect situational tendencies from opponent game data.

    Looks for repeated patterns in specific situations (e.g. always blitzing
    on 3rd & long) and returns them ranked by confidence.
    """
    situation_actions: dict[str, list[str]] = {}

    for game in opponent_data:
        for play in game.get("plays", []):
            situation = play.get("situation", "")
            action = play.get("name", "")
            if situation and action:
                situation_actions.setdefault(situation, []).append(action)

    tendencies: list[Tendency] = []
    for situation, actions in situation_actions.items():
        action_counts = Counter(actions)
        total = len(actions)
        if total < 2:
            continue

        most_common_action, count = action_counts.most_common(1)[0]
        frequency = count / total
        if frequency < 0.3:
            continue

        confidence = min(1.0, frequency * (min(total, 20) / 20))

        tendency_type = _classify_tendency(situation)
        tendencies.append(
            Tendency(
                tendency_type=tendency_type,
                situation=situation,
                action=most_common_action,
                frequency=round(frequency, 3),
                sample_size=total,
                confidence=round(confidence, 3),
            )
        )

    tendencies.sort(key=lambda t: t.confidence, reverse=True)
    return tendencies


def get_weakness_map(opponent_data: list[dict[str, Any]]) -> list[ExploitableWeakness]:
    """Identify exploitable weaknesses from opponent game data.

    Scans for areas where the opponent consistently underperforms or
    gives up big plays.
    """
    weakness_signals: dict[str, list[float]] = {}

    for game in opponent_data:
        for weakness in game.get("weaknesses", []):
            area = weakness.get("area", "general")
            severity = weakness.get("severity", 0.5)
            weakness_signals.setdefault(area, []).append(severity)

    weaknesses: list[ExploitableWeakness] = []
    for area, severities in weakness_signals.items():
        avg_severity = sum(severities) / len(severities)
        if avg_severity < 0.2:
            continue

        weaknesses.append(
            ExploitableWeakness(
                area=area,
                description=f"Consistent vulnerability in {area} across {len(severities)} games",
                severity=round(avg_severity, 3),
                suggested_exploit=f"Attack {area} with high-percentage plays",
            )
        )

    weaknesses.sort(key=lambda w: w.severity, reverse=True)
    return weaknesses


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _compute_threat_level(
    wins: int, losses: int, draws: int, weaknesses: list[ExploitableWeakness],
) -> float:
    """Compute a 0-1 threat level from record and weaknesses."""
    total = wins + losses + draws
    if total == 0:
        return 0.5

    win_rate = wins / total
    avg_weakness = (
        sum(w.severity for w in weaknesses) / len(weaknesses) if weaknesses else 0.0
    )
    # Higher win-rate = higher threat; more/worse weaknesses = lower threat
    threat = (win_rate * 0.7) + ((1 - avg_weakness) * 0.3)
    return round(min(1.0, max(0.0, threat)), 3)


def _classify_tendency(situation: str) -> TendencyType:
    """Map a situation string to a TendencyType."""
    s = situation.lower()
    if "3rd" in s or "4th" in s:
        return TendencyType.SITUATIONAL
    if "red zone" in s or "goal" in s:
        return TendencyType.OFFENSIVE
    if "prevent" in s or "zone" in s:
        return TendencyType.DEFENSIVE
    if "2 min" in s or "late" in s or "end" in s:
        return TendencyType.LATE_GAME
    if "open" in s or "first" in s or "start" in s:
        return TendencyType.EARLY_GAME
    if "momentum" in s or "streak" in s:
        return TendencyType.MOMENTUM
    return TendencyType.SITUATIONAL
