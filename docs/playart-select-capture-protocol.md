# Play-Select Play-Art Capture Protocol

**Status:** spec (no capture run yet) · **Date:** 2026-07-21 · **Owner:** VAF / play-art (3b)

## Why this pass exists

The [feasibility pass](#) established that reconstructing routes from *live gameplay*
is a dead end (ball-follow camera, no player detail — see the abandoned post-snap arc),
but that a tractable subset (3b) is reading the **play-SELECT play art**: the pre-play
menu where Madden draws each candidate play as a coloured route diagram.

The recon pass over `~/madden-recal-refs` found **exactly one** clean play-select frame
(`live_playcall_raw.png`). That one frame is enough to *confirm* the art is extractable —
colour-separable polylines, an explicit LOS hash, white player dots, near-top-down — but
**not** enough to prototype or validate an extractor (N=1, one formation family, one team).

**This pass produces the dataset.** Goal: a labelled set of play-select frames, diverse
enough to (a) build a route-extraction prototype and (b) measure its accuracy on a
**group-held-out** split (unseen formations + teams), per our ML eval hygiene.

This is **not** a live-gameplay or tracking capture. These are static menu screens.

---

## 0. What the target frame is

The **play-SELECT** screen ("Select a Play"), *not* formation-SELECT (which shows a
formation list + personnel bubbles and carries **no** route art — most of the existing
`grab/playcall_*` frames are this, which is the trap). The play-select screen shows **3
plays side-by-side**, each a small diagram:

- coloured **route polylines** (Madden's fixed per-route colours) ending in arrowheads,
- a yellow dashed **line of scrimmage** (horizontal reference),
- white **player dots** / OL chips on the LOS,
- the play name + formation printed below each tile.

Every captured screen therefore yields **3 labelled play tiles** for free.

---

## 1. Pre-capture settings (set once, verify each session)

| Setting | Value | Why |
|---|---|---|
| Output resolution | **1080p** | HUD/art calibrated at 1920×1080 (ADR 0013); capture card is native 1080p MJPEG |
| Play Call → **Dynamic Play Call** | **OFF** | ON replaces the 3-tile art panel with the simplified wheel — kills the signal |
| Play Call → Previous Play Information | ON (optional) | adds the "Previous Play" mini-diagram (a small bonus art source, top-right) |
| Camera | default broadcast | irrelevant to the menu, but keep consistent |

Capture-card sanity (**do this first, every session**):

```
<VAF_PY> grab_live.py --preflight
```

Confirm device `USB3.0 Video`, 1080p, **live signal — not green-noise / not black**.
If the frame is green-noise or ~all-black: reseat HDMI, re-preflight. **Never capture on
a bad feed** — a large fraction of the old `grab/` and `cov_pa/` frames are green-noise
dropouts and are worthless.

---

## 2. Sampling matrix — what to capture (this is the whole point)

A naive extractor breaks on: overlapping/crossing lines, curved routes, bunched dots,
and background bleed-through. Sample deliberately across the axes that cause those.

**Formations (start-position diversity) — the primary group key.** Cover the frontend
`Formation` union; ≥2 screens each:

`Gun Spread · Gun Trips TE · Gun Bunch / Shotgun Bunch · Gun Empty · Singleback Ace ·
Singleback Deuce Close · I-Form · Pistol · Shotgun Trips` (≈ 8–10 families).

**Route/concept shapes (line-geometry diversity).** Make sure the tiles collectively
include: **verticals** (parallel straight lines), **crossers / Mesh** (X-ing lines —
the hard case), **flat/out/corner** (right-angles), **screens** (short backward hooks),
**RPO / PA**, **drags**, **wheels** (curved). You don't pick these per-tile — you get 3
per screen — but choose formations/pages that surface them, and log what you got.

**Background / art robustness.** Route colours are fixed, but the live scene bleeds
through the dimmed panel. Capture **≥2 teams** and **≥2 stadiums or day/night** so the
extractor isn't tuned to one background.

**Hard cases (≥3 tiles each):** bunch/stack (overlapping dots), Empty (5 wide, max
lines), heavy sets (few routes), any motion arrows.

**Volume target**

| | Minimum viable | Comfortable |
|---|---|---|
| Screens | ~30 | ~40 |
| Play tiles (×3) | ~90 | ~120 |
| Formations | ≥8 | all families |
| Teams | ≥2 | 3 |

Include the existing `live_playcall_raw.png` as tile set #0.

---

## 3. Capture recipe (per screen)

The screen is **static**, so use a low-fps **duration grab** (redundant stills of the
held frame) — *not* `--record` (that's for motion/snap) and *not* a bare `--shots` burst
(the known feed-lag gotcha tears burst frames).

1. In-game: pick a formation → land on **"Select a Play"** (3 tiles with route art). Hold.
2. Grab ~12 redundant stills:
   ```
   <VAF_PY> grab_live.py --label playsel_<team>_<formation>_<NN> --duration 6 --fps 2
   ```
3. Page the play list (L1/R1) to the next set of 3 and repeat with `<NN>+1`.
4. Cull: keep the **sharpest** still per screen; drop any with a controller-glyph popup,
   scroll blur, or feed tear.

**Fallback if duration-grab stills come out torn/laggy:** record + extract —
```
<VAF_PY> grab_live.py --record --label playsel_<...> --seconds 8
```
then pull clean frames from the mp4 (the record path is lag-robust per the live gotcha).

`<VAF_PY>` = `services/visionaudioforge/.venv/Scripts/python.exe`;
`grab_live.py` lives in `~/madden-recal-refs/digit-campaign/`.

### Label scheme

`--label` becomes the output subdir/prefix. Encode the **formation** in the label so the
group-held-out split is a filename filter, not a re-labelling chore:

```
playsel_<team>_<formation>_<NN>      e.g.  playsel_kc_singleback-deuce-close_03
```

---

## 4. Per-frame accept/reject gate

Accept only if: full 1080p · all 3 tiles fully in-panel (LOS hash + dots + arrowheads not
clipped by UI) · no controller-glyph overlay on the art · no scroll blur · feed clean (no
green-noise/tear). Deep routes that exit the top of a tile are fine — the game's art clips
them too; note it.

---

## 5. Dataset manifest (`manifest.csv`)

One row per **screen** — this is the ground truth + group key for validation:

```
file, team, stadium_or_light, formation, play_left, play_mid, play_right, personnel, tags
```

`tags` ∈ {bunch, stack, empty, motion, crossers, verticals, screen, …}. Log the 3 play
names off the tiles now (they're printed) so validation doesn't need to re-OCR.

---

## 6. Train / validate split (do NOT skip)

Split **by group, never by frame or by screen** — the 3 tiles on one screen share art,
lighting, and background and will leak a play's signature into val (this is exactly the
frame-level-leakage trap that inflated the coverage numbers 0.86→0.45).

- **Hold out entire formations** (≥2 families unseen) **and ≥1 team** for validation.
- Train on the rest; report extractor accuracy on the held-out group.

---

## 7. Non-goals & standing caveat

- **Designed, not run.** This captures the play art *as drawn* (playbook routes + any
  pre-snap hot routes) — **not** the path your receiver physically ran. That distinction
  is inherent to 3b and unchanged from the feasibility pass.
- Not live gameplay, not player tracking. Static menu frames only.
- The **extraction algorithm is out of scope** for this pass — this pass only produces the
  labelled dataset it will be built and measured against.

---

## 8. Deliverable & effort

**Deliverable:** `playart-select/` frame set (~30–40 screens, ~90–120 tiles) + `manifest.csv`,
sufficient to prototype the extractor and measure it group-held-out.

**Effort:** ~1–1.5 h capture (~1–2 min/screen: navigate, hold, grab, label) + ~30 min
cull/manifest. Single session, feed permitting.
