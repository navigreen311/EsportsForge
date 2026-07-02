# Phase 1a Kickoff — State Report & Phase 0 Reconciliation

- **Phase:** 1a (Drill Lab cutover) — orientation / reconciliation only
- **Date:** 2026-07-02
- **Author:** Claude (state verification + reconciliation session)
- **Status:** Founder signed off on the reconciliation 2026-07-02; three scope resolutions folded in (see below). **Awaiting push authorization.** No implementation begins until push auth.
- **Scope of this session:** state verification + plan reconciliation only. No application code touched. No existing docs modified.

> **Founder sign-off (2026-07-02) — three scope resolutions folded in:**
> 1. **Playback pipeline IN SCOPE (Item 1).** YouTube-file → capture agent → VAF core playback path is a Phase 1a deliverable, not deferred. +2–3 days, accepted. Grounded against code (§7.1): it's an extension of the existing `TestVideoSource`, not a new build. → §7.1, §8 sequence.
> 2. **Event display only, NOT a coaching engine (Item 2).** Drill Lab renders `FORMATION_LOCKED` + related events as they fire; it does not analyze them. Coaching engine (frequency / distribution / tendency analysis) → **Phase 1b backlog** (§5.5). → §5.7 acceptance reframed to event-display.
> 3. **Day 0–5 sequence drafted (Item 3).** The eight prerequisite work items are sequenced in **§8**; founder reviews after.
>
> **Prior defaults now settled by sign-off:** the "8 prerequisites" framing is accepted (enumerated + reconciled in §8). Remaining ⚠️ items in §9 (integrity-mode label, flag names, cadence mapping, branch-merge decision) are carried as review questions — they do not block this report.

---

## 1 · State verification results

### 1.1 Verification matrix (against `main` @ `20230d7`)

| Item | Expected | Result |
|---|---|---|
| 1a — on `main`; HEAD `20230d7` w/ Phase 0 squash-merge message | yes | ✅ **PASS** (after a fast-forward pull — see 1.3) |
| 1b — tag `v0.1.0-phase0-complete` → `20230d7` | yes | ✅ **PASS** (annotated tag `804678a` → `20230d7`) |
| 1c — 15 ADRs `0001`–`0015` present as `.md` in `docs/adr/` | yes | ✅ **PASS** (+ `README.md`) |
| 1d — `docs/phase-completions/0-vaf-foundation.md` exists | yes | ❌ **FAIL on main** — exists only on unmerged branch (see 1.2) |
| 1e — `docs/phase-kickoffs/1a-drill-lab-cutover.md` exists | yes | ❌ **FAIL on main** — exists only on unmerged branch (see 1.2) |

`docs/phase-completions/` on main contains: `0-real-footage-validation.md`, `0-vaf-m5c-plan.md`, `0-vaf-remaining-milestones.md`.
`docs/phase-kickoffs/` on main contains: `1a-drill-lab-cutover-addendum.md`, `phase-1-revised-timeline.md`.

### 1.2 Root cause of 1d / 1e: two docs were authored but never merged

Both missing files exist on branch **`origin/docs/phase-0-completion` @ `eda61a3`** ("docs: Phase 0 completion + Phase 1a kickoff brief", 2026-05-07):

- `docs/phase-kickoffs/1a-drill-lab-cutover.md` (202 lines) — **the authoritative Phase 1a brief**
- `docs/phase-completions/0-vaf-foundation.md` (187 lines) — **the Phase 0 completion doc**

That branch diverged from main (1 commit each side) and was **never merged**. The Phase 0 squash (`20230d7`) absorbed the *addendum* and *revised timeline* but not this branch. That is why every surviving doc references these two files as **dead links**. This report sources the brief and completion doc **read-only** from that branch.

### 1.3 Local-clone note

At session start the local clone was stale at `eab26e7` (2026-05-02), 0 ahead / 146 behind `origin/main`. A clean `git pull --ff-only` advanced it to `20230d7`; the tag came with `git fetch --tags`. No divergence, nothing lost.

### 1.4 Documentation-vs-tag inconsistency (surfaced, not blocking)

`main` is **tagged `phase0-complete`**, but its surviving docs contradict that:
- `1a-drill-lab-cutover-addendum.md` is titled **"Superseded"** and says it will be deleted "once the Phase 0 sign-off lands."
- `0-vaf-remaining-milestones.md`: **"Plan, not yet started"** — lists M4.5 / M5c / OCR-cadence-reform as work to close 5 failing acceptance criteria.
- `phase-1-revised-timeline.md`: **"Phase 0 is not yet complete — 5 of 8 acceptance criteria fail."**
- The honest completion doc (`0-vaf-foundation.md`) that would resolve this **is on the unmerged branch, not on main.**

**Phase 0 is tagged complete; its documentation on main is not reconciled.** This is a Day-0 cleanup item (§7), not a blocker for this report.

---

## 2 · Phase 1a brief summary

Sourced from `1a-drill-lab-cutover.md` @ `eda61a3`. Drill Lab is first because it needs only one event type (`FORMATION_LOCKED`), is the most-mocked page today, and has the most visible regression signal (rep counter not advancing).

### 2.1 Prerequisite approvals — brief lists **6** (session brief said 8; resolved to 8 in §8, see §9)

1. **Phase 0 PR #62 merged to `main`.**
2. **Webhook failure-rate alarm wired** to CloudWatch (Phase 0 lesson L2); operator confirms it fires test-mode at >0.1% synthetic failure.
3. **Staff cohort identified** — 5 user_ids populated in `STAFF_COHORT_USER_IDS`.
4. **Trusted-player cohort identified** — 5 user_ids in `TRUSTED_PLAYERS_COHORT_USER_IDS`; players consented via opt-in form.
5. **Resource allocation** — 1 backend eng + 1 frontend eng for the 5-day build; 1 operator on call for the 7-day observation.
6. **Ops runbook entry** for flipping `VAF_REAL_PIPELINE_ENABLED_DRILL_LAB` published.

### 2.2 Calendar — 5-day build + 7-day observation (~2 weeks)

| Day | Work |
|---|---|
| Day 1 | Events WS endpoint in VAF core (`app/api/events.py` + dispatcher fan-out) |
| Day 2 | `useVisionEvents` hook (`frontend/src/hooks/useVisionEvents.ts`) + unit tests |
| Day 3 | Drill Lab page rewire behind feature flag (`drills/page.tsx`) |
| Day 4 | Settings → Game Settings flag exposure (ADR 0001) + ops runbook entry |
| Day 5 | End-to-end manual test on staging with the synthetic fixture |
| Day 6 | Staff-cohort flag flip + observation kickoff |
| Day 7–13 | 7-day observation window (Day 9 adds trusted players; Day 13 = promotion decision) |

### 2.3 Staff cohort composition & selection criteria

- **Founding-team cohort (Day 6 flip):** 5 hand-picked users who can drop everything to triage. Ivan Green primary + 4 TBD.
- **Trusted-player cohort (Day 9 flip):** 5 non-founding users selected on: ≥20 drill reps in last 30 days; ≥1 in-app feedback report submitted; subscription tier ≥ Competitive; ≥3 of 5 play Madden 26 (1–2 non-Madden intentional, to surface unsupported-title edge cases). Recruited via an in-app "Phase 1a beta" opt-in form posted Day 1.

### 2.4 Two-stage feature-flag pattern

Brief attributes this to **ADR 0001**; the canonical ADR is now **0012 (two-stage-flag-pattern)** — see reconciliation §4f.

- **Master kill-switch** — brief: `VAF_REAL_PIPELINE_ENABLED_DRILL_LAB` (stays `true` once enabled; drops everyone to mock instantly).
- **Widening flag** — brief: `VAF_DRILL_LAB_PROMOTED_TO_ALL` (default `false`; flip `true` on Day 13+ if acceptance passes).
- Per-cohort targeting via a hardcoded backend allowlist (`STAFF_COHORT_USER_IDS`, `TRUSTED_PLAYERS_COHORT_USER_IDS`) evaluated in `vaf_pipeline_enabled_for(user_id)`, gated behind the master kill-switch.

### 2.5 Rollback wires (per ADR 0003 + Spec #03 §4)

Configured in CloudWatch before Day 6:

| Wire | Threshold | Action |
|---|---|---|
| VAF webhook failure rate | >0.1% sustained / 60 min | Trigger **Phase 1c-blocking flag** (block 1c until Redis Streams ships). Does **not** auto-flip Drill Lab. |
| Drill Lab page error rate | >2× mocked baseline / 5 min | **Auto-flip master flag → `false`** |
| End-to-end latency p99 | >5 s sustained / 5 min | Manual investigation (no auto-flip) |
| WS connection failure rate | >5% / 5 min | **Auto-flip master flag → `false`** |
| User "broken" reports | >3 critical / 24 h | Manual investigation |

Manual path: flip master flag in `settings.json`, restart backend task (~30 s). Hook reverts to legacy REST polling on next 60 s poll. Rep counter is server-side, so drill state is preserved. Mock stays in tree until Phase 3 (ADR 0004) — rollback always available.

### 2.6 10-criterion acceptance checklist (promote to all Competitive+)

Day-13 meeting goes "yes" only if **all 10** pass; any "no" → fix root cause, restart 7-day clock.

1. Webhook delivery rate ≥ 99.9% over the 7-day window.
2. `FORMATION_LOCKED` delivery to page hook ≥ 99% of expected (one per drill rep).
3. Drill Lab page error-rate increase ≤ 10% vs mocked baseline.
4. End-to-end latency p95 ≤ 2 s sustained.
5. WS connection failure rate ≤ 1%.
6. Zero critical user-feedback reports in the cohort.
7. No auto-rollback fired during the window.
8. Webhook failure-rate alarm did NOT fire (ADR 0003).
9. Manual UX validation by 3 of 10 cohort users ("rep counter feels normal, no perceptible delay").
10. Mock REST endpoint received zero hits from the staff cohort during the window.

Pass all 10 → flip widening flag. 1–2 fail → fix, restart clock. 3+ fail → structural issue; pause 1a, possibly delay 1b.

---

## 3 · Q1 answer — Integrity Mode default

**Practice / Ranked Integrity Mode default for solo validation.** (Confirmed by founder.)

Phase 0 verified frame-level integrity gating (Tournament → frames dropped with `integrity_tournament_blocks_capture`). For solo validation against recorded clips, the Practice/Ranked policy is the correct default — it exercises the full processing path (FORMATION emission enabled) without the Tournament `no_processing` gate. The Madden adapter's declared policy (Tournament = no_processing, Ranked disables `FORMATION_LOCKED`, Broadcast = opponent_data_redacted) means **Ranked would suppress `FORMATION_LOCKED`** — so validation runs must use a mode where FORMATION is emitted (Practice / offline-lab), not Ranked, when testing the Drill Lab formation path specifically. ⚠️ Confirm intended mode label maps to "FORMATION emitted" (§9).

---

## 4 · Reconciliation against Phase 0 reality (items a–f)

**Framing:** The `docs/phase-0-completion` branch (brief + completion doc) is dated **2026-05-07** and references only **ADRs 0001–0010**. Tagged `main` (07-02) carries **ADRs 0011–0015**. The branch is a **mid-Phase-0 snapshot**; ADRs 0011–0015 landed *after* it and overturned several of its assumptions. The reconciliation below applies to both the brief **and** the branch's completion doc.

### 4a · Formation detection: CNN → OCR-of-overlay (ADR 0014)

- **Stale assumption (branch completion doc + `0-vaf-m5c-plan.md` + `0-vaf-remaining-milestones.md`):** formation detector is a stub (`shotgun_trips`/0.5); real detection = **M5c MobileNetV3-Small ONNX classifier**, macro-F1 ≥ 0.85, ~40k labeled frames, Colab training, `formation_v0_1.onnx` (~7 MB via Git LFS), inference p95 ≤ 20 ms.
- **Shipped reality (ADR 0014 + founder):** **OCR-of-overlay** — read the formation name off Madden's play-call overlay. 100% on the canonical 8; emits formation name + canonical family; a **state detector** governs play-call-screen visibility. No CNN, no ONNX model file, no macro-F1 gate, no classifier confidence threshold.
- **Impact on the brief:** **None on the frontend/cutover surface.** The brief's Drill Lab path only *consumes* `FORMATION_LOCKED`; it never assumes CNN. The CNN assumptions live only in the superseded planning docs. **Action:** drop all references to macro-F1 gates, ONNX model files, classifier confidence thresholds, and CNN inference latency from any live Phase 1a planning; treat M5c as superseded by ADR 0014.

### 4b · Per-frame budget: flat 80ms → tiered (ADR 0015)

- **Stale assumption (brief-era, `remaining-milestones` + `revised-timeline`):** ADR 0006 flat **80 ms per-frame budget "not revised"** (stated 3×); OCR must fit under 80 ms via snap-triggered cadence.
- **Shipped reality (ADR 0015):** **tiered budget** — hot path 80 ms, **OCR-tier 500 ms**. The flat-80ms stance is superseded.
- **Impact on the brief:** **No conflict.** The brief's latency wire is **end-to-end** (capture → render) p95 ≤ 2 s, not per-frame. An OCR-tier formation event (≤ 500 ms in-adapter) sits comfortably inside a 2 s e2e budget. **Action:** where any live plan references "flat 80 ms," update to the ADR 0015 tiered model; note that formation events propagate on the OCR tier, not the hot path.

### 4c · Event emission rate: per-frame → sampled cadence (ADR 0015) — ⚠️ REAL RECONCILIATION ITEM

- **Stale assumption:** Phase 0 stub emitted a SNAPSHOT every frame (32 events in a 6 s smoke). Brief acceptance criterion #2 and its monitoring assume **"one `FORMATION_LOCKED` per drill rep."**
- **Shipped reality (ADR 0015 + founder):** **sampled cadence** — formation fires **once per play-call screen**; other fields fire on their own cadence.
- **Impact on the brief — this is the one that touches consumer logic:** The Drill Lab rep counter must map **"play-call screen" → "rep"**, not "frame" → "rep" and not "N frames" → "rep." Acceptance criterion #2 ("≥ 99% of expected, one per rep") must be reframed as **"one `FORMATION_LOCKED` per play-call screen, and each play-call screen corresponds to a rep."** **Action:** the `useVisionEvents` consumer and rep-count logic must be written against the sampled, once-per-play-call-screen cadence; validate the play-call-screen → rep mapping explicitly against the YouTube corpus (§5).

### 4d · Prerequisites already satisfied by Phase 0

- **Approval #1 (PR #62 merged to `main`) — ✅ SATISFIED.** Squash-merged and tagged `v0.1.0-phase0-complete` @ `20230d7` (2026-07-02).
- **Phase 0 event/webhook transport — ✅ SATISFIED** (verified in the completion doc smoke: 32 valid `EventEnvelope` events, `failure_rate` 0.0). The consumer surface the brief builds on exists.

### 4e · Prerequisites NOT yet addressed (become first Day-0/Day-1 work)

- **Approval #2 (webhook failure-rate alarm → CloudWatch, Phase 0 lesson L2) — OPEN.** `WebhookPublisher.failure_rate` is exposed as a property but **not wired to any alarm**. Completion doc L2 says 1a acceptance should not start until the alarm (or an operator-checked dashboard) exists.
- **Approval #6 (ops runbook entry) — OPEN.**
- **Feature flag provisioning (ADR 0001 / brief Day 4) — OPEN** (flags not yet in `backend/app/core/settings.py`).
- **Events WS subscriber surface — OPEN.** Phase 0 shipped only the webhook publisher; `app/api/events.py` (`/ws/events/{session_id}`) + dispatcher fan-out is Day-1 build work per the brief.
- **Under the solo reframe (§5):** Approvals **#3/#4** (staff + trusted-player cohorts) collapse to `allowlist=[founder user_id only]`; **#5** (2 engineers + operator) collapses to solo.

### 4f · Other stale-but-not-covered assumptions

- **Two-stage flag ADR attribution:** brief cites **ADR 0001**; canonical is **ADR 0012 (two-stage-flag-pattern)**. Use 0012.
- **Flag names:** brief uses `VAF_REAL_PIPELINE_ENABLED_DRILL_LAB` + `VAF_DRILL_LAB_PROMOTED_TO_ALL`; founder final names are `VAF_DRILL_LAB_ENABLED_MASTER` + `VAF_DRILL_LAB_COHORT` (§5). ⚠️ Confirm canonical names (§9).
- **HUD calibration is now recurring maintenance (ADR 0013)** — not a one-off; relevant if YouTube clips use varied resolutions/overlays (§5 capture-variance category directly stresses this).
- **Dev backend port (ADR 0011):** the `:8001` zombie-listener (completion doc D2) is resolved by ADR 0011 — dev backend port correction. Relevant to the solo local-run loop.
- **Completion doc's own stale sections:** its "formation = stub / M5c CNN / macro-F1" narrative (test-results + L4 + L6) is superseded by ADR 0014; its latency/D4 framing by ADR 0015. If the branch is ever merged, the completion doc needs the same 4a/4b/4c edits before it can stand as an honest "Phase 0 complete" record.

**No re-architecting required.** The brief's cutover design is compatible with shipped Phase 0. The only consumer-logic change is 4c (cadence). Halt condition #3 does **not** trigger.

---

## 5 · Solo-founder reframe — curated YouTube corpus in lieu of cohort (Q2 final)

**Constraint:** solo founder; no cohort available for recruitment. **Reframe:** Phase 1a becomes **solo technical validation** using a curated YouTube Madden 26 clip corpus as the diverse-input corpus.

### 5.1 Rationale — why YouTube corpus > solo online play

A 5-person cohort on live play produces limited input variance bounded by those 5 players' hardware, teams, and styles. **12–15 curated YouTube clips deliver cross-player variance at scale** — different players, streamers, teams, game modes, capture conditions, and resolutions — faster and more broadly than solo online play could. This is a **stronger technical validation** of the pipeline's robustness (OCR, state detection, cadence) than the original cohort plan, given the constraint. It is **not** a downgrade; it trades *user-experience* validation (deferred, see 5.5) for *superior input-diversity* technical validation.

### 5.2 Corpus target — 12–15 clips, each 3–5 min

- **Baseline gameplay diversity (5–6):** CPU vs CPU, Play Now, Franchise, MUT, Head-to-Head, Superstar.
- **Team-color / OCR stress (3–4):** Ravens, Bengals, other historically hard-OCR teams.
- **Capture-condition variance (3–4):** streamer overlays, 4K downscaled, compressed re-uploads, phone-of-TV recordings. *(Directly stresses ADR 0013 HUD calibration + OCR robustness.)*
- **Edge cases (2–3):** 2-minute drills, red zone, blowouts.

Filename convention: `madden26_yt_<category>_<descriptor>.mp4`. Dropped in `agents/capture/fixtures/real/` (already gitignored per `agents/capture/fixtures/real/*.mp4`). **Not committed** — local fixtures, like the original captures.

### 5.3 Procurement note

Manual downloads, **one clip at a time, with pauses between**. Prior YouTube rate-limit incidents make batch/parallel `yt-dlp` risky. (The existing `0-real-footage-validation.md` reproduction command via `yt-dlp` is the template for a single clip.)

### 5.4 Revised observation model

**Not** multi-user, **not** 7-day observation-with-users. Instead: **7–10 days of intensive solo testing** running Drill Lab against the 12–15 clips. Per-clip logging: did events fire correctly, did the UI render, edge cases surfaced. Founder evaluates whether coaching output feels useful for each gameplay style.

### 5.5 Deferred backlog items

- **Phase 1a.5 / 1b — "recruit real user cohort for user-experience validation."** The UX side of Drill Lab (perceived latency, coaching usefulness with real users, feedback-channel loop) is **not** validated in Phase 1a. It moves to Phase 1a.5 (or folds into Phase 1b) once a cohort exists. Phase 1a validates the *pipeline*; a later phase validates the *experience with users*.
- **Phase 1b — "coaching engine: consume event stream, produce coaching insights."** Per founder Item 2: Phase 1a is **event display only**. The coaching engine — which consumes the `FORMATION_LOCKED`/event stream and produces analysis (formation **frequency**, **distribution**, **tendency** analysis, and derived coaching insight) — is explicitly **Phase 1b** work. It is **not built in Phase 1a**; keeping 1a to event-display keeps it focused on pipeline validation.

### 5.6 Two-stage flag under the reframe (per ADR 0012)

- `VAF_DRILL_LAB_ENABLED_MASTER` — master kill-switch. (⚠️ maps to brief's `VAF_REAL_PIPELINE_ENABLED_DRILL_LAB`.)
- `VAF_DRILL_LAB_COHORT` — widening flag, **`allowlist=[founder user_id only]` for all of Phase 1a; the widening path is not exercised.** (⚠️ maps to brief's `VAF_DRILL_LAB_PROMOTED_TO_ALL`.)

### 5.7 Revised acceptance criteria (adapted from the brief's 10)

**Scope guard (founder Item 2): acceptance is measured on *event display*, not coaching analysis.** "Correct events" below means the right `FORMATION_LOCKED`/related events reach and render on the page at the right time — **not** that any frequency/distribution/tendency insight is produced. The coaching engine is Phase 1b (§5.5).

1. Pipeline processes all 12–15 YouTube clips end-to-end **without crashes or hangs**.
2. Drill Lab **displays the correct events** for each clip — the right `FORMATION_LOCKED`/related events, rendered at the right time (event display; no coaching analysis expected in 1a).
3. **Zero false-positive `FORMATION_LOCKED`** on live-gameplay segments (state detector validated across diverse inputs).
4. Capture pipeline **sustains 30 fps equivalent** processing YouTube-sourced files (validates the **file-input path**, not just live capture).
5. Feature-flag **master kill-switch verified functional**.
6. Widening flag **stays at `allowlist=[founder only]`**; not exercised for widening.
7. **Rollback wires (ADR 0003) drill-verified** before session ends.
8. All events during solo validation are **auditable in the webhook-receiver logs**.
9. **No regressions** against Phase 0 acceptance criteria (see completion-doc "What was actually verified": adapter dispatch, integrity gate, envelope shape, webhook batching, backend receipt, ADR 0009 platform-neutrality).
10. Honest **per-clip subjective evaluation** of whether Drill Lab coaching feels useful across the diverse corpus (tracked per-clip).

---

## 6 · What this reframe changes vs the original brief (delta table)

| Dimension | Original brief | Solo reframe |
|---|---|---|
| Validation input | Live play by 10 cohort users | 12–15 curated YouTube clips (file input) |
| Cohorts | Founding (5) + trusted players (5) | `allowlist=[founder only]` |
| Observation | 7 days, user-facing, dashboards | 7–10 days intensive solo, per-clip log |
| Widening | Day 13 → all Competitive+ | Not exercised in 1a |
| Acceptance | 10 criteria (delivery %, page error, UX sign-offs) | 10 adapted (crash-free, correct events, zero false-positive FORMATION, 30fps file path, flag/rollback drills, per-clip usefulness) |
| Primary risk validated | UX + delivery at cohort scale | Pipeline robustness across input diversity |
| Deferred | — | UX-with-users → Phase 1a.5 / 1b |

---

## 7 · Proposed prerequisite work items — ordered for Day 0 / Day 1

**Day 0 (prerequisites / cleanup — must precede Day 1 build):**

1. **Doc reconciliation (from §1.4):** decide the fate of the unmerged `docs/phase-0-completion` branch (merge with 4a/4b/4c edits, or supersede). Remove/retire the "Superseded" addendum and the stale `remaining-milestones` / `revised-timeline` Phase-0-not-complete language so main's docs match the `phase0-complete` tag. ⚠️ (§9, Q-branch).
2. **Webhook failure-rate alarm (Approval #2 / L2):** wire `WebhookPublisher.failure_rate` to CloudWatch (or an operator-checked dashboard). Hard gate per completion-doc L2.
3. **Feature flags (ADR 0001 + 0012):** provision `VAF_DRILL_LAB_ENABLED_MASTER` + `VAF_DRILL_LAB_COHORT` in `backend/app/core/settings.py`; add `vaf_pipeline_enabled_for(user_id)` with `allowlist=[founder only]`. Add the ADR 0012 unit test (hash-stable assignment + kill-switch precedence).
4. **Ops runbook entry (Approval #6):** how to flip the master flag + rollback (~30 s path).
5. **Corpus procurement (§5.2/5.3):** download 12–15 clips one-at-a-time with pauses into `agents/capture/fixtures/real/`.

**Day 1+ (build sequence, brief §Build sequence, reconciled):**

6. Events WS endpoint `services/visionaudioforge/app/api/events.py` (`/ws/events/{session_id}`) + dispatcher fan-out. *(Phase 0 shipped only the webhook publisher.)*
7. `useVisionEvents` hook + unit tests — **written against the ADR 0015 sampled, once-per-play-call-screen cadence (§4c)**, not per-frame.
8. Drill Lab page rewire behind `VAF_DRILL_LAB_ENABLED_MASTER`; **rep counter maps play-call-screen → rep (§4c).**
9. Settings flag exposure (ADR 0001).
10. End-to-end validation against the YouTube corpus (file-input path); rollback-wire drill; per-clip log.

### 7.1 File-mode capture agent ingestion — NOW IN SCOPE (founder Item 1)

**Resolution:** the YouTube-file → capture agent → VAF core playback path is a **Phase 1a deliverable, not deferred.** Rationale (founder): Phase 1a must validate the *production* pipeline end-to-end, and real users need file-mode ingestion for replay review regardless. Accepted growth: **+2–3 days**.

**Grounded against code — this is an extension, not a new build (~2–3 days is realistic):**

- The path **already exists in skeleton.** `agents/capture/capture_agent/capture/test_video.py::TestVideoSource` opens an arbitrary MP4 via `cv2.VideoCapture`, yields `Frame`s, and the Phase 0 transport (`ws_client.py`) streams them to VAF core — the exact path that produced the Phase 0 smoke (32 valid events). The `CaptureSource` protocol (`capture/base.py`) is explicitly **"open per ADR — add a source = new module + registry entry, no agent-core changes."**
- **What the ~2–3 days actually covers (deltas from `TestVideoSource`):**
  1. **Play-once + EOF/completion signal.** Today the source *loops forever* (`cap.set(POS_FRAMES, 0); continue`). Per-clip validation needs play-through-once + a "clip complete" signal to tally per-clip results.
  2. **Configurable playback rate.** Add a max-speed / target-fps mode to satisfy acceptance criterion #4 ("30 fps-equivalent throughput on file input").
  3. **1080p resolution normalization before HUD crop.** HUD regions are calibrated at 1080p (ADR 0013); the capture-variance corpus (4K-downscaled, phone-of-TV) must be normalized to 1080p or OCR misses. Bounded (a downscale step).
  4. **Promote to a first-class source** (not labeled "test-video") selectable via agent config.
- **Two bounded watch-items (fit inside 2–3 days, flagged for awareness):**
  - **AV1 codec:** YouTube clips are frequently AV1 (the existing `0-real-footage-validation.md` clip was AV1); some OpenCV/FFmpeg builds can't decode AV1. **Mitigation:** download as H.264 mp4 at procurement time (the `yt-dlp` format string in the validation doc already constrains to mp4) — solved at Day-0, no code cost.
  - **Resolution variance** interacts with HUD calibration (delta 3 above) — in scope precisely because the founder wants capture-condition variance tested.

**No halt:** none of the above pushes the playback scope past the accepted 2–3 days.

---

## 8 · Proposed Phase 1a Day 0–5 Sequence (founder Item 3)

**The eight prerequisite work items** (reconciled for solo + playback-in-scope; lineage in the table). Founder reviews the sequence after this commit.

| # | Prerequisite work item | Lineage |
|---|---|---|
| P1 | Doc reconciliation — resolve unmerged `docs/phase-0-completion` + retire stale "Phase-0-not-complete" docs so main matches the `phase0-complete` tag (§1.4) | housekeeping / §9 Q-branch |
| P2 | Webhook failure-rate alarm → CloudWatch (or operator dashboard) | brief approval #2 / completion-doc L2 |
| P3 | Feature flags provisioned — `VAF_DRILL_LAB_ENABLED_MASTER` + `VAF_DRILL_LAB_COHORT` (`allowlist=[founder]`) + `vaf_pipeline_enabled_for()` + ADR 0012 unit test | brief approval (ADR 0001→0012) |
| P4 | Ops runbook entry — flip + rollback (~30 s path) | brief approval #6 |
| P5 | YouTube corpus procured & staged in `agents/capture/fixtures/real/` (12–15 clips, one-at-a-time, H.264 mp4) | solo-derived §5.2/5.3 |
| P6 | Solo Integrity-Mode default confirmed (FORMATION-emitting mode) | solo-derived §3 |
| P7 | **File-mode capture agent ingestion path** (extend `TestVideoSource`; §7.1) | founder Item 1 — NEW |
| P8 | Events WS subscriber surface — `app/api/events.py` (`/ws/events/{session_id}`) + dispatcher fan-out | brief Day 1 build |

> Brief approvals **#1** (PR #62 merged) is **already satisfied** (§4d); **#3/#4** (cohorts) collapse to `allowlist=[founder]` (folded into P3); **#5** (2 eng + operator) collapses to solo.

**Sequenced plan** (solo, single critical path):

| Day | Work | Prereqs advanced |
|---|---|---|
| **Day 0** | Prep & unblock (no page build). Resolve doc/branch state; start alarm wiring; scaffold flags + `vaf_pipeline_enabled_for`; confirm Integrity-Mode default; **begin corpus downloads** (runs in background across Days 0–4, one-at-a-time with pauses). | P1, P2 (start), P3 (scaffold), P5 (start), P6 |
| **Day 1** | **Event transport foundation.** Build `app/api/events.py` (`/ws/events/{session_id}`) + dispatcher fan-out to per-session subscriber queue + unit test. (Hook depends on this.) | P8 |
| **Day 2–3** | **File-mode ingestion (the +2–3 day item).** `FilePlaybackSource` extending `TestVideoSource`: play-once + EOF signal, configurable rate, 1080p normalization, first-class source config. Validate YouTube-file → agent → core → events. | P7 |
| **Day 3–4** | **Consumer.** `useVisionEvents` hook written against the ADR 0015 sampled once-per-play-call-screen cadence (§4c) + tests. Finalize flags + ADR 0012 unit test. | P3 (finish) |
| **Day 4–5** | **Page + ops.** Drill Lab page rewire behind master flag — **event display only** (Item 2); rep counter maps play-call-screen→rep. Finalize alarm (verify test-mode fires >0.1%) + runbook. | P2 (finish), P4 |
| **Day 5 → realistically Day 7–8** | **Validation.** End-to-end across the 12–15 clip corpus via the file-mode path; rollback-wire drill (ADR 0003); per-clip log; check revised acceptance criteria §5.7 (1–10). | — |

**Honest calendar note (not a halt — growth already accepted):** with P7 adding 2–3 days, the *validation* step realistically lands **Day 7–8**, not Day 5. The "Day 0–5" frame holds for the build-enabling + page work; validation tails past Day 5 by the accepted playback growth. No trade-off requiring a founder decision — the sequence is a straight critical path for one person.

---

## 9 · Open questions for founder (before Day 1)

- ✅ **RESOLVED by sign-off — Approvals count.** The **8**-prerequisite framing is accepted; the eight are enumerated + reconciled in §8 (brief's 6 approvals adapted for solo + 2 solo-derived, with #1 satisfied and #3/#4/#5 collapsed).
- ✅ **RESOLVED by sign-off — Playback scope (Item 1)** and **Coaching scope (Item 2)** — see §7.1 and §5.5/§5.7.

Still open (carried as review questions; none block the build):

1. **⚠️ Brief location (Q-branch, default = "report on main, note gap").** The authoritative brief + completion doc are on unmerged `origin/docs/phase-0-completion`. Options: (A) leave as-is, fix docs at Day 0 / P1 [current default]; (B) merge the branch into main first (with the §4a/4b/4c edits so the completion doc is honest); (C) other. Which?
2. **⚠️ Integrity Mode label (§3).** Confirm the solo default is a mode where `FORMATION_LOCKED` **is emitted** (Practice / offline-lab). The adapter's declared policy **disables `FORMATION_LOCKED` in Ranked** — so literal "Ranked" would suppress the very event Drill Lab needs. Is "Practice/Ranked default" shorthand for "the FORMATION-emitting mode," or should the adapter's Ranked policy be revisited?
3. **⚠️ Flag names (§4f/5.6).** Confirm `VAF_DRILL_LAB_ENABLED_MASTER` + `VAF_DRILL_LAB_COHORT` as canonical (replacing the brief's names), so code + docs use one set.
4. **Cadence mapping (§4c).** Confirm the semantic: **one play-call screen = one drill rep**? Drives rep-counter logic + acceptance criterion #2.
5. **30fps-equivalent target (§5.7 #4).** Confirm the bar is "file processed at ≥ 30 fps-equivalent throughput" (not a real-time capture constraint), given file input.

---

## 10 · Session outcome

- State verification: **2 of 5 items failed on main** (1d, 1e) — root cause identified (unmerged branch), docs recovered read-only. Verification otherwise passes.
- Reconciliation: brief is **compatible** with shipped Phase 0 and with the solo reframe; **no re-architecting required**; the single consumer-logic change is the sampled cadence (§4c). **Halt condition #3 did not trigger.**
- Founder sign-off folded in: **playback pipeline in scope (§7.1)**, **event-display-only (§5.5/5.7)**, **Day 0–5 sequence (§8)**. Playback estimate grounded against code at 2–3 days — no halt condition triggered.
- **No application code touched; no existing docs modified.** Committed locally on branch `docs/phase-1a-kickoff-state-report`; **awaiting push authorization.**
