# Play-clock CNN reader — training

Reproduces `app/adapters/madden26/models/play_clock_v0_1.onnx`, the dark-on-white
play-clock reader (a small 2-head CNN: tens 0-4, ones 0-9). Patch-NCC was ruled
out for this polarity — see `docs/phase-completions/play-clock-reader-findings.md`.

## Data (external, not committed)

8 live snap-capture clips (~90 s / 30 fps each) at
`~/madden-recal-refs/digit-campaign/<clip>/<clip>.mp4`, the same clips used for the
snap detector. `labels.json` here holds `{clip: {second: value}}` — the play-clock
value at each 1-fps sample, auto-derived by reading each clip's 1-fps contact sheet
and cleaning with countdown monotonicity (drop `?`/red, drop isolated misreads).
575 white-clock labelled seconds; each expands to the ~9 mid-second frames around
the read frame (`30·s+15`), giving ~5.2k training patches.

## Run

```
pip install torch==2.11.0 onnx onnxruntime opencv-python
python train_play_clock.py --clips-dir ~/madden-recal-refs/digit-campaign
```

Seeds are fixed; re-running yields the same weights. The exported ONNX is verified
for torch↔onnxruntime parity at export time.

## Accuracy (held-out by clip)

| Metric | Value | Use |
|---|---|---|
| exact value | 72% | best-effort `play_clock` payload (smoothed downstream) |
| within ±1 | 82% | — |
| reset-vs-resume decision | 94% | snap-detector FP annotation (`last_snap_pause`) |

The reset-vs-resume decision is far more robust than the exact read because the
reset gap (jump toward :40) dwarfs per-read digit noise.
