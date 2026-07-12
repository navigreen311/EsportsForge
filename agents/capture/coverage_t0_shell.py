"""Coverage v0.3 — T0 tier (safety SHELL: 1-high vs 2-high) probe.

Offline analysis only (not wired into the adapter). The coarsest, most useful coverage
signal — is it a 1-high shell (Cover 1/3) or a 2-high shell (Cover 2/4)? — evaluated
HELD-OUT BY CLIP on the existing coverage_dataset.

Key finding (see docs/phase-completions/coverage-v0.3-modeling-plan.md): the shell IS the
deep-safety count, so cropping the frame to the **deep field** (the top ~40% in the All-22
view, where the safeties sit) concentrates the signal and jumps T0 from ~0.67 (full frame)
to ~0.80-0.83 macro-F1. Cropping AWAY the crowd/sideline *helping* is evidence the signal is
the safeties, not a stadium confound. ~35-50% all work; 30% is too tight (cuts safeties).

Under the codebase's abstain-over-guess rule, the shippable operating point is a confidence
gate: conf>=0.8 -> ~0.89 accuracy on ~78% of plays (abstain on the rest); conf>=0.9 -> ~0.93
on ~69%.

CAVEATS: held-out by CLIP, not by GAME (no game labels in this corpus) — by-game would be
stricter; ~117 plays (data-bound, the learning curve is still rising); the top-40% crop is a
mildly eval-selected hyperparameter.

    python coverage_t0_shell.py --data /abs/agents/capture/coverage_dataset
"""

from __future__ import annotations

import argparse
import glob
import os
import re

import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F
from PIL import Image
from torchvision import models, transforms

torch.manual_seed(0)
np.random.seed(0)

CLASSES = ["cover1", "cover2", "cover3", "cover4"]
SHELL = {0: 0, 2: 0, 1: 1, 3: 1}  # cover1/cover3 = 1-high (0); cover2/cover4 = 2-high (1)
SHELL_NAME = {0: "1-high", 1: "2-high"}
DEEP_CROP = 0.40  # keep the top 40% of the frame — the deep field where the safeties are
NORM = transforms.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225])


def extract_deep(data: str, bot: float):
    """Frozen ResNet18 spatial features (512x3x3) of the top-`bot` band of each frame."""
    net = models.resnet18(weights=models.ResNet18_Weights.IMAGENET1K_V1)
    body = nn.Sequential(*list(net.children())[:-2]).eval()
    for p in body.parameters():
        p.requires_grad = False

    def emb(batch):
        with torch.no_grad():
            return F.adaptive_avg_pool2d(body(torch.stack(batch)), (3, 3)).flatten(1).numpy()

    paths = [p for c in CLASSES for p in sorted(glob.glob(os.path.join(data, c, "*.jpg")))]
    cid = lambda p: re.search(r"(cover\d_\d+)_f\d+", os.path.basename(p)).group(1)  # noqa: E731
    S, Sf, Y, G, bu, bf = [], [], [], [], [], []
    for i, p in enumerate(paths):
        im = Image.open(p).convert("RGB")
        w, h = im.size
        im = im.crop((0, 0, w, int(h * bot))).resize((224, 224))
        t = NORM(transforms.ToTensor()(im))
        bu.append(t)
        bf.append(torch.flip(t, [2]))
        Y.append(CLASSES.index(cid(p).split("_")[0]))
        G.append(cid(p))
        if len(bu) == 48 or i == len(paths) - 1:
            S.append(emb(bu))
            Sf.append(emb(bf))
            bu, bf = [], []
    return np.concatenate(S), np.concatenate(Sf), np.array(Y), np.array(G)


def evaluate(S, Sf, Y, G):
    """5-fold by-clip linear probe on the per-clip mean feature. Returns
    (macro-F1, acc, per-shell F1, true, pred, confidence)."""
    idx: dict = {}
    for i, g in enumerate(G):
        idx.setdefault(g, []).append(i)
    clips = sorted(idx)
    lab = {g: SHELL[int(Y[idx[g][0]])] for g in clips}
    folds = {g: int(g.split("_")[1]) % 5 for g in clips}
    ms = {g: S[idx[g]].mean(0) for g in clips}
    msf = {g: Sf[idx[g]].mean(0) for g in clips}
    prob: dict = {}
    for fold in range(5):
        tr = [g for g in clips if folds[g] != fold]
        te = [g for g in clips if folds[g] == fold]
        xtr = np.array([ms[g] for g in tr] + [msf[g] for g in tr], dtype=np.float32)
        ytr = np.array([lab[g] for g in tr] * 2)
        h = nn.Linear(4608, 2)
        opt = torch.optim.Adam(h.parameters(), 0.01, weight_decay=1e-2)
        ce = nn.CrossEntropyLoss()
        xt, yt = torch.tensor(xtr), torch.tensor(ytr).long()
        for _ in range(250):
            opt.zero_grad()
            ce(h(xt), yt).backward()
            opt.step()
        with torch.no_grad():
            pp = torch.softmax(h(torch.tensor(np.array([ms[g] for g in te], dtype=np.float32))), 1).numpy()
        for g, pr in zip(te, pp):
            prob[g] = pr
    t = np.array([lab[g] for g in clips])
    p = np.array([prob[g].argmax() for g in clips])
    conf = np.array([prob[g].max() for g in clips])

    def f1(c):
        tp = ((p == c) & (t == c)).sum()
        fp = ((p == c) & (t != c)).sum()
        fn = ((p != c) & (t == c)).sum()
        a = tp / (tp + fp) if tp + fp else 0.0
        b = tp / (tp + fn) if tp + fn else 0.0
        return 2 * a * b / (a + b) if a + b else 0.0

    per = {c: f1(c) for c in (0, 1)}
    return (per[0] + per[1]) / 2, (p == t).mean(), per, t, p, conf


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", required=True, help="coverage_dataset/ (cover1..4 frame subdirs)")
    ap.add_argument("--crop", type=float, default=DEEP_CROP, help="keep top fraction of the frame")
    args = ap.parse_args()

    S, Sf, Y, G = extract_deep(args.data, args.crop)
    f1, acc, per, t, p, conf = evaluate(S, Sf, Y, G)
    print(f"T0 SHELL (1-high vs 2-high), deep crop top {int(args.crop * 100)}%, 5-fold by-clip:")
    print(f"  macro-F1={f1:.3f}  acc={acc:.3f}  ({SHELL_NAME[0]} F1={per[0]:.2f}, {SHELL_NAME[1]} F1={per[1]:.2f})\n")
    print("  abstain operating points (confidence gate):")
    for thr in (0.5, 0.6, 0.7, 0.8, 0.9):
        m = conf >= thr
        cov = m.mean()
        prec = (p[m] == t[m]).mean() if m.sum() else 0.0
        print(f"    conf>={thr}: coverage={cov * 100:3.0f}%  accuracy={prec:.3f}")


if __name__ == "__main__":
    main()
