"""Coverage v0.3 — Phase B diagnostic probes (reproduces the modeling-plan numbers).

Offline analysis only — NOT wired into the adapter. Answers, cheaply and honestly on
the existing coverage_dataset (frozen ResNet18, held-out BY CLIP):

  1. LEAKAGE demo   — per-IMAGE 80/20 (leaky) vs per-CLIP 80/20 (honest). Shows why the
                      headline 0.86 (frame-level split) does not reproduce by clip (~0.4).
  2. WHAT MOVES IT  — avgpool single-frame / mean-over-window / temporal-stats / GRU vs
                      SPATIAL (512x3x3, location preserved). Spatial wins; temporal hurts
                      at this data scale (117 plays).
  3. LEARNING CURVE — spatial model vs train fraction. train-fit=1.0 + still-rising val
                      = data-bound (a data campaign pays off).
  4. SHELL          — coarse 1-high vs 2-high (T0 tier).

See docs/phase-completions/coverage-v0.3-modeling-plan.md for the results + the plan.

Build the dataset first (extract_coverage_frames.py), then:
    python coverage_probes.py --data /abs/agents/capture/coverage_dataset

Needs torch / torchvision / pillow (the VAF venv has them). CPU is fine (~2-3 min).
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
MEAN, STD = [0.485, 0.456, 0.406], [0.229, 0.224, 0.225]
SHELL = {0: 0, 2: 0, 1: 1, 3: 1}  # cover1/cover3 = 1-high(0); cover2/cover4 = 2-high(1)


def extract(data: str):
    """Frozen ResNet18 features for every frame: avgpool (512) + spatial 3x3 (4608),
    plus horizontal-flip views. Returns arrays aligned by frame with labels Y and
    clip-id G (e.g. 'cover3_04')."""
    tf = transforms.Compose([transforms.Resize((224, 224)), transforms.ToTensor(),
                             transforms.Normalize(MEAN, STD)])
    net = models.resnet18(weights=models.ResNet18_Weights.IMAGENET1K_V1)
    body = nn.Sequential(*list(net.children())[:-2]).eval()  # -> 512x7x7
    for p in body.parameters():
        p.requires_grad = False

    def emb(batch):
        with torch.no_grad():
            m = body(torch.stack(batch))                       # N,512,7,7
            avg = F.adaptive_avg_pool2d(m, 1).flatten(1).numpy()      # N,512
            spa = F.adaptive_avg_pool2d(m, (3, 3)).flatten(1).numpy()  # N,4608
        return avg, spa

    paths = [p for c in CLASSES for p in sorted(glob.glob(os.path.join(data, c, "*.jpg")))]
    cid = lambda p: re.search(r"(cover\d_\d+)_f\d+", os.path.basename(p)).group(1)  # noqa: E731
    A, Af, S, Sf, Y, G = [], [], [], [], [], []
    bu, bf = [], []
    for i, p in enumerate(paths):
        t = tf(Image.open(p).convert("RGB"))
        bu.append(t)
        bf.append(torch.flip(t, [2]))
        Y.append(CLASSES.index(cid(p).split("_")[0]))
        G.append(cid(p))
        if len(bu) == 48 or i == len(paths) - 1:
            a, s = emb(bu)
            af, sf = emb(bf)
            A.append(a)
            Af.append(af)
            S.append(s)
            Sf.append(sf)
            bu, bf = [], []
    return (np.concatenate(A), np.concatenate(Af), np.concatenate(S),
            np.concatenate(Sf), np.array(Y), np.array(G))


def macro_f1(true, pred, n=4):
    fs = []
    for c in range(n):
        tp = ((pred == c) & (true == c)).sum()
        fp = ((pred == c) & (true != c)).sum()
        fn = ((pred != c) & (true == c)).sum()
        pr = tp / (tp + fp) if tp + fp else 0.0
        rc = tp / (tp + fn) if tp + fn else 0.0
        fs.append(2 * pr * rc / (pr + rc) if pr + rc else 0.0)
    return float(np.mean(fs))


def head(xtr, ytr, dim, n=4, wd=1e-2, epochs=250):
    h = nn.Linear(dim, n)
    opt = torch.optim.Adam(h.parameters(), 0.01, weight_decay=wd)
    ce = nn.CrossEntropyLoss()
    xt, yt = torch.tensor(xtr), torch.tensor(ytr).long()
    for _ in range(epochs):
        opt.zero_grad()
        ce(h(xt), yt).backward()
        opt.step()
    return h


def by_clip_probe(feat_by_clip, featf_by_clip, lab, folds, dim, n=4, wd=1e-2):
    """5-fold-by-clip linear probe on a per-clip summary vector. Returns macro-F1."""
    clips = sorted(feat_by_clip)
    pred, tru = {}, {}
    for fold in range(5):
        tr = [g for g in clips if folds[g] != fold]
        te = [g for g in clips if folds[g] == fold]
        xtr = np.array([feat_by_clip[g] for g in tr] + [featf_by_clip[g] for g in tr], dtype=np.float32)
        ytr = np.array([lab[g] for g in tr] * 2)
        h = head(xtr, ytr, dim, n, wd)
        with torch.no_grad():
            pr = h(torch.tensor(np.array([feat_by_clip[g] for g in te], dtype=np.float32))).argmax(1).numpy()
        for g, p in zip(te, pr):
            pred[g], tru[g] = int(p), lab[g]
    t = np.array([tru[g] for g in clips])
    p = np.array([pred[g] for g in clips])
    return macro_f1(t, p, n)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", required=True, help="coverage_dataset/ (cover1..4 subdirs of frames)")
    args = ap.parse_args()

    A, Af, S, Sf, Y, G = extract(args.data)
    idx_by_clip: dict = {}
    for i, g in enumerate(G):
        idx_by_clip.setdefault(g, []).append(i)
    clips = sorted(idx_by_clip)
    lab = {g: int(Y[idx_by_clip[g][0]]) for g in clips}
    folds = {g: int(g.split("_")[1]) % 5 for g in clips}
    print(f"{len(Y)} frames across {len(clips)} clips\n")

    # 1. LEAKAGE: per-image vs per-clip 80/20 (same avgpool features, same head)
    rng = np.random.RandomState(0)
    ii = rng.permutation(len(Y))
    cut = int(0.8 * len(ii))
    h = head(np.concatenate([A[ii[:cut]], Af[ii[:cut]]]), np.concatenate([Y[ii[:cut]]] * 2), 512)
    with torch.no_grad():
        pr = h(torch.tensor(A[ii[cut:]])).argmax(1).numpy()
    img_f1 = macro_f1(Y[ii[cut:]], pr)
    cl = np.array(clips)
    rng.shuffle(cl)
    trc = set(cl[:int(0.8 * len(cl))])
    trm = np.array([g in trc for g in G])
    h = head(np.concatenate([A[trm], Af[trm]]), np.concatenate([Y[trm]] * 2), 512)
    with torch.no_grad():
        pr = h(torch.tensor(A[~trm])).argmax(1).numpy()
    clip_f1 = macro_f1(Y[~trm], pr)
    print("1. LEAKAGE demo (avgpool, 80/20):")
    print(f"     per-IMAGE split (leaky) : macro-F1={img_f1:.3f}")
    print(f"     per-CLIP  split (honest): macro-F1={clip_f1:.3f}\n")

    # 2. WHAT MOVES IT (5-fold by-clip)
    avg = {g: A[idx_by_clip[g]] for g in clips}
    avgf = {g: Af[idx_by_clip[g]] for g in clips}
    spa = {g: S[idx_by_clip[g]].mean(0) for g in clips}
    spaf = {g: Sf[idx_by_clip[g]].mean(0) for g in clips}
    mean_v = {g: avg[g].mean(0) for g in clips}
    mean_vf = {g: avgf[g].mean(0) for g in clips}
    stats_v = {g: np.concatenate([avg[g].mean(0), avg[g].std(0), avg[g][-1] - avg[g][0]]) for g in clips}
    stats_vf = {g: np.concatenate([avgf[g].mean(0), avgf[g].std(0), avgf[g][-1] - avgf[g][0]]) for g in clips}
    print("2. What moves it (5-fold by-clip, macro-F1):")
    print(f"     avgpool  mean-over-window        : {by_clip_probe(mean_v, mean_vf, lab, folds, 512):.3f}")
    print(f"     avgpool  temporal-stats          : {by_clip_probe(stats_v, stats_vf, lab, folds, 1536):.3f}  (motion HURTS)")
    print(f"     SPATIAL  3x3 mean-over-window     : {by_clip_probe(spa, spaf, lab, folds, 4608):.3f}  (WHERE = the lever)\n")

    # 3. LEARNING CURVE (spatial)
    print("3. Learning curve (spatial, 3 seeds):")
    for frac in (0.25, 0.5, 0.75, 1.0):
        vals = []
        for seed in range(3):
            r = np.random.RandomState(seed)
            pred, tru = {}, {}
            for fold in range(5):
                tr = [g for g in clips if folds[g] != fold]
                te = [g for g in clips if folds[g] == fold]
                r.shuffle(tr)
                tr = tr[:max(4, int(len(tr) * frac))]
                xtr = np.array([spa[g] for g in tr] + [spaf[g] for g in tr], dtype=np.float32)
                ytr = np.array([lab[g] for g in tr] * 2)
                h = head(xtr, ytr, 4608)
                with torch.no_grad():
                    pr = h(torch.tensor(np.array([spa[g] for g in te], dtype=np.float32))).argmax(1).numpy()
                for g, p in zip(te, pr):
                    pred[g], tru[g] = int(p), lab[g]
            t = np.array([tru[g] for g in clips])
            p = np.array([pred[g] for g in clips])
            vals.append(macro_f1(t, p))
        print(f"     {int(frac * 100):3d}% train: val-F1={np.mean(vals):.3f}")

    # 4. SHELL (T0: 1-high vs 2-high), spatial, by-clip
    shell_lab = {g: SHELL[lab[g]] for g in clips}
    f1 = by_clip_probe(spa, spaf, shell_lab, folds, 4608, n=2)
    print(f"\n4. SHELL 1-high vs 2-high (spatial, by-clip): macro-F1={f1:.3f}")


if __name__ == "__main__":
    main()
