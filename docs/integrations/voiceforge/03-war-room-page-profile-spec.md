# War Room Page Profile — Specification

> Companion: [02-madden26-language-profile-spec.md](02-madden26-language-profile-spec.md), [04-routing-matrix.md](04-routing-matrix.md), [05-priority-and-interruption-rules.md](05-priority-and-interruption-rules.md).
> War Room is the **first** page profile, the template for the other 8. Each page profile defines what intents the page surfaces, what scripts each intent produces, and what priority/interruption rules apply. Page profiles are language-agnostic — they compose with whatever language profile the active title supplies.

## Purpose

The War Room page is the player's pre-match command center: opponent dossier, gameplan summary, mental prep, in-tournament briefings between rounds. The voice surface there is the most "narrative" — long, structured, high-signal.

This profile defines:
1. **Intents** — the things War Room asks VoiceForge to say.
2. **Script templates** per intent (language-agnostic skeletons).
3. **Triggers** — what UI events / user actions / VAF events fire each intent.
4. **Priority + interruption rules** specific to War Room.
5. **Mood-update flow** — the player's TiltGuard input loop.
6. **Mental reset prompts** — between-round / between-drive scripts.

It does **not** define vocabulary (that's the language profile, e.g., [02-madden26-language-profile-spec.md](02-madden26-language-profile-spec.md)).

## File layout

```
backend/app/services/integrations/voiceforge/pages/war_room/
├── __init__.py
├── profile.py                    # WarRoomPage class — entry point
├── intents.py                    # enumeration of intents the page emits
├── triggers.py                   # mapping (UI event | VAF event) -> intent
├── priority.py                   # War Room-specific priority overrides
├── templates/
│   ├── pre_game_briefing.j2      # the long one — 60-90s
│   ├── mid_game_adjustment.j2    # 8-15s — between drives
│   ├── mood_update_response.j2   # responds to TiltGuard mood selections
│   ├── mental_reset_short.j2     # 8-12s — between rounds in tournaments
│   ├── mental_reset_long.j2      # 30-45s — extended breathing prompt
│   └── round_recap.j2            # post-round 6-10s
└── tests/
    └── test_*.py
```

## Intents

The exhaustive list War Room emits in v1:

| Intent | Length | Trigger | Priority |
|---|---|---|---|
| `WAR_ROOM_PRE_GAME_BRIEFING` | 60–90s | Player taps "Read briefing" OR auto-fires 90s before scheduled match start (opt-in setting) | NORMAL |
| `WAR_ROOM_MID_GAME_ADJUSTMENT` | 8–15s | Drive ends + player on War Room screen + agent flags an adjustment | NORMAL |
| `WAR_ROOM_MOOD_UPDATE_RESPONSE` | 5–12s | Player selects a mood in the TiltGuard widget | HIGH |
| `WAR_ROOM_MENTAL_RESET_SHORT` | 8–12s | Player taps "Start reset" OR `BETWEEN_ROUNDS` event from VAF | NORMAL |
| `WAR_ROOM_MENTAL_RESET_LONG` | 30–45s | Player taps the extended-reset option | LOW |
| `WAR_ROOM_ROUND_RECAP` | 6–10s | `MATCH_ENDED` VAF event with player still on War Room screen | NORMAL |
| `WAR_ROOM_OPPONENT_TENDENCY_REMINDER` | 4–6s | Player hovers an opponent tendency for >2s (subtle) | LOW |

Anything War Room wants VoiceForge to say maps to one of these intents.

## Pre-game briefing template (`pre_game_briefing.j2`)

The flagship cue. Five sections, each composed from language fragments:

```
[01] Opener (8-12s)
   {{ language.greeting }}
   You're going up against {{ opponent.spoken_name }} — {{ opponent.archetype_phrase }}.

[02] Opponent summary (15-25s)
   {{ language.opponent_tendency_intro }}
   Their top tendency: {{ opponent.top_tendency }}.
   {{ if opponent.recent_form }} Recent form: {{ opponent.recent_form }}. {{ endif }}
   {{ if opponent.weakness }} Their weakness: {{ opponent.weakness }}. {{ endif }}

[03] Gameplan key plays (20-30s)
   {{ language.key_plays_intro }}
   {{ for play in top_plays|take(3) }}
     {{ loop.index }}. {{ play.spoken_name }}, for {{ play.situation_phrase }}.
     {{ pause(short) }}
   {{ endfor }}

[04] Mental cue (8-15s)
   {{ language.mental_cue_for_tone[user.tone] }}
   {{ pause(medium) }}

[05] Closer (3-5s)
   {{ language.closer_for_tone[user.tone] }}
```

Total budget: **60–90 seconds.** The template is language-agnostic; Madden's language profile fills `{{ opponent.archetype_phrase }}` with "aggressive rush" while NBA's fills it with "high-PnR scorer."

The `{{ language.X }}` placeholders are looked up via the active language profile (e.g., `Madden26Language.greeting`). The `{{ opponent.X }}` placeholders are filled from the EsportsForge backend's opponent record.

### Variant: free tier

Free tier doesn't get TTS (per [06-subscription-tier-gating.md](06-subscription-tier-gating.md)). Instead, the same template renders to text in the dashboard with an "Upgrade for voice" CTA. The script template is identical; only the delivery channel differs. The router handles this fan-out — page profile authors don't think about it.

## Mid-game adjustment template (`mid_game_adjustment.j2`)

Short cue between drives.

```
{{ language.transition }}                            # "Quick adjustment."
{{ adjustment.lead }}                                # agent-supplied opening line
{{ language.mid_game_recommendation_phrase }}        # "Try"
{{ adjustment.spoken_play_name }}.
{{ if adjustment.why_short }}
  {{ language.because }} {{ adjustment.why_short }}.
{{ endif }}
```

Budget: 8–15s. Anything longer ducks back to a banner notification — voice should not block the player from getting back to the next drive.

## Mood update response template (`mood_update_response.j2`)

The player taps a mood pill in the TiltGuard widget. War Room responds.

Mood inputs (from existing TiltGuard schema): `green` (Locked In) / `yellow` (Wobbly) / `red` (Tilted).

```
{{ if mood == 'green' }}
  {{ language.mood_locked_in[user.tone] }}                   # affirmation, brief
{{ elif mood == 'yellow' }}
  {{ language.mood_wobbly[user.tone] }}                       # gentle redirect
  {{ language.suggest_short_reset[user.tone] }}               # offer the 8-12s reset
{{ elif mood == 'red' }}
  {{ language.mood_tilted[user.tone] }}                       # direct, calm-bias regardless of player tone
  {{ language.recommend_long_reset[user.tone] }}              # recommend the 30-45s reset
{{ endif }}
```

**Important:** for `red` mood, even an Intense-tone player gets a calm-leaning response. The point is to de-escalate, not to amplify. The language profile encodes this — Madden's `mood_tilted[Tone.INTENSE]` is itself calm phrasing ("Step back. Reset. Then we go.") rather than the usual intense register.

This is HIGH priority — interrupts whatever's playing. Player asked for a response; they get one immediately.

## Mental reset short template (`mental_reset_short.j2`)

The 30s breathing reset that the Tournament page also reuses.

```
{{ language.reset_lead_in }}                                  # "Let's reset."
{{ pause(medium) }}
Close your eyes if you can.
{{ pause(medium) }}
Four deep breaths. {{ pause(short) }}
In through the nose. {{ pause(long) }}
Hold. {{ pause(long) }}
Out slow. {{ pause(long) }}
{{ pause(medium) }}
{{ language.reset_outro_for_tone }}                            # "You're locked in." / "You're prepared." / "You've done the work."
```

Budget: 8–12s narrated; the actual breathing is the `pause(long)` × 3 ≈ 4s of silence. The narrator names the cycle once, then lets the player breathe.

## Mental reset long template (`mental_reset_long.j2`)

Extended version (30–45s). Same structure but with two full breath cycles + a visualization beat:

```
{{ language.reset_lead_in_long }}
{{ pause(long) }}
First cycle. In through the nose. {{ pause(long) }} Hold. {{ pause(long) }} Out slow. {{ pause(long) }}
{{ pause(medium) }}
Now visualise your opening play. See yourself executing it. {{ pause(long) }}
{{ pause(medium) }}
Second cycle. In. {{ pause(long) }} Hold. {{ pause(long) }} Out. {{ pause(long) }}
{{ pause(medium) }}
{{ language.reset_outro_long_for_tone }}
```

LOW priority — easily interrupted by anything urgent. If the player's about to be dropped into a match, this is not what should be playing.

## Triggers (`triggers.py`)

The mapping from observable events to intents:

```python
TRIGGERS = [
    Trigger(
        intent=Intent.WAR_ROOM_PRE_GAME_BRIEFING,
        sources=[
            UISource("button.read_briefing.click"),
            UISource("auto.scheduled_match_minus_90s"),
        ],
        gates=[OnPage("war_room")],
    ),
    Trigger(
        intent=Intent.WAR_ROOM_MOOD_UPDATE_RESPONSE,
        sources=[UISource("tiltguard.mood_changed")],
        gates=[OnPage("war_room")],
        payload_from="event.mood",
    ),
    Trigger(
        intent=Intent.WAR_ROOM_MENTAL_RESET_SHORT,
        sources=[
            UISource("button.start_reset.click"),
            VAFSource("BETWEEN_ROUNDS", from_pages=["war_room"]),
        ],
    ),
    Trigger(
        intent=Intent.WAR_ROOM_MENTAL_RESET_LONG,
        sources=[UISource("button.extended_reset.click")],
    ),
    Trigger(
        intent=Intent.WAR_ROOM_ROUND_RECAP,
        sources=[VAFSource("MATCH_ENDED", from_pages=["war_room"])],
    ),
    Trigger(
        intent=Intent.WAR_ROOM_OPPONENT_TENDENCY_REMINDER,
        sources=[UISource("hover.opponent_tendency.over_2s")],
        cooldown_sec=30,    # don't pester
    ),
    Trigger(
        intent=Intent.WAR_ROOM_MID_GAME_ADJUSTMENT,
        sources=[VAFSource("PLAY_ENDED + drive_complete", from_pages=["war_room"])],
        gates=[AgentApproval("GameplanAgent")],
    ),
]
```

The frontend hook (`useVoiceForge`) and the backend agents collectively enforce these triggers. The page profile declares them; the runtime wires them.

## Priority overrides

War Room defaults from [05-priority-and-interruption-rules.md](05-priority-and-interruption-rules.md), with these page-specific overrides:

```python
PRIORITY_OVERRIDES = {
    Intent.WAR_ROOM_MOOD_UPDATE_RESPONSE: Priority.HIGH,    # player asked, respond now
    Intent.WAR_ROOM_PRE_GAME_BRIEFING:    Priority.NORMAL,  # interruptable for danger
    Intent.WAR_ROOM_MENTAL_RESET_LONG:    Priority.LOW,     # easily interruptable
}
```

## Mood update flow — full sequence

The flow when a player taps a mood pill, end-to-end:

```
1. Frontend: TiltGuard widget click → POST /api/v1/tiltguard/mood
2. EsportsForge backend: persists mood + emits internal "mood_changed" event
3. Internal event handler routes to VoiceForge: POST /api/v1/cues/enqueue
   {
     page: "war_room",
     language: <session.title or null>,
     event_type: "MOOD_UPDATED",
     intent: "WAR_ROOM_MOOD_UPDATE_RESPONSE",
     priority: "HIGH",
     payload: { mood: "yellow" }
   }
4. VoiceForge router: war_room page profile + (active language) → mood_update_response.j2
5. Template renders → TTS → playback
6. If mood == "red": automatically chains to suggest_long_reset → frontend surfaces the "Start extended reset" button
7. Cue plays; queue manager interrupts any LOW-priority cue currently playing
```

The chain in step 6 is implemented as a follow-up cue enqueued from the same handler, with a 1.5s delay so the audio "Recommend the long reset" finishes before the next cue can interrupt.

## Language-agnostic by design

Madden + War Room and NBA + War Room use the **same templates** in this directory. What changes is which language fragment fills `{{ language.X }}`. NBA's `language.greeting` comes from the NBA language profile; football's comes from the Madden language profile.

This is the contract that makes adding a new title cheap: drop in a new language profile that supplies all the `language.*` keys War Room references, and War Room works for that title. No War Room template edits.

The set of `language.*` keys War Room expects is enumerated in `templates/_required_language_keys.py` and CI gates that any new language profile supplies them all.

## Testing

### Template unit tests
- Render every template with synthetic data — assert no orphan placeholders, no language-key gaps.
- Tone variants: each `language.X[Tone.Y]` lookup resolves for all tones.

### Trigger tests
- Simulate UI events / VAF events → assert the right intent fires (or not, due to gates).
- Mood-update chain: `red` mood → response cue + auto-chained long-reset suggestion within 2s.

### Cadence tests
- Pre-game briefing renders within 60–90s budget at Normal speed (Madden cadence).
- Mid-game adjustment within 15s budget.

### Integration tests (Phase 1)
- End-to-end: trigger pre-game briefing on War Room with a Madden language profile and a populated opponent record → audible 60–90s briefing.
- Mood update flow on Madden + War Room → mood-response cue audible within 2s of click.

## Page-profile pattern for the other 8

Each subsequent page profile (Gameplan, Arsenal, Drills, SimLab, Tournament, Analytics, Dashboard, In-Game) follows this same shape: intents → templates → triggers → priorities. The Tournament page profile, in particular, will reuse the mental-reset templates from War Room directly (a tournament between-round reset is the same script).

## What this spec does not decide

- **What Madden's language profile supplies** for `{{ language.greeting }}` etc. — that's [02-madden26-language-profile-spec.md](02-madden26-language-profile-spec.md).
- **Tier gating** — Doc #06 (free tier sees text only).
- **Integrity-mode gating** — Doc #07 (Tournament mode permits War Room voice between matches but silences during gameplay).
- **Other pages' profiles** — written when their phase starts, using this as the template.
