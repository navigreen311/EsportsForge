"""FilmVisualAI — auto replay analysis, play data extraction, and key moment tagging.

Provides automated film study by analyzing video replays, extracting
structured play-by-play data, and tagging key moments for review.
"""

from __future__ import annotations

import logging
from typing import Any

from app.schemas.visionaudio import (
    KeyMoment,
    MomentType,
    PlayData,
    ReplayAnalysis,
)

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Play classification rules
# ---------------------------------------------------------------------------

_PLAY_CLASSIFIERS: dict[str, dict[str, Any]] = {
    "pass_play": {
        "indicators": ["pass_thrown", "route_running", "reception", "incompletion"],
        "sub_types": ["short_pass", "deep_pass", "screen", "play_action"],
    },
    "run_play": {
        "indicators": ["handoff", "run_lane", "tackle_box"],
        "sub_types": ["inside_zone", "outside_zone", "power", "counter", "draw"],
    },
    "scoring_play": {
        "indicators": ["touchdown", "goal", "score_change"],
        "sub_types": ["passing_td", "rushing_td", "field_goal", "goal_scored"],
    },
    "turnover": {
        "indicators": ["interception", "fumble", "turnover_on_downs"],
        "sub_types": ["interception", "fumble", "strip_sack"],
    },
}

# Key moment importance thresholds
_MOMENT_IMPORTANCE: dict[MomentType, float] = {
    MomentType.SCORING_PLAY: 0.95,
    MomentType.TURNOVER: 0.90,
    MomentType.BIG_PLAY: 0.80,
    MomentType.MOMENTUM_SHIFT: 0.75,
    MomentType.FORMATION_CHANGE: 0.50,
    MomentType.SUBSTITUTION: 0.30,
}


class FilmVisualAI:
    """Film study AI for automated replay analysis.

    Processes replay event data, extracts structured play information,
    and identifies key moments for coaching review.
    """

    # ------------------------------------------------------------------
    # Auto analyze replay
    # ------------------------------------------------------------------

    def auto_analyze_replay(
        self,
        events: list[dict[str, Any]],
        title: str = "madden26",
    ) -> ReplayAnalysis:
        """Automatically analyze a replay from raw vision events.

        Segments events into plays, classifies each play, and identifies
        patterns across the replay.
        """
        if not events:
            return ReplayAnalysis(
                plays=[], key_moments=[], patterns=[], summary="No events to analyze.",
            )

        # Segment events into plays
        plays: list[PlayData] = []
        current_play_events: list[dict[str, Any]] = []
        play_number = 0

        for event in events:
            event_type = event.get("event", "")
            current_play_events.append(event)

            if event_type in ("play_end", "dead_ball", "whistle"):
                play_number += 1
                play_data = self.extract_play_data(current_play_events, play_number)
                plays.append(play_data)
                current_play_events = []

        # Handle remaining events as final play
        if current_play_events:
            play_number += 1
            plays.append(self.extract_play_data(current_play_events, play_number))

        # Tag key moments
        key_moments = self.tag_key_moments(plays, events)

        # Identify patterns
        patterns = self._identify_patterns(plays)

        # Build summary
        total_plays = len(plays)
        pass_plays = sum(1 for p in plays if p.play_type == "pass_play")
        run_plays = sum(1 for p in plays if p.play_type == "run_play")
        scoring = sum(1 for p in plays if p.play_type == "scoring_play")

        summary = (
            f"Analyzed {total_plays} plays: {pass_plays} pass, {run_plays} run, "
            f"{scoring} scoring. {len(key_moments)} key moments identified. "
            f"{len(patterns)} patterns detected."
        )

        return ReplayAnalysis(
            plays=plays,
            key_moments=key_moments,
            patterns=patterns,
            summary=summary,
            total_plays=total_plays,
        )

    # ------------------------------------------------------------------
    # Play data extraction
    # ------------------------------------------------------------------

    def extract_play_data(
        self,
        play_events: list[dict[str, Any]],
        play_number: int = 1,
    ) -> PlayData:
        """Extract structured play data from raw events for a single play.

        Classifies the play type, extracts yardage, formations, and result.
        """
        event_types = [e.get("event", "") for e in play_events]

        # Classify play
        play_type = "unknown"
        sub_type = "unknown"
        for pt, rules in _PLAY_CLASSIFIERS.items():
            matches = sum(1 for ind in rules["indicators"] if any(ind in et for et in event_types))
            if matches >= 1:
                play_type = pt
                # Determine sub-type
                for st in rules["sub_types"]:
                    if any(st in et for et in event_types):
                        sub_type = st
                        break
                break

        # Extract metadata from events
        start_time = play_events[0].get("timestamp_sec", 0.0) if play_events else 0.0
        end_time = play_events[-1].get("timestamp_sec", 0.0) if play_events else 0.0
        formation = None
        result = "incomplete"
        yards = 0

        for event in play_events:
            if event.get("event") == "formation_change":
                formation = event.get("detail", "unknown")
            if event.get("result"):
                result = event["result"]
            if event.get("yards"):
                yards = event["yards"]

        confidence = 0.75
        for event in play_events:
            conf = event.get("confidence", 0.75)
            confidence = min(confidence, conf)

        return PlayData(
            play_number=play_number,
            play_type=play_type,
            sub_type=sub_type,
            formation=formation,
            result=result,
            yards=yards,
            start_time_sec=start_time,
            end_time_sec=end_time,
            confidence=round(confidence, 3),
            raw_events=play_events,
        )

    # ------------------------------------------------------------------
    # Key moment tagging
    # ------------------------------------------------------------------

    def tag_key_moments(
        self,
        plays: list[PlayData],
        raw_events: list[dict[str, Any]],
    ) -> list[KeyMoment]:
        """Identify and tag key moments from analyzed plays.

        Looks for scoring plays, turnovers, big plays, momentum shifts,
        and other notable events.
        """
        moments: list[KeyMoment] = []

        for play in plays:
            # Scoring plays
            if play.play_type == "scoring_play":
                moments.append(KeyMoment(
                    moment_type=MomentType.SCORING_PLAY,
                    play_number=play.play_number,
                    timestamp_sec=play.start_time_sec,
                    importance=_MOMENT_IMPORTANCE[MomentType.SCORING_PLAY],
                    description=f"Scoring play: {play.sub_type} for {play.yards} yards",
                ))

            # Turnovers
            elif play.play_type == "turnover":
                moments.append(KeyMoment(
                    moment_type=MomentType.TURNOVER,
                    play_number=play.play_number,
                    timestamp_sec=play.start_time_sec,
                    importance=_MOMENT_IMPORTANCE[MomentType.TURNOVER],
                    description=f"Turnover: {play.sub_type}",
                ))

            # Big plays (20+ yards)
            elif play.yards >= 20:
                moments.append(KeyMoment(
                    moment_type=MomentType.BIG_PLAY,
                    play_number=play.play_number,
                    timestamp_sec=play.start_time_sec,
                    importance=_MOMENT_IMPORTANCE[MomentType.BIG_PLAY],
                    description=f"Big play: {play.yards} yards on {play.play_type}",
                ))

            # Formation changes
            if play.formation:
                moments.append(KeyMoment(
                    moment_type=MomentType.FORMATION_CHANGE,
                    play_number=play.play_number,
                    timestamp_sec=play.start_time_sec,
                    importance=_MOMENT_IMPORTANCE[MomentType.FORMATION_CHANGE],
                    description=f"Formation: {play.formation}",
                ))

        moments.sort(key=lambda m: m.importance, reverse=True)
        return moments

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _identify_patterns(plays: list[PlayData]) -> list[dict[str, Any]]:
        patterns: list[dict[str, Any]] = []

        if len(plays) < 3:
            return patterns

        # Formation tendencies
        formation_counts: dict[str, int] = {}
        for p in plays:
            if p.formation:
                formation_counts[p.formation] = formation_counts.get(p.formation, 0) + 1

        for formation, count in formation_counts.items():
            if count >= 3:
                pct = count / len(plays)
                patterns.append({
                    "pattern": f"Formation tendency: {formation}",
                    "frequency": round(pct, 2),
                    "count": count,
                    "suggestion": f"Opponent uses {formation} {pct:.0%} of plays — prepare a counter.",
                })

        # Play type tendencies
        type_counts: dict[str, int] = {}
        for p in plays:
            type_counts[p.play_type] = type_counts.get(p.play_type, 0) + 1

        for pt, count in type_counts.items():
            pct = count / len(plays)
            if pct >= 0.4:
                patterns.append({
                    "pattern": f"Play type tendency: {pt}",
                    "frequency": round(pct, 2),
                    "count": count,
                    "suggestion": f"{pt} is called {pct:.0%} of the time — predictable.",
                })

        return patterns


# Module-level singleton
film_visual_ai = FilmVisualAI()
