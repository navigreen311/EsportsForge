"""Share-Win card spec builder (Agent #9).

Produces the JSON spec that AnimaForge consumes to render a 1200x630, 30fps
branded share card. Every supported ``trigger_type`` has its own template per
blueprint Section 5; an unknown ``trigger_type`` returns the universal
``milestone-card`` fallback so the share-win pipeline never crashes on a new
or experimental trigger.

Output shape (consumed by ``AnimaForgeService.request_render``):

    {
      "template": "tournament-win-card",
      "duration": 20,
      "resolution": "1200x630",
      "fps": 30,
      "background": "#0A0C10",
      "accent_color": "#4ADE80",
      "logo": "esportsforge-white",
      "watermark": "esportsforge.gg",
      "gamertag": "<display_name>",
      "sequence": [...],
      "share_text": "...",
      "hashtags": ["#EsportsForge", ...],
    }
"""

from __future__ import annotations

from typing import Any, Mapping

# ---------------------------------------------------------------------------
# Brand constants (verbatim from blueprint Section 5)
# ---------------------------------------------------------------------------

BRAND_BACKGROUND = "#0A0C10"        # EsportsForge dark
BRAND_ACCENT = "#4ADE80"             # EsportsForge green
BRAND_LOGO = "esportsforge-white"
BRAND_WATERMARK = "esportsforge.gg"
RESOLUTION = "1200x630"              # OG image + Twitter card
FPS = 30


def _base_style(user: Any) -> dict[str, Any]:
    """Common branding applied to every share card."""
    return {
        "background": BRAND_BACKGROUND,
        "accent_color": BRAND_ACCENT,
        "logo": BRAND_LOGO,
        "watermark": BRAND_WATERMARK,
        "resolution": RESOLUTION,
        "fps": FPS,
        "gamertag": _gamertag(user),
    }


def _gamertag(user: Any) -> str:
    """Resolve a display name from a User-like object or mapping."""
    if user is None:
        return "Player"
    if isinstance(user, Mapping):
        return (
            user.get("display_name")
            or user.get("username")
            or user.get("email", "Player").split("@")[0]
        )
    return (
        getattr(user, "display_name", None)
        or getattr(user, "username", None)
        or getattr(user, "email", "Player").split("@")[0]
        or "Player"
    )


# ---------------------------------------------------------------------------
# Per-trigger templates
# ---------------------------------------------------------------------------

def _tournament_win(data: dict[str, Any], user: Any) -> dict[str, Any]:
    base = _base_style(user)
    tournament_name = data.get("tournament_name", "Tournament")
    record = data.get("record", "")
    title_id = data.get("title_id", "")
    return {
        **base,
        "template": "tournament-win-card",
        "duration": 20,
        "sequence": [
            {"t": 0,  "action": "logo-intro",       "duration": 2},
            {"t": 2,  "action": "trophy-animation", "duration": 4},
            {"t": 6,  "action": "stat-reveal",      "stat": tournament_name, "duration": 3},
            {"t": 9,  "action": "record-reveal",    "stat": record,          "duration": 3},
            {"t": 12, "action": "gamertag-reveal",  "text": base["gamertag"], "duration": 3},
            {"t": 15, "action": "title-reveal",     "text": title_id,         "duration": 3},
            {"t": 18, "action": "cta",              "duration": 2},
        ],
        "share_text": (
            f"Just won the {tournament_name} on @EsportsForge — Built to Win."
        ),
        "hashtags": ["#EsportsForge", f"#{title_id}" if title_id else "#BuiltToWin"],
    }


def _benchmark_milestone(data: dict[str, Any], user: Any) -> dict[str, Any]:
    base = _base_style(user)
    skill = data.get("skill", "Skill")
    percentile = int(data.get("percentile", 10))
    title_id = data.get("title_id", "")
    return {
        **base,
        "template": "percentile-milestone-card",
        "duration": 15,
        "sequence": [
            {"t": 0,  "action": "logo-intro",      "duration": 2},
            {"t": 2,  "action": "meter-fill",      "target": percentile, "duration": 5},
            {"t": 7,  "action": "skill-reveal",    "text": skill,        "duration": 3},
            {"t": 10, "action": "gamertag-reveal", "text": base["gamertag"], "duration": 3},
            {"t": 13, "action": "cta",             "duration": 2},
        ],
        "share_text": f"Hit Top {percentile}% in {skill} — @EsportsForge",
        "hashtags": ["#EsportsForge", "#BuiltToWin", f"#{title_id}" if title_id else "#BenchmarkAI"],
    }


def _win_streak(data: dict[str, Any], user: Any) -> dict[str, Any]:
    base = _base_style(user)
    streak = int(data.get("streak", 5))
    title_id = data.get("title_id", "")
    return {
        **base,
        "template": "win-streak-card",
        "duration": 15,
        "sequence": [
            {"t": 0,  "action": "logo-intro",       "duration": 2},
            {"t": 2,  "action": "counter-animate",  "target": streak, "duration": 5},
            {"t": 7,  "action": "fire-effect",      "duration": 3},
            {"t": 10, "action": "gamertag-reveal",  "text": base["gamertag"], "duration": 3},
            {"t": 13, "action": "cta",              "duration": 2},
        ],
        "share_text": f"{streak}-game win streak on @EsportsForge",
        "hashtags": ["#EsportsForge", "#WinStreak", f"#{title_id}" if title_id else "#BuiltToWin"],
    }


def _impactrank_fix(data: dict[str, Any], user: Any) -> dict[str, Any]:
    base = _base_style(user)
    improvement = float(data.get("improvement", 0))
    fix_name = data.get("fix_name", "Fix")
    title_id = data.get("title_id", "")
    return {
        **base,
        "template": "improvement-card",
        "duration": 20,
        "sequence": [
            {"t": 0,  "action": "logo-intro",      "duration": 2},
            {"t": 2,  "action": "before-bar",      "label": "Before", "duration": 3},
            {"t": 5,  "action": "after-bar",       "label": "After",
             "improvement": improvement, "duration": 4},
            {"t": 9,  "action": "fix-name-reveal", "text": fix_name, "duration": 3},
            {"t": 12, "action": "stat-reveal",
             "stat": f"+{improvement}% Win Rate",  "duration": 3},
            {"t": 15, "action": "gamertag-reveal", "text": base["gamertag"], "duration": 3},
            {"t": 18, "action": "cta",             "duration": 2},
        ],
        "share_text": (
            f"Fixed my biggest weakness. Win rate up {improvement}% — @EsportsForge"
        ),
        "hashtags": ["#EsportsForge", "#ImpactRank", f"#{title_id}" if title_id else "#BuiltToWin"],
    }


def _playertwin_milestone(data: dict[str, Any], user: Any) -> dict[str, Any]:
    base = _base_style(user)
    accuracy = float(data.get("accuracy", 0.75))
    games_played = int(data.get("games_played", 0))
    title_id = data.get("title_id", "")
    pct = int(round(accuracy * 100))
    return {
        **base,
        "template": "playertwin-milestone-card",
        "duration": 15,
        "sequence": [
            {"t": 0,  "action": "logo-intro",       "duration": 2},
            {"t": 2,  "action": "twin-gauge-fill",  "target": pct,           "duration": 5},
            {"t": 7,  "action": "stat-reveal",
             "stat": f"{games_played} games played", "duration": 3},
            {"t": 10, "action": "gamertag-reveal",  "text": base["gamertag"], "duration": 3},
            {"t": 13, "action": "cta",              "duration": 2},
        ],
        "share_text": (
            f"My @EsportsForge PlayerTwin hit {pct}% accuracy after "
            f"{games_played} games"
        ),
        "hashtags": ["#EsportsForge", "#PlayerTwin", f"#{title_id}" if title_id else "#BuiltToWin"],
    }


def _milestone_fallback(data: dict[str, Any], user: Any) -> dict[str, Any]:
    """Universal fallback — used when ``trigger_type`` is unknown."""
    base = _base_style(user)
    title_id = data.get("title_id", "")
    return {
        **base,
        "template": "milestone-card",
        "duration": 15,
        "sequence": [
            {"t": 0,  "action": "logo-intro",       "duration": 2},
            {"t": 2,  "action": "milestone-reveal", "duration": 5},
            {"t": 7,  "action": "gamertag-reveal",  "text": base["gamertag"], "duration": 3},
            {"t": 10, "action": "stat-reveal",      "stat": "New milestone", "duration": 3},
            {"t": 13, "action": "cta",              "duration": 2},
        ],
        "share_text": "New milestone unlocked on @EsportsForge",
        "hashtags": ["#EsportsForge", "#BuiltToWin", f"#{title_id}" if title_id else "#Milestone"],
    }


# ---------------------------------------------------------------------------
# Public dispatcher
# ---------------------------------------------------------------------------

_BUILDERS = {
    "tournament-win":        _tournament_win,
    "benchmark-milestone":   _benchmark_milestone,
    "win-streak":            _win_streak,
    "impactrank-fix":        _impactrank_fix,
    "playertwin-milestone":  _playertwin_milestone,
}


def build_share_card_spec(
    trigger_type: str,
    trigger_data: dict[str, Any],
    user: Any,
) -> dict[str, Any]:
    """Return the AnimaForge spec for *trigger_type*.

    Unknown trigger types return the universal ``milestone-card`` fallback so
    the pipeline never crashes on a new or experimental trigger.
    """
    builder = _BUILDERS.get(trigger_type)
    if builder is None:
        return _milestone_fallback(trigger_data or {}, user)
    return builder(trigger_data or {}, user)


__all__ = [
    "BRAND_ACCENT",
    "BRAND_BACKGROUND",
    "BRAND_LOGO",
    "BRAND_WATERMARK",
    "FPS",
    "RESOLUTION",
    "build_share_card_spec",
]
