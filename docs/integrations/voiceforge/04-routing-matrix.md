# Routing Matrix — Title × Page × Tier × Mode

> Companion: [01-core-service-spec.md](01-core-service-spec.md), [02-madden26-language-profile-spec.md](02-madden26-language-profile-spec.md), [03-war-room-page-profile-spec.md](03-war-room-page-profile-spec.md), [06-subscription-tier-gating.md](06-subscription-tier-gating.md), [07-integrity-mode-gating.md](07-integrity-mode-gating.md).
> The matrix is the API. Cue routing always traverses these four dimensions in this order. Authoring teams own different dimensions; the runtime composes them.

## The four dimensions

```
Title          → 11 values (madden26, cfb26, nba2k26, eafc26, mlb26,
                            warzone, fortnite, ufc5, undisputed,
                            pga2k25, video_poker)
Page           →  9 values (war_room, gameplan, arsenal, drills,
                            simlab, tournament, analytics, dashboard,
                            in_game)
Subscription   →  4 values (free, competitive, elite, team)
Integrity mode →  4 values (offline_lab, ranked, tournament, broadcast)
```

11 × 9 × 4 × 4 = **1,584 cells.** We do not enumerate them. Cells materialise at request time.

## Authoring split

Each dimension has its own author and its own artefact:

| Dimension | Authored by | Artefact |
|---|---|---|
| Title | Voice/content engineer per language | `languages/<title>/profile.py` (vocabulary, cadence, tones, fragments) |
| Page | Voice/content engineer per page | `pages/<page>/profile.py` (intents, templates, triggers, priority overrides) |
| Subscription | Backend + product | `policies/tier_gating.py` (single file — Doc #06) |
| Integrity mode | Backend + compliance | `policies/integrity_gating.py` (single file — Doc #07) |

Total v1 hand-authored artefacts: **11 + 9 + 1 + 1 = 22 files.** Far less than 1,584 — composition handles the explosion.

## Lookup at request time

When a cue arrives at the router (per [01-core-service-spec.md §"Router"](01-core-service-spec.md)):

```python
def route_cue(cue: CueRequest, ctx: UserContext) -> RoutedCue | DroppedCue:
    # Dimension 1: title
    language = LANGUAGES[cue.language]                  # Madden26Language

    # Dimension 2: page
    page = PAGES[cue.page]                              # WarRoomPage
    intent = page.intents[cue.intent]                   # WAR_ROOM_PRE_GAME_BRIEFING
    template = page.templates[intent.template_key]      # pre_game_briefing.j2

    # Dimension 3: tier (gate first, may drop or downgrade)
    tier_decision = tier_gating.evaluate(ctx.tier, cue.page, cue.intent)
    if tier_decision.drop:
        return DroppedCue("tier_below_minimum")
    if tier_decision.text_only:
        return RoutedCue.text_only(...)                 # send to dashboard, no synthesis

    # Dimension 4: integrity mode (gate, may drop)
    mode_decision = integrity_gating.evaluate(
        ctx.integrity_mode, cue.language, cue.page, cue.intent, cue.event_type
    )
    if mode_decision.drop:
        return DroppedCue(mode_decision.reason)

    # Compose
    rendered = template.render(
        language=language,
        page=page,
        user=ctx.voice_settings,
        payload=cue.payload,
    )

    return RoutedCue(
        text=rendered,
        ssml=apply_phonetic_overrides(rendered, language),
        voice_id=select_voice_id(ctx.tier, ctx.voice_settings),
        tts_provider=select_provider(ctx.integrity_mode),
        priority=intent.priority_or_override(page),
    )
```

Pure function over (cue, ctx). No DB calls; the language/page artefacts are loaded into memory at service boot. Tier and integrity gates are config-driven and reload-on-change.

## Conflict resolution

Two ways multiple "valid" results could compose:

### Tone variants

Each language's tone-keyed dictionaries (`GREETINGS[Tone.INTENSE]`, etc.) hold multiple phrasings. The renderer picks via:

1. **Round-robin per session** — the language profile holds a small per-session counter so the same phrase doesn't repeat back-to-back. Counter is in `VoiceSession.adapter_state["language_state"]`.
2. **Random-with-seed** — for stateless rendering (debug, fixture replay), seeded by `(session_id, intent, render_index)`.

Round-robin is default; random is for tests and the "preview voice" feature in Settings.

### Required language key missing

If a page template references `{{ language.X }}` and the active language profile doesn't supply `X`, the renderer:

1. **Checks the universal language profile** (`languages/universal/`) which supplies neutral fallbacks for common keys like greetings, transitions, errors.
2. If still missing, **drops the cue** and logs `language_key_missing`. CI gates this — every page profile's required keys must exist on every language profile that page supports.

The set of required keys per page is locked in `pages/<page>/templates/_required_language_keys.py`.

## Coverage matrix (v1 → Phase 5)

Hand-tracked, not auto-generated, because most cells are "deferred" not "intentionally null." Filled cell = the (title × page) combo has authored content; empty = falls back to text or silence.

|       | War Room | Gameplan | Arsenal | Drills | SimLab | Tournament | Analytics | Dashboard | In-Game |
|---|---|---|---|---|---|---|---|---|---|
| Madden 26   | **P1** | P2 | P2 | P2 | P2 | P2 | P2 | P2 | P2 |
| CFB 26      | P2 | P2 | P2 | P2 | P2 | P2 | P2 | P2 | P2 |
| NBA 2K26    | P3 | P3 | P3 | P3 | P3 | P3 | P3 | P3 | P3 |
| EA FC 26    | P3 | P3 | P3 | P3 | P3 | P3 | P3 | P3 | P3 |
| MLB 26      | P3 | P3 | P3 | P3 | P3 | P3 | P3 | P3 | P3 |
| Warzone     | P4 | P4 | P4 | P4 | P4 | P4 | P4 | P4 | P4 |
| Fortnite    | P4 | P4 | P4 | P4 | P4 | P4 | P4 | P4 | P4 |
| UFC 5       | P5 | P5 | P5 | P5 | P5 | P5 | P5 | P5 | P5 |
| Undisputed  | P5 | P5 | P5 | P5 | P5 | P5 | P5 | P5 | P5 |
| PGA 2K25    | P5 | P5 | P5 | P5 | P5 | P5 | P5 | P5 | P5 |
| Video Poker | P5 | P5 | P5 | P5 | P5 | P5 | P5 | P5 | P5 |

**P1 (Phase 1):** Madden + War Room only. Total cells with synthesised voice: **1**.
**P2 (Phase 2):** + CFB language; + Drills, SimLab, Gameplan, In-Game pages for football. Total cells: **2 × 5 = 10.**
**P3 (Phase 3):** + NBA / EAFC / MLB languages; their full 9-page set. Total cells after Phase 3: **5 titles × 9 pages = 45.**
**P4 (Phase 4):** + Warzone / Fortnite languages; FPS in-game profile upgrades. **63 cells.**
**P5 (Phase 5):** + UFC / Undisputed / PGA / Video Poker. **All 99 cells.**

(99 not 1,584 because tier × mode dimensions are policy, not authored content per cell.)

## Versioning

Each cell composes from artefacts that each version independently:
- `madden26@0.1.0` (language profile)
- `war_room@0.1.0` (page profile)
- Tier policy and integrity policy version with the core service.

Cue events emitted to the dashboard / log carry composed metadata: `composed_from = ["madden26@0.1.0", "war_room@0.1.0", "tier_policy@1.0.0", "integrity_policy@1.0.0"]`. Useful for triaging "why does this cue sound wrong" — we can pin down which artefact owns the bug.

When a language profile bumps a major version (breaking template-key changes), every page profile that depends on it must update or the CI gate (required-keys check) breaks the build.

## Page profile fallback chain

Some pages don't make sense for every title. PGA on the In-Game page is meaningful (pre-shot routine cues); Video Poker on the Tournament page is mostly meaningless (no rounds). When a (title × page) cell is intentionally null, the matrix marks it and the page silently shows no voice surface.

Three levels of "null":
1. **`Coverage.NOT_SHIPPED`** — cell will exist after a future phase. UI shows "Voice coming soon" banner.
2. **`Coverage.NOT_APPLICABLE`** — cell will never exist. UI shows nothing; no banner.
3. **`Coverage.AUTHORING`** — cell is being worked on right now. UI shows "Voice in beta" banner; cues fire but flagged.

The matrix file (`policies/coverage_matrix.py`) holds the authoritative state.

## Authoring workflow for adding a new (title × page) combo

1. Identify the language profile and page profile.
2. The page profile already has its templates and required-language-keys list.
3. Verify the language profile supplies every required key. If gaps, add to the language profile.
4. Run `pytest backend/tests/voiceforge/coverage/test_<title>_<page>.py` — auto-generated test that renders every intent's template with synthetic payloads.
5. Manually listen to the rendered cues for tone, pacing, vocabulary correctness.
6. Mark the cell in `coverage_matrix.py` from `NOT_SHIPPED` to `AUTHORING`, then `SHIPPED` after QA.

Steady-state authoring cost per new cell: **0.5–1 day.** Most of the work is in the language profile (one-time) and the page profile (one-time).

## What this spec does not decide

- **What's in tier gating** — Doc #06.
- **What's in integrity mode gating** — Doc #07.
- **Priority numbers** — Doc #05.
- **TTS provider mechanics** — Doc #01.
