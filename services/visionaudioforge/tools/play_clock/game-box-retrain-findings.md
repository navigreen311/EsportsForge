# Play-clock CNN — PS5 grey game-box retrain (findings)

**Outcome: retrain is FEASIBLE but is NOT a validated improvement over the shipped
EasyOCR. Recommendation: keep EasyOCR; do not wire a game-box CNN until independent
ground truth (or multi-game grey-box data) exists.** Honest negative/inconclusive result.

## Why this was attempted

The shipped v0_2 CNN (`play_clock_v0_2.onnx`) was trained on the standalone DARK-on-WHITE
play-clock and reads **0%** on the PS5 game scorebug (a small `:SS` in a GREY box, mean
~79 < the CNN's white-box gate 110). So `_read_play_clock` uses **EasyOCR** on the game box
today (`ocr_pipeline.py`). "Retrain the CNN for the game box" = train PCNet on grey-box
crops.

## What was done

`tools/play_clock/train_play_clock_game.py` — grey-box trainer:
- Labels `game_hud_1` via EasyOCR (`OCRPipeline._read_play_clock`), corrects isolated
  misreads by neighbour consensus (A,B,A → A,A,A), TEMPORAL split (train first 70% of the
  clip, test the tail).
- Data is ample: 2500 sampled frames, ~1343 train patches, **all 5 tens digits (0–4) and all
  10 ones digits (0–9) covered**. PCNet (the shipped 2-head architecture) trains cleanly.

## The result (and why it's inconclusive)

Held-out tail (728 labeled frames), vs the cleaned labels:

| Reader | exact | within ±1 |
|---|---|---|
| grey-box CNN (v0.3, this retrain) | **0.89** | 0.89 |
| raw EasyOCR (the shipped reader)  | **1.00** | — |

Two things this shows, and one it can't:
- **The CNN reads the grey box** (0.89) — a real improvement over v0_2's 0%. So a game-box
  CNN is *trainable*.
- **The comparison is CIRCULAR.** The "cleaned labels" are EasyOCR's own reads (the
  neighbour-consensus cleaning changed ~nothing on the tail — i.e. EasyOCR was already
  self-consistent there), so "EasyOCR = 1.00" just means EasyOCR agrees with itself. The
  CNN's 0.89 is **agreement with EasyOCR**, not accuracy vs ground truth.
- **The CNN's misses are tens-digit errors** (within-±1 == exact ⇒ every miss is off by
  >1, i.e. the tens digit, not adjacent-digit confusion). So on the ~11% where they
  disagree, the CNN is the likelier-wrong one (EasyOCR reads this box reliably).

**Net:** without an INDEPENDENT ground truth (hand-labeled values, or a second game so the
label source isn't the reader under test), there is no way to show the CNN *beats* EasyOCR
— and the evidence points the other way. Wiring the CNN as primary would risk regressing a
working EasyOCR path. This mirrors [[feedback_ml_eval_hygiene]]: don't ship a model as an
improvement when the only labels are produced by the incumbent it's being compared to.

## What would finish it (data-gated, low priority)

1. **Hand-labeled GT** — read ~50–100 grey-box crops by eye (spanning the tens digits),
   then score EasyOCR AND the CNN against that. If EasyOCR is already ~high, the CNN adds
   nothing for the game box; if EasyOCR has a systematic weak digit the CNN fixes, revisit.
2. **Multi-game grey-box clips** (fold into `docs/coverage-hardening-capture-protocol.md`)
   so training + testing don't share one game/stadium and the labels can be cross-checked.

Until then: **EasyOCR stays the shipped game-box play-clock reader.** The trainer is kept
so the retrain can be finished the moment GT/multi-game data lands. (The CNN also still
serves the standalone dark-on-white play-clock via v0_2, unchanged.)
