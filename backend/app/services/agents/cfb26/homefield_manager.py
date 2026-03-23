"""HomeField Advantage Manager — crowd noise and silent snap protocols for CFB 26."""

import logging
from dataclasses import dataclass

logger = logging.getLogger(__name__)

STADIUM_DB = {
    "tiger_stadium": {"name": "Tiger Stadium (LSU)", "capacity": 102321, "noise_rating": 9.5, "nickname": "Death Valley"},
    "beaver_stadium": {"name": "Beaver Stadium (PSU)", "capacity": 106572, "noise_rating": 9.2, "nickname": "Happy Valley"},
    "neyland": {"name": "Neyland Stadium (TENN)", "capacity": 102455, "noise_rating": 9.4, "nickname": "Rocky Top"},
    "the_shoe": {"name": "Ohio Stadium (OSU)", "capacity": 104944, "noise_rating": 9.0, "nickname": "The Horseshoe"},
    "kyle_field": {"name": "Kyle Field (TAMU)", "capacity": 102733, "noise_rating": 9.3, "nickname": "12th Man"},
    "big_house": {"name": "Michigan Stadium", "capacity": 107601, "noise_rating": 8.5, "nickname": "The Big House"},
    "default": {"name": "Generic Stadium", "capacity": 50000, "noise_rating": 6.0, "nickname": ""},
}


@dataclass
class SnapProtocol:
    snap_count_type: str  # "silent", "quick", "normal", "hard_count"
    cadence: str
    pre_snap_time: float  # seconds to get play off
    false_start_risk: float
    recommendation: str


@dataclass
class CrowdAdjustment:
    noise_level: float  # 0-10
    communication_difficulty: str  # "none", "moderate", "severe"
    audible_reliability: float  # 0.0-1.0
    hot_route_reliability: float
    adjustments: list


class HomeFieldManager:
    """Manages crowd noise impact and silent snap protocols for CFB 26."""

    def get_silent_snap_protocol(self, noise_level: float) -> SnapProtocol:
        if noise_level >= 8.5:
            return SnapProtocol(
                snap_count_type="silent",
                cadence="Leg lift or clap snap — no verbal cadence",
                pre_snap_time=2.0,
                false_start_risk=0.15,
                recommendation="Use only practiced silent-snap plays. Limit audibles to hand signals.",
            )
        elif noise_level >= 6.5:
            return SnapProtocol(
                snap_count_type="quick",
                cadence="Single-word snap on first sound — fast tempo",
                pre_snap_time=3.0,
                false_start_risk=0.08,
                recommendation="Quick snap rhythm. Simplify protection calls to pre-determined rules.",
            )
        elif noise_level >= 4.0:
            return SnapProtocol(
                snap_count_type="normal",
                cadence="Standard two-sound cadence",
                pre_snap_time=5.0,
                false_start_risk=0.03,
                recommendation="Normal operations. Can use full audible tree.",
            )
        else:
            return SnapProtocol(
                snap_count_type="hard_count",
                cadence="Varied cadence to draw offsides — home advantage",
                pre_snap_time=7.0,
                false_start_risk=0.01,
                recommendation="Exploit quiet environment with hard counts on short-yardage.",
            )

    def get_crowd_adjustment(self, home_away: str, stadium: str) -> CrowdAdjustment:
        profile = STADIUM_DB.get(stadium, STADIUM_DB["default"])
        noise = profile["noise_rating"] if home_away == "away" else profile["noise_rating"] * 0.3

        adjustments = []
        if noise >= 8.0:
            communication_difficulty = "severe"
            audible_reliability = 0.4
            hot_route_reliability = 0.5
            adjustments = [
                "Switch to silent snap count",
                "Pre-determine protection assignments",
                "Limit audibles to 2 max",
                "Use hand signal hot routes only",
                "Consider quick-tempo to prevent crowd build",
            ]
        elif noise >= 5.0:
            communication_difficulty = "moderate"
            audible_reliability = 0.7
            hot_route_reliability = 0.75
            adjustments = [
                "Use quick snap cadence",
                "Simplify audible tree to 3 options",
                "Point hot routes instead of calling",
            ]
        else:
            communication_difficulty = "none"
            audible_reliability = 0.95
            hot_route_reliability = 0.95
            adjustments = ["Full playbook available", "Use hard count to draw penalties"]

        return CrowdAdjustment(
            noise_level=noise,
            communication_difficulty=communication_difficulty,
            audible_reliability=audible_reliability,
            hot_route_reliability=hot_route_reliability,
            adjustments=adjustments,
        )

    def get_stadium_profile(self, stadium_name: str) -> dict:
        return STADIUM_DB.get(stadium_name, STADIUM_DB["default"])
