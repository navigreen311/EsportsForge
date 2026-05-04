"""Seed defensive secret weapons for all 11 titles.

Idempotent — re-running will UPDATE existing rows (matched by
(title_id, name)) rather than duplicate them.

Run from repo root:
    backend/venv/Scripts/python.exe backend/scripts/seed_arsenal_defensive.py
"""

from __future__ import annotations

import asyncio
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from sqlalchemy import select  # noqa: E402

from app.db.base import async_session, Base, engine  # noqa: E402
import app.models  # noqa: F401, E402  — register all models with Base
from app.models.secret_weapon import SecretWeapon  # noqa: E402


WEAPONS: list[dict[str, Any]] = [
    # ═══ MADDEN 26 ═══
    {
        "title_id": "madden-26",
        "side": "defense",
        "name": "Zero Blitz — All Out Pressure",
        "category": "Exotic Blitz",
        "formation": "Nickel 3-3-5",
        "play_name": "Zero Blitz",
        "description": (
            "Send all available rushers with zero coverage behind. Every DB blitzes. "
            "Forces immediate pressure. High risk — must work or it gives up a big play."
        ),
        "setup_steps": [
            "Navigate to Nickel 3-3-5 formation",
            "Select Zero Blitz from the play list",
            "Confirm opponent has no quick hot routes set up",
            "Check receiver alignment — bunch and trips formations beat this",
            "Use only first or second time this game",
        ],
        "instructions": [
            "Snap and immediately user-control your fastest blitzer",
            "Attack the A-gap or B-gap depending on opponent protection",
            "Get to the QB before any hot route develops",
            "If the QB releases on his first read — you are beaten, move on",
            "Best result is a strip sack or coverage sack",
        ],
        "when_to_use": (
            "Must get off the field on 3rd & long, opponent has no quick hot "
            "routes set up, this is the first or second use of zero blitz this game"
        ),
        "trigger_conditions": {
            "down": 3,
            "minDistance": 7,
            "opponentFormation": ["not-bunch", "not-trips"],
            "timesUsedThisGame": {"max": 2},
        },
        "difficulty": "hard",
        "tags": [
            "exotic-blitz",
            "zero-coverage",
            "pressure",
            "3rd-down",
            "high-risk",
            "defense",
        ],
        "verified": True,
        "source_type": "platform",
        "success_rate": 0.61,
    },
    {
        "title_id": "madden-26",
        "side": "defense",
        "name": "Cover 2 Trap — Curl Flat Beater",
        "category": "Coverage Trap",
        "formation": "4-3 Over",
        "play_name": "Cover 2 Trap",
        "description": (
            "Run Cover 2 with a user-controlled underneath defender that traps the "
            "curl-flat zone. Bait the throw, then deflect or intercept."
        ),
        "setup_steps": [
            "Select 4-3 Over formation",
            "Call Cover 2 zone",
            "Take user control of the MLB or strong safety",
            "Pre-snap disguise to look like Cover 3",
            "Read the QB eyes after the snap",
        ],
        "instructions": [
            "Drop your user defender to the curl-flat zone",
            "Track the QB eyes to the route",
            "When QB looks at the curl, jump it",
            "Time the deflection or interception window",
            "Stay patient — do not jump early or you give up the seam",
        ],
        "when_to_use": (
            "Opponent loves curl routes and flat combos, smash concept tendency "
            "showing on film, defense needs a turnover"
        ),
        "trigger_conditions": {
            "opponentTendency": ["curl-flat", "smash-concept"],
            "down": [2, 3],
        },
        "difficulty": "medium",
        "tags": [
            "coverage-trap",
            "cover-2",
            "user-coverage",
            "interception",
            "curl-beater",
            "defense",
        ],
        "verified": True,
        "source_type": "platform",
        "success_rate": 0.69,
    },

    # ═══ CFB 26 ═══
    {
        "title_id": "cfb-26",
        "side": "defense",
        "name": "Option Spy — Read & React",
        "category": "Exotic Blitz",
        "formation": "4-2-5",
        "play_name": "Option Spy",
        "description": (
            "Spy the QB with a linebacker on read-option looks. Defender mirrors "
            "the QB instead of crashing on the back, taking away the keeper."
        ),
        "setup_steps": [
            "Select 4-2-5 formation",
            "Set MLB to spy assignment",
            "Confirm opponent ran option last play (or is in option formation)",
            "Disguise pre-snap — look like Cover 3 to hide the spy",
        ],
        "instructions": [
            "On snap, MLB shadows the QB instead of attacking the LOS",
            "Force the QB to keep — then close on him",
            "If the QB hands off, the spy fills the cutback lane",
            "Tackle low — strip the ball if possible",
        ],
        "when_to_use": "Opponent is option-heavy or has run RPO twice in a row",
        "trigger_conditions": {
            "opponentTendency": ["option", "rpo-heavy"],
            "consecutiveOptionLooks": {"min": 2},
        },
        "difficulty": "medium",
        "tags": ["spy-defense", "option-defense", "rpo", "qb-contain", "defense"],
        "verified": True,
        "source_type": "platform",
        "success_rate": 0.66,
    },
    {
        "title_id": "cfb-26",
        "side": "defense",
        "name": "Quarters Robber — RPO Killer",
        "category": "Coverage Trap",
        "formation": "Nickel 4-2-5",
        "play_name": "Quarters Robber",
        "description": (
            "Quarters coverage with a robber dropping into the slant window. "
            "Specifically engineered to kill RPO quick game."
        ),
        "setup_steps": [
            "Select Nickel 4-2-5",
            "Call Quarters",
            "User-control the inside safety as the robber",
            "Pre-snap shade toward the slot receiver",
        ],
        "instructions": [
            "Robber drops into the slant window 5 yards deep",
            "Keep eyes on the QB — never on the receiver",
            "When the QB pulls and throws, you are sitting on the route",
            "Pick or pass break-up — either way you killed the RPO",
        ],
        "when_to_use": "Opponent runs RPO concepts, quick-game heavy offense",
        "trigger_conditions": {
            "opponentTendency": ["rpo-heavy", "quick-game"],
            "down": [1, 2],
        },
        "difficulty": "hard",
        "tags": ["coverage-trap", "quarters", "rpo-killer", "robber", "defense"],
        "verified": True,
        "source_type": "platform",
        "success_rate": 0.63,
    },

    # ═══ NBA 2K26 ═══
    {
        "title_id": "nba-2k26",
        "side": "defense",
        "name": "Full Court Press — Half-Court Trap",
        "category": "Press Defense",
        "formation": "Full Court",
        "play_name": "Press Trap",
        "description": (
            "Apply full-court pressure and trap the ball handler at the half-court "
            "line. Forces turnovers and disrupts opponent rhythm."
        ),
        "setup_steps": [
            "Call timeout to set the press defense",
            "Switch defensive assignment to press",
            "Position the fastest defender on the inbound ball handler",
            "Set the trap point at the half-court line",
        ],
        "instructions": [
            "Apply ball pressure immediately after the inbound",
            "Second defender traps at the half-court line",
            "Force the dribbler toward the sideline",
            "Anticipate the skip pass — get into the lane",
            "If beaten — sprint back, no fouling on the break",
        ],
        "when_to_use": (
            "Down by 10+ in the 4th quarter, opponent ball handler is weak under "
            "pressure, need a momentum shift fast"
        ),
        "trigger_conditions": {
            "pointMargin": {"max": -10},
            "quarter": 4,
            "opponentBallHandler": "weak-under-pressure",
        },
        "difficulty": "hard",
        "tags": ["press-defense", "trap", "turnover", "momentum", "full-court", "defense"],
        "verified": True,
        "source_type": "platform",
        "success_rate": 0.58,
    },
    {
        "title_id": "nba-2k26",
        "side": "defense",
        "name": "ICE PNR — Sideline Funnel",
        "category": "PNR Defense",
        "formation": "Half Court",
        "play_name": "Ice Pick & Roll",
        "description": (
            "Force the ball handler away from the screen and toward the sideline. "
            "Eliminates the pull-up three and the rim attack in one coverage."
        ),
        "setup_steps": [
            "Call ICE coverage on the ball-screen call",
            "On-ball defender shades toward the screener",
            "Big drops to the level of the screen, not the rim",
            "Weak-side help rotates toward the strong-side corner",
        ],
        "instructions": [
            "On screen action, jump the passing lane to the screener",
            "Force the ball handler toward the baseline",
            "Big stays back, not on the level — no foul, no rim attack",
            "Recover to the corner shooter on rotation",
        ],
        "when_to_use": "Opponent loves pull-up threes off PNR, end-of-clock late-game",
        "trigger_conditions": {
            "opponentTendency": ["pnr-heavy", "pull-up-three-shooter"],
            "shotClock": {"max": 14},
        },
        "difficulty": "medium",
        "tags": ["pnr-defense", "ice-coverage", "sideline-funnel", "shooter-defense", "defense"],
        "verified": True,
        "source_type": "platform",
        "success_rate": 0.71,
    },

    # ═══ EA FC 26 ═══
    {
        "title_id": "eafc-26",
        "side": "defense",
        "name": "Offside Trap — Counter Press",
        "category": "Counter Trap",
        "formation": "High Defensive Line",
        "play_name": "Offside Trap",
        "description": (
            "Push the defensive line very high and spring the offside trap on "
            "opponent through-balls. Catches attackers making runs behind the back four."
        ),
        "setup_steps": [
            "Set defensive line to very high in tactics",
            "Set offside trap on in defensive settings",
            "Position defenders in a flat line",
            "Identify when opponent is winding up a through-ball",
        ],
        "instructions": [
            "Watch for the opponent to wind up the through-ball",
            "Step all four defenders up simultaneously as the ball is played",
            "All four must step at the same moment",
            "Attackers caught offside — possession turns over",
            "Immediately transition to counter-attack",
        ],
        "when_to_use": (
            "Opponent relies on through-balls, you are protecting a lead, "
            "opponent striker is slow, possession-based opponent"
        ),
        "trigger_conditions": {
            "opponentTendency": ["through-ball-heavy"],
            "scoreline": "protecting-lead",
        },
        "difficulty": "hard",
        "tags": [
            "offside-trap",
            "defensive-line",
            "counter-attack",
            "trap",
            "possession-defense",
            "defense",
        ],
        "verified": True,
        "source_type": "platform",
        "success_rate": 0.64,
    },
    {
        "title_id": "eafc-26",
        "side": "defense",
        "name": "Counter Press — Trigger on Loss",
        "category": "High Press Trigger",
        "formation": "Standard Press",
        "play_name": "Counter Press",
        "description": (
            "The instant possession is lost, all six attacking players press "
            "the ball aggressively for 6 seconds before falling back into shape."
        ),
        "setup_steps": [
            "Set Press After Possession Loss in tactics",
            "Aggressive press intensity",
            "Identify your trigger — own half loss vs. opponent half loss",
        ],
        "instructions": [
            "On loss of possession, immediately press the ball carrier with R1/RB",
            "Two nearby attackers close passing lanes",
            "Win the ball back within 6 seconds or fall back",
            "Do not over-commit — leave a defender for cover",
        ],
        "when_to_use": "Possession-style opponent, you want to suffocate their build-up",
        "trigger_conditions": {
            "opponentTendency": ["possession-build", "slow-build-up"],
        },
        "difficulty": "medium",
        "tags": ["counter-press", "trigger", "high-press", "possession-defense", "defense"],
        "verified": True,
        "source_type": "platform",
        "success_rate": 0.62,
    },

    # ═══ MLB 26 ═══
    {
        "title_id": "mlb-26",
        "side": "defense",
        "name": "K-Sequence — Up & In, Down & Away",
        "category": "Strikeout Sequence",
        "formation": "Standard Pitching",
        "play_name": "Strikeout Sequence",
        "description": (
            "Set up the strikeout with high inside heat then break the batter "
            "away with the slider down-and-away. Classic sequence — works on "
            "right-on-right and left-on-left matchups."
        ),
        "setup_steps": [
            "Get ahead in the count — strike one is mandatory",
            "Identify the batter as a pull-hitter or chaser",
            "Confirm same-handed matchup for the slider",
        ],
        "instructions": [
            "Pitch 1: 4-seam fastball up and in, brushback effect",
            "Pitch 2: 4-seam outer-third strike — get to two strikes",
            "Pitch 3: slider down-and-away off the plate",
            "Most batters chase pitch 3 — strike three swinging",
        ],
        "when_to_use": "Two-strike count, pull-hitter or chase-prone batter, same-handed matchup",
        "trigger_conditions": {
            "count": {"strikes": 2},
            "batterTendency": ["pull-hitter", "chase-prone"],
            "matchup": "same-handed",
        },
        "difficulty": "medium",
        "tags": ["strikeout-sequence", "fastball-slider", "two-strike", "chase-pitch", "defense"],
        "verified": True,
        "source_type": "platform",
        "success_rate": 0.67,
    },
    {
        "title_id": "mlb-26",
        "side": "defense",
        "name": "Shift Buster Defense — Bunt Away",
        "category": "Shift Defense",
        "formation": "Shift",
        "play_name": "Anti-Bunt Shift",
        "description": (
            "When you have the shift on, the third baseman cheats up to defend "
            "the bunt down the third base line. Removes the easy bunt single."
        ),
        "setup_steps": [
            "Apply shift on a pull-heavy left-handed batter",
            "Move the third baseman 8 feet up and 5 feet in",
            "Confirm the second baseman is on the right side",
        ],
        "instructions": [
            "Third baseman charges on any bunt attempt",
            "Pitcher covers the third base line as a backup",
            "Right side runs the standard shift defense",
            "Bunt hit lost — batter must swing into your shift",
        ],
        "when_to_use": "Pull-heavy lefty at the plate, opponent has bunted in this series",
        "trigger_conditions": {
            "batterTendency": ["pull-heavy-lefty"],
            "opponentTendency": ["bunt-prone"],
        },
        "difficulty": "easy",
        "tags": ["shift-defense", "anti-bunt", "third-base-cheat", "defense"],
        "verified": True,
        "source_type": "platform",
        "success_rate": 0.74,
    },

    # ═══ WARZONE ═══
    {
        "title_id": "warzone",
        "side": "defense",
        "name": "Corner Hold — Crossfire Ambush",
        "category": "Ambush Setup",
        "formation": "Corner Position",
        "play_name": "Corner Ambush",
        "description": (
            "Pre-position in a corner with crossfire coverage. Let the enemy "
            "squad push into your kill-zone, then fire from multiple angles "
            "simultaneously."
        ),
        "setup_steps": [
            "Identify a corner or doorway chokepoint",
            "Position squad members with overlapping fields of fire",
            "Stay silent — no unnecessary movement, ADS only when ready",
            "Let other squads engage first — wait for weakened enemies",
        ],
        "instructions": [
            "Hold position — do not push",
            "When the enemy enters the kill-zone, all fire simultaneously",
            "Focus fire one target at a time — eliminate the fastest first",
            "Watch for flanks — assign one player to cover the back",
            "If overrun — smoke and fall back to the next position",
        ],
        "when_to_use": (
            "Final 3 squads, known enemy location, you have high ground or corner "
            "advantage, circle favors your position"
        ),
        "trigger_conditions": {
            "squadsRemaining": {"max": 3},
            "positionAdvantage": "corner-or-high-ground",
        },
        "difficulty": "medium",
        "tags": ["ambush", "hold-position", "crossfire", "defensive", "final-circle", "defense"],
        "verified": True,
        "source_type": "platform",
        "success_rate": 0.72,
    },
    {
        "title_id": "warzone",
        "side": "defense",
        "name": "Zone Edge Hold — Rotate Last",
        "category": "Hold Position",
        "formation": "Zone Edge",
        "play_name": "Late Rotation",
        "description": (
            "Hold the edge of the safe zone until the very last second. Let other "
            "squads fight through the gas while you bank intel from the high ground."
        ),
        "setup_steps": [
            "Identify the predicted next zone center",
            "Position your squad on the safe-zone edge between the current zone and next",
            "Confirm squad has gas masks or stims for late rotation",
            "Watch heli routes for incoming squads",
        ],
        "instructions": [
            "Stay outside the next circle until the last 30 seconds",
            "Bank intel — count squad markers and shots fired",
            "When you finally rotate, take the highest point with line-of-sight",
            "Engage weakened squads from cover — let them fight each other",
        ],
        "when_to_use": "Mid-late game, multiple squads still alive, you have armor and a gas mask",
        "trigger_conditions": {
            "squadsRemaining": {"min": 4, "max": 8},
            "yourLoadout": ["gas-mask", "stims"],
        },
        "difficulty": "medium",
        "tags": ["zone-edge", "late-rotation", "intel", "defensive-positioning", "defense"],
        "verified": True,
        "source_type": "platform",
        "success_rate": 0.69,
    },

    # ═══ FORTNITE ═══
    {
        "title_id": "fortnite",
        "side": "defense",
        "name": "90-Cone Defense — Vertical Hold",
        "category": "Anti-Rush",
        "formation": "Vertical Box",
        "play_name": "90-Cone Stack",
        "description": (
            "Stack 90s with cones inside to prevent your opponent from edit-pushing. "
            "The cone forces them to take longer to break through, giving you time to reset."
        ),
        "setup_steps": [
            "Build a tall vertical box with 90s on each level",
            "Place cones inside each box level for defense",
            "Confirm material count is sufficient for sustained build battle",
        ],
        "instructions": [
            "Take vertical first — height is the priority",
            "Each 90 should have a cone immediately replaced inside",
            "Hold high ground; do not chase a lower player",
            "If they break a piece, replace it before editing back through",
        ],
        "when_to_use": "Opponent is edit-pushing, you have high ground, late-game build fight",
        "trigger_conditions": {
            "opponentTendency": ["edit-aggressive", "rush-heavy"],
            "yourPosition": "high-ground",
            "buildPhase": "endgame",
        },
        "difficulty": "hard",
        "tags": ["box-defense", "90s", "cone-defense", "anti-rush", "vertical-hold", "defense"],
        "verified": True,
        "source_type": "platform",
        "success_rate": 0.66,
    },
    {
        "title_id": "fortnite",
        "side": "defense",
        "name": "Trap Reset — Edit Window Bait",
        "category": "Anti-Rush",
        "formation": "Box Edit",
        "play_name": "Trap Bait",
        "description": (
            "Place a trap on the wall and bait the opponent into editing through "
            "your wall. They take damage on entry — half-shield gone, free knock."
        ),
        "setup_steps": [
            "Place a damage trap on your front wall",
            "Edit a small window above the trap",
            "Pretend to peek through the window to bait the opponent in",
        ],
        "instructions": [
            "When opponent edits your wall — trap fires on their entry",
            "If they survive, finish with shotgun before they reset",
            "If they avoid the wall, you have intel they spotted the trap",
            "Reset traps after every fight",
        ],
        "when_to_use": "1v1 box fight, opponent is rotation-heavy or edit-aggressive",
        "trigger_conditions": {
            "playerCount": 1,
            "opponentTendency": ["edit-aggressive"],
            "trapsAvailable": {"min": 1},
        },
        "difficulty": "medium",
        "tags": ["trap-defense", "bait", "box-fight", "edit-defense", "defense"],
        "verified": True,
        "source_type": "platform",
        "success_rate": 0.61,
    },

    # ═══ UFC 5 ═══
    {
        "title_id": "ufc-5",
        "side": "defense",
        "name": "Sprawl & Brawl — Takedown Counter",
        "category": "Takedown Defense",
        "formation": "Orthodox Stance",
        "play_name": "Sprawl Defense",
        "description": (
            "Defend the takedown with a perfect sprawl, then counter with ground "
            "and pound or return to standing. Turns opponent grappling strength "
            "into your advantage."
        ),
        "setup_steps": [
            "Identify opponent is a takedown specialist",
            "Stay at distance — do not crowd the cage",
            "Watch for the shoot telegraph in the animation",
        ],
        "instructions": [
            "When opponent shoots — press Circle/B for sprawl",
            "Weight forward — drive hips down on their head",
            "Maintain dominant position after the sprawl",
            "Either ground-and-pound or disengage to standing",
            "Do not give up back position",
        ],
        "when_to_use": "Opponent attempts takedown, clinch range, opponent stamina dropping",
        "trigger_conditions": {
            "opponentTendency": ["takedown-heavy", "wrestler"],
            "position": "standing",
            "distance": "clinch-range",
        },
        "difficulty": "medium",
        "tags": ["takedown-defense", "sprawl", "counter", "ground-defense", "wrestling-counter", "defense"],
        "verified": True,
        "source_type": "platform",
        "success_rate": 0.74,
    },
    {
        "title_id": "ufc-5",
        "side": "defense",
        "name": "Counter Cross — Slip & Punish",
        "category": "Counter Setup",
        "formation": "Orthodox Stance",
        "play_name": "Slip Counter Cross",
        "description": (
            "Slip the opponent's lead jab and counter with a cross down the pipe. "
            "Punishes opponents who fall in love with the jab."
        ),
        "setup_steps": [
            "Identify opponent is jab-heavy",
            "Set distance just outside their jab range",
            "Keep stance loaded — back hand ready",
        ],
        "instructions": [
            "Slip the jab with LS-right (orthodox vs. orthodox)",
            "Immediately fire the cross down the centerline",
            "Reset and repeat — they will keep jabbing",
            "Do not overcommit — single shots only or you eat the counter-counter",
        ],
        "when_to_use": "Opponent is jab-heavy, round 2+, you have stamina for footwork",
        "trigger_conditions": {
            "opponentTendency": ["jab-heavy"],
            "round": [2, 3, 4, 5],
            "ownStamina": {"min": 60},
        },
        "difficulty": "medium",
        "tags": ["counter-strike", "slip", "cross", "jab-defense", "defense"],
        "verified": True,
        "source_type": "platform",
        "success_rate": 0.71,
    },

    # ═══ PGA 2K25 ═══
    {
        "title_id": "pga-2k25",
        "side": "defense",
        "name": "Bogey Save — Lay Up Recovery",
        "category": "Hazard Avoidance",
        "formation": "Recovery Shot",
        "play_name": "Lay Up Strategy",
        "description": (
            "When in trouble off the tee, lay up to a comfortable yardage instead "
            "of attempting the hero shot. Avoids the double-bogey blow-up."
        ),
        "setup_steps": [
            "Confirm the lie does not allow a clean clear of the hazard",
            "Identify a 100-150 yard lay-up zone with a clean approach",
            "Pick a club that lands short of all hazards",
        ],
        "instructions": [
            "Aim for the wide part of the fairway — never pin-hunt from trouble",
            "Smooth tempo — this is a position shot",
            "Play to your favorite full-swing yardage on the next shot",
            "Take the bogey — avoid the double",
        ],
        "when_to_use": (
            "Off-fairway in trouble, hazard between you and the green, "
            "stroke-management mode, you are at or above par"
        ),
        "trigger_conditions": {
            "lie": ["trouble", "rough", "trees"],
            "hazardBetweenLieAndGreen": True,
            "scoreVsPar": {"min": 0},
        },
        "difficulty": "easy",
        "tags": ["lay-up", "hazard-avoidance", "bogey-save", "course-management", "defense"],
        "verified": True,
        "source_type": "platform",
        "success_rate": 0.86,
    },
    {
        "title_id": "pga-2k25",
        "side": "defense",
        "name": "Wind Defense — Punch Low",
        "category": "Hazard Avoidance",
        "formation": "Tee Shot",
        "play_name": "Low Punch Tee Shot",
        "description": (
            "Hit a low punch tee shot in heavy crosswind to keep the ball under "
            "the wind line. Sacrifices distance for accuracy and stays in the fairway."
        ),
        "setup_steps": [
            "Identify wind speed > 12 mph crosswind",
            "Set shot type to punch / low",
            "Pick one extra club to compensate for distance loss",
            "Aim into the wind, not with it",
        ],
        "instructions": [
            "Reduce swing power to 75-80%",
            "Smooth tempo — do not rip a punch shot",
            "Trust the wind to bend the ball back",
            "Land in the fairway — distance is secondary",
        ],
        "when_to_use": "Crosswind > 12 mph, narrow fairway, accuracy over distance",
        "trigger_conditions": {
            "wind": {"crosswind_min": 12},
            "fairwayWidth": "narrow",
        },
        "difficulty": "medium",
        "tags": ["punch-shot", "wind-defense", "low-trajectory", "accuracy", "defense"],
        "verified": True,
        "source_type": "platform",
        "success_rate": 0.78,
    },

    # ═══ UNDISPUTED ═══
    {
        "title_id": "undisputed",
        "side": "defense",
        "name": "Shoulder Roll — Counter Hook",
        "category": "Counter Setup",
        "formation": "Philly Shell",
        "play_name": "Shoulder Roll Counter",
        "description": (
            "Use the Philly Shell shoulder roll to slip the opponent's right hand, "
            "then counter with a left hook to the temple. Mayweather-style defense "
            "into precision counter."
        ),
        "setup_steps": [
            "Set stance to Philly Shell defense",
            "Identify the opponent loves the right cross",
            "Keep the lead shoulder high to deflect right hands",
        ],
        "instructions": [
            "When opponent throws the right — turn the lead shoulder",
            "Slip the punch off the shoulder, head moves right",
            "Immediately fire the lead hook back at the same trajectory",
            "Reset to shell — do not stay in the pocket",
        ],
        "when_to_use": (
            "Opponent is right-hand-heavy, mid-distance, round 3+, you have "
            "stamina for footwork"
        ),
        "trigger_conditions": {
            "opponentTendency": ["right-hand-heavy"],
            "round": [3, 4, 5, 6, 7, 8, 9, 10, 11, 12],
            "ownStamina": {"min": 50},
        },
        "difficulty": "hard",
        "tags": ["shoulder-roll", "philly-shell", "counter-hook", "boxing-defense", "defense"],
        "verified": True,
        "source_type": "platform",
        "success_rate": 0.63,
    },
    {
        "title_id": "undisputed",
        "side": "defense",
        "name": "Guard Trap — Body Shot Bait",
        "category": "Counter Setup",
        "formation": "Tight Guard",
        "play_name": "Body Shot Bait",
        "description": (
            "Drop the guard slightly to the body and bait the body shot. When "
            "they go to the body, fire the right uppercut up the middle."
        ),
        "setup_steps": [
            "Show a high guard for two rounds",
            "In round 3+ start dropping the guard slightly",
            "Confirm opponent is body-punching to wear you down",
        ],
        "instructions": [
            "When opponent drops their right hand to throw the body shot",
            "Immediately fire the right uppercut up the middle",
            "Their head is dropped from the body shot — uppercut lands clean",
            "Reset guard high, do not eat the counter",
        ],
        "when_to_use": "Round 3+, body-shot-heavy opponent, your stamina is 50%+",
        "trigger_conditions": {
            "opponentTendency": ["body-shot-heavy"],
            "round": [3, 4, 5, 6, 7, 8, 9, 10, 11, 12],
            "ownStamina": {"min": 50},
        },
        "difficulty": "medium",
        "tags": ["guard-trap", "body-bait", "uppercut-counter", "defense"],
        "verified": True,
        "source_type": "platform",
        "success_rate": 0.67,
    },

    # ═══ VIDEO POKER ═══
    {
        "title_id": "video-poker",
        "side": "defense",
        "name": "Loss Limit Discipline — Stop Loss",
        "category": "Bankroll Protection",
        "formation": "Session Strategy",
        "play_name": "Loss Limit",
        "description": (
            "Set a hard loss limit before sitting down — when you hit it, walk "
            "away. Bankroll preservation is the most defensive play in video poker."
        ),
        "setup_steps": [
            "Define a loss limit before the session — typically 30% of bankroll",
            "Note the limit on paper, not just memory",
            "Pre-commit: phone alarm at the time you plan to leave",
        ],
        "instructions": [
            "Start the session with the limit clearly in mind",
            "Track wins and losses as you play",
            "When the session loss equals your limit — cash out immediately",
            "Do not chase losses — variance is brutal",
            "Walk away with what you have left",
        ],
        "when_to_use": "Every session — defensive bankroll discipline",
        "trigger_conditions": {
            "sessionLoss": {"reaches": "loss-limit"},
        },
        "difficulty": "easy",
        "tags": ["bankroll-protection", "loss-limit", "discipline", "stop-loss", "defense"],
        "verified": True,
        "source_type": "platform",
        "success_rate": 1.0,
    },
    {
        "title_id": "video-poker",
        "side": "defense",
        "name": "Variance Defense — Bet Down on Tilt",
        "category": "Bankroll Protection",
        "formation": "Session Strategy",
        "play_name": "Bet Reduction",
        "description": (
            "When variance is going against you, drop your bet level by 50% to "
            "ride out the cold streak without going broke. Bankroll preservation "
            "trumps EV when on tilt."
        ),
        "setup_steps": [
            "Identify when you are 5+ losing hands in a row",
            "Confirm bankroll is below 60% of session start",
            "Halve the coin level for the next 10 hands",
        ],
        "instructions": [
            "Drop coin level immediately on the next hand",
            "Continue optimal hold strategy — variance defense is bankroll-only",
            "If bankroll recovers — return to original bet",
            "If bankroll continues to fall — hit the loss limit and walk",
        ],
        "when_to_use": "Cold streak, bankroll below 60%, on tilt",
        "trigger_conditions": {
            "sessionLoss": {"min": 0.4},
            "consecutiveLosses": {"min": 5},
        },
        "difficulty": "easy",
        "tags": ["variance-defense", "bet-reduction", "tilt-management", "defense"],
        "verified": True,
        "source_type": "platform",
        "success_rate": 0.92,
    },
]


async def seed() -> None:
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
                    community_rating=4.3,
                    community_votes=86,
                    **w,
                ))
                inserted += 1
            else:
                for field, value in w.items():
                    setattr(existing, field, value)
                updated += 1
        await db.commit()

    print(
        f"[seed_arsenal_defensive] inserted={inserted} updated={updated} "
        f"total={len(WEAPONS)}"
    )


if __name__ == "__main__":
    asyncio.run(seed())
