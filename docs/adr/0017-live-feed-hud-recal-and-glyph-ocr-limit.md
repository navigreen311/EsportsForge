# ADR 0017 — Live-Feed HUD Recalibration (v2.3.0-live) and the Broadcast-Bar Glyph-OCR Limit

- **Status:** Accepted
- **Date:** 2026-07-08
- **Reference:** [ADR 0013](0013-hud-calibration-recurring-maintenance.md) (HUD calibration is recurring maintenance — this is the first live-PS5-feed recal event), [ADR 0014](0014-ocr-overlay-over-cnn-for-formation-signals.md) (OCR-of-overlay formation read), [ADR 0015](0015-tiered-budget-and-sampled-ocr-cadence.md) (sampled-OCR cadence).
- **Supersedes calibration artifact:** `services/visionaudioforge/app/adapters/madden26/hud_regions.json` v2.2.0 → **v2.3.0-live**.
- **Scope:** Title-adapter only (Forge Rule 5) — `hud_regions.json`, `ocr_pipeline.py`, `context_detector.py`, `adapter.py` (cadence + payload nullability in `schemas/events.py` + `state_assembler.py`). Core dispatch/envelope/integrity unchanged.

## Context

v2.2.0 was calibrated on CPU-vs-CPU YouTube clips (center-clustered scorebug) and on a single saved play-call frame. Bringing up the **real PS5 HDMI feed** (`agents/capture` HdmiCaptureSource → VAF core) exposed that the live feed renders a **different, full-width broadcast bar** and a **two-sub-view play-call flow**, and that the single saved frame was unrepresentative. Every v2.2.0 region missed. Recalibration was done live, eyeball-in-the-loop, against 52 grabbed frames + a 5-minute continuous live drive (1779 frames, 7 FORMATION_LOCKED, 210 SNAPSHOT).

## Decision

**Recalibrate to v2.3.0-live and accept a documented glyph-level OCR limit as the v0.1 known-weak boundary.**

Changes (all validated live):

1. **Regions remeasured** for the broadcast bar; `down`+`distance` merged into one `down_distance` region; `field_position` **parked** (no analog on the bar).
2. **Wide-cluster read.** Tight per-element crops don't OCR on this bar (EasyOCR's detector needs width). The quarter/clock/play_clock/down/distance cluster is read as **one wide box** + positional parse split on the two ordinals, with HUD glyph subs (`2↔Z`, `1↔7`, `&↔8`).
3. **ContextDetector retuned** off the banner-luma rule (which false-negatived the live feed) to **`0.30 ≤ dark_frac ≤ 0.78 AND bar_mean ≥ 60`** — `bar_mean` (bottom-bar luma) rejects the pause menu that `dark_frac` alone can't. **0 FP / 0 FN across 54 labelled live frames** (both play-call sub-views, gameplay, pause, replay, corrupted).
4. **Formation read is subtitle-first (committed), no banner fallback for the name.** The play-call flow has two sub-views: the formation-select **banner** shows the *hovered* (browsed) formation; the play-select **subtitle** shows the *committed* one. Locking the banner produced a live wrong-lock (`Gun Empty Trey` while the user snapped `Pistol Wing Flex`). We lock only the committed subtitle.
5. **Formation cadence `every_n:9`** (was capped `on_play_call` burst of 5, which was spent during browsing and never reached the play-select subtitle).
6. **Null-degrade** (see `schemas/events.py`, `state_assembler.py`): `score/quarter/clock` nullable; the assembler **skips** a fully-blank read and **degrades** a partial one instead of fabricating `0`/`0:00`.

## What is PROVEN live

- **FORMATION_LOCKED fires with the correct COMMITTED formation** — 7/7 in `play_call`, **0 false-fires** during gameplay/replay/menus (user-confirmed the names: IForm Pro, Pistol Bunch ×3, Full House Normal Wide, Strong Pro, Singleback Trips).
- **SNAPSHOT carries correct down/distance/quarter** across a full drive.
- **Clock MINUTES validated against the user's TV** (`1:18`, `1:14`, and a `6:00→4:39` countdown). The `7→1` minutes bias is **safe**: it only fires when the real minute is `1` (which renders as `7`); real `0/4/5/6` minutes read correctly.
- **ContextDetector** separation holds across all live states.

## The known-weak boundary: broadcast-bar italic numerals defeat EasyOCR at the glyph level

Madden 26's large italic HUD numerals are not reliably resolvable by EasyOCR. **Three symptoms, one root cause:**

- **(a) Scores don't detect at all** → nulled (a known `7-7` frame reads `None/None`; other frames return spurious noise). The nullable payload keeps SNAPSHOT flowing.
- **(b) Clock SECONDS suffer an irreducible `1↔7` collision** (a real `:17` reads `:11`). Minutes are fine (validated); seconds are not, because real-`1` and real-`7` both OCR as `7`.
- **(c) Single-digit distance suffers the same** (`4th & 1` reads `& 7`). **Multi-digit** cases (`10`) are recoverable via the ">25 impossible" rule; **single-digit** are NOT.

## Followups (banked — do NOT patch with more glyph substitutions)

- **Dedicated digit-OCR pass for the bar's numerals** — a template-match or a small digit classifier trained on this HUD's italic glyphs. **One pass resolves all three symptoms** (scores, clock-seconds `1↔7`, single-digit distance `1↔7`). This is explicitly **not** a glyph-substitution tweak; substitutions cannot break the `1↔7` tie because the two glyphs are OCR-indistinguishable. Supersedes the ADR 0013 "score-OCR hardening" followup and widens it to all bar numerals.
- **OPEN / unverified:** occasional clock **sticking** (~20s held at `4:39` in the live run). May be the string-clock smoother's mode-vote lag **or** a genuinely stopped game clock (dead-ball / play-call). **Not diagnosed — do not assume it is a bug.**
- **Canonical-family map gaps:** `Pistol Bunch` maps to `shotgun_bunch` (keyword `BUNCH`) rather than a pistol family; several formations read a full name but `canonical=None` (not in the v0.1 top-8). Cosmetic for v0.1 (full name is correct); revisit with the v0.3 24-formation taxonomy.

## Consequences

- v2.3.0-live replaces v2.2.0 as the canonical Madden calibration for the live PS5 feed. The v2.2.0 CPU-clip calibration remains recoverable in git history.
- Tier-1 (events on the live feed) is **proven** to the v0.1 known-weak boundary: formation + down/distance/quarter + clock-minutes correct; scores + sub-digit precision banked to the digit-OCR pass.
- The methodology's "single saved frame overfits" lesson is now concrete: the diverse live capture reversed two wrong conclusions (subtitle-only → the banner exists; then banner-first → the subtitle is the *committed* source). Calibrate against a diverse live set, not one frame.
