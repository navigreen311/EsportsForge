# T0 shell — game-tagged capture plan (by-game validation)

**Goal:** the T0 safety-shell classifier (1-high vs 2-high) is **0.83 macro-F1 held-out by
CLIP** with the deep-field crop (`coverage_t0_shell.py`) — promising, but by-clip may share
stadium/teams within a game, so it can flatter. This capture adds **game/session tags** so I
can validate **held-out by GAME** — the honest test that decides whether T0 ships. It also
adds data (the learning curve is still rising at 117 plays).

**Decision this unblocks:** if T0 holds by-game (~0.80), wire `detect_coverage` to emit
`1-high` / `2-high` + confidence + **abstain** (per the never-fabricate rule). If it collapses
by-game, the by-clip number was stadium-confounded and T0 needs a rethink.

---

## The one thing that makes this work: each SESSION = a different GAME

By-game validation is only meaningful if holding out a game tests an **unseen visual context**.
So:

- [ ] **Each session (game) = a DIFFERENT matchup in a DIFFERENT stadium** (different team
      uniforms + field + lighting). If every session is the same teams/stadium, by-game ≈
      by-clip and proves nothing.
- [ ] Tag every clip with its game number in the filename (below) so I can hold out whole games.

## Ground rules (same as before)

- [ ] **All-22 camera** (the deployment view). Don't zoom — the deep safeties (top ~40% of the
      frame) must stay visible; that's the whole signal.
- [ ] **Practice mode, you call the coverage** → the label is known. Capturing the specific
      Cover 1/2/3/4 is free and feeds both T0 (shell) and the 4-way effort.
- [ ] **Run pass plays; let each rep develop ~2–3 s after the snap** so the safeties rotate into
      the shell. A dead snap shows nothing.
- [ ] Vary **offensive formation / field position** within a session; keep the coverage fixed
      per clip.

## Shells (T0 only needs the pair; capture all four for free)

| Call | Shell |
|---|---|
| Cover 1 / Cover 3 | **1-high** |
| Cover 2 / Cover 4 | **2-high** |

Balance matters — each session should get **both shells** (all four calls = balanced).

## Capture — 5 games × 4 coverages (~5 reps each), ~60 s per clip

Filename tag: **`cov_g<GAME>_cover<N>`** (`g1…g5` = the five distinct matchups). For **each**
game, start a new matchup in a new stadium, set All-22, then:

```
# Game 1 (matchup/stadium A):
python grab_live.py --record --label cov_g1_cover1 --seconds 60
python grab_live.py --record --label cov_g1_cover2 --seconds 60
python grab_live.py --record --label cov_g1_cover3 --seconds 60
python grab_live.py --record --label cov_g1_cover4 --seconds 60
# Game 2 (DIFFERENT matchup/stadium B): cov_g2_cover1 … cov_g2_cover4
# Game 3 (C): cov_g3_cover1 … ; Game 4 (D): cov_g4_… ; Game 5 (E): cov_g5_…
```

20 clips, ~100 plays across 5 distinct games. (4 games minimum for leave-one-game-out; 5 is
better. `--fps 30` if the device rejects the default rate.)

- [ ] Game 1 — matchup/stadium: ________________  (cov_g1_cover1..4)
- [ ] Game 2 — matchup/stadium: ________________  (cov_g2_cover1..4)
- [ ] Game 3 — matchup/stadium: ________________  (cov_g3_cover1..4)
- [ ] Game 4 — matchup/stadium: ________________  (cov_g4_cover1..4)
- [ ] Game 5 — matchup/stadium: ________________  (cov_g5_cover1..4)

## Verify

- [ ] Each `cov_g<G>_cover<N>/…​.mp4` exists, ~60 s, All-22, full field visible.
- [ ] The five games are genuinely different stadiums/uniforms (not reskins of one).

## Hand off to me

- [ ] "Got g1..g5, cover1..4" (+ jot which matchup each game was, above).

Then, read-only on my side:
1. Extract deep-field frames per clip (`extract_coverage_frames.py` window + the top-40% crop).
2. **Leave-one-GAME-out** validation of T0 (train on existing corpus + 4 games, test the held-out
   game) — the honest number. Also re-check the 4-way tier by game.
3. **If T0 holds by-game (~0.80):** wire `detect_coverage` → emit `1-high`/`2-high` + confidence
   + abstain (T0 first; `defensive_coverage` stays free-str per ADR 0017). **If it drops:** the
   by-clip 0.83 was stadium-confounded → report honestly and rethink.

---

*Context: `agents/capture/coverage_t0_shell.py` (deep-crop shell probe) +
`docs/phase-completions/coverage-v0.3-modeling-plan.md` (the plan + T0 result). The broader
4-way / playable-cam capture is `COVERAGE_CAPTURE_PLAN.md`; this T0 plan is the near-term
priority because T0 is the tier closest to shippable.*
