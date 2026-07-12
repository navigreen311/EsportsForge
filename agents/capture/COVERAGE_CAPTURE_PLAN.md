# Coverage v0.3 — capture plan (All-22 primary + playable-cam fallback)

**Context:** the feasibility spike's original "research arc" verdict rested on a false premise
(that All-22 is replay-only). **All-22 is a live gameplay camera** on this setup, which
dissolves the domain-gap/detail blockers — see the correction in
`docs/phase-completions/coverage-v0.3-feasibility-spike.md`. So v0.3 is plausibly **largely
plumbing**, and this capture proves it two ways:

1. **Primary — does the existing ~0.86 classifier hold on LIVE All-22?** (It was measured on
   ~150 *curated* All-22 fixture frames; live gameplay adds stadium/lighting/motion/HUD
   variation.) If it holds → v0.3 is mostly wiring.
2. **Fallback — does coverage survive in a more *playable* camera?** Not everyone will play in
   All-22, so players get a camera choice (All-22 / Standard / Broadcast / Madden Classic). We
   label from the All-22 pass and test which cameras preserve the coverage signal.

The **same-play-multiple-angles** trick (you can re-run a practice rep in each camera) is what
makes the fallback clean: All-22 gives unambiguous ground truth, transferred to the same rep
in every other camera.

---

## Ground rules (read once)

- [ ] **Practice mode, you call the coverage** → the label is known by construction.
- [ ] **Run real pass plays** and **let each rep develop ~2–3 s after the snap** — the DBs must
      rotate into coverage (snap+1–2 s is the read window). A dead snap shows nothing.
- [ ] **Keep the HUD visible** (play clock + scorebug) so the snap detector auto-windows the
      frames; if a mode hides it, no problem — I'll window off contact sheets.
- [ ] **Fix a rep SCRIPT per coverage** — e.g. 5 plays, varying offensive formation/field
      position — and run that **same script, same order, in every camera**. That's what lets me
      match rep #k across cameras and transfer the All-22 label. Vary looks *between* reps, keep
      the coverage fixed *within* a clip.
- [ ] **Capture the All-22 angle FIRST** for each coverage (it's the label source), then re-run
      the same script in the playable cams.

## The four coverages (call one per clip)

| Class | Call in Madden (any variant) | Post-snap tell |
|---|---|---|
| **Cover 1** | Cover 1 / Cover 1 Robber / Man | 1 high safety, corners man-trail |
| **Cover 2** | Cover 2 / Cover 2 Man / Tampa 2 | 2 deep safeties split the halves |
| **Cover 3** | Cover 3 / Cover 3 Sky | 1 high safety, 3-deep zone |
| **Cover 4** | Cover 4 / Quarters / Palms | 2 deep safeties, 4-deep quarters |

---

## Phase 1 — PRIMARY: live All-22 (do this first; it's the decision-maker)

One clip per coverage, ~60 s, ~5 reps of your script, **All-22 camera**:

- [ ] `python grab_live.py --record --label madden26_cov1_a22 --seconds 60`
- [ ] `python grab_live.py --record --label madden26_cov2_a22 --seconds 60`
- [ ] `python grab_live.py --record --label madden26_cov3_a22 --seconds 60`
- [ ] `python grab_live.py --record --label madden26_cov4_a22 --seconds 60`

→ Hand these off first. I validate the ~0.86 classifier on the live frames. **If it holds,
v0.3 is largely plumbing** and Phase 2 just decides how many camera options we can offer.

## Phase 2 — FALLBACK: same reps in the playable cameras

Re-run the **same script per coverage** (same plays, same order) in each playable camera, so
rep #k matches the All-22 rep #k. Standard / Broadcast / Madden Classic:

- [ ] `... --label madden26_cov1_std`   `... cov1_bcast`   `... cov1_classic`
- [ ] `... --label madden26_cov2_std`   `... cov2_bcast`   `... cov2_classic`
- [ ] `... --label madden26_cov3_std`   `... cov3_bcast`   `... cov3_classic`
- [ ] `... --label madden26_cov4_std`   `... cov4_bcast`   `... cov4_classic`

(each `python grab_live.py --record --label <name> --seconds 60`; add `--fps 30` if the device
rejects the default rate.)

## Verify each recording

- [ ] Each `<label>/<label>.mp4` exists, ~60 s, non-trivial size, correct camera.
- [ ] The rep order matches across cameras for a given coverage (so labels transfer by index).

## Hand off to me

- [ ] Phase 1: "got cov1_a22 … cov4_a22" → I validate the classifier on live All-22.
- [ ] Phase 2 (when convenient): "got the std/bcast/classic sets" → I test each playable camera
      against the All-22 label.

Then, read-only on my side:
1. Extract snap+1–2 s frames per clip (snap detector, or eyeballed windows).
2. **Phase 1:** run the ~0.86 classifier on live All-22 frames → does it hold? (macro-F1 vs the
   known coverages). Holds → v0.3 mostly plumbing: retrain/adapt on live All-22, wire
   `detect_coverage`.
3. **Phase 2:** transfer All-22 labels to the same reps in std/bcast/classic → measure which
   cameras keep coverage readable (human + classifier). That decides the supported camera set;
   Madden Classic (wider/higher) is the best fallback bet, Broadcast the least likely.

---

*Context: `agents/capture/{extract_coverage_frames,train_coverage,crossval_coverage}.py` (the
All-22 pipeline; coverage window snap+1.0–2.0 s). Gated phases: Gameplan highlight (1b) +
Phase 1c, per ADR 0010/0017.*
