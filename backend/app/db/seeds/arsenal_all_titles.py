"""Seed the platform-verified Secret Weapon catalogue (3+ per title).

Run via:
    python -m app.db.seeds.arsenal_all_titles

Idempotent: skips weapons that already exist (matched by name + title_id).
"""

from __future__ import annotations

import asyncio
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.base import async_session
from app.models.secret_weapon import SecretWeapon


def _w(**kw: Any) -> dict[str, Any]:
    """Helper that fills in defaults for a weapon record."""
    base: dict[str, Any] = {
        "user_id": None,
        "sub_category": None,
        "formation": None,
        "play_name": None,
        "title_specific_data": {},
        "patch_version": None,
        "source_type": "platform",
        "source_url": None,
        "video_url": None,
        "thumbnail_url": None,
        "verified": True,
    }
    base.update(kw)
    base.setdefault("instructions", [])
    base.setdefault("setup_steps", [])
    base.setdefault("tags", [])
    base.setdefault("trigger_conditions", {})
    return base


WEAPONS: list[dict[str, Any]] = [
    # ───── Madden 26 ─────
    _w(
        title_id="madden-26",
        name="Fake Punt — Direct Snap HB Dive",
        category="Trick Play",
        formation="Punt",
        play_name="Fake Punt HB Dive",
        difficulty="medium",
        description="Direct-snap fake punt hands the ball to the up-back on a dive — exploits opponents who never key the running back from punt formation.",
        instructions=[
            "Snap directly to up-back (no audible pre-snap)",
            "Up-back hits A-gap immediately on snap",
            "Lead block from wing TE",
            "Cut upfield off any seam",
        ],
        setup_steps=["Special Teams → Punt → Fake Punt HB Dive"],
        when_to_use="4th & 2 or fewer, opponent stacked vs the run, in your own territory or just past midfield",
        trigger_conditions={
            "down": 4,
            "distance_max": 2,
            "field_position_min": 30,
            "field_position_max": 60,
            "opponent_tendency": "stacked-box",
        },
        tags=["fake punt", "4th down", "short yardage", "trick"],
    ),
    _w(
        title_id="madden-26",
        name="Flea Flicker — Gun Spread",
        category="Trick Play",
        formation="Gun Spread",
        play_name="Flea Flicker",
        difficulty="medium",
        description="QB hands off, RB pitches back, deep shot. Devastates teams selling out for the run on early downs.",
        instructions=[
            "Hand off to RB",
            "RB takes one step then pitches back to QB",
            "Pump-fake the seam, lock onto the deep post",
            "Hit the post if the safety bit on the run",
        ],
        setup_steps=["Gun Spread → Flea Flicker"],
        when_to_use="After 2-3 consecutive runs that gained ≥4 yards each — opponent is selling out vs run.",
        trigger_conditions={
            "consecutive_runs_min": 2,
            "opponent_tendency": "run-commit",
            "down": [1, 2],
        },
        tags=["flea flicker", "play action", "trick", "deep shot"],
    ),
    _w(
        title_id="madden-26",
        name="PA Crossers vs Cover 3",
        category="Unstoppable",
        formation="Gun Bunch",
        play_name="PA Crossers",
        difficulty="easy",
        description="Twin crossers under a deep dig — Cover 3's hook defenders cannot match both crossers, leaving an easy throw.",
        instructions=[
            "Read the safety alignment pre-snap",
            "PA fake to the back",
            "First read: shallow crosser",
            "Second read: deeper dig",
        ],
        setup_steps=["Gun Bunch → PA Crossers"],
        when_to_use="Opponent in Cover 3 shell — single high safety, hook defenders showing zone.",
        trigger_conditions={"opponent_coverage": "cover-3"},
        tags=["pa crossers", "cover 3 beater", "money play"],
    ),
    # ───── CFB 26 ─────
    _w(
        title_id="cfb-26",
        name="Wildcat Direct Snap",
        category="Trick Play",
        formation="Wildcat",
        play_name="Power",
        difficulty="easy",
        description="Direct snap to the back behind a pulling guard — short-yardage hammer.",
        instructions=[
            "Snap directly to the RB",
            "Pull backside guard",
            "RB follows the puller through the A-gap",
        ],
        setup_steps=["Wildcat package → Wildcat Power"],
        when_to_use="Any short-yardage situation — opponent personnel mismatch, base defense.",
        trigger_conditions={"distance_max": 2},
        tags=["wildcat", "short yardage", "power"],
    ),
    _w(
        title_id="cfb-26",
        name="Option Fake Pitch Pass",
        category="Trick Play",
        formation="Pistol Triple",
        play_name="Triple Pitch Pass",
        difficulty="hard",
        description="Show triple-option, pull the ball, throw to a wide-open backside post.",
        instructions=[
            "Mesh with the dive back — read end",
            "Fake pitch to the slot",
            "Reset and find the backside post",
        ],
        setup_steps=["Pistol Triple → Triple Pitch Pass"],
        when_to_use="Outside option setup — defender crashing on the pitch read.",
        trigger_conditions={"opponent_tendency": "edge-crash"},
        tags=["option", "pitch pass", "trick"],
    ),
    _w(
        title_id="cfb-26",
        name="Mesh Concept vs Man",
        category="Unstoppable",
        formation="Spread",
        play_name="Mesh",
        difficulty="easy",
        description="Two crossing routes that pick man defenders — easy completion every time.",
        instructions=[
            "Identify man coverage pre-snap",
            "Throw the first crosser to come open",
            "Lead the receiver away from trail defender",
        ],
        setup_steps=["Spread → Mesh"],
        when_to_use="Opponent in man coverage with no inside bracket.",
        trigger_conditions={"opponent_coverage": "man"},
        tags=["mesh", "man beater"],
    ),
    # ───── NBA 2K26 ─────
    _w(
        title_id="nba-2k26",
        name="Step-Back Three — Pro 3 Package",
        category="Cheese Dribble",
        formation="Iso",
        play_name="Step-Back Three",
        difficulty="medium",
        description="Hesi → step-back three exploiting defenders that overplay the drive direction.",
        instructions=[
            "Iso the wing",
            "Hesi (RS down → up) to bait the close-out",
            "Step-back (LT + RS opposite) to create separation",
            "Release at peak",
        ],
        setup_steps=["Hold LT and call iso for ball-handler"],
        when_to_use="Defender overplaying the drive direction with shot clock 8s or less.",
        trigger_conditions={"shot_clock_max": 10, "defender_position": "overplay"},
        tags=["step back", "iso", "cheese"],
    ),
    _w(
        title_id="nba-2k26",
        name="Post Spin Baseline Jumper",
        category="Unstoppable Scorer",
        formation="Post Up",
        play_name="Post Spin Fade",
        difficulty="medium",
        description="Spin baseline off a smaller defender, fade-away mid-range — bigs cannot recover.",
        instructions=[
            "Back down once",
            "Spin baseline (LS toward baseline + RT)",
            "Pop the fadeaway with RS",
        ],
        setup_steps=["Call iso post-up for big with size advantage"],
        when_to_use="Smaller defender on you in the post — mid-range zone.",
        trigger_conditions={"defender_position": "size-disadvantage"},
        tags=["post", "fade", "unstoppable"],
    ),
    _w(
        title_id="nba-2k26",
        name="Pick & Roll Lob — High PNR",
        category="Unstoppable",
        formation="High PNR",
        play_name="Pick and Roll Lob",
        difficulty="easy",
        description="Pull the screener, hit the lob if the defender switches late.",
        instructions=[
            "Call screen (LB)",
            "Reject if needed; otherwise drive off the screen",
            "Lob with Y/Triangle as the roller crosses the lane",
        ],
        setup_steps=["Quick play menu → High PNR"],
        when_to_use="Defender switches late or goes under the screen.",
        trigger_conditions={"defender_position": "late-switch"},
        tags=["pnr", "lob", "alley-oop"],
    ),
    # ───── EA FC 26 ─────
    _w(
        title_id="eafc-26",
        name="El Tornado — Open Space",
        category="Skill Move Combo",
        formation="Counter",
        difficulty="hard",
        description="El Tornado skill into the box, beats the recovering full-back consistently.",
        instructions=[
            "Receive in stride toward the byline",
            "El Tornado (RS quarter-roll up + opposite)",
            "Drive to near post, low shot",
        ],
        setup_steps=["Player must have 4★+ skill moves"],
        when_to_use="Final third with space, 1v1 defender on the wing.",
        trigger_conditions={"field_zone": "final-third", "defender_count": 1},
        tags=["skill move", "el tornado", "wing"],
    ),
    _w(
        title_id="eafc-26",
        name="Rabona Fake Cross — Near Post",
        category="Dead Ball Trick",
        formation="Set Piece",
        difficulty="hard",
        description="Rabona fake cross into the near post — keeper cheats far, near post is wide open.",
        instructions=[
            "Set up cross (LB taken)",
            "Rabona modifier (LB+RB) + low cross button",
            "Aim near post",
        ],
        setup_steps=["Corner kick situation, attacker stacked at near post"],
        when_to_use="Corner kick where keeper consistently cheats to the far post.",
        trigger_conditions={"set_piece": "corner", "keeper_position": "far-post"},
        tags=["set piece", "rabona", "near post"],
    ),
    _w(
        title_id="eafc-26",
        name="Through Ball Cheese — Behind Defense",
        category="Cheese Formation",
        formation="4-3-3 Attack",
        difficulty="easy",
        description="Quick striker + high line + lofted through ball = automatic chance.",
        instructions=[
            "Hold L1/LB to drag a striker forward",
            "Lofted through ball (Triangle/Y)",
            "First-time finish",
        ],
        setup_steps=["Set tactic: Pressure on Heavy Touch"],
        when_to_use="Opponent runs a high defensive line — you have a quick striker.",
        trigger_conditions={"opponent_shape": "high-line"},
        tags=["through ball", "high line", "cheese"],
    ),
    # ───── MLB 26 ─────
    _w(
        title_id="mlb-26",
        name="Elevated 4-Seam — 0-2 Count",
        category="Pitch Sequence",
        difficulty="easy",
        description="Climb the ladder above the zone — chase rate is highest at 0-2.",
        instructions=[
            "Pitch type: 4-Seam Fastball",
            "Location: 4-6 inches above the zone, glove side",
            "Max effort",
        ],
        setup_steps=[],
        when_to_use="Pitcher ahead 0-2, batter has shown a chase tendency.",
        trigger_conditions={"count": "0-2", "batter_tendency": "chase-high"},
        tags=["elevated heater", "0-2", "putaway"],
    ),
    _w(
        title_id="mlb-26",
        name="Backdoor Slider — 2-2 Count",
        category="Pitch Sequence",
        difficulty="medium",
        description="Backdoor slider to opposite-side hitter on a full count — paints the corner.",
        instructions=[
            "Pitch type: Slider",
            "Start a foot off the plate, finish on the corner",
            "Throw with intent — late break",
        ],
        setup_steps=[],
        when_to_use="2-2 count vs an opposite-handed batter who chases breaking balls.",
        trigger_conditions={"count": "2-2", "batter_tendency": "chase-breaking"},
        tags=["backdoor", "slider", "corner"],
    ),
    _w(
        title_id="mlb-26",
        name="Oppo Pull Cheese — Inside Pitch",
        category="Situational AB",
        difficulty="medium",
        description="Pull the inside pitch hard — pitcher who pounds inside has nowhere to go.",
        instructions=[
            "Set up early — back foot in the box",
            "PCI to the inside half",
            "Swing as the ball enters the zone",
        ],
        setup_steps=[],
        when_to_use="Pitcher consistently working inside; runners on, pull side open.",
        trigger_conditions={"pitcher_tendency": "inside-pound"},
        tags=["pull", "inside", "cheese"],
    ),
    # ───── Warzone ─────
    _w(
        title_id="warzone",
        name="Roof Edge — Final Circle Setup",
        category="Zone Edge",
        difficulty="medium",
        description="Lock down high ground on the final circle's edge — funnel approaches into one path.",
        instructions=[
            "Identify a building on the leeward side of the circle",
            "Stage utility pre-rotation",
            "Hold a corner that covers two angles",
        ],
        setup_steps=["Loadout: long-range optic + claymores"],
        when_to_use="Top 5 squads with a tall building on the safe side of the circle.",
        trigger_conditions={"circle_phase_min": 5, "height_advantage": True},
        tags=["high ground", "endgame", "rotation"],
    ),
    _w(
        title_id="warzone",
        name="Close Range Shotgun Slide",
        category="Movement Tech",
        difficulty="hard",
        description="Slide-cancel into a shotgun one-tap — the slide breaks aim assist on the defender.",
        instructions=[
            "Sprint into the room",
            "Slide-cancel just before the threshold",
            "One-tap with the secondary",
        ],
        setup_steps=["Secondary: pump shotgun"],
        when_to_use="Indoor / close quarters where you can close the gap in <2 seconds.",
        trigger_conditions={"indoor": True, "distance_max": 8},
        tags=["slide cancel", "shotgun", "movement"],
    ),
    _w(
        title_id="warzone",
        name="3-Plate Revive Bait",
        category="Situational",
        difficulty="hard",
        description="Drop your downed teammate on a 3-plate, hold an angle on the body — kills the looters.",
        instructions=[
            "Down a partner intentionally in an open lane",
            "Crack a 3-plate at the body",
            "Pre-aim a long sightline on the body",
        ],
        setup_steps=[],
        when_to_use="Late game when only 1-2 squads left and an open body draws greed.",
        trigger_conditions={"squad_count_max": 2, "endgame": True},
        tags=["bait", "down", "endgame"],
    ),
    # ───── Fortnite ─────
    _w(
        title_id="fortnite",
        name="90s Reset — Box Fight Opener",
        category="Build Reset",
        difficulty="hard",
        description="Reset on top of an opponent's box for a clean third-person edit shot.",
        instructions=[
            "Wall + ramp + wall + floor (90)",
            "Land directly on opponent's box",
            "Edit floor down → take the shot",
        ],
        setup_steps=["Materials min 100 wood/brick"],
        when_to_use="Opponent in a box, you have height.",
        trigger_conditions={"opponent_in_box": True, "materials_min": 80},
        tags=["90s", "box fight", "reset"],
    ),
    _w(
        title_id="fortnite",
        name="Double Edit — Window Peek",
        category="Edit Speed",
        difficulty="hard",
        description="Two-piece edit reveal — peek shot then close instantly.",
        instructions=[
            "Edit a window, fire one shot",
            "Reset the edit",
            "Edit a different window for the second shot",
        ],
        setup_steps=[],
        when_to_use="Defending against a push, need to peek without committing.",
        trigger_conditions={"defending": True},
        tags=["edit", "peek", "window"],
    ),
    _w(
        title_id="fortnite",
        name="Zone Launch Pad Rotation",
        category="Zone Launch",
        difficulty="medium",
        description="Launch pad rotation through storm — out-rotate a team that holds the high ground.",
        instructions=[
            "Pre-build a 1x1 with launch pad",
            "Jump on contour timing — glide through storm",
            "Re-deploy glider to land on a height advantage",
        ],
        setup_steps=["Carry launch pad + 50 mats"],
        when_to_use="Storm closing, you've lost high ground and direct rotation is blocked.",
        trigger_conditions={"storm_closing": True, "lost_high_ground": True},
        tags=["launch pad", "rotation", "zone"],
    ),
    # ───── UFC 5 ─────
    _w(
        title_id="ufc-5",
        name="Takedown Setup — Jab Feint",
        category="Submission Setup",
        difficulty="medium",
        description="Jab feint level-change for the double leg — opponent's guard is up, legs are exposed.",
        instructions=[
            "Throw a head-up jab feint",
            "Drop level immediately",
            "Shoot the double leg",
        ],
        setup_steps=["Pin opponent's back foot first"],
        when_to_use="3rd round, opponent fatigued and standing upright.",
        trigger_conditions={"round_min": 3, "opponent_stamina": "low"},
        tags=["takedown", "feint", "submission"],
    ),
    _w(
        title_id="ufc-5",
        name="Leg Kick Body Combo",
        category="Strike Exploit",
        difficulty="easy",
        description="Leg kick → body kick — opponent drops the guard for the leg, eats the body.",
        instructions=[
            "Outside leg kick",
            "Switch stance briefly",
            "Body kick to the same side",
        ],
        setup_steps=[],
        when_to_use="Opponent guarding high, inside-low distance.",
        trigger_conditions={"distance": "inside", "opponent_guard": "high"},
        tags=["leg kick", "body kick", "combo"],
    ),
    _w(
        title_id="ufc-5",
        name="Superman Punch Counter",
        category="Cheese Combo",
        difficulty="hard",
        description="Counter superman punch on opponent recovery from a parry.",
        instructions=[
            "Parry the lead hand",
            "Step in immediately on opponent's recovery",
            "Throw the superman punch over the top",
        ],
        setup_steps=[],
        when_to_use="Right after a successful parry, opponent in mid-recovery.",
        trigger_conditions={"after_parry": True},
        tags=["counter", "superman", "parry"],
    ),
    # ───── PGA 2K25 ─────
    _w(
        title_id="pga-2k25",
        name="Low Draw — Into Wind Shot",
        category="Wind Exploit",
        difficulty="medium",
        description="Low draw cuts through headwind — keeps ball under the gust line.",
        instructions=[
            "Club up one (use one less loft)",
            "Swing path inside-out",
            "Aim at the right rough, draw to centre",
        ],
        setup_steps=[],
        when_to_use="Headwind 15 mph or stronger on a fairway approach.",
        trigger_conditions={"wind_speed_min": 15, "wind_direction": "head"},
        tags=["low draw", "wind", "approach"],
    ),
    _w(
        title_id="pga-2k25",
        name="Bump & Run — Short Rough",
        category="Shot Shape",
        difficulty="easy",
        description="Bump-and-run from short rough — bypasses spin variance, predictable result.",
        instructions=[
            "Use 8-iron",
            "Half-swing, ball-position centre",
            "Aim for the front edge, let it roll",
        ],
        setup_steps=[],
        when_to_use="Just off the green, short rough, pin in the centre or back.",
        trigger_conditions={"lie": "short-rough", "distance_max": 30},
        tags=["bump and run", "chip"],
    ),
    _w(
        title_id="pga-2k25",
        name="Lag Putt Speed Read — Long",
        category="Situational Club",
        difficulty="medium",
        description="Long lag putt — overweight by 5% to handle green texture variance.",
        instructions=[
            "Read the line conservatively",
            "Add 5% to the recommended power",
            "Strike with neutral tempo",
        ],
        setup_steps=[],
        when_to_use="Putt 30 ft or longer, straight or slight break.",
        trigger_conditions={"distance_min": 30, "green_break": "minor"},
        tags=["lag putt", "long putt"],
    ),
    # ───── Undisputed ─────
    _w(
        title_id="undisputed",
        name="Jab-Cross-Jab — Guard Break",
        category="Punch Exploit",
        difficulty="medium",
        description="Three-piece that breaks turtling guards — last jab catches the gap.",
        instructions=[
            "Lead jab to set distance",
            "Cross to crack the guard",
            "Quick jab through the centre gap",
        ],
        setup_steps=[],
        when_to_use="Opponent turtling, inside boxing range.",
        trigger_conditions={"opponent_guard": "turtle", "distance": "inside"},
        tags=["jab", "combo", "guard break"],
    ),
    _w(
        title_id="undisputed",
        name="Overhand Counter — After Slip",
        category="Combo Ender",
        difficulty="hard",
        description="Slip the lead hook → overhand right over the top — opens the right hand line.",
        instructions=[
            "Slip outside on the lead hook",
            "Step in",
            "Loop the overhand right",
        ],
        setup_steps=[],
        when_to_use="After successfully slipping the opponent's lead hook.",
        trigger_conditions={"after_slip": True},
        tags=["counter", "overhand", "slip"],
    ),
    _w(
        title_id="undisputed",
        name="Clinch Work — Fatigue Drain",
        category="Stamina Trick",
        difficulty="easy",
        description="Initiate the clinch when opponent's stamina drops — drains them further safely.",
        instructions=[
            "Close the distance",
            "Tie up in clinch",
            "Throw short uppercuts and work for break",
        ],
        setup_steps=[],
        when_to_use="Opponent's stamina visibly dropping, you're inside boxing distance.",
        trigger_conditions={"opponent_stamina": "low"},
        tags=["clinch", "stamina"],
    ),
    # ───── Video Poker ─────
    _w(
        title_id="video-poker",
        name="Jacks or Better — Four Card Royal Hold",
        category="Optimal Hold",
        difficulty="easy",
        description="Always hold four to a royal flush over a paying pair on Jacks or Better.",
        instructions=[
            "Identify four-to-royal in dealt hand",
            "Discard the fifth card even if it makes a pair",
        ],
        setup_steps=[],
        when_to_use="Dealt four cards to a royal flush regardless of other made hands.",
        trigger_conditions={"hand": "four-to-royal", "paytable": "9/6"},
        tags=["royal flush", "optimal", "JoB"],
    ),
    _w(
        title_id="video-poker",
        name="Double Bonus — Low Pair vs Flush Draw",
        category="Variance Play",
        difficulty="medium",
        description="On Double Double Bonus, hold the low pair over a 4-card flush draw — paytable maths.",
        instructions=[
            "Hold the low pair",
            "Discard the flush draw cards",
        ],
        setup_steps=[],
        when_to_use="DDB paytable, dealt low pair + 4 to a flush.",
        trigger_conditions={"hand": "low-pair-vs-flush4", "paytable": "DDB"},
        tags=["DDB", "low pair", "ev"],
    ),
    _w(
        title_id="video-poker",
        name="Session End — Hit and Run Threshold",
        category="Session Strategy",
        difficulty="easy",
        description="End the session when you're up 20% of starting bankroll — banks the variance win.",
        instructions=[
            "Track session start credits",
            "Cash out when current ≥ start × 1.2",
        ],
        setup_steps=[],
        when_to_use="Up 20% or more on the session.",
        trigger_conditions={"session_pl_pct_min": 20},
        tags=["bankroll", "discipline", "session"],
    ),
]


async def seed(db: AsyncSession) -> int:
    """Insert weapons that don't already exist. Returns number inserted."""
    inserted = 0
    for spec in WEAPONS:
        existing = (
            await db.execute(
                select(SecretWeapon).where(
                    SecretWeapon.title_id == spec["title_id"],
                    SecretWeapon.name == spec["name"],
                )
            )
        ).scalar_one_or_none()
        if existing:
            continue
        db.add(SecretWeapon(**spec))
        inserted += 1
    if inserted:
        await db.commit()
    return inserted


async def _main() -> None:
    async with async_session() as session:
        n = await seed(session)
        print(f"Seeded {n} weapons (skipped {len(WEAPONS) - n} duplicates)")


if __name__ == "__main__":
    asyncio.run(_main())
