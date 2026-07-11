# Madden 26 Language Profile — Specification

> Companion: [01-core-service-spec.md](01-core-service-spec.md), [03-war-room-page-profile-spec.md](03-war-room-page-profile-spec.md), [04-routing-matrix.md](04-routing-matrix.md).
> Madden 26 is the **first** language profile, the template for the other 10. Each language profile is a sport-vocabulary + cadence + tone-variant package that page profiles compose with at render time.

## Purpose

A language profile is a self-contained module that supplies, for one title:
1. **Vocabulary** — the canonical names for in-game concepts (formations, coverages, fronts, plays, situational labels) and how to *say* them.
2. **Cadence** — the timing rhythms unique to this sport (how long a pre-snap window is, how short an in-game cue must be).
3. **Tone variants** — Intense / Standard / Calm phrasing of the same intent.
4. **Phonetic guides** — pronunciation hints for terms TTS engines mangle.
5. **Script fragments** — reusable phrases that page profiles compose into full scripts.

It does **not** contain page-specific scripts — those are owned by the page profiles ([03-war-room-page-profile-spec.md](03-war-room-page-profile-spec.md) for War Room, etc.). The Madden language profile + the War Room page profile compose into the actual script the player hears.

## File layout

```
backend/app/services/integrations/voiceforge/languages/madden26/
├── __init__.py
├── profile.py                      # Madden26Language class — entry point
├── vocabulary.py                   # canonical names + phonetic guides
├── cadence.py                      # sport-specific timing constants
├── tones.py                        # Intense / Standard / Calm phrase variants
├── fragments/
│   ├── pre_snap.py                 # reusable pre-snap phrasing
│   ├── post_play.py
│   ├── encouragement.py
│   ├── correction.py
│   └── briefing_components.py      # opener, opponent_summary, key_plays, mental_cue, closer
└── tests/
    └── test_*.py
```

## Vocabulary (`vocabulary.py`)

The single source of truth for how Madden concepts are spoken. Other modules import from here; nothing else hardcodes a formation name.

### Formations (offensive)

```python
OFFENSIVE_FORMATIONS = {
    "shotgun_trips":       Spoken("Shotgun Trips",      phonetic="SHOT-gun TRIPS"),
    "shotgun_bunch":       Spoken("Shotgun Bunch",      phonetic="SHOT-gun BUNCH"),
    "shotgun_empty":       Spoken("Shotgun Empty",      phonetic="SHOT-gun EM-tee"),
    "i_form_pro":          Spoken("I-Form Pro",         phonetic="I-form PRO"),
    "singleback_ace":      Spoken("Singleback Ace",     phonetic="SIN-gul-back ACE"),
    "pistol_strong":       Spoken("Pistol Strong",      phonetic="PIS-tul STRONG"),
    # ...full 24 formations matching the VAF Madden adapter's classifier
}
```

`Spoken` is a small dataclass — the canonical text + an optional ElevenLabs SSML phonetic override. ElevenLabs SSML supports `<phoneme>` tags; we use them for terms it consistently mispronounces.

### Coverages and defensive fronts

```python
COVERAGES = {
    "cover_0":  Spoken("Cover Zero",  phonetic="cover ZERO"),
    "cover_1":  Spoken("Cover One",   phonetic="cover ONE"),
    "cover_2":  Spoken("Cover Two",   phonetic="cover TOO"),
    "cover_3":  Spoken("Cover Three", phonetic="cover THREE"),
    "cover_4":  Spoken("Cover Four",  phonetic="cover FOR"),
    "cover_6":  Spoken("Cover Six",   phonetic="cover SIX"),
    "tampa_2":  Spoken("Tampa Two",   phonetic="TAM-pa TOO"),
    "man":      Spoken("Man",         phonetic="MAN"),
}
DEFENSIVE_FRONTS = {
    "4_3":      Spoken("Four-Three"),
    "3_4":      Spoken("Three-Four"),
    "nickel":   Spoken("Nickel",      phonetic="NIK-uhl"),
    "dime":     Spoken("Dime"),
    "quarter":  Spoken("Quarter"),
}
```

### Situational labels

```python
DOWN_PHRASING = {
    1: "first down",
    2: "second down",
    3: "third down",
    4: "fourth down",
}
DISTANCE_PHRASING = {
    "short":   "short yardage",      # 1-3 yards
    "medium":  "medium",              # 4-7 yards
    "long":    "long",                # 8+ yards
    "two_min": "two minute",          # special — overrides others in 2-min drill
}
FIELD_POSITION_PHRASING = {
    "OWN_GOAL":  "deep in your own end",
    "OWN_20":    "in your own twenty",
    "OWN_35":    "near midfield",
    "MIDFIELD":  "at midfield",
    "OPP_45":    "across midfield",
    "OPP_20":    "in the red zone",
    "OPP_GOAL":  "at the goal line",
}
```

These compose: `f"{DOWN_PHRASING[3]} and {DISTANCE_PHRASING['long']}, {FIELD_POSITION_PHRASING['OPP_20']}"` → "third down and long, in the red zone."

### Tendencies / archetypes

```python
OPPONENT_ARCHETYPES = {
    "aggressive_rush":  "aggressive rush",
    "zone_coverage":    "zone-heavy",
    "blitz_heavy":      "blitz-prone",
    "west_coast":       "West Coast",
    "spread_option":    "spread option",
    "balanced":         "balanced",
}
```

## Cadence (`cadence.py`)

Football-specific timing constants that the queue manager and script renderers consult.

```python
PRE_SNAP_WINDOW_SEC = 25            # play clock starts at 25–40s; safe upper-bound for cue length
POST_PLAY_WINDOW_SEC = 6            # short cues only — players are decompressing
RED_ZONE_URGENCY_BUMP = True        # red-zone cues bump priority by one class
TWO_MIN_DRILL_TRUNCATE_SEC = 4      # max in-game cue length when clock < 2:00 in half
SNAP_INTERRUPTION_RULE = "duck_only" # pre-snap cue ducks (doesn't cancel) when SNAP_DETECTED fires; resumes post-play if still relevant
```

These get read by:
- The queue manager (`SNAP_INTERRUPTION_RULE` is consulted when a `PLAY_STARTED` event arrives mid-cue).
- Script template authors via context: `{{ if cadence.in_two_min_drill }} {{ short_form }} {{ else }} {{ standard_form }} {{ endif }}`.
- TTS rate adjustment: in 2-min drill cadence, briefing_speed effectively bumps one notch (Normal → Fast).

The other 10 language profiles ship analogous `cadence.py` files. NBA's will have `CONTINUOUS_PLAY = True`, `MAX_IN_GAME_CUE_SEC = 1.5`, `INTERRUPT_ON_SHOT_CLOCK_RESET = True`.

## Tone variants (`tones.py`)

Each phrase concept has 3 spellings. Authors of page profiles select by the player's `voice_settings.tone`:

```python
GREETINGS = {
    Tone.INTENSE: [
        "Locked in. Let's hunt.",
        "Time to attack.",
        "No mercy today.",
    ],
    Tone.STANDARD: [
        "Welcome back.",
        "Ready when you are.",
        "Let's get to work.",
    ],
    Tone.CALM: [
        "Take a breath. We're set.",
        "You're prepared. Stay grounded.",
        "Trust the work. Here we go.",
    ],
}
ENCOURAGEMENT_AFTER_SCORE = {
    Tone.INTENSE: ["Step on their throat.", "Keep punching.", "Don't ease up."],
    Tone.STANDARD: ["Good drive. Keep it rolling.", "Nice score. Stay focused.", "On to the next one."],
    Tone.CALM: ["Steady drive. Reset and continue.", "Composed. Keep that rhythm.", "Solid execution. Stay measured."],
}
CORRECTION_AFTER_TURNOVER = {
    Tone.INTENSE: ["Shake it off. Get even.", "That's on you. Fix it now.", "Forget it — drive harder."],
    Tone.STANDARD: ["Reset. Next series.", "Move on. Defense will give us a chance.", "It happens. Stay engaged."],
    Tone.CALM: ["Breathe. The game is long.", "One play. Let it go.", "We've recovered from worse. Reset."],
}
```

Variants are picked round-robin or randomly per render — same intent shouldn't sound identical 5 times in a row.

The other languages each ship their own tones. Football's "drive" / "series" vocabulary doesn't transplant to basketball's "possession" or BR's "rotation."

## Phonetic guides

ElevenLabs SSML support is leveraged for known mispronunciations:

```python
SSML_OVERRIDES = {
    "RPO":            "<phoneme alphabet='ipa' ph='ɑːr.piː.oʊ'>RPO</phoneme>",   # not "Reep-oh"
    "Tampa 2":        "<phoneme alphabet='ipa' ph='ˈtæm.pə tuː'>Tampa Two</phoneme>",
    "PA Crossers":    "<phoneme alphabet='ipa' ph='ˌpiː.eɪ ˈkrɒs.ərz'>PA Crossers</phoneme>",
    # opponent names that the platform commonly sees:
    "xViper_Elite":   "<phoneme alphabet='ipa' ph='ˈeks ˈvaɪ.pər ɪˈliːt'>xViper Elite</phoneme>",
}
```

The list is hand-curated. We add entries when QA flags mispronunciations during integration testing.

## Script fragments (`fragments/`)

Page profiles compose Madden cues from these fragments. Each fragment is a small Jinja-style template with parameter slots.

Example — `fragments/briefing_components.py`:

```python
PRE_GAME_OPENER = """
{{ greeting }} {{ pause(short) }}
You're going up against {{ opponent.spoken_name }} — {{ opponent.archetype_phrase }}.
Their tendency: {{ opponent.top_tendency }}.
"""

PRE_GAME_KEY_PLAYS = """
Three plays you'll lean on today:
{% for play in top_plays %}
  {{ loop.index }}. {{ play.spoken_name }}, for {{ play.situation_phrase }}.
  {{ pause(short) }}
{% endfor %}
"""

PRE_GAME_MENTAL_CUE = """
{{ pause(medium) }}
{{ mental_cue_for_tone }} {{ pause(short) }}
{{ closer_for_tone }}
"""
```

The War Room page profile concatenates these fragments + interpolates them with real game/opponent data. Other page profiles (Tournament, Drills) reuse the same fragments where they fit.

The `{{ pause(short|medium|long) }}` tokens render to SSML `<break>` tags with sport-aware durations:

```python
# In Madden's renderer:
PAUSE_DURATIONS = {
    "short":  "300ms",
    "medium": "700ms",
    "long":   "1200ms",
}
# In NBA's renderer (continuous play, much shorter):
# PAUSE_DURATIONS = { "short": "100ms", "medium": "300ms", "long": "500ms" }
```

## What pages compose with this language

Per the matrix (Doc #04), Madden + each page produces a script. Coverage in v1:

| Page | v1 status | Reuses Madden language for |
|---|---|---|
| War Room | ✅ Phase 1 | Pre-game briefing (full); mid-game adjustment (short); mood update; mental reset |
| Gameplan | Phase 2 | "Read me the kill sheet" — read 5 plays with situation + why |
| Arsenal | Phase 2 | Step-by-step weapon coaching — pre-execution mental cue, post-deployment debrief |
| Drills | Phase 2 | Rep cues during drill execution; encouragement / correction beats |
| SimLab | Phase 2 | Scenario announcement + post-decision correction |
| Tournament | Phase 2 | Round briefing (compressed War Room); between-round reset prompts |
| Analytics | Phase 2 | Analyst-style review playback ("on this drive, you...") |
| Dashboard | Phase 2 | Daily Forge summary; weekly narrative read-out |
| In-Game | Phase 2 (gated by Integrity Mode per Doc #07) | Live coaching during pre-snap windows |

Phase 1 ships **only War Room** for Madden. The other 8 pages stay text-only on the Madden + Page cells until Phase 2.

## Integration with VisionAudioForge

When the VAF event bus emits a Madden football payload (see VAF Doc #03), the EsportsForge agent that subscribes (e.g., GameplanAgent) decides whether a voice cue is warranted and submits to VoiceForge with `language: "madden26"`. The language profile and the page profile compose at render time.

The VAF events are the trigger; the cue construction happens in the agent; the cue rendering happens in VoiceForge. Three layers, each replaceable.

## Testing strategy

### Vocabulary tests
- Every key in `OFFENSIVE_FORMATIONS` resolves through TTS without artefacts (manual listening pass per formation).
- SSML phonetic overrides validated via TTS — pronunciation matches the IPA spec.

### Cadence tests
- Fragment renderer with `cadence.in_two_min_drill = True` produces shorter output than default.
- Pause-token expansion produces correct SSML for football durations.

### Tone variant tests
- Every tone-keyed dictionary has at least one entry per `Tone.{INTENSE, STANDARD, CALM}`. CI guards this.
- Round-robin selection doesn't pick the same variant twice in a row.

### Integration tests
- Compose a Madden language + War Room page → render a full briefing with synthetic data → assert output validates against script-template schema (paragraph count, length budgets, no orphan placeholders).

## Maintenance

Language profiles need updates per Madden patch. Football vocabulary is stable, but Madden 26 → Madden 27 may rename or add formations. The profile is independent of the binary — patching `vocabulary.py` and bumping the profile version is sufficient; no rebuild.

## What this spec does not decide

- **War Room script structure** — Doc #03.
- **Other titles' language profiles** — written using this as the template when their phase starts.
- **TTS provider mechanics** — Doc #01.
