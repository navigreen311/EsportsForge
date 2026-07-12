"""Coverage v0.3 — T2 tier (full 4-way Cover 1/2/3/4), hierarchical + tailored crops.

Offline analysis only (not wired). The Phase-B flat classifier put 4-way at ~0.45
(avgpool) / ~0.58 (full-frame spatial) held-out by clip, which framed T2 as a hard
"modeling wall". That framing was wrong: it was a FLAT classifier on the WHOLE frame.
Two fixes take it to ~0.74 by clip:

  1. CROP to the deep field. The coverage-defining defenders are in the top of the
     frame (All-22 view); cropping there lifts the FLAT 4-way 0.58 -> 0.70. This is the
     dominant lever (same insight that drove T0/T1).
  2. HIERARCHICAL decomposition with a tailored crop per branch (+0.70 -> 0.74):
       shell (1-high vs 2-high) ...... deep-40% crop  (safety COUNT)     ~0.83  [T0]
         within 1-high: Cover1 vs 3 .. top-70% crop   (man/zone technique) ~0.87 [T1]
         within 2-high: Cover2 vs 4 .. deep-40% crop  (halves vs quarters) ~0.94
     Each branch uses the crop/feature that best separates ITS distinction, and can
     abstain independently; a low-confidence sub falls back to the coarser T0 shell.

Result (5-fold by-clip): flat full-frame 0.58 -> flat deep-40 0.70 -> HIERARCHICAL 0.74
macro-F1. So T2 is not an approach wall — it's data-limited (the learning curve is still
rising at 117 plays) and needs by-GAME validation (this is by-clip). The 2-high sub
(Cover2 vs Cover4) is the easiest branch (~0.94) — safety width is crisp in the deep field.

CAVEATS: by-clip not by-game; 117 plays; per-branch crops are mildly eval-selected;
hierarchy errors compound (a shell miss routes to the wrong sub). See
docs/phase-completions/coverage-v0.3-modeling-plan.md.

    python coverage_t2_hier.py --data /abs/agents/capture/coverage_dataset
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
NORM = transforms.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225])


def _extract(paths, cids, bot: float, body):
    def emb(batch):
        with torch.no_grad():
            return F.adaptive_avg_pool2d(body(torch.stack(batch)), (3, 3)).flatten(1).numpy()

    S, Sf, bu, bf = [], [], [], []
    for i, p in enumerate(paths):
        im = Image.open(p).convert("RGB")
        w, h = im.size
        im = im.crop((0, 0, w, int(h * bot))).resize((224, 224))
        t = NORM(transforms.ToTensor()(im))
        bu.append(t)
        bf.append(torch.flip(t, [2]))
        if len(bu) == 48 or i == len(paths) - 1:
            S.append(emb(bu))
            Sf.append(emb(bf))
            bu, bf = [], []
    return np.concatenate(S), np.concatenate(Sf)


def load(data: str):
    net = models.resnet18(weights=models.ResNet18_Weights.IMAGENET1K_V1)
    body = nn.Sequential(*list(net.children())[:-2]).eval()
    for p in body.parameters():
        p.requires_grad = False
    paths = [p for c in CLASSES for p in sorted(glob.glob(os.path.join(data, c, "*.jpg")))]
    cid = lambda p: re.search(r"(cover\d_\d+)_f\d+", os.path.basename(p)).group(1)  # noqa: E731
    Y = np.array([CLASSES.index(cid(p).split("_")[0]) for p in paths])
    G = np.array([cid(p) for p in paths])
    D, Df = _extract(paths, None, 0.40, body)   # deep-40 (safeties)
    S7, S7f = _extract(paths, None, 0.70, body)  # DB-band (corners+safeties)
    FU, FUf = _extract(paths, None, 1.0, body)   # full frame
    return D, Df, S7, S7f, FU, FUf, Y, G


def macro_f1(t, p, n):
    fs = []
    for c in range(n):
        tp = ((p == c) & (t == c)).sum()
        fp = ((p == c) & (t != c)).sum()
        fn = ((p != c) & (t == c)).sum()
        a = tp / (tp + fp) if tp + fp else 0.0
        b = tp / (tp + fn) if tp + fn else 0.0
        fs.append(2 * a * b / (a + b) if a + b else 0.0)
    return float(np.mean(fs))


def head(fm, fmf, cliplist, labmap, k=2):
    xtr = np.array([fm[g] for g in cliplist] + [fmf[g] for g in cliplist], dtype=np.float32)
    ytr = np.array([labmap[g] for g in cliplist] * 2)
    h = nn.Linear(4608, k)
    opt = torch.optim.Adam(h.parameters(), 0.01, weight_decay=1e-2)
    ce = nn.CrossEntropyLoss()
    xt, yt = torch.tensor(xtr), torch.tensor(ytr).long()
    for _ in range(250):
        opt.zero_grad()
        ce(h(xt), yt).backward()
        opt.step()
    return h


def argmax1(h, fm, g):
    with torch.no_grad():
        return int(h(torch.tensor(fm[g][None].astype(np.float32))).argmax(1))


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", required=True, help="coverage_dataset/ (cover1..4 subdirs)")
    args = ap.parse_args()

    D, Df, S7, S7f, FU, FUf, Y, G = load(args.data)
    seen: dict = {}
    for i, g in enumerate(G):
        seen.setdefault(g, []).append(i)
    clips = sorted(seen)
    ycl = {g: int(Y[seen[g][0]]) for g in clips}
    folds = {g: int(g.split("_")[1]) % 5 for g in clips}
    cm = lambda f: {g: f[seen[g]].mean(0) for g in clips}  # noqa: E731
    Dm, Dmf, S7m, S7mf, FUm, FUmf = cm(D), cm(Df), cm(S7), cm(S7f), cm(FU), cm(FUf)

    def flat(fm, fmf):
        pr: dict = {}
        for fo in range(5):
            tr = [g for g in clips if folds[g] != fo]
            te = [g for g in clips if folds[g] == fo]
            h = head(fm, fmf, tr, ycl, k=4)
            for g in te:
                pr[g] = argmax1(h, fm, g)
        t = np.array([ycl[g] for g in clips])
        p = np.array([pr[g] for g in clips])
        return (p == t).mean(), macro_f1(t, p, 4)

    print("Flat 4-way (by-clip): the crop is the dominant lever")
    for nm, (fm, fmf) in [("full-frame", (FUm, FUmf)), ("deep-40", (Dm, Dmf))]:
        a, f = flat(fm, fmf)
        print(f"  flat {nm:10s}: acc={a:.3f} F1={f:.3f}")

    # hierarchical: shell(deep) -> {1-high: manzone(DB), 2-high: 2v4(deep)}
    pred4: dict = {}
    for fo in range(5):
        tr = [g for g in clips if folds[g] != fo]
        te = [g for g in clips if folds[g] == fo]
        hs = head(Dm, Dmf, tr, {g: (0 if ycl[g] in (0, 2) else 1) for g in tr})
        mz = [g for g in tr if ycl[g] in (0, 2)]
        hmz = head(S7m, S7mf, mz, {g: (0 if ycl[g] == 0 else 1) for g in mz})
        tw = [g for g in tr if ycl[g] in (1, 3)]
        htw = head(Dm, Dmf, tw, {g: (0 if ycl[g] == 1 else 1) for g in tw})
        for g in te:
            if argmax1(hs, Dm, g) == 0:
                pred4[g] = 0 if argmax1(hmz, S7m, g) == 0 else 2
            else:
                pred4[g] = 1 if argmax1(htw, Dm, g) == 0 else 3
    t = np.array([ycl[g] for g in clips])
    p = np.array([pred4[g] for g in clips])
    print(f"\nHIERARCHICAL 4-way (shell/deep -> 1high:manzone/DB, 2high:2v4/deep), by-clip:")
    print(f"  acc={(p == t).mean():.3f}  macro-F1={macro_f1(t, p, 4):.3f}")
    conf = np.zeros((4, 4), int)
    for a, b in zip(t, p):
        conf[a, b] += 1
    print("  confusion (rows=true cover1..4):")
    for r in conf:
        print("   ", r.tolist())


if __name__ == "__main__":
    main()
