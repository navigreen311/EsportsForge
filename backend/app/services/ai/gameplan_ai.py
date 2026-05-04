"""GameplanAI — Claude-powered competitive gameplan generation.

Replaces the previous forgecore stub with a real call that consumes a
player's identity, opponent dossier, ImpactRank priorities, PlayerTwin,
recent session history, and the current meta alert / patch — and returns
a structured plan matching the frontend Gameplan schema.

Falls back to a deterministic mock plan when no ANTHROPIC_API_KEY is
configured so the rest of the page still renders end-to-end.
"""

from __future__ import annotations

import json
import logging
import time
from dataclasses import dataclass
from typing import Any

from app.services.ai.claude_client import ClaudeClient

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Per-title play vocabularies — used to keep Claude in-bounds for each game
# ---------------------------------------------------------------------------

TITLE_PLAY_CONTEXT: dict[str, dict[str, list[str]]] = {
    "madden26": {
        "formations": [
            "Gun Trips TE", "Shotgun Bunch", "I-Form Pro", "Singleback Ace",
            "Gun Spread", "Empty Trey", "Pistol Strong", "I-Form Close",
        ],
        "playTypes": [
            "play-action", "zone-beater", "man-beater", "run", "screen", "rpo",
            "quick-pass", "deep-shot",
        ],
        "situations": [
            "3rd-medium", "red-zone", "2-min-drill", "4th-short", "opening-drive",
        ],
    },
    "cfb26": {
        "formations": [
            "Spread Option", "Pistol Trips", "Shotgun Bunch", "I-Form",
            "Air Raid Empty", "Singleback Wing",
        ],
        "playTypes": [
            "rpo", "play-action", "option-run", "quick-pass", "deep-shot",
            "screen", "zone-beater", "man-beater",
        ],
        "situations": [
            "3rd-medium", "red-zone", "2-min-drill", "4th-short",
            "opening-drive", "tempo",
        ],
    },
    "nba2k26": {
        "formations": [
            "5-Out", "Post Up", "Pick & Roll", "Horns", "Motion Offense", "4-Out 1-In",
        ],
        "playTypes": [
            "post-move", "spot-up", "drive", "pick-roll", "cut", "transition",
        ],
        "situations": [
            "half-court", "transition", "shot-clock", "end-of-period", "crunch-time",
        ],
    },
    "fc26": {
        "formations": [
            "4-3-3", "4-2-3-1", "4-4-2", "3-5-2", "5-3-2", "4-1-2-1-2",
        ],
        "playTypes": [
            "skill-combo", "through-ball", "crossing", "set-piece", "counter-attack",
        ],
        "situations": [
            "open-play", "corner", "free-kick", "counter", "final-third",
        ],
    },
    "mlbtheshow26": {
        "formations": [
            "Standard", "Shift", "Ted Williams", "Infield-In", "Corner-In",
        ],
        "playTypes": [
            "4-seam", "slider", "changeup", "curveball", "sinker", "cutter",
        ],
        "situations": [
            "0-2-count", "full-count", "risp", "2-outs", "save-situation",
        ],
    },
    "warzone": {
        "formations": [
            "Long Range", "Mid Range", "Close Quarters", "Sniper Setup",
        ],
        "playTypes": [
            "loadout", "movement-tech", "positioning", "rotation", "peek",
        ],
        "situations": [
            "early-game", "mid-game", "final-circle", "1v1", "clutch",
        ],
    },
    "fortnite": {
        "formations": [
            "Box Fight", "High Ground", "Zone Wars", "Reset Position",
        ],
        "playTypes": [
            "edit-play", "build-reset", "peek", "launch-pad", "zone-launch",
        ],
        "situations": [
            "early-game", "mid-game", "final-zone", "box-fight", "endgame",
        ],
    },
    "ufc5": {
        "formations": [
            "Orthodox", "Southpaw", "Clinch", "Ground-and-Pound",
        ],
        "playTypes": [
            "strike-combo", "takedown", "submission-setup", "clinch-work", "counter",
        ],
        "situations": [
            "standing", "clinch", "ground", "low-stamina", "final-round",
        ],
    },
    "pga2k25": {
        "formations": [
            "Fairway", "Rough", "Bunker", "Tee Box", "Green",
        ],
        "playTypes": [
            "driver", "iron", "wedge", "chip", "putt", "bump-and-run",
        ],
        "situations": [
            "tee-shot", "approach", "short-game", "putting", "wind-play",
        ],
    },
    "undisputed": {
        "formations": [
            "Orthodox", "Southpaw", "Peek-a-Boo", "Outside Fighter",
        ],
        "playTypes": [
            "jab-combo", "body-work", "counter-punch", "footwork", "clinch",
        ],
        "situations": [
            "early-rounds", "mid-fight", "late-rounds", "hurt-opponent", "being-hurt",
        ],
    },
    "videopoker": {
        "formations": [
            "Jacks-or-Better", "Double-Bonus", "Deuces-Wild",
        ],
        "playTypes": [
            "optimal-hold", "variance-play", "bonus-hunt",
        ],
        "situations": [
            "dealt-hand", "bonus-trigger", "session-management",
        ],
    },
}


def get_title_context(title_id: str) -> dict[str, list[str]]:
    return TITLE_PLAY_CONTEXT.get(title_id, TITLE_PLAY_CONTEXT["madden26"])


# ---------------------------------------------------------------------------
# Inputs
# ---------------------------------------------------------------------------


@dataclass
class GameplanInputs:
    user_id: str
    title_id: str
    mode: str
    opponent: dict[str, Any] | None
    identity: dict[str, Any] | None
    priorities: list[dict[str, Any]]
    player_twin: dict[str, Any] | None
    recent_games: list[dict[str, Any]]
    meta_alert: dict[str, Any] | None
    patch_version: str | None


# ---------------------------------------------------------------------------
# In-memory TTL cache (no Redis required for local dev)
# ---------------------------------------------------------------------------


_CACHE: dict[str, tuple[float, dict[str, Any]]] = {}
_CACHE_TTL_SEC = 60 * 60  # 1 hour


def _cache_key(inputs: GameplanInputs) -> str:
    opp_id = (inputs.opponent or {}).get("id") or "no-opp"
    return f"gameplan:{inputs.user_id}:{opp_id}:{inputs.title_id}:{inputs.patch_version or 'na'}:{inputs.mode}"


def cache_get(inputs: GameplanInputs) -> dict[str, Any] | None:
    key = _cache_key(inputs)
    entry = _CACHE.get(key)
    if not entry:
        return None
    expires_at, data = entry
    if time.time() > expires_at:
        _CACHE.pop(key, None)
        return None
    return data


def cache_set(inputs: GameplanInputs, data: dict[str, Any]) -> None:
    _CACHE[_cache_key(inputs)] = (time.time() + _CACHE_TTL_SEC, data)


def cache_clear_for_user(user_id: str) -> None:
    for key in list(_CACHE.keys()):
        if key.startswith(f"gameplan:{user_id}:"):
            _CACHE.pop(key, None)


# ---------------------------------------------------------------------------
# Prompt builders
# ---------------------------------------------------------------------------


def build_system_prompt(inputs: GameplanInputs) -> str:
    identity = inputs.identity or {}
    twin = inputs.player_twin or {}
    return f"""You are GameplanAI for EsportsForge. You generate elite competitive gameplans for serious players who want to win.

PLAYER IDENTITY:
Offensive style: {identity.get('offensive_identity', 'unknown')}
Defensive philosophy: {identity.get('defensive_philosophy', 'unknown')}
Risk tolerance: {identity.get('risk_tolerance', 5)}/10
Pace preference: {identity.get('pace_preference', 'balanced')}
Comfort zones: {', '.join((identity.get('comfort_zones') or {}).keys()) if isinstance(identity.get('comfort_zones'), dict) else 'unknown'}
Agent directness: {identity.get('agent_directness', 'direct')}

PLAYER TWIN DATA:
Tendencies: {json.dumps(twin.get('tendencies') or {})}
Execution ceiling: {json.dumps(twin.get('execution_ceiling') or {})}
Coverage recognition: {json.dumps(twin.get('coverage_accuracy') or {})}

TITLE: {inputs.title_id}

RULES FOR GAMEPLAN GENERATION:
- Every play MUST be specifically chosen to exploit THIS opponent's detected tendencies.
- Confidence scores must reflect the matchup (NOT generic ratings). Vary them — most plays land between 65 and 92.
- Evidence must cite the opponent's actual stats from their dossier when present. If a stat isn't supplied, write "no observed data — based on archetype heuristic" rather than fabricate a percentage.
- Respect player identity — if they are explosive, do not fill the plan with clock control.
- Respect PlayerTwin — avoid concepts the player has low execution on unless a high-leverage matchup demands it.
- Kill Sheet = the 5 plays with the highest opponent-specific success expectation.
- Script View = an opening-drive sequence ordered by opponent's typical opening adjustments.
- Mark isTrendingCountered: true for plays the meta alert flags as currently countered.
- Be decisive. No hedging. Every play has a reason.
- Return ONLY valid JSON. No prose. No markdown fences."""


_USER_PROMPT_SCHEMA_TAIL = """
Return ONLY valid JSON in this exact shape:
{
  "gameplan": {
    "opponentSummary": {
      "topCoverage": "string",
      "topCoveragePercent": number,
      "blitzRate": number,
      "tendency3": "string",
      "tendency3Percent": number,
      "defensiveSchemer": "string",
      "winRate": number
    },
    "plays": [
      {
        "id": "p-1",
        "rank": 1,
        "name": "string",
        "formation": "string",
        "tags": ["zone-beater"],
        "confidence": 86,
        "impactScore": 7.5,
        "masteryLevel": "Competition Ready",
        "executionRate": 78,
        "isTrendingCountered": false,
        "isKillSheetPlay": true,
        "whenToCall": "string",
        "conceptBreakdown": "string",
        "evidence": {
          "why": "string",
          "data": "string",
          "risk": "string",
          "comparable": "string"
        },
        "proofAIConfidence": 84,
        "callStructure": {
          "layer1": {"name": "string", "description": "string"},
          "layer2": [{"audible": "string", "trigger": "string", "description": "string"}],
          "layer3": "string"
        },
        "metaStatus": "Strong",
        "patchVersion": "string"
      }
    ],
    "killSheet": [
      {"rank": 1, "name": "string", "formation": "string", "confidence": 90, "whenToCall": "string"}
    ],
    "scriptView": [
      {"order": 1, "playName": "string", "formation": "string", "callWhen": "string", "confidence": 85, "impactScore": 7, "masteryLevel": "Competition Ready"}
    ],
    "antiBlitzPackage": {"complete": true, "plays": ["string"], "missing": null, "healthMessage": "string"},
    "redZonePackage": {"complete": false, "plays": ["string"], "missing": "string", "healthMessage": "string"},
    "twoMinDrill": [{"time": "2:00", "situation": "Down 3+", "call": "string"}],
    "metaVersion": "string",
    "overallStrategy": "string"
  }
}
Generate exactly 10 plays.
"""


def build_user_prompt(inputs: GameplanInputs) -> str:
    opp = inputs.opponent or {}
    title_ctx = get_title_context(inputs.title_id)
    parts = [
        f"OPPONENT: {opp.get('gamertag', 'Unknown')}",
        f"ARCHETYPE: {opp.get('archetype', 'unclassified')}",
        f"GAMES PLAYED VS THEM: {opp.get('encounter_count', 0)}",
        "",
        "THEIR TENDENCIES:",
        json.dumps(opp.get("tendencies") or {}, indent=2),
        "",
        "MY TOP PRIORITIES (ImpactRank):",
        "\n".join(
            f"{p['fix_priority']}. {p['description']} — costing {p['win_rate_damage']}% win rate"
            for p in inputs.priorities
        ) or "(none recorded)",
        "",
        "RECENT GAMES VS THIS OPPONENT:",
        "\n".join(
            f"{g.get('played_at', '')}: {g.get('result', '')} ({g.get('mode', '')})"
            for g in inputs.recent_games
        ) or "(no games)",
        "",
        "CURRENT META ALERT:",
        (
            f"{inputs.meta_alert['weapon_name']}: {inputs.meta_alert['weapon_why']}"
            if inputs.meta_alert
            else "No alert"
        ),
        "",
        f"CURRENT PATCH: {inputs.patch_version or 'unknown'}",
        f"TITLE: {inputs.title_id}",
        f"MODE: {inputs.mode}",
        f"AVAILABLE FORMATIONS: {', '.join(title_ctx['formations'])}",
        f"PLAY TYPES: {', '.join(title_ctx['playTypes'])}",
        f"SITUATIONS: {', '.join(title_ctx['situations'])}",
        _USER_PROMPT_SCHEMA_TAIL,
    ]
    return "\n".join(parts)


# ---------------------------------------------------------------------------
# Mock fallback (no key)
# ---------------------------------------------------------------------------


def _mock_gameplan(inputs: GameplanInputs) -> dict[str, Any]:
    """Deterministic plan that exercises the full schema — used when no key
    is available so the page still renders without crashing."""
    title_ctx = get_title_context(inputs.title_id)
    formations = title_ctx["formations"]
    play_types = title_ctx["playTypes"]
    situations = title_ctx["situations"]
    opp_name = (inputs.opponent or {}).get("gamertag", "Unknown")
    archetype = (inputs.opponent or {}).get("archetype", "Balanced")

    plays = []
    for i in range(10):
        formation = formations[i % len(formations)]
        ptype = play_types[i % len(play_types)]
        situation = situations[i % len(situations)]
        confidence = 92 - (i * 3)
        plays.append({
            "id": f"p-{i+1}",
            "rank": i + 1,
            "name": f"{ptype.replace('-', ' ').title()} from {formation}",
            "formation": formation,
            "tags": [ptype, situation],
            "confidence": max(60, confidence),
            "impactScore": round(9.0 - (i * 0.4), 1),
            "masteryLevel": "Competition Ready" if i < 3 else "Practicing",
            "executionRate": 85 - (i * 3),
            "isTrendingCountered": i == 6,
            "isKillSheetPlay": i < 5,
            "whenToCall": f"Best vs {archetype} archetype in {situation}",
            "conceptBreakdown": (
                f"Mock breakdown — without an Anthropic key the planner serves a deterministic plan. "
                f"This {ptype} from {formation} is sequenced to exploit a {archetype}-leaning opponent."
            ),
            "evidence": {
                "why": f"Archetype heuristic — {archetype} opponents typically over-commit in {situation}.",
                "data": "no observed data — based on archetype heuristic",
                "risk": f"If {opp_name} adjusts to {ptype}, fall back to a complementary call.",
                "comparable": "Pattern matched in archived plans for the same archetype.",
            },
            "proofAIConfidence": max(55, 88 - (i * 4)),
            "callStructure": {
                "layer1": {"name": f"Base {ptype}", "description": f"Run from {formation}"},
                "layer2": [{
                    "audible": f"Hot {ptype}",
                    "trigger": "Pressure look",
                    "description": "Quick pivot if pressure shows pre-snap",
                }],
                "layer3": "If they adjust, escalate to a deep variant of the same concept.",
            },
            "metaStatus": "Strong" if i < 6 else "Stable",
            "patchVersion": inputs.patch_version or "unknown",
        })

    kill_sheet = [
        {
            "rank": p["rank"],
            "name": p["name"],
            "formation": p["formation"],
            "confidence": p["confidence"],
            "whenToCall": p["whenToCall"],
        }
        for p in plays if p["isKillSheetPlay"]
    ]
    script_view = [
        {
            "order": idx + 1,
            "playName": p["name"],
            "formation": p["formation"],
            "callWhen": f"Open with this — establish {p['tags'][0]}." if idx == 0 else f"Follow-up to keep {opp_name} off-balance.",
            "confidence": p["confidence"],
            "impactScore": p["impactScore"],
            "masteryLevel": p["masteryLevel"],
        }
        for idx, p in enumerate(plays[:5])
    ]
    return {
        "gameplan": {
            "opponentSummary": {
                "topCoverage": "Cover 3",
                "topCoveragePercent": 62,
                "blitzRate": 31,
                "tendency3": "Run-first 3rd & medium",
                "tendency3Percent": 58,
                "defensiveSchemer": archetype,
                "winRate": 50,
            },
            "plays": plays,
            "killSheet": kill_sheet,
            "scriptView": script_view,
            "antiBlitzPackage": {
                "complete": True,
                "plays": ["Hot route RB", "Quick screen", "Sight adjustment"],
                "missing": None,
                "healthMessage": "All 3 anti-blitz essentials covered",
            },
            "redZonePackage": {
                "complete": False,
                "plays": ["Fade route", "Power run"],
                "missing": "Back shoulder option",
                "healthMessage": "Add a back shoulder fade for complete package",
            },
            "twoMinDrill": [
                {"time": "2:00", "situation": "Down 3+", "call": "No huddle, attack sidelines"},
                {"time": "1:30", "situation": "1 timeout", "call": "Mid-field crosser to chunk yards"},
                {"time": "0:30", "situation": "Goal-to-go", "call": "Spike or back-shoulder fade"},
            ],
            "metaVersion": inputs.patch_version or "unknown",
            "overallStrategy": (
                f"Mock-only plan vs {opp_name} ({archetype}). "
                "Set ANTHROPIC_API_KEY in backend env and regenerate for real, opponent-specific output."
            ),
            "_source": "mock",
        }
    }


# ---------------------------------------------------------------------------
# Service
# ---------------------------------------------------------------------------


@dataclass
class GameplanResult:
    gameplan: dict[str, Any]
    cached: bool
    input_tokens: int = 0
    output_tokens: int = 0
    source: str = "claude"


_claude = ClaudeClient()


async def generate_gameplan(inputs: GameplanInputs) -> GameplanResult:
    cached = cache_get(inputs)
    if cached:
        return GameplanResult(gameplan=cached, cached=True, source=cached.get("_source", "claude"))

    if not _claude.is_available:
        plan = _mock_gameplan(inputs)
        cache_set(inputs, plan["gameplan"])
        return GameplanResult(gameplan=plan["gameplan"], cached=False, source="mock")

    system = build_system_prompt(inputs)
    user = build_user_prompt(inputs)

    try:
        # generate_json strips markdown fences and parses for us.
        parsed = await _claude.generate_json(
            user,
            system=system,
            max_tokens=3500,
            temperature=0.4,
        )
    except Exception as exc:  # noqa: BLE001
        logger.warning("GameplanAI fell back to mock: %s", exc)
        plan = _mock_gameplan(inputs)
        cache_set(inputs, plan["gameplan"])
        return GameplanResult(gameplan=plan["gameplan"], cached=False, source="mock")

    gameplan = parsed.get("gameplan", parsed)
    gameplan.setdefault("metaVersion", inputs.patch_version or "unknown")
    gameplan["_source"] = "claude"
    cache_set(inputs, gameplan)

    usage = _claude.usage._history[-1] if _claude.usage._history else {}  # noqa: SLF001
    return GameplanResult(
        gameplan=gameplan,
        cached=False,
        input_tokens=int(usage.get("input_tokens", 0)),
        output_tokens=int(usage.get("output_tokens", 0)),
        source="claude",
    )
