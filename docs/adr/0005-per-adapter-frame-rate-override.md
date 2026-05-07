# ADR 0005 — Per-Adapter Frame-Rate Override

- **Status:** Accepted
- **Date:** 2026-05-06
- **Reference:** [FORGE_ARCHITECTURE_PATTERN.md](../FORGE_ARCHITECTURE_PATTERN.md) — Rule 1 (multi-dimensional from day one — frame rate is sport-cadence-dependent), Rule 5 (adapters added without core changes — frame-rate override is part of an adapter's self-declared contract).
- **Modifies:** [specs/01-capture-agent.md §2 "Base cadence"](../specs/01-capture-agent.md), [specs/02-visionaudioforge-core.md §2 "Adapter contract"](../specs/02-visionaudioforge-core.md).

## Context

The capture agent spec (Spec #1) sets a default frame rate of **12 fps base / 24 fps adaptive max**. This rate is sized for football-style cadence (slow pre-snap, fast post-snap) and is reasonable for Madden 26, CFB 26, MLB 26, and PGA 2K25.

It is **not** the right default for fast-paced FPS / battle-royale titles. Warzone and Fortnite have continuous high-motion gameplay where a 12 fps base rate can miss kill confirmations, loot pickups, and zone-phase transitions that happen in <100 ms windows.

Hardcoding 12 fps as a global default that can't be lifted per adapter would force a future global bump (with all the cost of higher bandwidth for every title) when only a subset of titles need it.

## Decision

**Adopt 12 fps as the default base rate; expose a per-adapter override via the `TitleAdapter` contract.**

Each adapter declares its own frame-rate preferences:

```python
class TitleAdapter(Protocol):
    title: TitleEnum
    version: str
    max_processing_ms: int

    # New (this ADR):
    preferred_base_fps: int       # default 12
    preferred_max_fps: int        # default 24
    cadence_profile: CadenceProfile   # FOOTBALL | BASKETBALL | FPS | BR | COMBAT | GOLF | CARD
```

The capture agent receives the active title's preferred FPS as part of the `session_open` handshake from the core (the core looks it up from the matched adapter) and uses those values rather than its config defaults.

**Per-archetype recommendations (default values; adapters may override further):**

| Archetype | Base FPS | Max FPS | Rationale |
|---|---|---|---|
| Football (Madden 26, CFB 26) | 12 | 24 | Slow pre-snap, fast post-snap. The current default. |
| Basketball (NBA 2K26) | 15 | 30 | Continuous play; shot clock resets need quick capture. |
| Soccer (EA FC 26) | 12 | 24 | Continuous but slower-paced than basketball. |
| Baseball (MLB 26) | 8 | 15 | Mostly static between pitches. |
| FPS / Battle Royale (Warzone, Fortnite) | **20** | **30** | Continuous high-motion; kill events in <100 ms. |
| Combat sport (UFC 5, Undisputed) | 15 | 30 | Round-based; strikes happen in <200 ms. |
| Golf (PGA 2K25) | 4 | 12 | Pre-shot routine + slow swing. Bandwidth-friendly. |
| Card (Video Poker) | 2 | 6 | Static UI, deal/hold/redeal events only. |

## Consequences

- Capture-agent config (`config.toml`) keeps `target_fps` as a player-overridable field, but the **default** comes from the active adapter's declared preference. Server's `session_open` handshake carries the adapter-preferred values.
- Bandwidth varies by title — Warzone players use ~67% more bandwidth than Madden players. Acceptable.
- Adapter authors making FPS / BR / combat adapters in Phases 4 and 5 specifically choose their preferred FPS at adapter authoring time; no global retrofit needed.
- The cadence-profile enum becomes a useful signal elsewhere in the platform (VoiceForge already declares cadence rules per language profile — this aligns the two).

## Notes / followups

- Phase 1 (Madden 26) ships with `preferred_base_fps = 12` — current default. No change to capture-agent behaviour at v0.1.
- Phase 4 (Warzone, Fortnite) is the first time a non-default FPS lands. At that point the capture-agent code path that consumes `session_open.preferred_fps` gets exercised in production for the first time — include in Phase 4 testing matrix.
