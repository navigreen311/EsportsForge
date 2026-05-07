# ADR 0007 — Title Detection: Fallback Strategy + Madden/CFB Disambiguation

- **Status:** Accepted
- **Date:** 2026-05-06
- **Reference:** [FORGE_ARCHITECTURE_PATTERN.md](../FORGE_ARCHITECTURE_PATTERN.md) — Rule 5 (adapter routing depends on accurate title detection — graceful fallback prevents single-method failure).
- **Modifies:** [specs/02-visionaudioforge-core.md §1 "Title detection"](../specs/02-visionaudioforge-core.md).

## Context

Spec #2 chose template-matching against per-adapter `hud_signature.png` files via normalized cross-correlation, with a 0.85 confidence threshold to lock and a 30-second timeout to give up.

Two real-world risks weren't fully addressed:

1. **Single-method brittleness.** Template matching fails on low-quality captures (compressed feeds, off-axis camera, non-standard resolution scaling). One bad frame burst could exceed 30 seconds without lock.
2. **Madden 26 vs CFB 26 ambiguity.** Both are NFL-style football HUDs with similar layouts (down/distance bar, scoreboard top-left, formation overlay bottom-center). Normalized cross-correlation may report similar confidence scores for both, neither passing 0.85 cleanly.

## Decision

### 1. Fallback chain for title detection

**Primary:** Normalized cross-correlation against `hud_signature.png` per adapter (as Spec #2 specifies).

**Fallback after 5 frames without confidence ≥ 0.85:** Escalate to **ORB feature matching** (also already mentioned in the spec but as an alternative, not a fallback). ORB is more robust to lighting/scaling variation but slower.

**Final timeout:** 30 seconds (unchanged from Spec #2). If neither method locks, surface the error to the player.

### 2. Madden 26 vs CFB 26 disambiguation

When primary template matching scores both Madden and CFB above 0.7 but neither above 0.85 (or scores differ by less than 0.1), trigger a **team-abbreviation OCR tiebreaker:**

- Crop the team-abbreviation regions from `hud_regions.json` (both adapters include this region).
- Run Tesseract on both regions to extract abbreviations.
- Cross-reference against:
  - The 32-team **NFL abbreviation list** (`NE`, `KC`, `DAL`, etc.) — match → Madden 26.
  - The **CFB Top 130 abbreviation list** (`OSU`, `BAMA`, `MICH`, `UGA`, etc.) — match → CFB 26.
- The matched list determines the title; confidence is reported as the OCR confidence on the abbreviation region.

If neither abbreviation list matches (e.g., custom franchise team in Madden), default to the higher template-match score with a `disambiguation_uncertain` flag in the session log.

## Consequences

- Title-detection latency p95 increases slightly: median lock still <2 s, but the 5-frame fallback path takes ~5 s when it fires.
- Madden/CFB disambiguation logic lives in the core's title-detection module (not in either adapter — the adapters share no code).
- The team-abbreviation lists are version-controlled (`backend/app/services/integrations/visionaudio/data/nfl_abbrevs.json`, `cfb_abbrevs.json`) and updated when rosters change.
- Custom-franchise edge case is handled gracefully (defaults to template-match winner), not as a hard error.

## Notes / followups

- Track `disambiguation_uncertain` rate during Phase 0 / 1a. If >5% of Madden/CFB sessions hit it, the disambiguation logic needs improvement (e.g., stadium signature analysis).
- ORB feature matching benchmark on Phase 0 capture-card output to validate the 5-frame fallback latency assumption.
- When new football titles join (none currently planned), they'll need to participate in the same disambiguation map.
