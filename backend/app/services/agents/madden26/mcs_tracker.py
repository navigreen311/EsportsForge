"""MCS Circuit Tracker — Tournament bracket intelligence synced to official schedule.

Tracks MCS (Madden Championship Series) tournaments, scouting opponents,
and generating tournament-specific gameplans.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.game_session import GameSession, GameMode

from app.schemas.madden26.tournament import (
    Bracket,
    BracketMatch,
    BracketRound,
    FormReport,
    FormTrend,
    MatchStatus,
    OpponentPrep,
    RecentMatch,
    TournamentBook,
    TournamentPlay,
    TournamentStatus,
)


# ---------------------------------------------------------------------------
# Simulated data store (replaced by real DB / MCS API in production)
# ---------------------------------------------------------------------------

_TOURNAMENTS: dict[str, dict] = {
    "mcs-2026-qualifier-1": {
        "tournament_id": "mcs-2026-qualifier-1",
        "tournament_name": "MCS 2026 Online Qualifier #1",
        "status": TournamentStatus.IN_PROGRESS,
        "total_rounds": 4,
        "current_round": 2,
        "participants_count": 16,
        "rounds": [
            {
                "round_number": 1,
                "round_name": "Round of 16",
                "matches": [
                    {"match_id": "m1", "round_number": 1, "player_a_id": "p1", "player_a_name": "ProPlayer1", "player_b_id": "p2", "player_b_name": "ProPlayer2", "winner_id": "p1", "score_a": 28, "score_b": 14, "status": "completed"},
                    {"match_id": "m2", "round_number": 1, "player_a_id": "p3", "player_a_name": "ProPlayer3", "player_b_id": "p4", "player_b_name": "ProPlayer4", "winner_id": "p3", "score_a": 21, "score_b": 17, "status": "completed"},
                ],
            },
            {
                "round_number": 2,
                "round_name": "Quarterfinals",
                "matches": [
                    {"match_id": "m5", "round_number": 2, "player_a_id": "p1", "player_a_name": "ProPlayer1", "player_b_id": "p3", "player_b_name": "ProPlayer3", "status": "pending"},
                ],
            },
        ],
    },
}

_PLAYER_FORM: dict[str, dict] = {
    "p1": {
        "opponent_id": "p1",
        "opponent_name": "ProPlayer1",
        "last_5": "4-1",
        "last_10": "7-3",
        "win_streak": 3,
        "loss_streak": 0,
        "avg_for": 24.5,
        "avg_against": 16.2,
        "recent": [
            {"opponent_name": "ProPlayer2", "result": "W", "score": "28-14", "date": "2026-03-20", "tournament_name": "MCS Qualifier #1"},
            {"opponent_name": "RandomPlayer", "result": "W", "score": "35-10", "date": "2026-03-18"},
            {"opponent_name": "TopDog", "result": "L", "score": "14-21", "date": "2026-03-15"},
            {"opponent_name": "NewComer", "result": "W", "score": "31-7", "date": "2026-03-12"},
            {"opponent_name": "Veteran", "result": "W", "score": "17-14", "date": "2026-03-10"},
        ],
    },
    "p3": {
        "opponent_id": "p3",
        "opponent_name": "ProPlayer3",
        "last_5": "3-2",
        "last_10": "6-4",
        "win_streak": 1,
        "loss_streak": 0,
        "avg_for": 20.1,
        "avg_against": 18.5,
        "recent": [
            {"opponent_name": "ProPlayer4", "result": "W", "score": "21-17", "date": "2026-03-20", "tournament_name": "MCS Qualifier #1"},
            {"opponent_name": "Underdog", "result": "L", "score": "10-14", "date": "2026-03-17"},
            {"opponent_name": "RisingStar", "result": "W", "score": "24-21", "date": "2026-03-14"},
        ],
    },
}


class MCSTracker:
    """MCS Circuit Tracker — tournament bracket intelligence.

    Provides bracket state, opponent scouting queues, tournament-specific
    gameplans, and opponent form tracking for the Madden Championship Series.
    """

    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def get_tournament_sessions(self, user_id: str) -> list[GameSession]:
        """Query tournament game sessions for a user from the database."""
        try:
            uid = uuid.UUID(user_id) if isinstance(user_id, str) else user_id
            result = await self.db.execute(
                select(GameSession)
                .where(
                    GameSession.user_id == uid,
                    GameSession.mode == GameMode.TOURNAMENT,
                )
                .order_by(GameSession.played_at.desc())
            )
            return list(result.scalars().all())
        except (ValueError, Exception):
            return []

    # -----------------------------------------------------------------------
    # Public API
    # -----------------------------------------------------------------------

    def get_tournament_bracket(self, tournament_id: str) -> Bracket:
        """Return the current bracket state for a tournament."""
        data = _TOURNAMENTS.get(tournament_id)
        if data is None:
            raise ValueError(f"Tournament '{tournament_id}' not found.")

        rounds: list[BracketRound] = []
        for rd in data["rounds"]:
            matches = [
                BracketMatch(
                    match_id=m["match_id"],
                    round_number=m["round_number"],
                    player_a_id=m.get("player_a_id"),
                    player_a_name=m.get("player_a_name"),
                    player_b_id=m.get("player_b_id"),
                    player_b_name=m.get("player_b_name"),
                    winner_id=m.get("winner_id"),
                    score_a=m.get("score_a"),
                    score_b=m.get("score_b"),
                    status=MatchStatus(m.get("status", "pending")),
                    scheduled_time=m.get("scheduled_time"),
                )
                for m in rd["matches"]
            ]
            rounds.append(
                BracketRound(
                    round_number=rd["round_number"],
                    round_name=rd["round_name"],
                    matches=matches,
                )
            )

        return Bracket(
            tournament_id=data["tournament_id"],
            tournament_name=data["tournament_name"],
            status=data["status"],
            total_rounds=data["total_rounds"],
            current_round=data["current_round"],
            rounds=rounds,
            participants_count=data["participants_count"],
            last_synced_at=datetime.now(timezone.utc).isoformat(),
        )

    def get_opponent_queue(
        self, user_id: str, tournament_id: str
    ) -> list[OpponentPrep]:
        """Return upcoming opponents with prep notes for the user."""
        data = _TOURNAMENTS.get(tournament_id)
        if data is None:
            raise ValueError(f"Tournament '{tournament_id}' not found.")

        preps: list[OpponentPrep] = []
        for rd in data["rounds"]:
            for m in rd["matches"]:
                status = m.get("status", "pending")
                if status != "pending":
                    continue

                # Determine which side is the opponent
                opponent_id = None
                opponent_name = None
                if m.get("player_a_id") == user_id:
                    opponent_id = m.get("player_b_id")
                    opponent_name = m.get("player_b_name")
                elif m.get("player_b_id") == user_id:
                    opponent_id = m.get("player_a_id")
                    opponent_name = m.get("player_a_name")
                else:
                    # User not in this match — skip
                    continue

                if opponent_id is None:
                    continue

                form = _PLAYER_FORM.get(opponent_id, {})
                trend = self._calculate_trend(form)

                preps.append(
                    OpponentPrep(
                        opponent_id=opponent_id,
                        opponent_name=opponent_name or "TBD",
                        round_number=rd["round_number"],
                        form_trend=trend,
                        record=form.get("last_10", "0-0"),
                        key_weakness="",
                        prep_notes=f"Form: {form.get('last_5', 'N/A')} last 5.",
                    )
                )

        return preps

    def generate_tournament_book(
        self, user_id: str, tournament_id: str
    ) -> TournamentBook:
        """Generate a 15-play max tournament gameplan.

        The book is built to cover all likely opponents in the bracket with
        versatile plays that handle multiple defensive schemes.
        """
        data = _TOURNAMENTS.get(tournament_id)
        if data is None:
            raise ValueError(f"Tournament '{tournament_id}' not found.")

        opponents_scouted = 0
        for rd in data["rounds"]:
            for m in rd["matches"]:
                if m.get("player_a_id") == user_id or m.get("player_b_id") == user_id:
                    opponents_scouted += 1

        # Build a balanced 15-play tournament book
        plays: list[TournamentPlay] = [
            TournamentPlay(play_name="Gun Bunch Wk - Corner Strike", formation="Gun Bunch", situation="3rd & medium vs cover 3", priority=1, target_opponent_weakness="zone coverage"),
            TournamentPlay(play_name="Shotgun Trips TE - Mesh", formation="Shotgun Trips TE", situation="3rd & short-medium", priority=2, target_opponent_weakness="man coverage"),
            TournamentPlay(play_name="I-Form Close - Power O", formation="I-Form Close", situation="Goal line / short yardage", priority=3, target_opponent_weakness="undersized DL"),
            TournamentPlay(play_name="Gun Empty Trey - Blitz Beater", formation="Gun Empty", situation="Blitz situations", priority=4, target_opponent_weakness="aggressive blitz"),
            TournamentPlay(play_name="Singleback Ace - PA Crossers", formation="Singleback Ace", situation="Play action on 1st/2nd down", priority=5, target_opponent_weakness="run-commit LBs"),
            TournamentPlay(play_name="Pistol Strong - Counter", formation="Pistol Strong", situation="Red zone / 2nd & short", priority=6, target_opponent_weakness="aggressive edge players"),
            TournamentPlay(play_name="Gun Bunch Wk - Screen Wheel", formation="Gun Bunch", situation="Blitz heavy / pressure", priority=7, target_opponent_weakness="overcommitting pass rush"),
            TournamentPlay(play_name="Shotgun Cluster - Out Route", formation="Shotgun Cluster", situation="2-point conversion", priority=8, target_opponent_weakness="off coverage"),
            TournamentPlay(play_name="Under Center Ace - Boot Over", formation="Under Center Ace", situation="Red zone / 2-point", priority=9, target_opponent_weakness="zone blitz"),
            TournamentPlay(play_name="Singleback Bunch - HB Dive", formation="Singleback Bunch", situation="Clock management / safe run", priority=10, target_opponent_weakness="light box"),
            TournamentPlay(play_name="Shotgun Y-Trips - Deep Post", formation="Shotgun Y-Trips", situation="1st down shot play", priority=11, target_opponent_weakness="single high safety"),
            TournamentPlay(play_name="Gun Split Close - Levels", formation="Gun Split Close", situation="3rd & long", priority=12, target_opponent_weakness="zone coverage gaps"),
            TournamentPlay(play_name="I-Form Tight - QB Sneak", formation="I-Form Tight", situation="4th & inches", priority=13, target_opponent_weakness="spread DL alignment"),
            TournamentPlay(play_name="Shotgun Doubles - Slants", formation="Shotgun Doubles", situation="Quick game / hot route", priority=14, target_opponent_weakness="press coverage"),
            TournamentPlay(play_name="Gun Trey Open - HB Wheel", formation="Gun Trey Open", situation="2-minute drill", priority=15, target_opponent_weakness="LB in coverage"),
        ]

        return TournamentBook(
            tournament_id=tournament_id,
            tournament_name=data["tournament_name"],
            user_id=user_id,
            plays=plays,
            total_plays=len(plays),
            opponents_scouted=opponents_scouted,
            strategy_summary="Balanced 15-play book covering zone beaters, man beaters, blitz adjustments, and situational plays.",
            generated_at=datetime.now(timezone.utc).isoformat(),
        )

    def track_form(self, opponent_id: str) -> FormReport:
        """Return a form report on a specific opponent's recent performance."""
        form = _PLAYER_FORM.get(opponent_id)
        if form is None:
            raise ValueError(f"No form data for opponent '{opponent_id}'.")

        trend = self._calculate_trend(form)

        recent_matches = [
            RecentMatch(
                opponent_name=m["opponent_name"],
                result=m["result"],
                score=m["score"],
                date=m["date"],
                tournament_name=m.get("tournament_name"),
            )
            for m in form.get("recent", [])
        ]

        return FormReport(
            opponent_id=form["opponent_id"],
            opponent_name=form["opponent_name"],
            trend=trend,
            last_5_record=form.get("last_5", "0-0"),
            last_10_record=form.get("last_10", "0-0"),
            win_streak=form.get("win_streak", 0),
            loss_streak=form.get("loss_streak", 0),
            recent_matches=recent_matches,
            avg_score_for=form.get("avg_for", 0.0),
            avg_score_against=form.get("avg_against", 0.0),
            analysis=self._generate_form_analysis(form, trend),
        )

    # -----------------------------------------------------------------------
    # Private helpers
    # -----------------------------------------------------------------------

    def _calculate_trend(self, form: dict) -> FormTrend:
        """Derive a form trend from raw stats."""
        if not form:
            return FormTrend.NEUTRAL

        win_streak = form.get("win_streak", 0)
        loss_streak = form.get("loss_streak", 0)
        last_5 = form.get("last_5", "0-0")

        try:
            wins, losses = (int(x) for x in last_5.split("-"))
        except (ValueError, AttributeError):
            return FormTrend.NEUTRAL

        if win_streak >= 4:
            return FormTrend.HOT
        if wins >= 4:
            return FormTrend.HOT
        if wins >= 3:
            return FormTrend.WARM
        if loss_streak >= 3:
            return FormTrend.SLUMPING
        if losses >= 3:
            return FormTrend.COLD
        return FormTrend.NEUTRAL

    def _generate_form_analysis(self, form: dict, trend: FormTrend) -> str:
        """Generate a human-readable form analysis."""
        name = form.get("opponent_name", "Unknown")
        last_5 = form.get("last_5", "N/A")
        avg_for = form.get("avg_for", 0)
        avg_against = form.get("avg_against", 0)

        trend_desc = {
            FormTrend.HOT: "in excellent form",
            FormTrend.WARM: "playing well",
            FormTrend.NEUTRAL: "performing inconsistently",
            FormTrend.COLD: "struggling recently",
            FormTrend.SLUMPING: "in a significant slump",
        }

        return (
            f"{name} is {trend_desc.get(trend, 'unknown form')} "
            f"({last_5} last 5). Averaging {avg_for:.1f} pts scored "
            f"and {avg_against:.1f} pts allowed per game."
        )
