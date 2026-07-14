"""Train + eval the play-clock 2-head CNN on the PS5 GAME scorebug (grey box).

The shipped v0_2 CNN was trained on the standalone DARK-on-WHITE play-clock and reads
0% on the PS5 game scorebug (a small ':SS' in a GREY box, mean ~79 < the white gate),
so `_read_play_clock` uses EasyOCR (~83%) on the game box today. This retrains PCNet on
the grey game box using game_hud_1.

Data + labels (single game — honest caveat, one stadium/lighting; the digit font is
consistent across games so it should transfer, but that is UNVERIFIED until multi-game
grey-box clips exist — see docs/coverage-hardening-capture-protocol.md):
  * EasyOCR (`OCRPipeline._read_play_clock`) labels each sampled frame's grey box.
  * Isolated misreads are corrected by neighbor consensus (A,B,A -> A,A,A) -> near-GT.
  * TEMPORAL split: train on the first `--split` of the clip, test on the tail — so the
    test frames are a different stretch of play than training (not a random per-frame
    split, which would leak near-duplicate adjacent frames).
Eval reports CNN-exact and raw-EasyOCR-exact BOTH against the cleaned labels on the held-
out tail — a fair "which reads the grey box better" comparison. Exports v0_3 only on
--export.

    cd services/visionaudioforge
    PYTHONPATH="$PWD" .venv/Scripts/python.exe tools/play_clock/train_play_clock_game.py \
        --clip C:/Users/ivann/madden-recal-refs/digit-campaign/game_hud_1/game_hud_1.mp4 [--export]
"""

from __future__ import annotations

import argparse
from pathlib import Path

import cv2
import numpy as np
import torch
import torch.nn as nn

torch.manual_seed(0)
np.random.seed(0)

GAME_BOX = (1420, 1032, 62, 32)        # PS5 game scorebug play_clock (grey :SS)
IH, IW = 48, 96                        # net input (must match play_clock_reader)


def _gray(frame: np.ndarray) -> np.ndarray:
    x, y, w, h = GAME_BOX
    return cv2.cvtColor(frame[y:y + h, x:x + w], cv2.COLOR_BGR2GRAY).astype(np.float32)


def patch(gray: np.ndarray) -> np.ndarray:
    return cv2.resize(gray, (IW, IH)) / 255.0


def _clean(vals: list[int | None]) -> list[int | None]:
    """Correct isolated EasyOCR misreads by neighbour consensus (A,B,A -> A,A,A).
    Conservative: only rewrites a value when both temporal neighbours agree and
    differ from it — leaves real countdown transitions and resets untouched."""
    out = list(vals)
    for i in range(1, len(vals) - 1):
        a, b, c = vals[i - 1], vals[i], vals[i + 1]
        if a is not None and a == c and b != a:
            out[i] = a
    return out


def label_clip(clip: Path, stride: int):
    """Sample every `stride` frames; return (grays, raw, cleaned) aligned lists."""
    from app.adapters.madden26.ocr_pipeline import OCRPipeline
    ocr = OCRPipeline()
    cap = cv2.VideoCapture(str(clip))
    grays: list[np.ndarray] = []
    raw: list[int | None] = []
    i = 0
    while True:
        ok, f = cap.read()
        if not ok:
            break
        if i % stride == 0:
            grays.append(_gray(f))
            v = ocr._read_play_clock(f)
            raw.append(int(v) if v is not None else None)
        i += 1
    cap.release()
    return grays, raw, _clean(raw)


class PCNet(nn.Module):
    def __init__(self) -> None:
        super().__init__()

        def blk(i, o):
            return nn.Sequential(nn.Conv2d(i, o, 3, padding=1), nn.BatchNorm2d(o),
                                 nn.ReLU(), nn.MaxPool2d(2))
        self.f = nn.Sequential(blk(1, 16), blk(16, 32), blk(32, 64), blk(64, 128))
        self.fc = nn.Sequential(nn.Flatten(), nn.Linear(128 * 3 * 6, 128), nn.ReLU(),
                                nn.Dropout(0.3))
        self.ht = nn.Linear(128, 5)
        self.ho = nn.Linear(128, 10)

    def forward(self, x):
        z = self.fc(self.f(x))
        return self.ht(z), self.ho(z)


def _aug(x):
    dx, dy = np.random.randint(-3, 4), np.random.randint(-2, 3)
    x = torch.roll(x, shifts=(dy, dx), dims=(2, 3))
    g = 0.8 + 0.4 * torch.rand(x.shape[0], 1, 1, 1)
    bri = -0.1 + 0.2 * torch.rand(x.shape[0], 1, 1, 1)
    return ((x - 0.5) * g + 0.5 + bri + torch.randn_like(x) * 0.03).clamp(0, 1)


def train(X, tens, ones, epochs=40):
    net = PCNet()
    opt = torch.optim.Adam(net.parameters(), 1e-3, weight_decay=1e-4)
    sched = torch.optim.lr_scheduler.StepLR(opt, 15, 0.3)
    ce = nn.CrossEntropyLoss()
    Xt = torch.tensor(np.array(X)).unsqueeze(1).float()
    Tt, Ot = torch.tensor(tens).long(), torch.tensor(ones).long()
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
    ap.add_argument("--clip", type=Path, required=True)
    ap.add_argument("--stride", type=int, default=6, help="sample every N frames (~5fps)")
    ap.add_argument("--split", type=float, default=0.7, help="fraction of the clip for train")
    ap.add_argument("--export", action="store_true", help="write play_clock_v0_3.onnx")
    ap.add_argument("--out", type=Path,
                    default=Path(__file__).resolve().parents[2]
                    / "app/adapters/madden26/models/play_clock_v0_3.onnx")
    args = ap.parse_args()

    print("labeling clip via EasyOCR (warms ~2s)...", flush=True)
    grays, raw, clean = label_clip(args.clip, args.stride)
    n = len(grays)
    cut = int(n * args.split)
    # Build train set from cleaned labels where present.
    Xtr, Ttr, Otr = [], [], []
    for i in range(cut):
        if clean[i] is not None:
            Xtr.append(patch(grays[i]))
            Ttr.append(clean[i] // 10)
            Otr.append(clean[i] % 10)
    print(f"frames: {n} (train<{cut}, test>={cut}) | train patches: {len(Xtr)}", flush=True)
    net = train(Xtr, Ttr, Otr)

    # Held-out tail eval: CNN vs cleaned-GT, and raw-EasyOCR vs cleaned-GT.
    cnn_ok = ez_ok = tot = within1 = 0
    for i in range(cut, n):
        gt = clean[i]
        if gt is None:
            continue
        tot += 1
        x = torch.tensor(patch(grays[i]))[None, None].float()
        with torch.no_grad():
            lt, lo = net(x)
        pred = int(lt.argmax()) * 10 + int(lo.argmax())
        cnn_ok += (pred == gt)
        within1 += (abs(pred - gt) <= 1)
        ez_ok += (raw[i] == gt)
    if tot:
        print(f"\n=== held-out tail ({tot} labeled frames) vs cleaned labels ===")
        print(f"  CNN exact       : {cnn_ok}/{tot} = {cnn_ok / tot:.2f}")
        print(f"  CNN within +/-1 : {within1}/{tot} = {within1 / tot:.2f}")
        print(f"  raw EasyOCR exact: {ez_ok}/{tot} = {ez_ok / tot:.2f}  (the shipped reader)")

    if args.export:
        torch.onnx.export(net, (torch.zeros(1, 1, IH, IW),), str(args.out),
                          input_names=["patch"], output_names=["tens", "ones"],
                          dynamic_axes={"patch": {0: "n"}, "tens": {0: "n"}, "ones": {0: "n"}},
                          opset_version=17, dynamo=False)
        print(f"\nexported {args.out} ({args.out.stat().st_size // 1024} KB)")
    else:
        print("\n(--export not set — no ONNX written)")


if __name__ == "__main__":
    main()
