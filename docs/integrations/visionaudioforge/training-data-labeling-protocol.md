# Training-Data Labeling Protocol — Agent Pre-screen + Clean Selector + Human Label

- **Status:** v1 — established during M5c sub-task 2 (Madden 26 formation classifier, 2026-06-29).
- **Audience:** title-adapter authors building any on-field *classifier* that needs labeled gameplay frames (formation, coverage, defensive front, etc.) — Madden 26, CFB 26, NBA 2K26, EA FC 26, MLB 26, and beyond.
- **Cross-references:** [HUD calibration methodology §"Single-frame agent labeling limits"](madden26-hud-calibration-methodology.md), [M5c plan sub-task 2](../../phase-completions/0-vaf-m5c-plan.md), [local capture protocol](madden26-local-capture-protocol.md). Aligns with the Forge "adapters extended without core changes" principle (the labeling pipeline lives in `scripts/` + adapter assets; core is untouched).

## The pattern, in one line

**Agent pre-screens skips → a tightened selector produces a clean pool → a human labels the canonical classes.**

Each step does what it is reliably good at, and nothing it isn't.

## Why this shape (the camera limit)

Every sports sim renders gameplay through an elevated, ball-following, zoomed broadcast camera — **not** an all-22 view. From a single static frame a coding agent (or any single-frame model) **cannot** recover the fine on-field geometry a classifier is trained on: in Madden that's QB depth (shotgun/pistol/under-center) and WR-count-per-side (trips/bunch/doubles/empty). M5c measured this directly — confident agent yield was ~0–1 of 12 sampled frames, below the escalation line, and cropping/upscaling didn't help.

But the agent **is** highly reliable at *rejecting* non-trainable frames, and a selector **can** be tightened to emit only clean, locked pre-snap frames. So the human only has to do the irreducible part — naming the class — on a small, clean pool, with frame-scrubbing for context.

Treat this as the default assumption for a new title: **do not** plan for an agent to label fine on-field geometry from gameplay frames. Budget the division of labor below.

## The three steps

### 1. Agent pre-screen (high-accuracy SKIP)
The agent reliably rejects: coach/player close-ups, crowd & sideline cuts, replay graphics, kickoffs/punts/special teams, and mid-play piles. Use this as a cheap first filter and as a sanity check on the selector's output. **Calibrate on a small sample first** (≈10–20 frames): attempt the actual labeling task and measure confident yield *before* bulk-producing anything. If the fine-class yield is low, stop — bad ground truth poisons the classifier worse than fewer labels.

### 2. Tightened selector (clean pool)
`scripts/hud_calibration/sample_pre_snap_candidates.py` (v2) emits a frame only when the players are **locked**, not mid-play:
- **Two consecutive near-zero-motion samples** — the scene was still across ~1 s (offense set), not a single-frame lull. (The v1 single-frame low-motion rule was the main source of unusable mid-play frames.)
- **Field-green dominance** (strong threshold) — rejects close-ups / replay graphics / sideline cuts.
- **Live scorebug present** (HUD-band contrast) — confirms gameplay, not a menu/replay.
- **OCR kickoff/punt drop** — reads the down/distance panel on gate-passing frames and drops special-teams plays (outside the canonical offensive taxonomy). Cheap because it runs only on the small post-gate set.
- **Per-clip cap, proportional** — under-cap clips simply contribute less; do not pad.

Tune the gates to land the pool in a sane band (M5c target: 400–1,200 frames). Verify the output with a small visual sample; if it's still >20% mid-play / non-canonical, the gates aren't fixing the real problem — stop and rethink rather than hand a dirty pool to a human.

### 3. Human labels the canonical classes
A human runs the keyboard labeling tool (`scripts/hud_calibration/label_formations.py`): single-keypress per class, frame-scrubbing for snap context, skip/medium for ambiguity, incremental crash-safe CSV, resume support. The human does only the irreducible judgment the camera still demands.

A complementary free win: where the title offers a **single-scenario practice/drill mode**, capture one clip per class — every frame's label is known from the clip, so those frames **auto-label** with no human pass and form a balanced training backbone (M5c got 690 practice auto-labels this way).

## Accept / partial-relabel / escalate thresholds

After labeling, the human spot-checks a stratified sample (≈30 frames across classes):

| Spot-check accuracy | Action |
| --- | --- |
| **≥ 95%** | Accept — labeling complete, proceed to the split/training step. |
| **85–94%** | Partial relabel — identify the classes that struggled and re-label just those with closer attention. |
| **< 85%** | Escalate — the signal isn't there at this source/quality; reconsider the selector, the camera/source, or fall back to fully-manual labeling. |

The same thresholds apply when the *agent* attempts step 1's labeling on a calibration sample: if the agent's confident fine-class accuracy is below 85%, it pre-screens skips only and the human owns the canonical labels.

## Capture mode determines the learnable signal

**Before capturing, decide what signal the model needs — then pick the capture mode that contains it.** M5c learned this the expensive way (ADR 0014): the CPU-vs-CPU capture was ideal for *live-gameplay* HUD OCR (scorebug, down/distance) and for *on-field* frames, but it **structurally omitted the play-call screen** — the CPU picks plays off-screen, so the formation-name overlay never appears. When the pixel-based formation CNN failed (single-frame gameplay-camera classification ceilinged at ~0.22 macro-F1), the pivot to reading the formation *name* off the play-call overlay required **re-capturing in a different mode** (practice play-select + human-played gameplay) because the original footage simply didn't contain that signal.

The rule for future title adapters:

| Signal the model needs | Capture mode that contains it |
| --- | --- |
| Live-gameplay HUD (score, clock, down) via OCR | Any in-play footage (incl. CPU-vs-CPU) |
| On-field geometry (formation, coverage) via CNN | In-play footage — **but** verify the broadcast camera exposes enough player detail (M5c: it did not for fine formations) |
| Explicit UI text (formation/play NAME) via OCR | A mode that *shows the menu/overlay* — practice play-select, human-played play-call. **NOT** CPU-vs-CPU. |

Two consequences:
1. **Prefer OCR-of-overlay over CNN-from-pixels when the game displays the signal as text** (ADR 0014). Reading the game's own label is far more reliable than inferring geometry — but it dictates the capture mode.
2. **Plan capture per-signal up front.** A single capture batch may not contain every signal a title adapter needs; budget for multiple capture modes (live gameplay + menu/overlay screens) rather than discovering the gap after a failed model.

## Environment requirements

**Labeling tools need `opencv-python` (the GUI build), not `opencv-python-headless`.** This is a recurring gotcha worth fixing once:

- The keyboard labeling tool calls `cv2.namedWindow` / `cv2.imshow` to show frames. The **headless** OpenCV build compiles those GUI functions out, so launching the tool against it throws:
  `cv2.error: (-2) The function is not implemented. Rebuild the library with Windows, GTK+ 2.x or Cocoa support … in function 'cvNamedWindow'`.
- There's a genuine split: the **core VAF service** runs headless on Linux ECS and *wants* `opencv-python-headless`; the **dev labeling tool** runs on a Windows desktop and *needs* the GUI build. The two OpenCV variants share the `cv2` import namespace and **cannot coexist** — installing one shadows the other.
- Resolution (M5c): the dev `services/visionaudioforge/.venv` and `requirements.txt` use **`opencv-python`** (GUI). It's a functional superset — headless contexts simply never hit the GUI calls. Production Linux deployments may pin `opencv-python-headless`; the GUI calls live only in `scripts/` (labeling/calibration tooling), never in the core service path.
- **Caveat:** `easyocr` declares `opencv-python-headless` as a dependency, so a fresh `pip install -r requirements.txt` can pull headless back in and shadow the GUI build. Install `opencv-python` last, or `pip install --force-reinstall opencv-python` after the rest.
- **Pattern for tooling code:** keep `cv2.namedWindow`/`imshow` calls behind the interactive entry point (e.g. a `run()` / `--smoke` path), and offer a no-GUI `--check` mode, so the module still imports and unit-tests in headless CI.

Every future title adapter's labeling tool inherits this requirement — it's an environment split, not a per-title detail.

## Reusability for future titles

- **CFB 26** — same EA engine/camera as Madden; the protocol transfers directly (formation taxonomy differs but the geometry-from-gameplay limit is identical).
- **NBA 2K26 / EA FC 26 / MLB 26** — different sports, same broadcast-camera limitation. Re-tune the selector's motion/field/HUD gates to the title and the "locked" definition to the sport (set offense / set-piece / pre-pitch), keep the three-step division of labor.
- The **agent-pre-screen + clean-selector + human-label** shape and the **accept/relabel/escalate** thresholds are title-agnostic. Only the gate thresholds and the class taxonomy are per-title.

## Forge alignment

- **Rule 5** (adapters extended without core changes): the entire pipeline is `scripts/` tooling + per-adapter assets (`formation_candidates.json`, `formation_labels.csv`); the core dispatcher / event contract is untouched.
- **Rule 4** (events structured & canonical): labels feed model training whose outputs become typed `EventEnvelope` fields; consumers never see labeling provenance.
