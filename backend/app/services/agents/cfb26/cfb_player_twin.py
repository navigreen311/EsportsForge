"""CFB PlayerTwin — college football specific player behavior extensions."""

import logging
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)

TRICK_PLAY_TELLS = {
    "fake_punt": ["punter alignment offset", "gunner pre-snap movement", "shield count mismatch"],
    "flea_flicker": ["RB hesitation after handoff", "WR delayed release", "OL passive block"],
    "hook_and_lateral": ["WR curl route at sideline", "trailing WR closing distance"],
    "wildcat": ["QB split wide", "RB direct snap alignment"],
    "philly_special": ["TE motioning to QB position", "QB split out wide"],
}

OPTION_DEFENSE_KEYS = {
    "triple_option": {"dive_key": "DE read", "pitch_key": "OLB/SS", "qb_key": "contain player"},
    "speed_option": {"pitch_key": "force player", "qb_key": "DE/OLB"},
    "zone_read": {"give_key": "backside DE", "qb_key": "cutback lane"},
    "rpo": {"run_key": "LB level", "pass_key": "safety rotation"},
}


@dataclass
class TrickPlayProfile:
    recognition_score: float  # 0-100
    tells_identified: list
    reaction_time_avg: float  # seconds
    success_rate_vs_tricks: float
    weakest_trick_play: str
    drill_recommendations: list


@dataclass
class OptionDefenseProfile:
    overall_rating: float
    dive_key_discipline: float
    pitch_key_discipline: float
    qb_contain_rate: float
    overcommit_rate: float
    best_option_defense: str
    worst_option_defense: str
    tendencies: dict = field(default_factory=dict)


class CFBPlayerTwin:
    """CFB-specific PlayerTwin extensions for trick play and option defense."""

    def __init__(self):
        self._trick_data: dict[str, list] = {}
        self._option_data: dict[str, list] = {}

    def get_trick_play_readiness(self, user_id: str) -> TrickPlayProfile:
        history = self._trick_data.get(user_id, [])
        if not history:
            return TrickPlayProfile(
                recognition_score=50.0,
                tells_identified=["Basic alignment reads"],
                reaction_time_avg=1.5,
                success_rate_vs_tricks=0.45,
                weakest_trick_play="fake_punt",
                drill_recommendations=["Practice punt formation recognition", "Film study: trick play tells"],
            )

        correct = sum(1 for h in history if h.get("recognized", False))
        total = len(history)
        all_tells = set()
        for h in history:
            all_tells.update(h.get("tells_seen", []))

        trick_fails = {}
        for h in history:
            trick = h.get("trick_type", "unknown")
            if not h.get("defended", False):
                trick_fails[trick] = trick_fails.get(trick, 0) + 1

        weakest = max(trick_fails, key=trick_fails.get) if trick_fails else "none"

        return TrickPlayProfile(
            recognition_score=min(100, (correct / max(total, 1)) * 100),
            tells_identified=list(all_tells)[:10],
            reaction_time_avg=sum(h.get("reaction_time", 1.5) for h in history) / max(len(history), 1),
            success_rate_vs_tricks=correct / max(total, 1),
            weakest_trick_play=weakest,
            drill_recommendations=self._generate_trick_drills(weakest),
        )

    def get_option_defense_profile(self, user_id: str) -> OptionDefenseProfile:
        history = self._option_data.get(user_id, [])
        if not history:
            return OptionDefenseProfile(
                overall_rating=50.0,
                dive_key_discipline=50.0,
                pitch_key_discipline=50.0,
                qb_contain_rate=0.5,
                overcommit_rate=0.3,
                best_option_defense="zone_read",
                worst_option_defense="triple_option",
            )

        discipline_scores = {"dive": [], "pitch": [], "contain": []}
        option_results = {}
        for h in history:
            option_type = h.get("option_type", "unknown")
            if option_type not in option_results:
                option_results[option_type] = {"stopped": 0, "total": 0}
            option_results[option_type]["total"] += 1
            if h.get("stopped", False):
                option_results[option_type]["stopped"] += 1
            for key in ["dive", "pitch", "contain"]:
                if key in h:
                    discipline_scores[key].append(h[key])

        best = max(option_results, key=lambda k: option_results[k]["stopped"] / max(option_results[k]["total"], 1)) if option_results else "zone_read"
        worst = min(option_results, key=lambda k: option_results[k]["stopped"] / max(option_results[k]["total"], 1)) if option_results else "triple_option"

        return OptionDefenseProfile(
            overall_rating=sum(sum(v) / max(len(v), 1) for v in discipline_scores.values()) / 3 * 100,
            dive_key_discipline=sum(discipline_scores["dive"]) / max(len(discipline_scores["dive"]), 1) * 100,
            pitch_key_discipline=sum(discipline_scores["pitch"]) / max(len(discipline_scores["pitch"]), 1) * 100,
            qb_contain_rate=sum(discipline_scores["contain"]) / max(len(discipline_scores["contain"]), 1),
            overcommit_rate=0.3,
            best_option_defense=best,
            worst_option_defense=worst,
        )

    def get_dynasty_tendencies(self, user_id: str) -> dict:
        return {
            "recruiting_style": "balanced",
            "redshirt_discipline": 0.7,
            "transfer_portal_usage": "moderate",
            "scheme_loyalty": 0.8,
            "development_focus": "offensive_skill",
        }

    def _generate_trick_drills(self, weakest: str) -> list:
        drills = ["Film study: identify pre-snap tells for trick plays"]
        tells = TRICK_PLAY_TELLS.get(weakest, [])
        for tell in tells[:3]:
            drills.append(f"Recognition drill: spot '{tell}' in pre-snap alignment")
        return drills
