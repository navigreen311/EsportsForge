# EsportsForge — Distance to Local Feature-Complete (Static Recon Map)

- **Date:** 2026-07-07
- **Status:** ✅ **SUPERSEDED — LOCAL FEATURE-COMPLETE ACHIEVED 2026-07-14** (see the update section directly below). The original 2026-07-07 map read: ⚠️ **STATIC MAP — not a live-verified state.** Every status below was derived by **reading code, tests, and committed validation JSONs — nothing was executed.** This is the current best map, to be **VERIFIED when Tier 1 is actually built**, not settled fact. Treat "done" claims as "done in code + tests," not "demonstrated running end-to-end."
- **Method:** 4 parallel read-only recon passes (docs/ADRs, VAF+capture, backend, frontend) + a git-state check, against trunk `main @ b3240a4` and the unmerged feature branches, on 2026-07-07.
- **Related:** [ADR 0010](../adr/0010-phase-1c-gated-on-adapter-v0-3.md) (v0.3 gate), ADR 0017 (COVERAGE_LOCKED contract — *on unmerged `feat/v0.3-coverage-contract`*), ADR 0018 (coverage classifier — *on unmerged `ai-feature/coverage-seedstab`*).

---

## ✅ 2026-07-14 UPDATE — LOCAL FEATURE-COMPLETE ACHIEVED (live-verified). Tag `v0.3.0-phase1c-complete`.

The static map below (2026-07-07) is **superseded**. Everything it scoped is now shipped to
`main` with green CI, and the spine has been **run live off the real PS5**, not just built.
Distance to local feature-complete: **done.**

**Tier 1 — the live v0.1 spine — DONE + LIVE-VERIFIED.** HDMI capture-card source built and
run live; `SNAPSHOT` + `FORMATION_LOCKED` proven end-to-end PS5 → capture → core → events →
**browser** (Drill Lab reps auto-completed off a live feed). Recipe banked in
`docs/runbooks/1a-drill-lab-flag.md`. The `.env.local`/port/DB gotchas from that first live
run are documented there.

**Tier 2 — all intended phases — DONE.**
- **Snap boundaries:** `PLAY_STARTED` / `PLAY_ENDED` wired from the M5b snap detector and
  fired **live** off the PS5.
- **v0.2 defensive front + v0.3 coverage:** shipped; `COVERAGE_LOCKED` live on the bus.
- **Coverage hardening — GATE CLEARED:** by-game validation across 3 new games (Jags/Chiefs,
  Chiefs/Ravens, Colts/Rams), **held-out macro-F1 = 0.92** (ADR-0010 ≥0.85). The reader
  generalizes by-game. See `docs/coverage-hardening-results.md`.
- **Phase 1c (Arsenal + War Room) cutover:** shipped (1c.0–1c.3). **War Room live-verified**
  — a real PS5 coverage rendered the "Cover 3 detected" banner in the browser. Arsenal rides
  the same live-proven `useCoverageGameState` bridge (event-driven trigger + manual fallback).
- Gameplan coverage-highlight, live scores (single-digit), VAF CI test gate: all shipped.

**Known limits (characterized, non-blocking, documented):**
- **Cover 6/9** are mirror coverages; the coach-cam L/R orientation flips with drive
  direction, so the side is marginally confusable (not OCR-fixable) — folded into the 0.92.
- **Cross-matchup SNAPSHOT HUD** (scores/clock/down/quarter) is matchup-calibrated (the PS5
  bar shifts with team-abbrev width) — coverage is unaffected; situational fields are
  best-effort off KC/LV. Dynamic-layout HUD is the tracked follow-up.
- **Play-clock CNN** on the grey game box: investigated, EasyOCR kept (honest negative — no
  independent GT showed the CNN beats it). See `tools/play_clock/game-box-retrain-findings.md`.
- The **capture-card dshow driver** locks up if the agent thrashes on a lost feed (USB
  re-plug to recover); the **Arsenal trigger surface** is competition-mode-only (its live
  log-confirmation was deferred, not a code gap).

**Out of scope (unchanged):** public / AWS / multi-user deployment; the ADR-0010 "7-day
production-stable" staging gate (a rollout gate, not a local prerequisite).

---

## Done definition (scope of this map — historical, 2026-07-07)

**Local feature-complete = PS5 → capture → vision → events → app surfaces them, working end-to-end for the owner's own local use, all intended phases wired.** **PUBLIC / AWS / multi-user DEPLOYMENT IS OUT OF SCOPE** (parked as separate future work). Split into two tiers:

- **Tier 1 — the live v0.1 spine off the PS5:** `SNAPSHOT` + `FORMATION_LOCKED` → Drill Lab / SimLab, live off a real PS5 feed.
- **Tier 2 — all intended phases:** adds play-boundaries, v0.2 pre-snap defensive front, v0.3 post-snap coverage → Gameplan highlight / Arsenal / War Room.

## Ground-truth git state (as of recon)

- **Trunk = `main @ b3240a4`** (local == origin). Phase 1a + Phase 1b merged.
- **Unmerged branches** (local == origin each; **none merged to main**): `feat/coverage-classifier-probe` `ce33860`, `ai-feature/coverage-resolution` `e4838dc`, `ai-feature/coverage-seedstab` `0df566e` (coverage model + ADR 0018), `feat/v0.3-coverage-contract` `3e9e31e` (ADR 0017), `feat/alembic-remediation` `43842fe` (DB migration infra).
- **On `main` the coverage feature is genuinely ABSENT** (not merely flag-gated): `detect_coverage()` returns `None`, nothing emits `COVERAGE_LOCKED`, and ADR 0017/0018 are not present.

## Phase / component status table

| Component / Phase | Status | What remains for local | Blocked vs buildable (in-scope?) | Effort |
|---|---|---|---|---|
| VAF core service (:8100) | done+working (file-driven) | — | none | — |
| Event bus / WS transport | done+working (E2E-proven from file) | — | none | — |
| Adapter v0.1 (OCR-of-overlay) | partial | emits `SNAPSHOT` + `FORMATION_LOCKED` only | none for v0.1 | — |
| Capture — file / test-video source | done+tested | — | none | — |
| **Capture — HDMI capture-card (the PS5 hop)** | **NOT STARTED** | build `cv2.CAP_DSHOW` source + device enum | **in-scope, real; hardware on hand** | **~1 session (low-conf)** |
| Frontend `useVisionEvents` hook | done+tested | — | none | — |
| Drill Lab (Phase 1a) | done behind flag | flip flag; confirm live browser render | in-scope config | hours |
| SimLab (Phase 1b) | done behind flag | flip flag; retire legacy poll path later | in-scope config | hours |
| WS-URL / flag config gap | gap | frontend discards broker `ws_url` & reads an unset env var; flags off | in-scope, easy | hours |
| PS5 HUD recalibration | pending (one-time) | recalibrate `hud_regions.json` for the PS5 1080p source | in-scope | hours–session |
| Null-HUD payload drop bug | tracked | schema fix (score/clock optional) | in-scope | hours |
| `field_position` OCR (71.4%, <80% bar) | partial | temporal median / digit tuning | in-scope, optional | ~session |
| Snap detector → `PLAY_STARTED`/`PLAY_ENDED` | stub | real PRE/POST-snap state machine | in-scope | session+ (tuning) |
| Adapter v0.2 (pre-snap defensive front) | not started | new CV detector (no OCR overlay to lean on) | in-scope, **feasibility-risky** | multi-session (large) |
| Adapter v0.3 (coverage → `COVERAGE_LOCKED`) | not started | wire banked model into `detect_coverage`, real-time frame/snap selection, emit, merge ADR 0017 | in-scope, **feasibility-risky** | multi-session (large) |
| Coverage classifier model | **done ~0.86 but UNMERGED + unwired** | merge arc; wire into adapter (row above) | none (model); wiring is v0.3 | merge ~hours |
| Gameplan coverage highlight | wired-but-inert (`deriveCoverageHighlight`→`null`) | implement highlight/banner once v0.3 emits | **adapter-gated (v0.3), NOT model-gated** | ~session |
| Arsenal + War Room live (Phase 1c) | not started | full cutover | adapter-gated (v0.3) | multi-session |
| Merge unmerged branches → main | pending | reconcile + merge 4 branches | in-scope | ~session |
| Phase 2 (Film Room) / Phase 3 (mock deletion) | not started | later tracks | arguably out of "spine" scope | large / hours |

## Work cost vs calendar cost

- **WORK COST — all of it.** There is no external dependency that isn't locally buildable; the whole remaining path is build effort.
- **CALENDAR COST — effectively zero for local "done."** The only wall-clock gate in the system is **ADR 0010's "adapter v0.3 production-stable for 7 days"** — that is a **public-rollout / Phase-1c stability gate (staging + production-stable for exposing features to others)**. It does **NOT** gate the owner's local use. Under this map's local-only definition it is out of scope.

## Critical path

- **The single most valuable buildable-now item is the HDMI capture-card source** — the *only* thing between "works on recorded clips" and "works live off the PS5." Everything downstream of a frame already works.
- **⚠️ Record correction:** Gameplan coverage-downstream is **ADAPTER-gated, NOT model-gated.** The coverage model clearing its ~0.86 bar did **not** unblock Gameplan: on trunk `detect_coverage()` returns `None`, nothing emits `COVERAGE_LOCKED`, and ADR 0017 is unmerged. Gameplan needs the **v0.3 adapter (real-time coverage inference → emission)** built first — itself a large, unstarted, feasibility-risky task. Gameplan is **not** the next move.
- **Order:** **(1)** HDMI capture source → **(2)** WS-URL/flag config + PS5 HUD recalibration → **(3)** live browser render + null-HUD fix = **Tier 1 live.** Then Tier 2: **(4)** snap detector → **(5)** merge coverage arc + v0.3 live-coverage wiring → **(6)** Gameplan highlight → **(7)** v0.2 defensive front → **(8)** Phase 1c (Arsenal + War Room).

## Bottom line

- **Tier 1 ≈ 2–3 build sessions**, dominated by the capture-card source + config/calibration. Nearest, highest-value "local done."
- **Tier 2 = many more sessions, OPEN-ENDED.** Do **not** false-precision it — it is unknowable until the two feasibility unknowns are attempted.
- **Two genuine feasibility unknowns that most move the estimate:**
  1. **HDMI capture-card effort** (low-confidence ~1 session) — hardware is on hand but the software source module is unbuilt and device/format handling is unpredictable. Gates Tier 1, so it resolves early.
  2. **v0.3 LIVE-coverage feasibility** — the ~0.86 model was trained on **curated fixtures / stills**; **real-time inference on live-captured frames (snap timing, deep-secondary region-crop, frame selection) is a different, unproven problem.** ADR 0017 flags system-level coverage feasibility as unproven. v0.2 (defensive front) carries the same "needs a real CV model, no OCR overlay" risk. Tier 2's total is not estimable until (1) and a v0.3 live probe are attempted.

## Integrity caveats

- **Nothing was executed** (static read). Statuses = code + tests + committed validation JSONs, not live runs.
- **"Live browser render" (Phase 1a criterion #2) is deferred/unproven** in the docs — only the wiring was confirmed, not a running-app render.
- **One recon conflict, resolved:** the backend pass inferred the frontend uses the broker's returned `ws_url`; the frontend pass (line-level cites) found it **discards** `ws_url` and reads an **unset** env var (`NEXT_PUBLIC_VAF_WS_URL`). The frontend finding is taken as authoritative → the "WS-URL gap" row (easy in-scope fix).
- **Coverage model + ADR 0017 + ADR 0018 are on UNMERGED branches;** on `main` the coverage feature is genuinely **absent**, not flag-gated.
- **Phase 0's `v0.1.0-phase0-complete` tag is unreconciled** with on-trunk docs (the honest completion doc lives on an unmerged `docs/*` branch; surviving on-main docs still say "5 of 8 criteria fail").
