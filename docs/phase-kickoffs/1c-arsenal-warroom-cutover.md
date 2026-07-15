# Phase 1c Kickoff — Arsenal + War Room Live-Vision Cutover

- **Status:** kickoff / scoped 2026-07-14. **Gate MET** — the ADR-0010 blocker (coverage
  stability) is cleared: held-out **macro-F1 = 0.92** across 3 games (PR #135,
  `docs/coverage-hardening-results.md`). Phase 1c is unblocked.
- **Shape:** the last feature-complete surface — bring Arsenal + War Room onto the live
  vision bus, the way Drill Lab (1a) / SimLab (1b) / Gameplan-highlight already are.
- **Related:** [ADR 0010](../adr/0010-phase-1c-gated-on-adapter-v0-3.md),
  [runbook 1a-drill-lab-flag](../runbooks/1a-drill-lab-flag.md) (the flag + live-run recipe
  Phase 1c reuses), `coverage-hardening-results.md`.

## Key finding — this is almost entirely FRONTEND

- **Backend needs no schema change.** `/arsenal/trigger` takes a free-form
  `game_state: dict[str, Any]` and passes it to the LLM — a detected coverage flows through
  as a `defensiveCoverage` field with zero backend work.
- **Everything downstream of a `COVERAGE_LOCKED` already exists to reuse:** `useVisionEvents`
  (subscription), the `useSimLabAutoRep`/`useDrillLabAutoRep` bridge pattern (event → action,
  deduped by `event_id`), `vafFlags` (per-surface env flags), the broker `sessions/start`,
  and Gameplan's highlight-banner seam.
- **What's missing:** arsenal/warroom flags; a coverage→game-state bridge hook; the War Room
  live banner; the Arsenal live-trigger wiring; and the ADR-0010 operational loose end
  (`ADAPTER_VERSION` still says `phase-0`).

## Decisions (locked)

- **Build order: War Room banner FIRST, then Arsenal triggers.** The banner is read-only and
  low-risk — it proves the coverage→UI loop end-to-end (the same reason Gameplan-highlight was
  the easy win) before the more involved Arsenal trigger UX.
- **Arsenal trigger model: event-driven + manual fallback.** A live `COVERAGE_LOCKED` feeds
  the coverage into `game_state` and fires the trigger immediately (responsive); the existing
  2-minute manual poll stays as the fallback when vision is off/absent.

## Work breakdown (each a shippable PR)

- **1c.0 — Foundation (~½ session).** `arsenalVisionEnabled()` / `warRoomVisionEnabled()` in
  `vafFlags.ts` + the backend master flags (mirror `VAF_DRILL_LAB_ENABLED`, broker 403 gate).
  Bump `ADAPTER_VERSION` off `madden26@0.0.1-phase-0` and record the 0.92 gate evidence in
  ADR-0010 / the runbook.
- **1c.1 — Coverage→game-state bridge (~1 session).** `useCoverageGameState` hook (analog of
  `useSimLabAutoRep`): subscribe `COVERAGE_LOCKED` via `useVisionEvents`, dedupe by
  `event_id`, expose the latest coverage (+ the payload's down/distance) and thread it into
  the Arsenal `gameStateStore` (`defensiveCoverage`) + expose for War Room. Tests mirror
  `useSimLabAutoRep.test.ts`.
- **1c.2 — War Room live banner (~1 session) [FIRST SURFACE].** A "Cover N detected →
  suggested adjustment" banner on the War Room page, gated by `warRoomVisionEnabled` + a
  broker session, driven by the 1c.1 bridge. Read-only display (mirror Gameplan-highlight
  banner + 30s timeout).
- **1c.3 — Arsenal live triggers (~1–2 sessions).** On live `COVERAGE_LOCKED`, set
  `defensiveCoverage` in `game_state` and fire `/arsenal/trigger` immediately (event-driven);
  keep the 2-min poll as fallback. Surface the returned weapon recommendation. Optionally tune
  the trigger LLM prompt to weight the coverage.
- **1c.4 — Live verification (live PS5 session).** Flip both flags, rebuild, drive a rep,
  confirm the War Room banner + Arsenal weapon-trigger light up on live coverage (the A1
  Drill Lab proof, repeated for these surfaces).

**Total ≈ 4–5 sessions**, dominated by frontend.

## Risk / caveat

- **Cross-matchup HUD limit (from #135):** the fixed-bbox SNAPSHOT HUD (down/distance/quarter)
  only reads on the calibrated matchup (KC/LV) — the PS5 bar is laid out by team-abbrev width.
  **Coverage — the core Phase-1c signal — is unaffected** (it reads on-field play-art, not the
  bar). So coverage-keyed banners/triggers work now; the *situational* refinement (down/
  distance) is degraded off-KC/LV until the dynamic-HUD follow-up. Don't block 1c on it — key
  the surfaces on coverage, treat situational fields as best-effort.
- **6/9 mirror confusion** (marginal, documented) rides along in `COVERAGE_LOCKED`; the banner
  should render the read as-is (the smoother already mode-votes per play).
