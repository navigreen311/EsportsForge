"""Coverage v0.3 — T1 tier (MAN vs ZONE) signal-presence probe.

Offline analysis only (not wired). Asks the honest first question for T1: **is the
man/zone signal even present in this footage?** — before any effort to build a full
classifier.

The corpus is labeled Cover 1/2/3/4, which does NOT map cleanly to man/zone: only
**Cover 1 is unambiguously man**, Cover 3/4 are zone, and **Cover 2 is ambiguous**
(zone vs Cover-2-Man). Man/zone also correlates with the safety shell here (Cover 1 =
1-high + man; Cover 3 = 1-high + zone; Cover 4 = 2-high + zone). So the CLEAN test that
isolates man/zone from the shell is **Cover 1 (man) vs Cover 3 (zone) — both 1-high**:
same shell, differing only in man vs zone.

Result (5-fold by-clip, top-70% crop = the DB band, corners+safeties): **F1 ~0.87,
acc ~0.88** (baseline 0.65). So the man/zone signal — DB technique/orientation — is
present and strongly learnable, even more separable than the shell. Abstain: conf>=0.6
-> ~0.89 acc on ~94% of plays; conf>=0.9 -> ~0.90 on ~75%.

Unlike T0 (deep safeties, top-40%), the man/zone tell is in the DBs' coverage technique,
so the best crop is the wider **top ~70%** (corners + safeties), not the deep strip.

WHAT THIS IS NOT: a full T1 classifier. It only proves the signal exists on a Cover1-vs-
Cover3 slice. A real T1 needs DIVERSE man coverages (Cover 0/1-Robber/2-Man/man-under)
and zone coverages, and must resolve Cover 2 — this corpus has only Cover 1 as man. Same
by-clip (not by-game) / 117-play / data-bound caveats as T0. See
docs/phase-completions/coverage-v0.3-modeling-plan.md.

    python coverage_t1_manzone.py --data /abs/agents/capture/coverage_dataset
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

# The clean within-1-high slice: Cover 1 = man, Cover 3 = zone.
MAN_SUBDIR, ZONE_SUBDIR = "cover1", "cover3"
CROP = 0.70  # top 70% of the frame = the DB band (corners + safeties)
NORM = transforms.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225])


def extract(data: str, bot: float):
    net = models.resnet18(weights=models.ResNet18_Weights.IMAGENET1K_V1)
    body = nn.Sequential(*list(net.children())[:-2]).eval()
    for p in body.parameters():
        p.requires_grad = False

    def emb(batch):
        with torch.no_grad():
            return F.adaptive_avg_pool2d(body(torch.stack(batch)), (3, 3)).flatten(1).numpy()

    paths = [p for c in (MAN_SUBDIR, ZONE_SUBDIR)
             for p in sorted(glob.glob(os.path.join(data, c, "*.jpg")))]
    cid = lambda p: re.search(r"(cover\d_\d+)_f\d+", os.path.basename(p)).group(1)  # noqa: E731
    S, Sf, Y, G, bu, bf = [], [], [], [], [], []
    for i, p in enumerate(paths):
        im = Image.open(p).convert("RGB")
        w, h = im.size
        im = im.crop((0, 0, w, int(h * bot))).resize((224, 224))
        t = NORM(transforms.ToTensor()(im))
        bu.append(t)
        bf.append(torch.flip(t, [2]))
        Y.append(0 if MAN_SUBDIR in p else 1)  # man=0, zone=1
        G.append(cid(p))
        if len(bu) == 48 or i == len(paths) - 1:
            S.append(emb(bu))
            Sf.append(emb(bf))
            bu, bf = [], []
    return np.concatenate(S), np.concatenate(Sf), np.array(Y), np.array(G)


def evaluate(S, Sf, Y, G):
    idx: dict = {}
    for i, g in enumerate(G):
        idx.setdefault(g, []).append(i)
    clips = sorted(idx)
    lab = {g: int(Y[idx[g][0]]) for g in clips}
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

    n = len(clips)
    base = max(sum(lab.values()), n - sum(lab.values())) / n
    return (f1(0) + f1(1)) / 2, (p == t).mean(), base, t, p, conf


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", required=True, help="coverage_dataset/ (needs cover1 + cover3 subdirs)")
    ap.add_argument("--crop", type=float, default=CROP, help="keep top fraction of the frame")
    args = ap.parse_args()

    S, Sf, Y, G = extract(args.data, args.crop)
    f1, acc, base, t, p, conf = evaluate(S, Sf, Y, G)
    print(f"T1 MAN vs ZONE — Cover1(man) vs Cover3(zone), SAME 1-high shell, top {int(args.crop*100)}% crop, 5-fold by-clip:")
    print(f"  macro-F1={f1:.3f}  acc={acc:.3f}  (majority baseline={base:.2f})  -> signal is present\n")
    print("  abstain operating points (confidence gate):")
    for thr in (0.5, 0.6, 0.7, 0.8, 0.9):
        m = conf >= thr
        prec = (p[m] == t[m]).mean() if m.sum() else 0.0
        print(f"    conf>={thr}: coverage={m.mean()*100:3.0f}%  accuracy={prec:.3f}")


if __name__ == "__main__":
    main()
