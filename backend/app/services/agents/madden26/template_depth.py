"""
template_depth — hand-authored plain-language depth for the built-in core
template plays, so a gameplan generated WITHOUT an ANTHROPIC_API_KEY still shows
the deeper Concept Breakdown / When to Call / Evidence / teaching-audible content
(matching what the AI path produces with a key).

Only the core play sheet (`_build_core_plays`) reaches the frontend via
`mapBackendGameplan`, so depth is authored for those 10 plays, keyed by name.

Tone rules mirror the generation prompt: plain English, define any term a casual
player wouldn't know inline (light box, single-high, EMOL), depth not word count.
"""

from __future__ import annotations

from typing import Any

from app.schemas.madden26.gameplan import PlayAudible, PlayEvidence

# name -> {notes, base_read, when_to_call, evidence{...}, audibles[{...}]}
_DEPTH: dict[str, dict[str, Any]] = {
    "PA Boot Over": {
        "notes": (
            "You fake the run, then the quarterback rolls out to the other side while "
            "the tight end works across the field behind the defense. The fake sucks the "
            "linebackers toward the run, and rolling out moves you away from the rush — so "
            "you get a clean, easy throw on the move to the TE crossing open."
        ),
        "base_read": "After the fake, roll out and find the tight end crossing behind the linebackers; if he's covered, take the flat or throw it away on the run.",
        "when_to_call": "Early downs off a believable run game — it only works if the defense respects your run. Great after you've had a few runs to set up the fake.",
        "evidence": {
            "why": "A defense that's been keying your run will bite on the fake, and rolling out beats the pass rush by moving the pocket. The crossing TE ends up behind flat-footed linebackers.",
            "data": "Play-action is at its best on 1st and 2nd down, when the defense still has to honor the run.",
            "risk": "An edge rusher who ignores the fake and chases you can wreck the rollout. Tell: a defensive end crashing hard upfield. Get the ball out early or tuck and run.",
            "comparable": "A staple boot that consistently hits the TE for a chunk once the run game is established.",
        },
        "audibles": [
            {
                "label": "Check to a quick pass",
                "target_play": "Quick Slants",
                "look_for": "An edge rusher teeing off / crashing hard upfield pre-snap.",
                "recognize": "If the end is way outside and flying, the rollout won't have room and he'll chase you down.",
                "do": "Check to Quick Slants so the ball comes out fast, before the rush gets home.",
                "counter_look_for": "After the quick game, the end slowing down and playing contain instead of rushing.",
                "counter_do": "Go back to the boot — with him playing soft, the rollout has room again.",
            }
        ],
    },
    "Mesh Cross": {
        "notes": (
            "Two receivers run shallow crossing routes that brush past each other over the "
            "middle, like a legal pick. Against man coverage the defenders chasing them "
            "collide, and one of your guys pops open. The ball comes out fast, so it also "
            "beats the blitz."
        ),
        "base_read": "Watch the two crossers and throw to whichever one comes free as they cross; if both are covered, check it down.",
        "when_to_call": "3rd-and-short-to-medium and any time you expect man coverage or pressure. The quick crossers get the ball out before the rush arrives.",
        "evidence": {
            "why": "Man defenders have to follow your receivers, so when the crossers cross, their defenders run into each other and someone's uncovered.",
            "data": "Mesh shines against man coverage and blitzes — common looks on 3rd down and in the red zone.",
            "risk": "Zone, or a switch call where defenders pass you off, removes the pick. Tell: defenders sitting in an area instead of chasing. Then a corner or vertical wins instead.",
            "comparable": "A go-to answer any time the defense presses and plays man near the sticks.",
        },
        "audibles": [
            {
                "label": "Fade the outside receiver",
                "target_play": "Fade",
                "look_for": "One safety alone deep in the middle (single-high).",
                "recognize": "Single-high means just one deep safety in the middle, so your outside receiver is one-on-one with no help over the top.",
                "do": "Put the outside receiver on a Fade and give him a back-shoulder ball — it's a 1-on-1 he can win.",
                "counter_look_for": "The corner bailing deep and giving cushion after the fade threat.",
                "counter_do": "Go back to the mesh underneath — he's playing off, so the short crossers are wide open.",
            }
        ],
    },
    "Zone Run Left": {
        "notes": (
            "A patient run where the whole line blocks the same direction and the back "
            "picks the first open lane that appears. You're not aiming at one hole — you "
            "read the blocks and cut off them. Reliable, low-risk yards on early downs."
        ),
        "base_read": "Take the handoff, press it toward the play side, and cut off the first crease that opens — don't force it, take what the blocks give you.",
        "when_to_call": "1st and 2nd down to stay on schedule, especially against a light front (fewer defenders up near the line).",
        "evidence": {
            "why": "Zone blocking flows one way and stretches the defense sideways; wherever a defender over-runs it, the back cuts behind him for the lane.",
            "data": "Best when the box is light — fewer defenders up front means more room to find a crease.",
            "risk": "A penetrating defensive lineman who shoots a gap can blow up the timing. Tell: a lineman crowding the gap he's shooting. Bounce it outside or cut back away from him.",
            "comparable": "A dependable early-down run that keeps you out of long-yardage downs.",
        },
        "audibles": [
            {
                "label": "Check to a pass",
                "target_play": "Quick Slants",
                "look_for": "A stacked box — 8 or more defenders crowded near the line.",
                "recognize": "Count bodies near the ball; 8+ means they're selling out to stop the run and are light in coverage.",
                "do": "Check to Quick Slants and throw behind the crowded box for easy yards.",
                "counter_look_for": "After the pass, a safety backing out and the box thinning back to 6-7.",
                "counter_do": "Run the zone again — the numbers up front are back in your favor.",
            }
        ],
    },
    "Deep Post": {
        "notes": (
            "A shot play: the receiver runs up the field, then breaks toward the middle on "
            "a post, aiming for the gap between the safeties. If there's only one deep "
            "safety, or the safeties are too wide, that middle window is a big play."
        ),
        "base_read": "Read the deep middle. If there's one safety or a clear gap between two, let the post go; if the middle's crowded, come down to the shorter routes.",
        "when_to_call": "2nd-and-medium or a play-action setup when you want a chunk — you want them in a single-high look (one deep safety).",
        "evidence": {
            "why": "A single deep safety can't cover the whole middle. The post attacks the space he vacates, especially with a route pulling him the other way.",
            "data": "Deep shots pay off most against single-high coverages (one deep safety), common on early downs.",
            "risk": "Two deep safeties (Cover 2 or quarters) close the middle. Tell: two safeties standing deep and wide pre-snap. Take the checkdown instead of forcing it.",
            "comparable": "A classic single-high beater that turns one wrong safety step into six points.",
        },
        "audibles": [
            {
                "label": "Check it down short",
                "target_play": "Quick Slants",
                "look_for": "Two deep safeties splitting the field pre-snap.",
                "recognize": "Two men standing deep and wide means the middle is covered — the post won't be there.",
                "do": "Check to a quick short throw and take the easy yards underneath.",
                "counter_look_for": "A safety rotating down late, leaving a single-high look.",
                "counter_do": "Take the post shot — with one safety deep, the middle's open again.",
            }
        ],
    },
    "Quick Slants": {
        "notes": (
            "Fast in-breaking routes thrown almost immediately after the snap. It's your "
            "get-it-out-quick answer to pressure and press coverage — a high-percentage, "
            "low-risk completion that keeps the offense on schedule."
        ),
        "base_read": "Pick the best matchup pre-snap and throw the slant on rhythm the moment the receiver breaks in — don't hold it.",
        "when_to_call": "Any time you expect a blitz or press man, and on early downs when you just want a safe completion. Great to slow down an aggressive pass rush.",
        "evidence": {
            "why": "The ball is out before the rush arrives, and a quick inside break beats a defender pressing at the line. Low risk, steady yards.",
            "data": "Quick game is your friend against heavy blitz looks — the throw beats the pressure.",
            "risk": "An underneath defender sitting in the throwing lane can jump it. Tell: a linebacker squatting in the middle. Work the backside slant away from him.",
            "comparable": "A reliable pressure-beater and chain-mover you can lean on all game.",
        },
        "audibles": [
            {
                "label": "Take a shot",
                "target_play": "Deep Post",
                "look_for": "The corners playing way off, giving big cushion.",
                "recognize": "If defenders are backed way off, the slant gains little — but the deep middle may be soft.",
                "do": "Check to a Deep Post and attack the space they're conceding.",
                "counter_look_for": "Corners jumping up into press after the deep threat.",
                "counter_do": "Go back to the slants — press coverage is exactly what quick slants beat.",
            }
        ],
    },
    "Power Run": {
        "notes": (
            "A physical downhill run: a guard pulls across and the fullback leads through "
            "the hole, so you attack one gap with two extra blockers in front. It's a "
            "move-the-pile call that wears a defense down and gets the tough yard."
        ),
        "base_read": "Follow the pulling guard and fullback through the hole and press downhill — lean forward for the extra yard.",
        "when_to_call": "Short yardage and goal line against a light box (6 or fewer up front). With extra blockers leading, you win the numbers at the point of attack.",
        "evidence": {
            "why": "The pulling guard and lead fullback give you more blockers than defenders at the hole, so you overpower a light front for the yard.",
            "data": "Best when the box is light — extra blockers make short yardage a numbers win.",
            "risk": "A nose tackle shooting a gap or an interior stunt can blow it up. Tell: a lineman crowding your center. Slide the protection or run away from him.",
            "comparable": "A short-yardage hammer that converts when you absolutely need a yard.",
        },
        "audibles": [
            {
                "label": "Check to play-action",
                "target_play": "PA Boot Over",
                "look_for": "A stacked box — safeties creeping down, 8+ near the line.",
                "recognize": "If they've loaded up to stop the run, there's grass behind them in coverage.",
                "do": "Check to PA Boot Over — fake the power and throw off the run they sold out to stop.",
                "counter_look_for": "After the boot, defenders staying back / not crashing the run.",
                "counter_do": "Run the power again — they're respecting the pass now, so the box is lighter.",
            }
        ],
    },
    "RPO Glance": {
        "notes": (
            "A run-pass option where you read one defender — the end man on the line (the "
            "EMOL, the outside defender on the edge). If he crashes down to play the run, "
            "you pull it and throw the quick glance slant behind him; if he stays home, "
            "you hand off. You take whatever he gives you."
        ),
        "base_read": "Eyes on the edge defender. He crashes in → pull it and throw the glance. He stays / widens → hand off the run.",
        "when_to_call": "Early downs when you want a safe play with a built-in answer — it punishes aggressive edge defenders without any guesswork.",
        "evidence": {
            "why": "The edge defender can't be right — if he plays the run, the glance behind him is open; if he plays the pass, the run has a numbers edge.",
            "data": "RPOs shine against defenses whose edge players fly downhill at run action.",
            "risk": "A disciplined edge defender who stays square takes both away. Tell: an end who sits and reads instead of committing. Hand it off and take the run.",
            "comparable": "A low-risk early-down staple that keeps aggressive defenders honest.",
        },
        "audibles": [
            {
                "label": "Keep it a run",
                "target_play": "Zone Run Left",
                "look_for": "A light box with the edge defender widening out.",
                "recognize": "If the edge is bailing and the box is light, the run has clear numbers.",
                "do": "Kill the pass and just run it — they've given up the box.",
                "counter_look_for": "A safety dropping down late to plug the run after you gash them.",
                "counter_do": "Throw the glance — with the safety down, there's space behind the edge again.",
            }
        ],
    },
    "Screen Left": {
        "notes": (
            "A trap for the rush: the line lets the rushers come, then you dump a quick "
            "pass to the back behind a wall of blockers who slip out in front of him. The "
            "harder they rush, the better it works — you turn their aggression into your "
            "big gain."
        ),
        "base_read": "Let the rush come, then throw it to the back and let him follow his blockers — don't hold it, the timing is quick.",
        "when_to_call": "Obvious passing downs when you expect a heavy blitz. It punishes defenses that sell out to sack the quarterback.",
        "evidence": {
            "why": "When defenders rush hard and turn their backs, there's grass in front of the back and blockers leading him. Their pressure becomes your open field.",
            "data": "Screens are at their best on 3rd-and-long against blitz-happy defenses.",
            "risk": "A spy or a defender who reads the screen and sits can blow it up. Tell: a rusher who stops short instead of chasing. Get to a different call if you see it.",
            "comparable": "A great changeup that makes an aggressive pass rush pay for over-pursuing.",
        },
        "audibles": [
            {
                "label": "Check to a quick pass",
                "target_play": "Quick Slants",
                "look_for": "The defense playing soft / not bringing pressure.",
                "recognize": "If they rush only three or four and drop everyone, there's no rush to trap — the screen has no room.",
                "do": "Check to Quick Slants and take the easy underneath throw instead.",
                "counter_look_for": "Them ramping the blitz back up after you hit the quick game.",
                "counter_do": "Go back to the screen — the pressure you want is back.",
            }
        ],
    },
    "Smash Concept": {
        "notes": (
            "A two-man combo to one side: an outside receiver runs a short hitch while the "
            "inside man runs a corner behind him. It puts the cornerback in a bind — if he "
            "sits on the short hitch, the corner route is open over the top; if he runs "
            "with the corner, the hitch is open underneath."
        ),
        "base_read": "Read the cornerback. He sits down on the hitch → throw the corner over him; he carries the corner → throw the hitch underneath.",
        "when_to_call": "2nd-and-medium and red zone against Cover 2 (two deep safeties, corners sitting short) — it puts that short corner in conflict.",
        "evidence": {
            "why": "Against a corner who plays the flat, the two routes high-low him — he can only take one, and you throw the other.",
            "data": "Smash is a Cover 2 killer, a common look on 2nd-and-medium and in the red zone.",
            "risk": "Man coverage or a safety squatting on the corner takes it away. Tell: a defender trailing your inside receiver man-to-man. Work a man-beater instead.",
            "comparable": "A steady high-low answer any time the corner is sitting short in zone.",
        },
        "audibles": [
            {
                "label": "Check to a man-beater",
                "target_play": "Mesh Cross",
                "look_for": "Defenders locked on receivers man-to-man (they follow motion).",
                "recognize": "If a defender chases a man across the formation, it's man coverage — the high-low read won't work.",
                "do": "Check to Mesh so the crossing routes rub the man defenders off.",
                "counter_look_for": "Defenders dropping back into zone after mesh burns them.",
                "counter_do": "Go back to Smash — vs zone the corner is in conflict again.",
            }
        ],
    },
    "Four Verticals": {
        "notes": (
            "All the receivers run straight downfield to stretch the deep defenders until "
            "one has to cover two. Against a single deep safety, the two inside seams put "
            "him in a bind — he can't take both, so one comes open down the middle. Your "
            "big-chunk shot play."
        ),
        "base_read": "Read the deep middle safety — throw the inside seam he doesn't cover. If everyone's covered deep, dump the checkdown.",
        "when_to_call": "2-minute and 2nd-or-3rd-and-long when you need a chunk and expect deep zone. You want a single-high look so the seams open.",
        "evidence": {
            "why": "One deep-middle safety can't cover two seam routes. Send both at him and the one he leaves is a big play.",
            "data": "Four verts feasts on single-high coverages (one deep safety), common on passing downs.",
            "risk": "Two deep safeties (quarters) cover both seams. Tell: two safeties deep and wide pre-snap. Check to the crossers underneath instead of forcing it.",
            "comparable": "A go-to shot play to flip the field against single-high defenses.",
        },
        "audibles": [
            {
                "label": "Hot slant vs the blitz",
                "target_play": "Quick Slants",
                "look_for": "An all-out blitz — more rushers than you can block.",
                "recognize": "Count rushers vs blockers; if they bring more than you can block, someone's coming free.",
                "do": "Hot-route an inside receiver to a Slant and throw it now to beat the pressure.",
                "counter_look_for": "The defense backing off the blitz and dropping more into coverage.",
                "counter_do": "Go back to the verticals — with the blitz gone, you have time for the deep routes.",
            }
        ],
    },
}


def depth_for(play_name: str) -> dict[str, Any]:
    """
    Return Play depth fields (notes/base_read/when_to_call/evidence/audibles) for
    a core template play, ready to splat into ``Play(...)``. Empty dict when the
    play has no authored depth (Play's fields then stay None).
    """
    raw = _DEPTH.get(play_name)
    if not raw:
        return {}
    out: dict[str, Any] = {
        "notes": raw["notes"],
        "base_read": raw["base_read"],
        "when_to_call": raw["when_to_call"],
        "evidence": PlayEvidence(**raw["evidence"]),
        "audibles": [PlayAudible(**a) for a in raw["audibles"]],
    }
    return out
