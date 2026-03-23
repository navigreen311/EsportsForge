"""SchemeAI — Concept stacking, coverage answer matrix, hot route builder for Madden 26."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Optional

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.madden26 import MaddenPlay, MaddenScheme
from app.schemas.madden26.scheme import (
    Concept,
    CoverageAnswer,
    CoverageMatrix,
    CoverageType,
    HotRoute,
    RouteType,
    SchemeAnalysis,
    SchemeName,
    SchemeTendency,
    Situation,
    SituationPlay,
)


# ---------------------------------------------------------------------------
# Scheme knowledge base (static Madden 26 football intelligence)
# ---------------------------------------------------------------------------

_SCHEME_DATA: dict[str, dict[str, Any]] = {
    SchemeName.WEST_COAST: {
        "description": (
            "West Coast offense relies on short-to-intermediate timing routes, "
            "using the pass to set up the run. Emphasises RAC (run after catch) "
            "and high-percentage completions."
        ),
        "strengths": [
            "High completion percentage",
            "Controls tempo and clock",
            "Exploits underneath zones",
            "Strong against Cover 3 and Cover 4",
            "Good RAC opportunities",
        ],
        "weaknesses": [
            "Struggles against press-man coverage",
            "Vulnerable to aggressive blitzes",
            "Limited deep-shot opportunities",
            "Requires precise timing",
        ],
        "best_formations": [
            "Singleback Ace",
            "Gun Doubles",
            "I-Form Pro",
            "Gun Trips TE",
            "Singleback Wing",
        ],
        "recommended_playbooks": ["49ers", "Rams", "Dolphins", "Chiefs"],
    },
    SchemeName.SPREAD: {
        "description": (
            "Spread offense spaces the field horizontally with 3-4 WR sets, "
            "isolating defenders and creating one-on-one matchups. "
            "Relies on quick reads and RPO concepts."
        ),
        "strengths": [
            "Creates favorable matchups in space",
            "Forces defense to declare coverage early",
            "Effective against zone coverages",
            "Opens up QB run game",
            "Excellent in 2-minute drill",
        ],
        "weaknesses": [
            "Weaker run blocking with lighter personnel",
            "Susceptible to Cover 2 Man shells",
            "QB pressure from overloaded blitzes",
            "Less effective in short yardage",
        ],
        "best_formations": [
            "Gun Spread",
            "Gun Trips",
            "Gun Empty",
            "Gun Ace",
            "Pistol Spread",
        ],
        "recommended_playbooks": ["Bills", "Cardinals", "Eagles", "Ravens"],
    },
    SchemeName.GUN_BUNCH: {
        "description": (
            "Gun Bunch stacks three receivers to one side creating rub/pick routes "
            "and overloading zone defenders. Dominant in short-to-medium passing."
        ),
        "strengths": [
            "Natural rub routes beat man coverage",
            "Overloads one side of the field",
            "Effective mesh and drive concepts",
            "Hard to defend without specific adjustments",
            "Great red zone package",
        ],
        "weaknesses": [
            "Predictable formation tendency",
            "Vulnerable to specific zone drops",
            "Limited outside run game",
            "Can be scouted easily if overused",
        ],
        "best_formations": [
            "Gun Bunch",
            "Gun Bunch TE",
            "Gun Bunch Wk",
        ],
        "recommended_playbooks": ["Patriots", "Bengals", "Chargers"],
    },
}

# Default data for schemes not explicitly mapped
_DEFAULT_SCHEME: dict[str, Any] = {
    "description": "Custom scheme with adaptive play-calling.",
    "strengths": ["Flexible", "Adaptable to opponent"],
    "weaknesses": ["Requires game-time adjustment"],
    "best_formations": ["Gun Doubles", "Singleback Ace"],
    "recommended_playbooks": [],
}

# ---------------------------------------------------------------------------
# Core concept library
# ---------------------------------------------------------------------------

_CONCEPTS: list[dict[str, Any]] = [
    {
        "name": "Mesh",
        "tags": ["quick", "man_beater"],
        "beats_coverages": [CoverageType.COVER_1, CoverageType.MAN_PRESS, CoverageType.COVER_0],
        "down_distance_fit": ["3rd_and_short", "2nd_and_medium", "red_zone"],
        "stackable_with": ["Flood", "Wheel"],
    },
    {
        "name": "Flood",
        "tags": ["zone_beater", "high_low"],
        "beats_coverages": [CoverageType.COVER_3, CoverageType.COVER_2, CoverageType.COVER_4],
        "down_distance_fit": ["2nd_and_long", "1st_and_10"],
        "stackable_with": ["Mesh", "Drive"],
    },
    {
        "name": "Smash",
        "tags": ["zone_beater", "corner_route"],
        "beats_coverages": [CoverageType.COVER_2, CoverageType.COVER_4_PALMS],
        "down_distance_fit": ["1st_and_10", "2nd_and_medium"],
        "stackable_with": ["Flood", "Mesh"],
    },
    {
        "name": "Drive",
        "tags": ["quick", "crossing"],
        "beats_coverages": [CoverageType.COVER_3, CoverageType.COVER_3_MATCH, CoverageType.MAN_OFF],
        "down_distance_fit": ["3rd_and_medium", "2nd_and_long"],
        "stackable_with": ["Mesh", "Flood"],
    },
    {
        "name": "Four Verticals",
        "tags": ["deep", "aggressive"],
        "beats_coverages": [CoverageType.COVER_3, CoverageType.COVER_1],
        "down_distance_fit": ["2nd_and_long", "3rd_and_long", "backed_up"],
        "stackable_with": ["Post-Wheel"],
    },
    {
        "name": "Post-Wheel",
        "tags": ["deep", "shot_play"],
        "beats_coverages": [CoverageType.COVER_2, CoverageType.COVER_4],
        "down_distance_fit": ["1st_and_10", "play_action"],
        "stackable_with": ["Four Verticals"],
    },
    {
        "name": "Screen",
        "tags": ["quick", "blitz_beater", "run"],
        "beats_coverages": [CoverageType.COVER_0, CoverageType.MAN_PRESS],
        "down_distance_fit": ["2nd_and_long", "3rd_and_long"],
        "stackable_with": ["Draw", "Mesh"],
    },
    {
        "name": "RPO Read",
        "tags": ["rpo", "run", "quick"],
        "beats_coverages": [CoverageType.COVER_3, CoverageType.COVER_4],
        "down_distance_fit": ["1st_and_10", "2nd_and_short"],
        "stackable_with": ["Zone Run", "Mesh"],
    },
    {
        "name": "Zone Run",
        "tags": ["run", "outside"],
        "beats_coverages": [],
        "down_distance_fit": ["1st_and_10", "2nd_and_short", "goal_line"],
        "stackable_with": ["RPO Read", "Play Action"],
    },
    {
        "name": "Power Run",
        "tags": ["run", "inside", "physical"],
        "beats_coverages": [],
        "down_distance_fit": ["3rd_and_short", "goal_line", "4th_and_short"],
        "stackable_with": ["Play Action", "Zone Run"],
    },
]

# ---------------------------------------------------------------------------
# Coverage answer defaults
# ---------------------------------------------------------------------------

_COVERAGE_ANSWERS: dict[CoverageType, dict[str, Any]] = {
    CoverageType.COVER_0: {
        "best_plays": ["Quick Slants", "Screen", "Mesh Over"],
        "primary_read": "Hot route to the blitz side — slant or drag",
        "key_adjustment": "Block RB, hot route outside WR to slant",
    },
    CoverageType.COVER_1: {
        "best_plays": ["Mesh", "Crossers", "Deep Post"],
        "primary_read": "Find the crosser underneath the single high safety",
        "key_adjustment": "Motion to identify man assignment",
    },
    CoverageType.COVER_2: {
        "best_plays": ["Smash", "Post-Wheel", "Seam Route"],
        "primary_read": "Attack the hole between safeties",
        "key_adjustment": "Streak the slot to split safeties",
    },
    CoverageType.COVER_2_MAN: {
        "best_plays": ["Mesh", "Drive", "Bunch Crossers"],
        "primary_read": "Rub routes underneath",
        "key_adjustment": "Stack releases from bunch",
    },
    CoverageType.COVER_3: {
        "best_plays": ["Flood", "Drive", "Corner Route"],
        "primary_read": "High-low the flat defender",
        "key_adjustment": "Put RB on a flat route to hold the defender",
    },
    CoverageType.COVER_3_MATCH: {
        "best_plays": ["Drive", "Switch Concept", "Dagger"],
        "primary_read": "Cross the pattern-match rules",
        "key_adjustment": "Motion pre-snap to confuse match assignments",
    },
    CoverageType.COVER_4: {
        "best_plays": ["Flood", "Smash", "Dig Route"],
        "primary_read": "Curl-flat area — intermediate in routes",
        "key_adjustment": "Curl route WR to sit in the window",
    },
    CoverageType.COVER_4_PALMS: {
        "best_plays": ["Smash", "Levels", "Out Routes"],
        "primary_read": "Sideline throws under the palms read",
        "key_adjustment": "Out route by #1 receiver",
    },
    CoverageType.COVER_6: {
        "best_plays": ["Attack Cover 2 side", "Post to Cover 4 side"],
        "primary_read": "Identify the 2-side and throw the seam",
        "key_adjustment": "Streak on the Cover 2 side",
    },
    CoverageType.MAN_PRESS: {
        "best_plays": ["Slant-Flat", "Mesh", "Quick Out"],
        "primary_read": "Quick release to beat the jam",
        "key_adjustment": "Hot route to quick slants/drags",
    },
    CoverageType.MAN_OFF: {
        "best_plays": ["Curl", "Comeback", "Drive"],
        "primary_read": "Sit routes in soft coverage",
        "key_adjustment": "Curl route by primary receiver",
    },
}


# ---------------------------------------------------------------------------
# SchemeAI service
# ---------------------------------------------------------------------------

class SchemeAI:
    """
    SchemeAI for Madden 26 — concept stacking, coverage answers, hot routes.

    This service encapsulates Madden football IQ: it knows how to break down
    schemes, identify what beats each coverage, stack concepts together, and
    suggest hot route adjustments.
    """

    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    # ------------------------------------------------------------------
    # DB helpers
    # ------------------------------------------------------------------

    async def _get_scheme_from_db(self, scheme_name: str) -> MaddenScheme | None:
        """Query the database for a MaddenScheme by name."""
        result = await self.db.execute(
            select(MaddenScheme)
            .options(selectinload(MaddenScheme.plays))
            .where(MaddenScheme.name == scheme_name)
        )
        return result.scalar_one_or_none()

    async def _get_plays_for_scheme(self, scheme_name: str) -> list[MaddenPlay]:
        """Query plays belonging to a scheme by scheme name."""
        result = await self.db.execute(
            select(MaddenPlay)
            .join(MaddenScheme)
            .where(MaddenScheme.name == scheme_name)
        )
        return list(result.scalars().all())

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    async def analyze_scheme(self, scheme_name: str) -> SchemeAnalysis:
        """Return a full breakdown of the given scheme."""
        # Try DB first, fall back to static data
        db_scheme = await self._get_scheme_from_db(scheme_name)

        key = self._resolve_scheme_key(scheme_name)
        data = _SCHEME_DATA.get(key, _DEFAULT_SCHEME)

        # Enrich static data with DB scheme if available
        if db_scheme and db_scheme.concepts:
            data = {**data, **db_scheme.concepts}

        concepts = self._get_concepts_for_scheme(key)
        matrix = await self.build_coverage_answer_matrix(scheme_name)
        situation_map = self._build_situation_map(concepts)

        return SchemeAnalysis(
            scheme=scheme_name,
            description=data["description"],
            strengths=data["strengths"],
            weaknesses=data["weaknesses"],
            core_concepts=concepts,
            best_formations=data["best_formations"],
            coverage_answers=matrix,
            situation_plays=situation_map,
            recommended_playbooks=data.get("recommended_playbooks", []),
        )

    async def get_concept_stack(
        self, formation: str, down_distance: str
    ) -> list[Concept]:
        """Return concepts that stack together for a given formation & down-distance."""
        matching: list[Concept] = []

        for c in _CONCEPTS:
            fits_down = any(
                dd in down_distance.lower() for dd in c["down_distance_fit"]
            )
            if fits_down:
                matching.append(
                    Concept(
                        name=c["name"],
                        formation=formation,
                        play_name=f"{formation} — {c['name']}",
                        primary_read=f"Primary read for {c['name']}",
                        tags=c["tags"],
                        beats_coverages=c["beats_coverages"],
                        down_distance_fit=c["down_distance_fit"],
                        stackable_with=c["stackable_with"],
                    )
                )

        # Sort so stackable pairs are adjacent
        return self._order_by_stackability(matching)

    async def build_coverage_answer_matrix(
        self, scheme: str, formation_filter: Optional[str] = None
    ) -> CoverageMatrix:
        """Build a matrix showing what beats each coverage within the scheme."""
        answers: list[CoverageAnswer] = []

        for cov, info in _COVERAGE_ANSWERS.items():
            answers.append(
                CoverageAnswer(
                    coverage=cov,
                    best_plays=info["best_plays"],
                    primary_read=info["primary_read"],
                    key_adjustment=info.get("key_adjustment"),
                    confidence=0.82,
                )
            )

        return CoverageMatrix(
            scheme=scheme,
            answers=answers,
            generated_at=datetime.now(timezone.utc).isoformat(),
            notes=f"Coverage matrix for {scheme}. Adjust based on opponent tendencies.",
        )

    async def suggest_hot_routes(
        self, play: str, coverage_read: CoverageType
    ) -> list[HotRoute]:
        """Suggest optimal hot-route adjustments for a play vs a coverage read."""
        suggestions: list[HotRoute] = []

        hot_route_map: dict[CoverageType, list[dict[str, Any]]] = {
            CoverageType.COVER_0: [
                {"receiver": "WR1", "original": "Streak", "route": RouteType.SLANT,
                 "reason": "Quick inside release beats zero blitz", "yards": 8.0},
                {"receiver": "RB", "original": "Block", "route": RouteType.FLAT,
                 "reason": "Hot route RB to flat as safety valve vs blitz", "yards": 5.0},
            ],
            CoverageType.COVER_1: [
                {"receiver": "Slot", "original": "Curl", "route": RouteType.POST,
                 "reason": "Post route splits the single high safety", "yards": 18.0},
                {"receiver": "TE", "original": "Block", "route": RouteType.DRAG,
                 "reason": "Drag underneath man coverage for easy completion", "yards": 7.0},
            ],
            CoverageType.COVER_2: [
                {"receiver": "WR1", "original": "Out", "route": RouteType.STREAK,
                 "reason": "Streak down the sideline between CB and safety", "yards": 22.0},
                {"receiver": "Slot", "original": "Slant", "route": RouteType.POST,
                 "reason": "Post into the hole between two safeties", "yards": 20.0},
            ],
            CoverageType.COVER_3: [
                {"receiver": "WR2", "original": "Curl", "route": RouteType.CORNER,
                 "reason": "Corner route to the flat void in Cover 3", "yards": 14.0},
                {"receiver": "RB", "original": "Block", "route": RouteType.FLAT,
                 "reason": "Flat route holds the flat defender for high-low", "yards": 4.0},
            ],
            CoverageType.MAN_PRESS: [
                {"receiver": "WR1", "original": "Streak", "route": RouteType.SLANT,
                 "reason": "Quick slant beats press at the LOS", "yards": 9.0},
                {"receiver": "WR2", "original": "Out", "route": RouteType.DRAG,
                 "reason": "Drag across the formation to create separation", "yards": 8.0},
            ],
        }

        entries = hot_route_map.get(coverage_read, [
            {"receiver": "Slot", "original": "Curl", "route": RouteType.DRAG,
             "reason": f"Generic drag adjustment vs {coverage_read.value}", "yards": 6.0},
        ])

        for entry in entries:
            suggestions.append(
                HotRoute(
                    receiver=entry["receiver"],
                    original_route=entry["original"],
                    suggested_route=entry["route"],
                    reason=entry["reason"],
                    expected_yards=entry.get("yards"),
                )
            )

        return suggestions

    async def get_situation_plays(
        self, scheme: str, situation: Situation
    ) -> list[SituationPlay]:
        """Return the best plays for a given scheme and game situation."""
        situation_library: dict[Situation, list[dict[str, Any]]] = {
            Situation.RED_ZONE: [
                {"play": "PA Boot Over", "formation": "Singleback Ace",
                 "reason": "Play action frees the TE in the flat", "rate": 0.68},
                {"play": "Mesh Cross", "formation": "Gun Bunch",
                 "reason": "Mesh rub creates separation in tight quarters", "rate": 0.72},
                {"play": "Goal Line Power", "formation": "Goal Line",
                 "reason": "Physical run when they expect pass", "rate": 0.55},
            ],
            Situation.THIRD_AND_LONG: [
                {"play": "Four Verticals", "formation": "Gun Spread",
                 "reason": "Stretch the field vertically to move the sticks", "rate": 0.38},
                {"play": "Crossers", "formation": "Gun Doubles",
                 "reason": "Deep crossing routes find soft spots in zone", "rate": 0.45},
                {"play": "Screen", "formation": "Gun Trips",
                 "reason": "Screen against aggressive pass rush", "rate": 0.42},
            ],
            Situation.TWO_MINUTE: [
                {"play": "Quick Slants", "formation": "Gun Spread",
                 "reason": "Fast completion, get out of bounds or stop the clock", "rate": 0.65},
                {"play": "Stick Concept", "formation": "Gun Trips",
                 "reason": "Quick reads, stop the clock with sideline throws", "rate": 0.60},
            ],
            Situation.GOAL_LINE: [
                {"play": "QB Sneak", "formation": "Under Center",
                 "reason": "Highest success rate inside the 1-yard line", "rate": 0.78},
                {"play": "Power Run", "formation": "Goal Line",
                 "reason": "Physical downhill run with lead blocker", "rate": 0.60},
            ],
            Situation.BACKED_UP: [
                {"play": "Quick Out", "formation": "Gun Doubles",
                 "reason": "Safe throw to the sideline to gain breathing room", "rate": 0.58},
                {"play": "Zone Run", "formation": "Singleback Ace",
                 "reason": "Run to move the chains safely", "rate": 0.50},
            ],
        }

        entries = situation_library.get(situation, [
            {"play": "Generic Play", "formation": "Gun Doubles",
             "reason": f"Default concept for {situation.value}", "rate": 0.50},
        ])

        return [
            SituationPlay(
                play_name=e["play"],
                formation=e["formation"],
                situation=situation,
                reason=e["reason"],
                success_rate=e.get("rate"),
                tags=[scheme],
            )
            for e in entries
        ]

    async def detect_scheme_tendency(
        self, play_history: list[dict[str, Any]]
    ) -> SchemeTendency:
        """Analyze a play history to detect predictability and tendencies."""
        total = len(play_history)
        if total == 0:
            return SchemeTendency(
                total_plays_analyzed=0,
                most_called_plays=[],
                formation_distribution={},
                run_pass_ratio={"run": 0.0, "pass": 0.0},
                predictability_score=0.0,
                predictable_situations=[],
                recommendations=["Play more games to generate data."],
            )

        # Count play calls
        play_counts: dict[str, int] = {}
        formation_counts: dict[str, int] = {}
        run_count = 0
        pass_count = 0

        for entry in play_history:
            name = entry.get("play_name", "unknown")
            formation = entry.get("formation", "unknown")
            play_type = entry.get("play_type", "pass")

            play_counts[name] = play_counts.get(name, 0) + 1
            formation_counts[formation] = formation_counts.get(formation, 0) + 1
            if play_type in ("run", "qb_run"):
                run_count += 1
            else:
                pass_count += 1

        # Top 5 plays
        sorted_plays = sorted(play_counts.items(), key=lambda x: x[1], reverse=True)
        top_5 = [{"play": p, "count": c} for p, c in sorted_plays[:5]]

        # Formation distribution
        formation_dist = {f: round(c / total, 2) for f, c in formation_counts.items()}

        # Run/pass ratio
        rp_ratio = {
            "run": round(run_count / total, 2) if total else 0.0,
            "pass": round(pass_count / total, 2) if total else 0.0,
        }

        # Predictability: higher concentration = more predictable
        max_play_pct = (sorted_plays[0][1] / total) if sorted_plays else 0
        predictability = min(1.0, max_play_pct * 2)  # Scale up

        # Identify predictable situations
        predictable_sits: list[str] = []
        if rp_ratio["run"] > 0.7:
            predictable_sits.append("Overall too run-heavy")
        if rp_ratio["pass"] > 0.7:
            predictable_sits.append("Overall too pass-heavy")
        if max_play_pct > 0.25:
            predictable_sits.append(
                f"Over-reliance on '{sorted_plays[0][0]}' ({sorted_plays[0][1]}/{total})"
            )

        recommendations: list[str] = []
        if predictability > 0.5:
            recommendations.append("Diversify play calls — top play is used too often.")
        if len(formation_counts) < 3:
            recommendations.append("Use more formations to keep the defense guessing.")
        if abs(rp_ratio["run"] - rp_ratio["pass"]) > 0.3:
            heavier = "run" if rp_ratio["run"] > rp_ratio["pass"] else "pass"
            recommendations.append(f"Balance run/pass — currently {heavier}-heavy.")

        return SchemeTendency(
            total_plays_analyzed=total,
            most_called_plays=top_5,
            formation_distribution=formation_dist,
            run_pass_ratio=rp_ratio,
            predictability_score=round(predictability, 2),
            predictable_situations=predictable_sits,
            recommendations=recommendations,
        )

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    @staticmethod
    def list_schemes() -> list[dict[str, str]]:
        """Return all recognized scheme names with a short description."""
        results: list[dict[str, str]] = []
        for key, data in _SCHEME_DATA.items():
            results.append({
                "name": key.value if isinstance(key, SchemeName) else str(key),
                "description": data["description"][:120] + "...",
            })
        return results

    @staticmethod
    def _resolve_scheme_key(name: str) -> SchemeName | str:
        """Attempt to resolve a string to a SchemeName enum."""
        try:
            return SchemeName(name.lower().replace(" ", "_"))
        except ValueError:
            return name

    @staticmethod
    def _get_concepts_for_scheme(scheme_key: Any) -> list[Concept]:
        """Select concepts relevant to a given scheme."""
        concepts: list[Concept] = []
        for c in _CONCEPTS:
            formation = "Gun Doubles"  # default
            concepts.append(
                Concept(
                    name=c["name"],
                    formation=formation,
                    play_name=f"{formation} — {c['name']}",
                    primary_read=f"Primary read for {c['name']}",
                    tags=c["tags"],
                    beats_coverages=c["beats_coverages"],
                    down_distance_fit=c["down_distance_fit"],
                    stackable_with=c["stackable_with"],
                )
            )
        return concepts

    @staticmethod
    def _order_by_stackability(concepts: list[Concept]) -> list[Concept]:
        """Reorder concepts so stackable pairs are adjacent."""
        if len(concepts) <= 1:
            return concepts

        ordered: list[Concept] = [concepts[0]]
        remaining = list(concepts[1:])

        while remaining:
            last = ordered[-1]
            best_idx = 0
            best_score = -1
            for i, c in enumerate(remaining):
                score = len(set(c.stackable_with) & {last.name})
                if score > best_score:
                    best_score = score
                    best_idx = i
            ordered.append(remaining.pop(best_idx))

        return ordered

    def _build_situation_map(
        self, concepts: list[Concept]
    ) -> dict[str, list[SituationPlay]]:
        """Build a situation -> plays map from a concept list."""
        sit_map: dict[str, list[SituationPlay]] = {}
        for concept in concepts:
            for dd in concept.down_distance_fit:
                if dd not in sit_map:
                    sit_map[dd] = []
                sit_map[dd].append(
                    SituationPlay(
                        play_name=concept.play_name,
                        formation=concept.formation,
                        situation=Situation.RED_ZONE,  # placeholder
                        reason=f"{concept.name} fits {dd}",
                        tags=concept.tags,
                    )
                )
        return sit_map
