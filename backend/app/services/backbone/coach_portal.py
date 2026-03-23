"""CoachPortal — coach dashboard, drill assignment, playbook sharing, war room, seat management.

Provides the coaching layer of EsportsForge, enabling coaches to monitor
player progress, assign targeted drills, share playbooks, run live war rooms,
and manage subscription seats.
"""

from __future__ import annotations

import logging
import uuid
from collections import defaultdict
from datetime import datetime, timezone
from typing import Any

from app.schemas.coach import (
    CoachDashboard,
    DrillAssignment,
    DrillResult,
    SeatManagement,
    SharedPlaybook,
    WarRoom,
)

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# In-memory stores
# ---------------------------------------------------------------------------

_coaches: dict[str, dict[str, Any]] = {}
_drills: dict[str, DrillAssignment] = {}
_playbooks: dict[str, SharedPlaybook] = {}
_war_rooms: dict[str, WarRoom] = {}
_seats: dict[str, SeatManagement] = {}
_player_data: dict[str, dict[str, Any]] = defaultdict(lambda: {"sessions": 0, "improvement": 0.0})


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def get_coach_dashboard(coach_id: str) -> CoachDashboard:
    """Build the coach dashboard with player summaries and activity feed.

    Aggregates drill progress, player performance trends, and
    recent activity into a single overview.
    """
    coach = _coaches.get(coach_id, {"team_name": "My Team", "players": []})
    player_ids = coach.get("players", [])

    # Aggregate drill data
    coach_drills = [d for d in _drills.values() if d.coach_id == coach_id]
    active_drills = sum(1 for d in coach_drills if d.status in ("assigned", "in_progress"))
    pending_reviews = sum(1 for d in coach_drills if d.status == "completed")

    # Player performance
    top_performers: list[dict[str, Any]] = []
    struggling: list[dict[str, Any]] = []
    total_improvement = 0.0

    for pid in player_ids:
        data = _player_data[pid]
        improvement = data.get("improvement", 0.0)
        total_improvement += improvement
        entry = {"player_id": pid, "improvement_pct": round(improvement, 2), "sessions": data.get("sessions", 0)}
        if improvement >= 5.0:
            top_performers.append(entry)
        elif improvement < -2.0:
            struggling.append(entry)

    avg_improvement = total_improvement / max(len(player_ids), 1)

    # Recent activity
    recent = []
    for d in sorted(coach_drills, key=lambda x: x.due_date or "", reverse=True)[:10]:
        recent.append({
            "type": "drill",
            "player_id": d.player_id,
            "drill_title": d.title,
            "status": d.status,
        })

    return CoachDashboard(
        coach_id=coach_id,
        team_name=coach.get("team_name", "My Team"),
        player_count=len(player_ids),
        active_drills=active_drills,
        pending_reviews=pending_reviews,
        overall_improvement_pct=round(avg_improvement, 2),
        top_performers=sorted(top_performers, key=lambda x: x["improvement_pct"], reverse=True)[:5],
        struggling_players=sorted(struggling, key=lambda x: x["improvement_pct"])[:5],
        recent_activity=recent,
    )


def assign_drill(
    coach_id: str,
    player_id: str,
    title: str,
    description: str,
    drill_type: str = "execution",
    target_metric: str = "accuracy",
    target_value: float = 0.8,
    due_date: str | None = None,
) -> DrillResult:
    """Assign a targeted drill to a specific player.

    Creates a drill assignment with a target metric and value,
    tracked over time until completion or expiration.
    """
    drill_id = f"drill_{uuid.uuid4().hex[:12]}"

    # Validate coach has this player
    coach = _coaches.get(coach_id, {"players": []})
    if player_id not in coach.get("players", []):
        # Auto-add for now (in production, would enforce)
        coach.setdefault("players", []).append(player_id)
        _coaches[coach_id] = coach

    current = _player_data[player_id].get(target_metric, 0.0)

    drill = DrillAssignment(
        drill_id=drill_id,
        coach_id=coach_id,
        player_id=player_id,
        title=title,
        description=description,
        drill_type=drill_type,
        target_metric=target_metric,
        target_value=target_value,
        current_value=current,
        status="assigned",
        due_date=due_date,
    )
    _drills[drill_id] = drill

    logger.info("Drill assigned: id=%s coach=%s player=%s title=%s", drill_id, coach_id, player_id, title)

    return DrillResult(
        success=True,
        drill_id=drill_id,
        message=f"Drill '{title}' assigned to player {player_id}. Target: {target_metric} >= {target_value}.",
    )


def share_playbook(
    coach_id: str,
    title: str,
    game_title: str,
    strategies: list[dict[str, Any]],
    player_ids: list[str],
    notes: str = "",
) -> SharedPlaybook:
    """Share a playbook with selected players.

    Creates a versioned playbook document that players can access
    from their mobile or desktop client.
    """
    playbook_id = f"pb_{uuid.uuid4().hex[:12]}"

    playbook = SharedPlaybook(
        playbook_id=playbook_id,
        coach_id=coach_id,
        title=title,
        game_title=game_title,
        strategies=strategies,
        player_ids=player_ids,
        version=1,
        last_updated=_now_iso(),
        notes=notes,
    )
    _playbooks[playbook_id] = playbook

    # Ensure players are on coach roster
    coach = _coaches.setdefault(coach_id, {"team_name": "My Team", "players": []})
    for pid in player_ids:
        if pid not in coach["players"]:
            coach["players"].append(pid)

    logger.info("Playbook shared: id=%s coach=%s players=%d", playbook_id, coach_id, len(player_ids))
    return playbook


def get_war_room(
    coach_id: str,
    game_title: str,
    player_ids: list[str] | None = None,
) -> WarRoom:
    """Initialize or retrieve a live war room session.

    The war room provides real-time recommendations, opponent tendencies,
    and adjustment tracking during a coaching session.
    """
    room_key = f"{coach_id}_{game_title}"
    existing = _war_rooms.get(room_key)

    if existing and existing.status == "active":
        return existing

    room_id = f"war_{uuid.uuid4().hex[:12]}"
    room = WarRoom(
        room_id=room_id,
        coach_id=coach_id,
        game_title=game_title,
        active_players=player_ids or [],
        live_recommendations=[
            {"recommendation": "Start with your base gameplan. Observe for 3-5 plays before adjusting.", "priority": "high"},
            {"recommendation": "Monitor opponent's opening tendencies — formation, play type, and tempo.", "priority": "medium"},
        ],
        opponent_tendencies={},
        adjustments_made=[],
        status="active",
    )
    _war_rooms[room_key] = room

    logger.info("War room opened: id=%s coach=%s game=%s", room_id, coach_id, game_title)
    return room


def manage_seats(
    coach_id: str,
    action: str = "status",
    player_id: str | None = None,
) -> SeatManagement:
    """Manage coach subscription seats — add/remove players, check status.

    Actions: status, add_player, remove_player.
    """
    seat = _seats.get(coach_id)
    if not seat:
        seat = SeatManagement(
            coach_id=coach_id,
            plan="team",
            total_seats=10,
            used_seats=0,
            available_seats=10,
            players=[],
        )
        _seats[coach_id] = seat

    if action == "add_player" and player_id:
        if seat.used_seats >= seat.total_seats:
            logger.warning("Seat limit reached for coach %s", coach_id)
        else:
            seat.players.append({"player_id": player_id, "added_at": _now_iso()})
            seat.used_seats = len(seat.players)
            seat.available_seats = seat.total_seats - seat.used_seats

            # Add to coach roster
            coach = _coaches.setdefault(coach_id, {"team_name": "My Team", "players": []})
            if player_id not in coach["players"]:
                coach["players"].append(player_id)

    elif action == "remove_player" and player_id:
        seat.players = [p for p in seat.players if p.get("player_id") != player_id]
        seat.used_seats = len(seat.players)
        seat.available_seats = seat.total_seats - seat.used_seats

    return seat
