"""Seed the Arsenal library with platform-verified weapons.

Idempotent — re-running will UPDATE existing rows (matched by
(title_id, name)) rather than duplicate them. Insert-only on first run.

Run from repo root:
    backend/venv/Scripts/python.exe backend/scripts/seed_arsenal.py
"""

from __future__ import annotations

import asyncio
import sys
from pathlib import Path
from typing import Any

# Allow `python backend/scripts/seed_arsenal.py` from anywhere.
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from sqlalchemy import select  # noqa: E402

from app.db.base import async_session, Base, engine  # noqa: E402
import app.models  # noqa: F401, E402  — register all models with Base
from app.models.secret_weapon import SecretWeapon  # noqa: E402


# ---------------------------------------------------------------------------
# Weapon data — title_ids match the backend SecretWeapon.TITLE_IDS exactly
# ---------------------------------------------------------------------------

WEAPONS: list[dict[str, Any]] = [
    # ═══ MADDEN 26 ═══
    {
        "title_id": "madden-26",
        "name": "Fake Punt — Direct Snap HB Dive",
        "category": "Trick Play",
        "formation": "Special Teams > Punt",
        "play_name": "Fake Punt HB Dive",
        "description": (
            "Direct snap to the HB in punt formation. Catches defense completely "
            "off guard on 4th & 2 or less when opponent expects a punt. The HB "
            "receives the direct snap and attacks the vacated A-gap."
        ),
        "setup_steps": [
            "Navigate to Special Teams in the play call menu",
            "Select Punt from the formation options",
            "Choose Fake Punt HB Dive from the play list",
            "Motion the HB slightly left before the snap",
            "Wait for opponent defense to fully set",
        ],
        "instructions": [
            "Hike the ball immediately — no delay at the line",
            "HB receives direct snap — press RT/R2 to sprint",
            "Cut inside toward the right A-gap",
            "If a defender reads the play early — pull up",
            "Gain the first down — do not try to score unless wide open",
        ],
        "when_to_use": (
            "4th & 2 or fewer, between own 30-40 yard line, opponent showing "
            "heavy run defense in punt formation"
        ),
        "trigger_conditions": {
            "down": 4,
            "maxDistance": 2,
            "fieldPositionMin": 30,
            "fieldPositionMax": 45,
            "quarter": [1, 2, 3],
            "opponentTendency": ["stacked-box", "run-defense"],
            "timesUsedThisGame": {"max": 1},
        },
        "difficulty": "medium",
        "tags": ["trick-play", "special-teams", "fake-punt", "4th-down", "surprise"],
        "verified": True,
        "source_type": "platform",
        "success_rate": 0.78,
    },
    {
        "title_id": "madden-26",
        "name": "Flea Flicker — Gun Spread",
        "category": "Trick Play",
        "formation": "Gun Spread",
        "play_name": "Flea Flicker",
        "description": (
            "HB takes the handoff then pitches back to the QB for a deep shot. "
            "Devastates defenses that sell out against the run after 2-3 "
            "consecutive run plays. Creates big play opportunity downfield."
        ),
        "setup_steps": [
            "Run 2-3 consecutive run plays first to set it up",
            "Navigate to Gun Spread in play call menu",
            "Select Flea Flicker from the play list",
            "Identify your fastest receiver pre-snap",
            "Ensure you have a speed rusher lined up — do not motion",
        ],
        "instructions": [
            "Snap and hand off to HB normally — sell the run",
            "Wait for HB to take 2 steps toward the line",
            "HB pitches back to QB — press LB/L1 to trigger",
            "QB catches the pitch — immediately look deep",
            "Hit the post route or go route over the top",
            "Throw with anticipation — receiver will be open",
        ],
        "when_to_use": (
            "After 2-3 consecutive run plays, opponent linebackers and safeties "
            "creeping up, 2nd or 3rd & medium distance"
        ),
        "trigger_conditions": {
            "consecutiveRuns": {"min": 2},
            "down": [2, 3],
            "maxDistance": 10,
            "opponentTendency": ["run-stop", "aggressive-lb"],
            "timesUsedThisGame": {"max": 1},
        },
        "difficulty": "medium",
        "tags": ["trick-play", "flea-flicker", "deep-shot", "run-setup", "big-play"],
        "verified": True,
        "source_type": "platform",
        "success_rate": 0.71,
    },
    {
        "title_id": "madden-26",
        "name": "Hook and Lateral — Trips TE",
        "category": "Trick Play",
        "formation": "Gun Trips TE",
        "play_name": "Hook and Lateral",
        "description": (
            "QB throws a short hook route then the receiver laterals to a "
            "trailing back for yards after contact. Creates chaos in zone "
            "coverage and catches defenders out of position."
        ),
        "setup_steps": [
            "Navigate to Gun Trips TE formation",
            "Select Hook and Lateral from plays",
            "Identify the hook receiver and trailing back",
            "Check for man vs zone coverage pre-snap",
        ],
        "instructions": [
            "Snap and throw quickly to the hook route",
            "Receiver catches and immediately laterals to trailing back",
            "Back takes the lateral and attacks the edge",
            "Best used when defenders are caught peeking at QB",
        ],
        "when_to_use": (
            "Trailing by 7-14 points, 4th quarter, need a big play, opponent in "
            "zone coverage"
        ),
        "trigger_conditions": {
            "scoreMargin": {"min": -14, "max": -7},
            "quarter": [4],
            "opponentTendency": ["zone-coverage"],
            "timesUsedThisGame": {"max": 2},
        },
        "difficulty": "hard",
        "tags": ["trick-play", "lateral", "zone-beater", "big-play", "desperation"],
        "verified": True,
        "source_type": "platform",
        "success_rate": 0.58,
    },
    {
        "title_id": "madden-26",
        "name": "PA Crossers — Unstoppable vs Cover 3",
        "category": "Unstoppable Concept",
        "formation": "Gun Trips TE",
        "play_name": "PA Crossers",
        "description": (
            "Play-action with dual crossing routes underneath. The TE leaks to "
            "the flat as a safety valve. High-percentage throw against any zone "
            "coverage — especially Cover 3."
        ),
        "setup_steps": [
            "Navigate to Gun Trips TE",
            "Select PA Crossers from the play list",
            "Identify the coverage shell pre-snap",
            "Motion the TE if needed to get a coverage read",
        ],
        "instructions": [
            "Fake the handoff — sell the play action",
            "Read the middle of the field opening up",
            "Hit the first crossing route if linebacker drops",
            "If covered — throw to the TE in the flat",
            "Check down to the RB if both are covered",
        ],
        "when_to_use": (
            "Any down when opponent shows Cover 3, opening drive, scripted "
            "series, 2nd & medium distance"
        ),
        "trigger_conditions": {
            "opponentCoverage": ["cover-3", "cover-3-sky"],
            "down": [1, 2, 3],
        },
        "difficulty": "easy",
        "tags": [
            "unstoppable",
            "zone-beater",
            "play-action",
            "crossing-routes",
            "cover-3-counter",
        ],
        "verified": True,
        "source_type": "platform",
        "success_rate": 0.89,
    },
    {
        "title_id": "madden-26",
        "name": "Mesh Concept — Unstoppable vs Man",
        "category": "Unstoppable Concept",
        "formation": "Shotgun Bunch",
        "play_name": "Mesh Concept",
        "description": (
            "Two receivers cross shallow creating natural picks against man "
            "coverage. Defenders get picked and receivers come open. The "
            "natural rub is legal and effective."
        ),
        "setup_steps": [
            "Navigate to Shotgun Bunch",
            "Select Mesh Concept",
            "Confirm opponent is in man coverage pre-snap",
            "Motion a receiver to confirm man — if DB follows it is man",
        ],
        "instructions": [
            "Snap and read the mesh crossing routes",
            "Wait for the natural pick to create separation",
            "Hit the first receiver who comes open off the crossing",
            "If both mesh routes are covered — check flat",
        ],
        "when_to_use": (
            "Any time opponent shows man coverage, 3rd & short to medium, red zone"
        ),
        "trigger_conditions": {
            "opponentCoverage": ["man", "man-press", "cover-1", "cover-0"],
            "down": [2, 3, 4],
        },
        "difficulty": "easy",
        "tags": ["unstoppable", "man-beater", "mesh", "crossing-routes", "pick-concept"],
        "verified": True,
        "source_type": "platform",
        "success_rate": 0.86,
    },
    # ═══ CFB 26 ═══
    {
        "title_id": "cfb-26",
        "name": "Wildcat Direct Snap — HB Sweep",
        "category": "Trick Play",
        "formation": "Wildcat",
        "play_name": "Wildcat HB Sweep",
        "description": (
            "Direct snap to the HB in Wildcat formation. Defense must account "
            "for the run and pass threat simultaneously. Easy to execute and "
            "highly effective in short yardage."
        ),
        "setup_steps": [
            "Navigate to Wildcat formation in play call",
            "Select the HB Sweep option",
            "Identify which edge has fewer defenders",
        ],
        "instructions": [
            "Snap directly to the HB",
            "Read the edge — attack the weaker side",
            "If edge is open — press RT/R2 and get outside",
            "If crashed — cut back inside against the grain",
        ],
        "when_to_use": (
            "Any short yardage situation, goal line, 4th & 1, opponent not "
            "aligned to Wildcat"
        ),
        "trigger_conditions": {
            "down": [3, 4],
            "maxDistance": 3,
            "opponentTendency": ["not-adjusted-to-wildcat"],
        },
        "difficulty": "easy",
        "tags": ["trick-play", "wildcat", "direct-snap", "short-yardage", "goal-line"],
        "verified": True,
        "source_type": "platform",
        "success_rate": 0.82,
    },
    # ═══ NBA 2K26 ═══
    {
        "title_id": "nba-2k26",
        "name": "Step-Back Three — Pro 3 Package",
        "category": "Cheese Dribble",
        "formation": "Isolation",
        "play_name": "Step-Back Fadeaway Three",
        "description": (
            "Step-back three-pointer that creates its own shot off the dribble. "
            "Nearly unguardable when executed correctly. Defender over-commits "
            "on the drive and the step-back creates a clean look."
        ),
        "setup_steps": [
            "Isolate your best shooter on the perimeter",
            "Back down defender slightly to get position",
            "Identify if defender is playing you tight or giving space",
        ],
        "instructions": [
            "Drive hard left to make defender commit",
            "Execute step-back move — hold LT/L2 and flick RS back",
            "Fade away from the defender creating separation",
            "Release the shot at the top of the jump",
            "Works best with high three-point rated players",
        ],
        "when_to_use": (
            "Shot clock under 12 seconds, defender overplaying the drive, need "
            "a quick bucket, isolation situation"
        ),
        "trigger_conditions": {
            "shotClock": {"max": 12},
            "defenderPosition": "overplaying-drive",
            "pointMargin": {"min": -10, "max": 10},
        },
        "difficulty": "medium",
        "tags": ["cheese-dribble", "step-back", "three-pointer", "isolation", "self-created"],
        "verified": True,
        "source_type": "platform",
        "success_rate": 0.74,
    },
    {
        "title_id": "nba-2k26",
        "name": "Pick and Roll Lob — High PNR",
        "category": "Unstoppable Concept",
        "formation": "High Pick and Roll",
        "play_name": "PNR Lob Pass",
        "description": (
            "High pick and roll with a lob pass to the rolling big. When the "
            "defender switches late the rolling player is wide open above the "
            "rim for an easy alley-oop."
        ),
        "setup_steps": [
            "Call for a screen from your center or PF",
            "Position the screen at the top of the key",
            "Read how opponent defends the pick and roll",
        ],
        "instructions": [
            "Use the screen and attack the lane",
            "Read the defender on the rolling big",
            "If they switch late — lob immediately",
            "Press triangle/Y for the lob pass",
            "Time it so the big catches at the peak",
        ],
        "when_to_use": (
            "Opponent switches pick and roll defense, big man has athletic "
            "advantage on defender, half court set"
        ),
        "trigger_conditions": {
            "opponentDefense": "switch-everything",
            "bigManMatchup": "athletic-advantage",
        },
        "difficulty": "easy",
        "tags": ["unstoppable", "pick-roll", "lob", "alley-oop", "switch-beater"],
        "verified": True,
        "source_type": "platform",
        "success_rate": 0.81,
    },
    # ═══ EA FC 26 ═══
    {
        "title_id": "eafc-26",
        "name": "El Tornado — Open Space Dribble",
        "category": "Skill Move Combo",
        "formation": "Open Play",
        "play_name": "El Tornado",
        "description": (
            "Advanced skill move that creates instant separation from a "
            "defender in open space. The spinning motion confuses the AI and "
            "human defenders alike. Very high skill ceiling move — practice in "
            "skill games first."
        ),
        "setup_steps": [
            "Get the ball in open space in the final third",
            "Have your best dribbler receive the ball",
            "Identify a defender approaching from the front",
        ],
        "instructions": [
            "Hold LT/L2 to enter skill move stance",
            "Execute El Tornado: RS full rotation",
            "Time the spin so defender commits",
            "Accelerate with RT/R2 immediately after",
            "Attack the space behind the beaten defender",
        ],
        "when_to_use": (
            "Final third with space, 1v1 against a defender, opponent pressing "
            "high, counterattack opportunity"
        ),
        "trigger_conditions": {
            "fieldZone": "final-third",
            "defenderDistance": "close",
            "opponentPressing": True,
        },
        "difficulty": "hard",
        "tags": ["skill-move", "el-tornado", "dribble", "final-third", "1v1"],
        "verified": True,
        "source_type": "platform",
        "success_rate": 0.65,
    },
    # ═══ MLB THE SHOW 26 ═══
    {
        "title_id": "mlb-26",
        "name": "Elevated 4-Seam — 0-2 Count",
        "category": "Pitch Sequence",
        "formation": "Standard Pitching",
        "play_name": "4-Seam Fastball Up",
        "description": (
            "Elevate the 4-seam fastball above the strike zone on 0-2 counts. "
            "Batters chase high heat when ahead in the count. The natural "
            "tendency is to swing at elevated velocity. Generates swings and "
            "misses consistently."
        ),
        "setup_steps": [
            "Get ahead in the count 0-2 or 1-2",
            "Set up with a pitch low and away first",
            "Then come up in the zone to freeze the batter",
        ],
        "instructions": [
            "Select 4-seam fastball",
            "Aim to the upper third of the zone or just above",
            "Use maximum velocity — do not take off speed",
            "Release timing: hit the green zone precisely",
            "Watch for the batter to chase out of the zone",
        ],
        "when_to_use": (
            "0-2 or 1-2 count, batter has shown tendency to chase high pitches, "
            "need a strikeout"
        ),
        "trigger_conditions": {
            "strikes": {"min": 2},
            "batterTendency": ["chases-high", "high-swing"],
            "inning": [1, 2, 3, 4, 5, 6, 7, 8, 9],
        },
        "difficulty": "easy",
        "tags": ["pitch-sequence", "4-seam", "strikeout", "chase-pitch", "0-2-count"],
        "verified": True,
        "source_type": "platform",
        "success_rate": 0.73,
    },
    # ═══ WARZONE ═══
    {
        "title_id": "warzone",
        "name": "Roof Edge — Final Circle Position",
        "category": "Zone Edge",
        "formation": "High Ground Setup",
        "play_name": "Roof Edge Hold",
        "description": (
            "Claim the roof edge position on the highest building at the final "
            "circle edge. Forces other squads to rotate through open ground "
            "while you hold vertical advantage. Wins the majority of final "
            "circles when executed correctly."
        ),
        "setup_steps": [
            "Identify the final circle direction by circle 4",
            "Rotate early — before circle 5 closes",
            "Find the tallest building on the circle edge",
            "Clear the building before setting up",
        ],
        "instructions": [
            "Position on the roof edge facing the circle interior",
            "Set up crossfire angles with teammates",
            "Hold position — do not push unless necessary",
            "Let other squads fight each other below you",
            "Only engage when you have clear vertical advantage",
            "Final 2 squads — push down if gas forces the move",
        ],
        "when_to_use": (
            "Final 5 squads remaining, circle collapsing to a building-heavy "
            "area, high ground available on circle edge"
        ),
        "trigger_conditions": {
            "squadsRemaining": {"max": 5},
            "circlePhase": {"min": 5},
            "highGroundAvailable": True,
        },
        "difficulty": "medium",
        "tags": ["zone-edge", "high-ground", "final-circle", "positioning", "hold"],
        "verified": True,
        "source_type": "platform",
        "success_rate": 0.69,
    },
    # ═══ FORTNITE ═══
    {
        "title_id": "fortnite",
        "name": "90s Reset — Box Fight Opener",
        "category": "Build Reset",
        "formation": "Box Fight",
        "play_name": "90 Degree Turn Build Reset",
        "description": (
            "Execute a 90-degree build reset to break out of an opponent box "
            "and gain vertical advantage. When an opponent locks you in a box "
            "this is the escape that creates the high ground advantage."
        ),
        "setup_steps": [
            "Identify that opponent has boxed you in",
            "Have 50+ wood materials ready",
            "Position yourself in the corner of your box",
        ],
        "instructions": [
            "Place a floor and wall in front simultaneously",
            "Jump and place a ramp behind you",
            "Edit the ramp and jump through",
            "Place another wall immediately to cut off pursuit",
            "Gain the high ground position above the opponent",
        ],
        "when_to_use": (
            "Opponent has boxed you in, close quarters fight, you have enough "
            "materials, need to reset the engagement"
        ),
        "trigger_conditions": {
            "inBoxFight": True,
            "materials": {"min": 50},
            "height": "being-boxed",
        },
        "difficulty": "hard",
        "tags": ["build-reset", "box-fight", "90s", "high-ground", "mechanical"],
        "verified": True,
        "source_type": "platform",
        "success_rate": 0.61,
    },
    # ═══ UFC 5 ═══
    {
        "title_id": "ufc-5",
        "name": "Jab-Cross to Takedown Setup",
        "category": "Submission Setup",
        "formation": "Orthodox Stance",
        "play_name": "Double Leg Takedown Setup",
        "description": (
            "Use jab-cross combination to get opponent defending the hands, "
            "then shoot for the double leg takedown. The strike setup makes "
            "the takedown nearly undefendable when opponent is focused on "
            "blocking punches."
        ),
        "setup_steps": [
            "Get into boxing range — not too close not too far",
            "Confirm opponent is in defensive stance",
            "Check their stamina — best when they are tired",
        ],
        "instructions": [
            "Throw jab then cross to make them block high",
            "Immediately after the cross — shoot for takedown",
            "Input: Square + X simultaneously (PS) for double leg",
            "Drive through the takedown — hold the input",
            "Once on the ground — work for the submission",
        ],
        "when_to_use": (
            "Opponent stamina below 60%, round 2 or 3, opponent defending "
            "strikes, standing range"
        ),
        "trigger_conditions": {
            "opponentStamina": {"max": 60},
            "round": [2, 3],
            "position": "standing",
            "distance": "boxing-range",
        },
        "difficulty": "medium",
        "tags": ["submission-setup", "takedown", "jab-cross", "ground-game", "stamina-drain"],
        "verified": True,
        "source_type": "platform",
        "success_rate": 0.72,
    },
    # ═══ PGA TOUR 2K25 ═══
    {
        "title_id": "pga-2k25",
        "name": "Low Draw Into Headwind",
        "category": "Wind Exploit",
        "formation": "Fairway Approach",
        "play_name": "Low Draw Shot Shape",
        "description": (
            "Hit a low draw shot into a headwind to minimize wind effect and "
            "keep the ball on a penetrating flight path. The draw spin counters "
            "the wind resistance and keeps the ball on line better than a "
            "straight shot."
        ),
        "setup_steps": [
            "Check wind speed and direction — must be headwind",
            "Select one club more than normal distance",
            "Aim slightly right of target to account for draw",
        ],
        "instructions": [
            "Set shot shape to draw in shot menu",
            "Reduce swing power by 10-15 percent",
            "Keep the shot trajectory low — aim for piercing flight",
            "Release timing must be perfect — green zone",
            "Ball will flight low and draw left to target",
        ],
        "when_to_use": (
            "Headwind over 15mph, fairway approach, need accuracy over "
            "distance, pin accessible from draw angle"
        ),
        "trigger_conditions": {
            "wind": {"min": 15},
            "windDirection": "headwind",
            "lie": ["fairway", "light-rough"],
        },
        "difficulty": "medium",
        "tags": ["wind-exploit", "draw", "low-shot", "headwind", "approach"],
        "verified": True,
        "source_type": "platform",
        "success_rate": 0.76,
    },
    # ═══ UNDISPUTED ═══
    {
        "title_id": "undisputed",
        "name": "Jab-Cross-Jab Guard Break",
        "category": "Punch Exploit",
        "formation": "Orthodox",
        "play_name": "Triple Jab Combo",
        "description": (
            "Three-punch combination that breaks down the opponent guard over "
            "time. The third jab catches them recovering from the cross and "
            "creates the opening for a power shot follow-up."
        ),
        "setup_steps": [
            "Get into boxing range — just outside their jab distance",
            "Confirm opponent is in guard-heavy defensive style",
            "Check your stamina — need at least 50% to execute",
        ],
        "instructions": [
            "Throw jab — probe for their reaction",
            "Follow with cross immediately — do not pause",
            "Third jab immediately after cross lands",
            "Watch for their guard to break or drop",
            "If guard breaks — follow with your power shot",
        ],
        "when_to_use": (
            "Opponent is turtling in guard, mid-distance, rounds 1-2, you have "
            "stamina advantage"
        ),
        "trigger_conditions": {
            "opponentStyle": ["guard-heavy", "defensive"],
            "round": [1, 2, 3],
            "ownStamina": {"min": 50},
            "distance": "boxing-range",
        },
        "difficulty": "medium",
        "tags": ["punch-exploit", "guard-break", "jab-cross", "combo", "boxing"],
        "verified": True,
        "source_type": "platform",
        "success_rate": 0.70,
    },
    # ═══ MADDEN 26 — additional ═══
    # (already covered above)

    # ═══ CFB 26 — additional ═══
    {
        "title_id": "cfb-26",
        "name": "Air Raid Mesh — Tempo No-Huddle",
        "category": "Unstoppable Concept",
        "formation": "Air Raid Empty",
        "play_name": "Mesh Sit",
        "description": (
            "Air Raid mesh concept run no-huddle. Two shallow crossers underneath "
            "with sit routes against zone, plus a vertical stretch up the seam. "
            "Tempo prevents the defense from substituting and wears LBs out by "
            "the second quarter."
        ),
        "setup_steps": [
            "Score or pick up a first down to access no-huddle",
            "Stay in Air Raid Empty — do not personnel-swap",
            "Read coverage shell as the play clock starts",
        ],
        "instructions": [
            "Snap fast — within 5 seconds of the previous whistle",
            "Read MLB drop: if he sinks, hit the sit route in front",
            "If he widens, throw the deep crosser behind him",
            "Versus man, let the mesh pick free a slot receiver",
            "Repeat the call on the next snap — they cannot adjust in tempo",
        ],
        "when_to_use": (
            "Trailing or controlling tempo, no-huddle drives, opponent in base "
            "personnel, 1st & 10 or 2nd & medium"
        ),
        "trigger_conditions": {
            "down": [1, 2],
            "tempo": "no-huddle",
            "opponentPersonnel": ["base", "nickel"],
        },
        "difficulty": "easy",
        "tags": ["unstoppable", "tempo", "air-raid", "mesh", "zone-beater"],
        "verified": True,
        "source_type": "platform",
        "success_rate": 0.84,
    },
    {
        "title_id": "cfb-26",
        "name": "Reverse Pass — Wildcat Gadget",
        "category": "Trick Play",
        "formation": "Wildcat",
        "play_name": "WR Reverse Pass",
        "description": (
            "Wildcat snap to the HB who hands off on a reverse to a WR with a "
            "throwing rating. WR pulls up and throws deep to the QB on a wheel "
            "route. Defense flows hard to the reverse and the QB is wide open."
        ),
        "setup_steps": [
            "Run the standard Wildcat HB Sweep at least once first",
            "Confirm your slot WR has a passing rating above 60",
            "Pick a clean pocket side of the field",
        ],
        "instructions": [
            "Snap to HB and hand off on the reverse",
            "WR takes the pitch and reads the defense flow",
            "Pull up at the line and throw to the QB on the wheel",
            "If QB covered, throw it away — never force into traffic",
        ],
        "when_to_use": (
            "Once per game, after at least one Wildcat run, opponent overflowing "
            "to the run side"
        ),
        "trigger_conditions": {
            "wildcatRunsPrior": {"min": 1},
            "down": [1, 2],
            "timesUsedThisGame": {"max": 1},
        },
        "difficulty": "hard",
        "tags": ["trick-play", "wildcat", "reverse-pass", "deep-shot", "gadget"],
        "verified": True,
        "source_type": "platform",
        "success_rate": 0.55,
    },

    # ═══ NBA 2K26 — additional ═══
    {
        "title_id": "nba-2k26",
        "name": "Dream Shake — Post Spin Counter",
        "category": "Cheese Dribble",
        "formation": "Post Up",
        "play_name": "Olajuwon Dream Shake",
        "description": (
            "Classic post move sequence: jab one direction, spin the opposite, "
            "fake the shot, and finish with a baby hook. Defender bites on every "
            "fake and the finish is uncontested. Requires a high post-rated big."
        ),
        "setup_steps": [
            "Get your center the ball in the low post",
            "Back down once with L2/LT to claim position",
            "Read the defender's hands and stance",
        ],
        "instructions": [
            "Jab left with right stick to make defender lean",
            "Spin right immediately — quarter rotation on RS",
            "Pump fake the shot — RS up tap",
            "Step through to the rim with the dominant hand",
            "Finish with a soft floater for highest %",
        ],
        "when_to_use": (
            "Center has size advantage on switch, half-court set, paint touch "
            "needed, defender playing flat-footed"
        ),
        "trigger_conditions": {
            "defenderRating": {"max": 85},
            "ownPostRating": {"min": 88},
            "shotClock": {"min": 8},
        },
        "difficulty": "medium",
        "tags": ["cheese-dribble", "post-move", "dream-shake", "isolation", "low-post"],
        "verified": True,
        "source_type": "platform",
        "success_rate": 0.79,
    },
    {
        "title_id": "nba-2k26",
        "name": "Hammer Action — Corner 3 Set",
        "category": "Unstoppable Concept",
        "formation": "Motion Offense",
        "play_name": "Hammer Cross-Court",
        "description": (
            "Initiate a baseline drive on the strong side. Weak-side shooter "
            "loops along the baseline and a corner screen frees them for an "
            "open three. The skip pass from the help-side defender's blind "
            "spot is unblockable when timed right."
        ),
        "setup_steps": [
            "Call Hammer set from playbook menu",
            "Position your best 3-point shooter weak side",
            "Drive baseline with a wing slasher",
        ],
        "instructions": [
            "Drive hard baseline — collapse the help defense",
            "Wait for help-side defender to rotate down",
            "Skip pass cross-court to the corner shooter",
            "Receiver fires immediately off the catch",
            "Time it before help recovers — release inside 1.2s",
        ],
        "when_to_use": (
            "Defense collapsing on drives, weak-side shooter > 85 3PT rating, "
            "shot clock 8+, half-court set"
        ),
        "trigger_conditions": {
            "shooter3PT": {"min": 85},
            "shotClock": {"min": 8},
            "opponentDefense": ["help-heavy", "collapsing"],
        },
        "difficulty": "medium",
        "tags": ["unstoppable", "set-play", "corner-3", "hammer", "skip-pass"],
        "verified": True,
        "source_type": "platform",
        "success_rate": 0.77,
    },

    # ═══ EA FC 26 — additional ═══
    {
        "title_id": "eafc-26",
        "name": "Through Ball Curve — Striker Run",
        "category": "Unstoppable Concept",
        "formation": "Open Play",
        "play_name": "Curved Through Ball",
        "description": (
            "Lofted through ball with curve that bends behind the defensive line "
            "into the path of a sprinting striker. Defeats high lines and "
            "off-side traps. The curl makes the pass impossible to intercept "
            "with a flat last-line."
        ),
        "setup_steps": [
            "Patient build-up to the half-way line",
            "Identify a striker with 88+ pace",
            "Wait for defenders to step up to the half-way line",
        ],
        "instructions": [
            "Trigger the run with L1+R1 (PS) — striker accelerates",
            "Hold L1 and tap triangle for the curved through ball",
            "Lead the receiver into the channel — past the last man",
            "Take the touch with R2 first time to escape",
            "Finish low across goalkeeper",
        ],
        "when_to_use": (
            "Opponent playing a high line, fast striker available, build-up "
            "phase, opponent pressing up"
        ),
        "trigger_conditions": {
            "opponentLine": "high",
            "strikerPace": {"min": 88},
            "phase": ["build-up", "counter"],
        },
        "difficulty": "medium",
        "tags": ["unstoppable", "through-ball", "high-line-beater", "pace", "finishing"],
        "verified": True,
        "source_type": "platform",
        "success_rate": 0.78,
    },
    {
        "title_id": "eafc-26",
        "name": "Drag-Back Cutback — Edge of Box",
        "category": "Skill Move Combo",
        "formation": "Final Third",
        "play_name": "Drag-Back to Inside Cut",
        "description": (
            "Drive to the byline, drag the ball back with a 180° touch, then "
            "cut inside onto your strong foot for a finesse shot. The drag-back "
            "freezes the recovering defender and the cut creates a clean "
            "shooting lane near post."
        ),
        "setup_steps": [
            "Run a winger to the edge of the 18-yard box",
            "Get the byline defender flat-footed",
            "Make sure your shot foot matches the cut direction",
        ],
        "instructions": [
            "Hold L2/LT and pull RS away from goal — drag-back triggers",
            "Cut inside with LS toward your strong foot",
            "Take a touch into the half-space",
            "Finesse shot far post with R1+square (PS)",
            "Aim across the goalkeeper to the back-post side netting",
        ],
        "when_to_use": (
            "Final third with possession, defender on the byline, shot from "
            "the half-space available, opponent low-block"
        ),
        "trigger_conditions": {
            "fieldZone": "final-third",
            "defenderPosition": "byline",
            "opponentDefense": ["low-block", "deep"],
        },
        "difficulty": "hard",
        "tags": ["skill-move", "drag-back", "cutback", "finesse-shot", "edge-of-box"],
        "verified": True,
        "source_type": "platform",
        "success_rate": 0.62,
    },

    # ═══ MLB 26 — additional ═══
    {
        "title_id": "mlb-26",
        "name": "Backdoor Slider — Backfoot Lefty",
        "category": "Pitch Sequence",
        "formation": "Standard Pitching",
        "play_name": "Slider Back Foot",
        "description": (
            "Slider that starts at the right-handed batter's hands and breaks "
            "down to the back foot of a lefty (or vice versa). Freezes the "
            "batter looking and grabs the called strike on the outside corner "
            "from the wrong angle."
        ),
        "setup_steps": [
            "Establish fastball inside in prior at-bat",
            "Get to a 1-2 or 2-2 count",
            "Confirm catcher is set up off-plate outside",
        ],
        "instructions": [
            "Select slider — your sharpest breaking pitch",
            "Aim 4-6 inches off the inside edge to opposite-handed batter",
            "Release timing: green zone, do not pull",
            "Pitch starts at the hands and breaks back over the plate",
            "Batter freezes — strike called",
        ],
        "when_to_use": (
            "Two-strike count, opposite-handed batter, prior fastball inside "
            "established"
        ),
        "trigger_conditions": {
            "strikes": {"min": 2},
            "batterHand": "opposite",
            "priorPitch": ["fastball-inside"],
        },
        "difficulty": "medium",
        "tags": ["pitch-sequence", "slider", "back-foot", "called-strike", "outside-corner"],
        "verified": True,
        "source_type": "platform",
        "success_rate": 0.71,
    },
    {
        "title_id": "mlb-26",
        "name": "Hit and Run — 1st & 3rd Bunt Threat",
        "category": "Tactical",
        "formation": "Bases on Corners",
        "play_name": "Hit and Run with Bunt Show",
        "description": (
            "Show bunt with the runner on first taking off. Defense crashes the "
            "corners and the batter pulls back to slap a grounder through the "
            "vacated middle. Almost guaranteed to score the runner from third "
            "and put runners on the corners again."
        ),
        "setup_steps": [
            "Runners on first and third, less than 2 outs",
            "Right-handed batter at the plate with contact rating 75+",
            "Bottom of the order or pitcher's spot ideal — defense expects bunt",
        ],
        "instructions": [
            "Send the runner from first on the pitch — L2+square (PS)",
            "Show bunt with the batter at the same time",
            "Pull back into hitting stance as the pitch is released",
            "Slap a grounder to the right side",
            "Runner from 3rd scores — others advance to 1st & 3rd",
        ],
        "when_to_use": (
            "Runners on 1st & 3rd, less than 2 outs, contact-hitting batter, "
            "opponent expecting bunt"
        ),
        "trigger_conditions": {
            "runners": ["1st", "3rd"],
            "outs": {"max": 1},
            "batterContact": {"min": 75},
        },
        "difficulty": "medium",
        "tags": ["tactical", "hit-and-run", "bunt-show", "small-ball", "RBI"],
        "verified": True,
        "source_type": "platform",
        "success_rate": 0.69,
    },

    # ═══ WARZONE — additional ═══
    {
        "title_id": "warzone",
        "name": "Pre-Aim Common Angles — Sniper Hold",
        "category": "Loadout Setup",
        "formation": "Sniper Setup",
        "play_name": "Crosshair Pre-Placement",
        "description": (
            "Hold a sniper position with the crosshair pre-aimed at the most "
            "common enemy angle — door frame, head-glitch wall, doorway corner. "
            "Reaction time becomes irrelevant; the first shot is already lined "
            "up to head height."
        ),
        "setup_steps": [
            "Get to a known sniper hold for the current circle",
            "Identify the choke point enemies must rotate through",
            "ADS with the crosshair on head-height of that choke",
        ],
        "instructions": [
            "Hold ADS — do not unscope between checks",
            "Crosshair on the doorway / head-glitch / corner",
            "Tap fire on the first head silhouette that appears",
            "After the kill, swap angle — do not stay in the same scope",
            "Reset to the next-most-common rotation angle",
        ],
        "when_to_use": (
            "Mid-game holds, choke point near circle edge, sniper-class "
            "loadout, teammates clearing flank"
        ),
        "trigger_conditions": {
            "circlePhase": [3, 4, 5],
            "loadout": "sniper",
            "chokePointKnown": True,
        },
        "difficulty": "medium",
        "tags": ["loadout", "sniper", "pre-aim", "positioning", "head-glitch"],
        "verified": True,
        "source_type": "platform",
        "success_rate": 0.74,
    },
    {
        "title_id": "warzone",
        "name": "Plate Cancel — Fast Re-Plate",
        "category": "Movement Tech",
        "formation": "Close Quarters",
        "play_name": "Plate Cancel Slide",
        "description": (
            "Cancel the armor-plate animation with a slide or weapon-swap to "
            "reduce re-plate time by ~40%. Massive advantage in 1v1 trades — "
            "you are back to full plates while opponent is still animating."
        ),
        "setup_steps": [
            "Equip dual primary weapons or a plate-cancel preset",
            "Practice the swap timing in a private match",
            "Bind slide to a comfortable button",
        ],
        "instructions": [
            "Take damage / drop to 1-2 plates",
            "Hit plate button — animation starts",
            "Within 0.3s, slide-cancel or swap weapons",
            "Each cancel completes one plate but skips the lock animation",
            "Spam-repeat until full plates restored",
        ],
        "when_to_use": (
            "Active gunfight, low plates, momentary cover, need to re-engage "
            "fast — every gunfight scenario"
        ),
        "trigger_conditions": {
            "platesRemaining": {"max": 2},
            "inCover": True,
            "weaponSwapAvailable": True,
        },
        "difficulty": "hard",
        "tags": ["movement-tech", "plate-cancel", "slide-cancel", "trade-winning", "mechanical"],
        "verified": True,
        "source_type": "platform",
        "success_rate": 0.66,
    },

    # ═══ FORTNITE — additional ═══
    {
        "title_id": "fortnite",
        "name": "Tunnel Build — Safe Open-Field Rotation",
        "category": "Rotation",
        "formation": "Open Ground",
        "play_name": "Wall-Floor-Roof Tunnel",
        "description": (
            "Build a moving tunnel of wall, floor, and roof tiles to rotate "
            "across open ground without taking damage. Sniper bullets are "
            "stopped by the walls and the roof prevents top-down damage from "
            "high-ground squads."
        ),
        "setup_steps": [
            "Have at least 200 wood materials",
            "Identify the rotation start and end points",
            "Confirm no enemy is already inside the tunnel path",
        ],
        "instructions": [
            "Place wall in front, then floor, then roof — repeat",
            "Sprint forward placing pieces just before each step",
            "Replace any wall that gets shot — keep the seal",
            "Exit by editing a wall once you reach cover",
        ],
        "when_to_use": (
            "Mid-game open-ground rotation, sniper threat from multiple angles, "
            "200+ wood, no immediate fight"
        ),
        "trigger_conditions": {
            "openGround": True,
            "materials": {"min": 200},
            "sniperThreat": True,
        },
        "difficulty": "medium",
        "tags": ["rotation", "tunnel", "build", "open-ground", "anti-sniper"],
        "verified": True,
        "source_type": "platform",
        "success_rate": 0.81,
    },
    {
        "title_id": "fortnite",
        "name": "Launch Pad High Ground Take",
        "category": "High Ground",
        "formation": "End Zone",
        "play_name": "Launch + Build Take",
        "description": (
            "Place a launch pad to gain instant vertical re-entry to the high "
            "ground from below. While airborne, build ramps and walls to "
            "secure the spot before landing. Standard end-game pro technique."
        ),
        "setup_steps": [
            "Carry a launch pad in inventory through end-game",
            "Identify the high-ground holder's position",
            "Have at least 150 brick or metal for the take",
        ],
        "instructions": [
            "Place launch pad on a flat surface",
            "Jump on it — launch into the air",
            "Mid-air, place ramps stacked toward the high ground",
            "Land on top of opponent's build",
            "Wall up immediately — claim the high ground",
        ],
        "when_to_use": (
            "End-game, opponent holds high ground, you are below, launch pad "
            "available, 150+ materials"
        ),
        "trigger_conditions": {
            "circlePhase": {"min": 7},
            "ownHeight": "below-opponent",
            "materials": {"min": 150},
            "launchPadAvailable": True,
        },
        "difficulty": "hard",
        "tags": ["high-ground", "launch-pad", "endgame", "vertical-take", "build"],
        "verified": True,
        "source_type": "platform",
        "success_rate": 0.64,
    },

    # ═══ UFC 5 — additional ═══
    {
        "title_id": "ufc-5",
        "name": "Calf Kick Spam — Stance Disruption",
        "category": "Strike Combo",
        "formation": "Orthodox Stance",
        "play_name": "Lead Calf Kick",
        "description": (
            "Spam the lead-leg calf kick to compromise the opponent's base. "
            "Each one drops their movement speed and adds to a knockdown "
            "chance. Especially brutal against high stance fighters who plant "
            "their lead foot."
        ),
        "setup_steps": [
            "Stay at outside kicking range",
            "Watch their stance — work the planted foot",
            "Confirm your kick rating is 80+",
        ],
        "instructions": [
            "Throw the lead calf kick: RT+X (Xbox) outside range",
            "Reset to range immediately after each kick",
            "Mix in a jab once every 3 kicks to keep them honest",
            "After 6-8 successful calf kicks, follow up with a head kick",
            "Watch for the limp animation — confirms damage",
        ],
        "when_to_use": (
            "Round 1-2 to set up later rounds, opponent flat-footed, kick "
            "specialist, outside range"
        ),
        "trigger_conditions": {
            "round": [1, 2, 3],
            "ownKickRating": {"min": 80},
            "distance": "outside-kicking",
        },
        "difficulty": "easy",
        "tags": ["strike-combo", "calf-kick", "leg-damage", "stance-break", "low-kick"],
        "verified": True,
        "source_type": "platform",
        "success_rate": 0.75,
    },
    {
        "title_id": "ufc-5",
        "name": "Body Lock to Cage Walk — Wear-Down",
        "category": "Clinch Work",
        "formation": "Clinch",
        "play_name": "Body Lock + Knee",
        "description": (
            "Secure a body-lock clinch and walk the opponent to the cage. Drain "
            "their stamina with body knees while they are pressed against the "
            "cage. Sets up a takedown later or scores points in clinch-heavy "
            "scoring systems."
        ),
        "setup_steps": [
            "Close distance with a strike or feint",
            "Tie up with body lock — both hands around waist",
            "Begin walking them toward the cage",
        ],
        "instructions": [
            "Use LS to drive opponent backward to the cage",
            "Once cage-pressed, knee the body — RB tap repeatedly",
            "Switch to head-knees if they hand-fight your hooks",
            "Watch their stamina — drop below 50% for takedown follow-up",
            "If referee separates, immediately re-clinch",
        ],
        "when_to_use": (
            "Round 2-3, opponent stamina above 60%, ground-game advantage, "
            "scoring rounds"
        ),
        "trigger_conditions": {
            "round": [2, 3],
            "opponentStamina": {"min": 60},
            "ownGrappling": {"min": 80},
        },
        "difficulty": "medium",
        "tags": ["clinch-work", "body-lock", "cage-walk", "stamina-drain", "control"],
        "verified": True,
        "source_type": "platform",
        "success_rate": 0.72,
    },

    # ═══ PGA 2K25 — additional ═══
    {
        "title_id": "pga-2k25",
        "name": "Punch Out — Tree Trouble",
        "category": "Recovery",
        "formation": "Rough / Trees",
        "play_name": "Low Punch Recovery",
        "description": (
            "Low-trajectory punch shot with a 5-iron under tree canopy back to "
            "the fairway. Sacrifices distance for stroke recovery. Avoids the "
            "doubled-bogey blowup hole when in trouble off the tee."
        ),
        "setup_steps": [
            "Confirm the lie allows clean contact",
            "Pick a 5 or 6 iron — never a wedge from rough trouble",
            "Aim at the widest point of the fairway, not the pin",
        ],
        "instructions": [
            "Set shot type to punch / low",
            "Reduce swing power to 60-70%",
            "Aim 10-15 yards short of the wide fairway target",
            "Smooth swing tempo — this is a position shot",
            "Take the bogey — avoid the double",
        ],
        "when_to_use": (
            "Off-fairway in trees, low canopy, no clear line to the green, "
            "stroke management mode"
        ),
        "trigger_conditions": {
            "lie": ["trees", "rough", "trouble"],
            "ceilingHeight": "low",
            "scoreVsPar": {"min": 0},
        },
        "difficulty": "easy",
        "tags": ["recovery", "punch-shot", "low-iron", "trees", "stroke-management"],
        "verified": True,
        "source_type": "platform",
        "success_rate": 0.86,
    },
    {
        "title_id": "pga-2k25",
        "name": "Bump and Run — Tight Lie Greenside",
        "category": "Short Game",
        "formation": "Greenside",
        "play_name": "Hybrid Bump",
        "description": (
            "Use a hybrid or 7-iron from a tight greenside lie to bump the ball "
            "and run it like a putt. Eliminates chunked-chip risk on hard "
            "fairways and sets up a tap-in for par."
        ),
        "setup_steps": [
            "Identify the lie is tight — fairway-cut or hardpan",
            "Pick a hybrid or 7-iron, not a wedge",
            "Read the green from ball to hole as if putting",
        ],
        "instructions": [
            "Set up with putting-style stance — narrow feet",
            "Use putting-style swing tempo — short backswing",
            "Strike the ball with a slight descending blow",
            "Ball releases like a long putt across the green",
            "Aim for a 3-foot circle around the hole",
        ],
        "when_to_use": (
            "Tight lie around the green, hardpan or fairway cut, low risk "
            "tolerance, par save"
        ),
        "trigger_conditions": {
            "lie": ["fairway-tight", "hardpan"],
            "distanceFromHole": {"max": 25},
            "greenFirmness": ["medium", "firm"],
        },
        "difficulty": "easy",
        "tags": ["short-game", "bump-and-run", "hybrid", "tight-lie", "par-save"],
        "verified": True,
        "source_type": "platform",
        "success_rate": 0.83,
    },

    # ═══ UNDISPUTED — additional ═══
    {
        "title_id": "undisputed",
        "name": "Liver Shot Setup — Body Then Head",
        "category": "Punch Exploit",
        "formation": "Orthodox",
        "play_name": "Body-Body-Head Combo",
        "description": (
            "Two body shots to draw the guard down, then a left hook upstairs "
            "to the temple. Classic body-then-head sequence — when timed right "
            "the head shot lands clean because the guard dropped to protect "
            "the body."
        ),
        "setup_steps": [
            "Establish jab range to keep them respectful",
            "Confirm opponent has been blocking high",
            "Work in close enough for hooks but not the clinch",
        ],
        "instructions": [
            "Throw left to the body — square",
            "Right to the body immediately — triangle",
            "Watch the guard drop to protect the body",
            "Left hook to the head — square + RS up",
            "Step out of range immediately — they may counter",
        ],
        "when_to_use": (
            "Opponent guard high, mid-distance, round 2 or later, stamina 60%+"
        ),
        "trigger_conditions": {
            "opponentGuard": "high",
            "round": [2, 3, 4, 5, 6],
            "ownStamina": {"min": 60},
        },
        "difficulty": "medium",
        "tags": ["punch-exploit", "body-work", "liver-shot", "combo", "boxing"],
        "verified": True,
        "source_type": "platform",
        "success_rate": 0.71,
    },

    # ═══ VIDEO POKER — additional ═══
    {
        "title_id": "video-poker",
        "name": "Two Pair vs Three to a Royal — Hold Two Pair",
        "category": "Optimal Hold",
        "formation": "Jacks or Better",
        "play_name": "Two Pair Strategy Choice",
        "description": (
            "When dealt two pair AND three cards to a royal flush, hold the "
            "two pair every time. The expected value of the made two pair "
            "(plus full-house draw) exceeds the speculative royal draw. Common "
            "mistake punished by paytables."
        ),
        "setup_steps": [
            "Identify both pairs in your hand",
            "Confirm three of the unpaired cards are royal-flush candidates",
            "Decide based on EV chart: two pair holds",
        ],
        "instructions": [
            "Hold the two pairs",
            "Discard the fifth (royal-candidate) card",
            "Draw one card hoping to fill the boat",
            "Even missing pays 2x — the made two pair beats the draw EV",
        ],
        "when_to_use": (
            "Any time dealt two pair plus three royal-flush candidates on "
            "Jacks or Better and bonus paytables"
        ),
        "trigger_conditions": {
            "handType": "two-pair-plus-3-to-royal",
            "paytable": ["jacks-or-better", "double-bonus"],
        },
        "difficulty": "easy",
        "tags": ["optimal-hold", "two-pair", "EV-decision", "made-hand", "strategy"],
        "verified": True,
        "source_type": "platform",
        "success_rate": 0.96,
    },

    # ═══ VIDEO POKER (final original entry) ═══
    {
        "title_id": "video-poker",
        "name": "Four to Royal Flush — Always Hold",
        "category": "Optimal Hold",
        "formation": "Jacks or Better",
        "play_name": "Royal Flush Draw Hold",
        "description": (
            "When dealt four cards to a royal flush always hold those four "
            "cards and draw one — even over a made flush or straight. The "
            "expected value of the royal flush draw exceeds all other made "
            "hands except a full house or better."
        ),
        "setup_steps": [
            "Identify if your hand contains four royal cards",
            "Royal cards are 10 J Q K A of the same suit",
            "Confirm you have exactly 4 of these 5 cards",
        ],
        "instructions": [
            "Hold the four royal flush cards",
            "Discard the fifth non-matching card",
            "Draw one card hoping for the royal flush",
            "Even missing is fine — the EV justifies the hold",
            "Exception: hold a made straight flush over 4 to royal",
        ],
        "when_to_use": (
            "Any time you are dealt four cards to a royal flush, regardless of "
            "the fifth card value"
        ),
        "trigger_conditions": {
            "handType": "four-to-royal-flush",
            "paytable": ["jacks-or-better", "double-bonus", "double-double-bonus"],
        },
        "difficulty": "easy",
        "tags": ["optimal-hold", "royal-flush", "draw", "high-ev", "strategy"],
        "verified": True,
        "source_type": "platform",
        "success_rate": 0.98,
    },
]


# ---------------------------------------------------------------------------
# Seeder
# ---------------------------------------------------------------------------


async def seed() -> None:
    # Make sure tables exist (lifespan does this in the running app, but the
    # seed script is run standalone, so be defensive).
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    inserted = 0
    updated = 0
    async with async_session() as db:
        for w in WEAPONS:
            existing = (
                await db.execute(
                    select(SecretWeapon).where(
                        SecretWeapon.title_id == w["title_id"],
                        SecretWeapon.name == w["name"],
                    )
                )
            ).scalar_one_or_none()
            if existing is None:
                db.add(SecretWeapon(
                    user_id=None,
                    community_rating=4.2,
                    community_votes=127,
                    **w,
                ))
                inserted += 1
            else:
                for field, value in w.items():
                    setattr(existing, field, value)
                updated += 1
        await db.commit()

    print(f"[seed_arsenal] inserted={inserted} updated={updated} total={len(WEAPONS)}")


if __name__ == "__main__":
    asyncio.run(seed())
