"""Train + export the play-clock 2-head CNN reader (models/play_clock_v0_2.onnx).

Dev/training-only (imports torch; the service runs the ONNX via onnxruntime). The
training data is the 8 live snap-capture clips under ``--clips-dir`` (external,
~/madden-recal-refs/digit-campaign/<clip>/<clip>.mp4) — NOT committed. Labels are
``labels.json`` here: {clip: {second: value}}, auto-derived by reading each clip's
1-fps play-clock contact sheet and cleaning with countdown monotonicity.

Held-out-by-clip this reads 77% exact / 82% within-±1 per frame (~2x the 40% NCC
baseline that was ruled out), and 94% on the snap-detector reset-vs-resume
decision. Training frames are bounded to each labelled second's play-clock plateau
via tick detection (`_ticks`), so no patch straddles a mid-second countdown tick —
this is what took exact from 72% to 77% on the same 8 clips. See
docs/phase-completions/play-clock-reader-findings.md.

    python train_play_clock.py --clips-dir ~/madden-recal-refs/digit-campaign

Reproducibility: seeds are fixed; Date.now()-free. Re-running yields the same
weights given the same clips + labels.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import cv2
import numpy as np
import torch
import torch.nn as nn

torch.manual_seed(0)
np.random.seed(0)

VALBOX = (1448, 1022, 88, 38)          # white digit box (absolute 1920x1080 coords)
IH, IW = 48, 96                        # net input size (must match play_clock_reader)
CLIPS = ["snap_run", "snap_run2", "snap_run3", "snap_huddle",
         "snap_redzone", "snap_nohuddle", "snap_special", "snap_replays"]


WIN = 7             # half-window: consider frames 30·s+15 ± WIN
TICK_TH = 6.0       # VALBOX frame-diff peak that marks a digit change (a countdown tick)


def _vgray(frame: np.ndarray) -> np.ndarray:
    x, y, w, h = VALBOX
    return cv2.cvtColor(frame[y:y + h, x:x + w], cv2.COLOR_BGR2GRAY).astype(np.float32)


def patch(frame: np.ndarray) -> np.ndarray:
    return cv2.resize(_vgray(frame), (IW, IH)) / 255.0


def _ticks(grays: dict) -> list:
    """Frames where the VALBOX changed (a digit flipped) — PEAKS in the frame-diff.
    Used to bound each labelled second to its own play-clock plateau so no training
    patch straddles a mid-second countdown tick (the dominant label-noise source)."""
    idx = sorted(grays)
    d = {idx[j]: float(np.abs(grays[idx[j]] - grays[idx[j - 1]]).mean()) for j in range(1, len(idx))}
    ticks = []
    for j in range(1, len(idx)):
        i = idx[j]
        nxt = d.get(idx[j + 1], 0.0) if j + 1 < len(idx) else 0.0
        if d.get(i, 0.0) >= TICK_TH and d.get(i, 0.0) >= d.get(idx[j - 1], 0.0) and d.get(i, 0.0) >= nxt:
            ticks.append(i)
    return ticks


def dataset(clips_dir: Path, labels: dict, clips: list[str]):
    import bisect
    X, T, O = [], [], []
    for clip in clips:
        if clip not in labels:
            continue
        secs = {int(s): int(v) for s, v in labels[clip].items()}
        lo, hi = min(secs) * 30, max(secs) * 30 + 30
        cap = cv2.VideoCapture(str(clips_dir / clip / f"{clip}.mp4"))
        grays, i = {}, 0
        while True:
            ok, f = cap.read()
            if not ok or i > hi + 2:
                break
            if lo - 2 <= i:
                grays[i] = _vgray(f)
            i += 1
        cap.release()
        ticks = _ticks(grays)
        for s, v in secs.items():
            a = s * 30 + 15
            j = bisect.bisect_right(ticks, a)
            prev = ticks[j - 1] if j > 0 else a - WIN            # last tick <= anchor
            nxt = ticks[j] if j < len(ticks) else a + WIN + 1    # first tick > anchor
            for fi in range(max(a - WIN, prev + 1), min(a + WIN, nxt - 1) + 1):  # plateau ∩ window; skip tick frames
                if fi in grays:
                    X.append(cv2.resize(grays[fi], (IW, IH)) / 255.0)
                    T.append(v // 10)
                    O.append(v % 10)
    return np.array(X), np.array(T), np.array(O)


class PCNet(nn.Module):
    def __init__(self) -> None:
        super().__init__()

        def blk(i, o):
            return nn.Sequential(nn.Conv2d(i, o, 3, padding=1), nn.BatchNorm2d(o),
                                 nn.ReLU(), nn.MaxPool2d(2))
        self.f = nn.Sequential(blk(1, 16), blk(16, 32), blk(32, 64), blk(64, 128))  # 48x96 -> 3x6
        self.fc = nn.Sequential(nn.Flatten(), nn.Linear(128 * 3 * 6, 128), nn.ReLU(), nn.Dropout(0.3))
        self.ht = nn.Linear(128, 5)     # tens 0-4
        self.ho = nn.Linear(128, 10)    # ones 0-9

    def forward(self, x):
        z = self.fc(self.f(x))
        return self.ht(z), self.ho(z)


def _aug(x):
    dx, dy = np.random.randint(-3, 4), np.random.randint(-2, 3)
    x = torch.roll(x, shifts=(dy, dx), dims=(2, 3))
    g = 0.8 + 0.4 * torch.rand(x.shape[0], 1, 1, 1)
    bri = -0.1 + 0.2 * torch.rand(x.shape[0], 1, 1, 1)
    return ((x - 0.5) * g + 0.5 + bri + torch.randn_like(x) * 0.03).clamp(0, 1)


def train(Xtr, Ttr, Otr, epochs=40):
    net = PCNet()
    opt = torch.optim.Adam(net.parameters(), 1e-3, weight_decay=1e-4)
    sched = torch.optim.lr_scheduler.StepLR(opt, 15, 0.3)
    ce = nn.CrossEntropyLoss()
    Xt = torch.tensor(Xtr).unsqueeze(1)
    Tt = torch.tensor(Ttr).long()
    Ot = torch.tensor(Otr).long()
    for _ in range(epochs):
        net.train()
        idx = torch.randperm(len(Xt))
        for i in range(0, len(Xt), 128):
            b = idx[i:i + 128]
            lt, lo = net(_aug(Xt[b]))
            loss = ce(lt, Tt[b]) + ce(lo, Ot[b])
            opt.zero_grad()
            loss.backward()
            opt.step()
        sched.step()
    net.eval()
    return net


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--clips-dir", type=Path, required=True)
    ap.add_argument("--out", type=Path,
                    default=Path(__file__).resolve().parents[2]
                    / "app/adapters/madden26/models/play_clock_v0_2.onnx")
    args = ap.parse_args()
    labels = json.load(open(Path(__file__).parent / "labels.json"))
    Xtr, Ttr, Otr = dataset(args.clips_dir, labels, CLIPS)
    print(f"training on {len(Xtr)} patches from {len(labels)} clips")
    net = train(Xtr, Ttr, Otr)
    torch.onnx.export(net, torch.zeros(1, 1, IH, IW), str(args.out),
                      input_names=["patch"], output_names=["tens", "ones"],
                      dynamic_axes={"patch": {0: "n"}, "tens": {0: "n"}, "ones": {0: "n"}},
                      opset_version=17, dynamo=False)
    print(f"exported {args.out} ({args.out.stat().st_size // 1024} KB)")


if __name__ == "__main__":
    main()
