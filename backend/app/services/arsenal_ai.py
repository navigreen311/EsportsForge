"""ArsenalAI helpers — Claude prompts shared by /trigger, /discover, /upload."""

from __future__ import annotations

import json
import re
from typing import Any

import anthropic
from app.core.config import settings


CLAUDE_MODEL = "claude-sonnet-5"


# ---------------------------------------------------------------------------
# JSON parsing helpers
# ---------------------------------------------------------------------------

def _strip_json_fence(text: str) -> str:
    """Remove ```json fences if present."""
    text = text.strip()
    if text.startswith("```"):
        # remove leading ``` and optional language tag, plus trailing ```
        text = re.sub(r"^```(?:json)?\s*", "", text)
        text = re.sub(r"\s*```$", "", text)
    return text.strip()


def parse_json_object(text: str) -> dict[str, Any] | None:
    """Best-effort: extract the first JSON object from `text`."""
    try:
        return json.loads(_strip_json_fence(text))
    except Exception:
        match = re.search(r"\{.*\}", text, flags=re.DOTALL)
        if match:
            try:
                return json.loads(match.group(0))
            except Exception:
                return None
    return None


def _strip_cite_tags(text: str) -> str:
    """web_search injects <cite index="...">...</cite> tags inside string values —
    valid JSON content, but they pollute stored fields. Strip them."""
    text = re.sub(r"<cite\b[^>]*>", "", text)
    return text.replace("</cite>", "")


def _salvage_json_objects(text: str) -> list[dict[str, Any]]:
    """Extract every COMPLETE top-level {...} object from a (possibly truncated)
    JSON array. Robust to max_tokens truncation cutting off the final entry."""
    start = text.find("[")
    if start == -1:
        return []
    out: list[dict[str, Any]] = []
    i, n = start + 1, len(text)
    while i < n:
        while i < n and text[i] not in "{]":
            i += 1
        if i >= n or text[i] == "]":
            break
        depth, j, in_str, esc, closed = 0, i, False, False, False
        while j < n:
            ch = text[j]
            if in_str:
                if esc:
                    esc = False
                elif ch == "\\":
                    esc = True
                elif ch == '"':
                    in_str = False
            elif ch == '"':
                in_str = True
            elif ch == "{":
                depth += 1
            elif ch == "}":
                depth -= 1
                if depth == 0:
                    try:
                        obj = json.loads(text[i:j + 1])
                        if isinstance(obj, dict):
                            out.append(obj)
                    except Exception:
                        pass
                    closed = True
                    j += 1
                    break
            j += 1
        if not closed:  # truncated final object — stop here
            break
        i = j
    return out


def parse_json_array(text: str) -> list[dict[str, Any]]:
    """Best-effort: extract JSON objects from `text` — tolerant of ```json fences,
    web_search <cite> tags, and max_tokens truncation (salvages complete objects)."""
    text = _strip_cite_tags(_strip_json_fence(text))
    try:
        parsed = json.loads(text)
        if isinstance(parsed, list):
            return [p for p in parsed if isinstance(p, dict)]
        if isinstance(parsed, dict):
            return [parsed]
    except Exception:
        pass
    salvaged = _salvage_json_objects(text)
    if salvaged:
        return salvaged
    match = re.search(r"\[.*\]", text, flags=re.DOTALL)
    if match:
        try:
            arr = json.loads(match.group(0))
            return [p for p in arr if isinstance(p, dict)]
        except Exception:
            return []
    return []


# ---------------------------------------------------------------------------
# Prompts
# ---------------------------------------------------------------------------

TITLE_RULES = """\
TITLE-SPECIFIC RULES:

Football (madden-26, cfb-26):
- Trick plays: only when element of surprise is high
- Never suggest same trick play twice in a game
- Consider field position for fake punts/FGs
- Unstoppable concepts: suggest vs correct coverage shell

Basketball (nba-2k26):
- Cheese dribbles: only when defender overcommits
- Set plays: suggest when shot clock is under 10s
- Never suggest stamina moves when player is fatigued

Soccer (eafc-26):
- Skill combos: only in final third with space
- Cheese formations: suggest when trailing or protecting lead
- Dead ball tricks: only on set pieces

FPS (warzone, fortnite):
- Movement tech: suggest in high-pressure final circles
- Build resets (Fortnite): suggest when opponent is pushing
- Loadout exploits: suggest based on current equipped loadout

Fighting (ufc-5, undisputed):
- Submission setups: only when opponent is fatigued
- Strike exploits: suggest based on opponent health vs own health
- Never suggest stamina-heavy combos when own stamina is low

Baseball (mlb-26):
- Pitch sequences: suggest based on count and batter tendency
- Shift busters: suggest when defense has shifted
- Only suggest high-risk plays in appropriate score situations

Golf (pga-2k25):
- Wind exploits: suggest when specific wind conditions match
- Shot shapes: suggest for difficult lies and angles
- Pressure putts: suggest optimal line read technique

Video Poker (video-poker):
- Optimal holds: always suggest based on dealt hand
- Never suggest high-variance plays without sufficient credits
"""


def build_trigger_system(title_id: str, saved_weapons: list[dict[str, Any]],
                         game_state: dict[str, Any]) -> str:
    return f"""\
You are ArsenalAI for EsportsForge.
Title: {title_id}
Player saved weapons: {json.dumps(saved_weapons)}
Current game state: {json.dumps(game_state)}

Evaluate each saved weapon against the current game state.
Check trigger conditions match the game state.
Consider: element of surprise, risk vs reward, timing.

{TITLE_RULES}

If a weapon should deploy, return ONLY JSON:
{{ "trigger": true, "weapon_id": "<id>", "reason": "<why>",
   "urgency": "now"|"soon"|"watch",
   "timing": "<specific timing instruction>" }}

If nothing ready, return ONLY JSON: {{ "trigger": false }}

No markdown, no preamble.
"""


def build_discover_system(title_id: str, patch_version: str | None) -> str:
    pv = patch_version or "latest"
    return f"""\
You are ArsenalAI for EsportsForge.
Search the web for secret weapons and trick plays for {title_id}.
Current patch: {pv}

For each play/technique found, extract:
- name: clear descriptive name
- category: appropriate for {title_id}
- formation: in-game formation if known (or null)
- play_name: exact in-game move/play name (or null)
- description: what it does and why it works
- instructions: array of numbered execution steps
- setup_steps: pre-execution setup array
- when_to_use: human-readable trigger description
- trigger_conditions: structured JSON conditions
- difficulty: easy | medium | hard
- source_url: where you found it

TITLE-SPECIFIC FORMATTING:
Football: include formation, play name, down/distance triggers
Basketball: include move name, defender situation, shot clock
Soccer: include skill move name, field zone, score situation
FPS: include loadout, circle phase, positioning
Fighting: include stance, stamina context, distance
Baseball: include count, pitch name, batter situation
Golf: include club, wind conditions, lie type
Poker: include hand type, optimal hold pattern

Return ONLY a valid JSON array of AT MOST 6 plays. No markdown. No preamble. No <cite> tags.
Format: [{{ "name", "category", "formation", "play_name",
"description", "instructions": [], "setup_steps": [], "when_to_use",
"trigger_conditions": {{}}, "difficulty", "source_url" }}]

Limit to 6 results.
"""


def build_extract_system(title_id: str) -> str:
    return f"""\
You are ArsenalAI for EsportsForge.
Analyze user-submitted content describing a play/move for {title_id} and
extract a structured weapon.

Return ONLY JSON with the keys:
  name, category, formation (nullable), play_name (nullable),
  description, setup_steps: [], instructions: [], when_to_use,
  trigger_conditions: {{}}, difficulty: "easy"|"medium"|"hard",
  tags: []

Title-specific extraction rules:
Football: identify formation, play name, pre-snap adjustments
Basketball: identify move type, button sequence if mentioned
Soccer: identify skill move name, field zone, setup
FPS: identify positioning, loadout, movement technique
Fighting: identify combo, timing, stance requirements
Baseball: identify pitch type, sequence, count situation
Golf: identify club selection, shot shape, conditions
Poker: identify hand type, hold pattern, paytable context

No markdown. No preamble.
"""


# ---------------------------------------------------------------------------
# Anthropic client (sync + async helpers)
# ---------------------------------------------------------------------------

def _client() -> anthropic.AsyncAnthropic | None:
    key = settings.anthropic_api_key
    if not key:
        return None
    return anthropic.AsyncAnthropic(api_key=key)


async def call_claude(
    *,
    system: str,
    user_content: str | list[dict[str, Any]],
    max_tokens: int = 1500,
    tools: list[dict[str, Any]] | None = None,
) -> str:
    """Plain text-out Claude call. Returns "" if no API key configured."""
    client = _client()
    if client is None:
        return ""

    kwargs: dict[str, Any] = {
        "model": CLAUDE_MODEL,
        "max_tokens": max_tokens,
        "system": system,
        "messages": [
            {
                "role": "user",
                "content": user_content
                if isinstance(user_content, list)
                else user_content,
            }
        ],
    }
    if tools:
        kwargs["tools"] = tools

    response = await client.messages.create(**kwargs)
    chunks: list[str] = []
    for block in response.content:
        if getattr(block, "type", None) == "text":
            chunks.append(block.text)
    return "".join(chunks)
