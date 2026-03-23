"""Madden 26 — Claude prompt templates for each intelligence agent.

Each constant is a format-string that the corresponding agent fills with
runtime context before sending to Claude via ``ClaudeClient.generate``.
"""

# ---------------------------------------------------------------------------
# SchemeAI
# ---------------------------------------------------------------------------

SCHEME_ANALYSIS_PROMPT = """\
Analyze the following Madden 26 offensive/defensive scheme in depth.

Scheme name: {scheme_name}

Provide your analysis as valid JSON with this exact structure:
{{
  "description": "<2-3 sentence overview of the scheme>",
  "strengths": ["<strength 1>", "<strength 2>", ...],
  "weaknesses": ["<weakness 1>", "<weakness 2>", ...],
  "core_concepts": [
    {{
      "name": "<concept name>",
      "formation": "<best formation>",
      "primary_read": "<what to read>",
      "tags": ["<tag1>", "<tag2>"],
      "beats_coverages": ["<coverage1>", "<coverage2>"],
      "down_distance_fit": ["<situation1>", "<situation2>"],
      "stackable_with": ["<concept name>"]
    }}
  ],
  "best_formations": ["<formation 1>", "<formation 2>", ...],
  "recommended_playbooks": ["<team1>", "<team2>", ...],
  "concept_stacking_notes": "<explain how to layer concepts together>"
}}

Focus on Madden 26 gameplay mechanics — route tech, blocking AI, user \
matchups, and the current competitive meta. Include at least 5 core \
concepts with detailed stacking advice.
"""

SCHEME_ANALYSIS_SYSTEM = (
    "You are SchemeAI, the offensive and defensive scheme intelligence engine "
    "for Madden 26. You have expert-level knowledge of every formation, concept, "
    "route combination, and blocking scheme in the game. You understand the "
    "competitive meta and how concepts stack together to create unbeatable play "
    "sequences. Always respond with valid JSON only — no markdown, no commentary."
)

# ---------------------------------------------------------------------------
# GameplanAI
# ---------------------------------------------------------------------------

GAMEPLAN_GENERATION_PROMPT = """\
Generate a complete 10-play gameplan for Madden 26.

Player profile:
{player_profile}

Opponent tendencies:
{opponent_tendencies}

Roster strengths:
{roster}

Scheme preference: {scheme}

Provide your gameplan as valid JSON with this exact structure:
{{
  "plays": [
    {{
      "name": "<play name>",
      "formation": "<formation>",
      "play_type": "<run|pass_short|pass_medium|pass_deep|screen|play_action|rpo|qb_run>",
      "concept": "<offensive concept>",
      "primary_read": "<what to read pre/post snap>",
      "beats": ["<coverage/defense it beats>"],
      "situation_tags": ["<situation1>", "<situation2>"],
      "notes": "<execution tips>"
    }}
  ],
  "opening_script": ["<play name 1>", "<play name 2>", "<play name 3>", "<play name 4>", "<play name 5>"],
  "red_zone_picks": ["<play name>", "<play name>"],
  "anti_blitz_picks": ["<play name>", "<play name>"],
  "gameplan_notes": "<overall strategy summary>"
}}

Design the gameplan to exploit the opponent's weaknesses while staying \
within the player's execution ceiling. The opening script (first 5 plays) \
should probe the defense and establish tendencies. Include a balance of \
runs, short/medium/deep passes, screens, and play action. Tailor plays \
to roster strengths.
"""

GAMEPLAN_GENERATION_SYSTEM = (
    "You are GameplanAI for Madden 26. You build complete, competition-ready "
    "gameplans tailored to a player's skill level, their opponent's tendencies, "
    "and roster strengths. Every recommendation must be executable in Madden 26 "
    "gameplay. Always respond with valid JSON only — no markdown, no commentary."
)

# ---------------------------------------------------------------------------
# KillSheet
# ---------------------------------------------------------------------------

KILL_SHEET_PROMPT = """\
Generate a kill sheet of exactly 5 plays that will beat this specific opponent.

Opponent tendencies:
{opponent_tendencies}

Opponent scouting data:
- Zone coverage rate: {zone_rate}
- Man coverage rate: {man_rate}
- Blitz rate: {blitz_rate}
- Favorite formation: {favorite_formation}
- Run stop rate: {run_stop_rate}

Roster context:
{roster_context}

Provide your kill sheet as valid JSON with this exact structure:
{{
  "kills": [
    {{
      "play_name": "<specific Madden 26 play name>",
      "playbook": "<playbook/formation group>",
      "formation": "<exact formation>",
      "concept": "<what makes this play work>",
      "effectiveness_score": <0.0-1.0>,
      "yards_per_attempt": <expected YPA>,
      "opponent_weakness_exploited": "<specific weakness>",
      "hot_route_adjustments": ["<adjustment 1>"],
      "setup_notes": "<how to set this play up in-game>"
    }}
  ],
  "exploit_notes": ["<key insight 1>", "<key insight 2>"],
  "counter_warnings": ["<what to watch for 1>", "<what to watch for 2>"]
}}

Each play must directly exploit an identified weakness. Order plays from \
most to least effective. Include specific hot route adjustments and setup \
instructions for in-game execution.
"""

KILL_SHEET_SYSTEM = (
    "You are the Kill Sheet generator for Madden 26. You analyze opponent "
    "scouting data and produce exactly 5 targeted plays that exploit their "
    "specific weaknesses. Your recommendations are surgical — each play "
    "attacks a specific vulnerability. Always respond with valid JSON only."
)

# ---------------------------------------------------------------------------
# ReadAI
# ---------------------------------------------------------------------------

COVERAGE_READ_PROMPT = """\
Identify the defensive coverage from the following pre-snap alignment cues.

Pre-snap information:
- Deep safeties: {safety_count_deep}
- Corners in press: {press}
- Soft coverage (7+ yards off): {soft_coverage}
- Asymmetric look: {asymmetric}
- LB depth: {lb_depth}
- Additional indicators: {additional_indicators}

Provide your read as valid JSON:
{{
  "primary_coverage": "<cover_0|cover_1|cover_2|cover_2_man|cover_3|cover_3_match|cover_4|cover_4_palms|cover_6|man_press|man_off>",
  "confidence": "<high|medium|low>",
  "indicators": ["<indicator 1>", "<indicator 2>"],
  "vulnerable_zones": ["<zone 1>", "<zone 2>"],
  "recommended_targets": ["<target 1>", "<target 2>"],
  "reasoning": "<explain your read>"
}}

Analyze the alignment cues like a competitive Madden player would. Identify \
the most likely coverage shell and where the soft spots are.
"""

BLITZ_READ_PROMPT = """\
Detect whether a blitz is coming from these pre-snap cues.

Pre-snap information:
- Defenders near LOS (within 3 yards): {defenders_near_los}
- Visual blitz indicators: {blitz_indicators}
- Rushers on previous play: {rushed_last_play}
- Down and distance: {down_and_distance}

Provide your blitz read as valid JSON:
{{
  "blitz_detected": <true|false>,
  "blitz_probability": <0.0-1.0>,
  "likely_source": "<mlb|olb|cb|ss|fs|db_blitz|simulated|none>",
  "number_of_rushers": <int>,
  "hot_route_suggestion": "<what to audible to>",
  "protection_adjustment": "<blocking adjustment>",
  "indicators": ["<detected indicator 1>"],
  "reasoning": "<explain the read>"
}}
"""

COVERAGE_READ_SYSTEM = (
    "You are ReadAI for Madden 26. You are an expert at reading pre-snap "
    "defensive alignments to identify coverage shells and detect incoming "
    "blitzes. You think like a top-tier competitive Madden player who reads "
    "safety depth, corner alignment, and LB positioning to diagnose the defense "
    "before the snap. Always respond with valid JSON only."
)

# ---------------------------------------------------------------------------
# ClockAI
# ---------------------------------------------------------------------------

CLOCK_DECISION_PROMPT = """\
Determine the optimal clock management decision for this game state.

Game state:
- Quarter: {quarter}
- Time remaining: {time_remaining} seconds
- Score: User {score_user} - Opponent {score_opponent}
- Down: {down}, Yards to go: {yards_to_go}
- Yard line: {yard_line}
- User has possession: {is_user_possession}
- User timeouts: {timeouts_user}
- Opponent timeouts: {timeouts_opponent}

Provide your decision as valid JSON:
{{
  "action": "<kneel|hurry_up|milk_clock|normal|spike|timeout>",
  "reasoning": "<detailed explanation>",
  "urgency": <0.0-1.0>,
  "recommended_play_type": "<run|pass_short|pass_medium|pass_deep|screen|draw|qb_sneak|spike|kneel>",
  "seconds_burned_estimate": <float>,
  "two_minute_plan": {{
    "total_plays_planned": <int>,
    "estimated_score_probability": <0.0-1.0>,
    "play_calls": [
      {{
        "play_name": "<name>",
        "play_type": "<type>",
        "clock_action": "<action>",
        "target_yards": <int>,
        "rationale": "<why this play>"
      }}
    ]
  }}
}}

Think through the scenario like a competitive Madden player. Consider \
timeout management, whether to hurry or milk, spike vs. timeout tradeoffs, \
and the optimal play sequence to maximize win probability.
"""

CLOCK_DECISION_SYSTEM = (
    "You are ClockAI for Madden 26. You are an expert at end-game clock "
    "management, two-minute drill sequencing, fourth-down decisions, and "
    "timeout optimization. You calculate win probabilities and recommend "
    "the play-by-play sequence that maximizes the chance of winning. "
    "Always respond with valid JSON only."
)

# ---------------------------------------------------------------------------
# MetaBot
# ---------------------------------------------------------------------------

META_ANALYSIS_PROMPT = """\
Produce a weekly competitive meta analysis for Madden 26.

Current patch version: {patch_version}
Current date: {current_date}

Known meta context:
{meta_context}

Community trends / patch notes:
{patch_notes}

Provide your analysis as valid JSON:
{{
  "patch_version": "{patch_version}",
  "top_strategies": ["<strategy 1>", "<strategy 2>", ...],
  "rising_strategies": ["<strategy 1>", "<strategy 2>", ...],
  "declining_strategies": ["<strategy 1>", "<strategy 2>", ...],
  "exploits": [
    {{
      "name": "<exploit name>",
      "description": "<what it does>",
      "counter": "<how to counter>",
      "time_remaining": "<how long until patched>",
      "risk_level": "<high|medium|low>"
    }}
  ],
  "meta_summary": "<3-4 sentence summary of the current meta state>"
}}

Analyze the competitive Madden 26 meta considering the patch version, \
community strategies, and known exploits. Identify what's rising, what's \
falling, and what the counter-meta looks like.
"""

META_ANALYSIS_SYSTEM = (
    "You are MetaBot for Madden 26. You track the competitive meta across "
    "all platforms, analyzing strategy prevalence, exploit lifecycles, and "
    "patch impact. You provide actionable intelligence on what works now, "
    "what's emerging, and what to avoid. Always respond with valid JSON only."
)
