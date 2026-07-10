"""Seed-ensemble eval for the deep-secondary region-crop coverage model.

Trains the ORIG-crop / 320 pipeline at the 3 banked seeds (1337/42/7) per fold,
averages their logits, and evaluates the ensemble on the same rotated 5-fold
clip-level CV. Reports single-seed vs ensemble macro-F1, the 16-stable-clip
check, and cover3_11's ensemble vote margin.

Framed as a production-model candidate (is the ensemble more seed-robust without
regressing?), NOT a cover3_11 rescue. New eval script — nothing baseline touched.
"""
import statistics
import sys
from pathlib import Path
from collections import defaultdict, Counter

import torch, torch.nn as nn
from torch.utils.data import DataLoader, Subset
from torchvision import transforms

sys.path.insert(0, str(Path(__file__).resolve().parent))
from train_coverage import (IMAGENET_MEAN, IMAGENET_STD, CoverageFolder,
                            build_model, clip_level_split, evaluate)

DATA = "agents/capture/coverage_dataset"
FOLDS = [{"01","06","11","16"}, {"02","07","12","17"}, {"03","08","13","18"},
         {"04","09","14","19"}, {"05","10","15","20"}]
SEEDS = [1337, 42, 7]
CROP = (0.08, 0.05, 0.92, 0.60)          # ORIG production crop
RES, LR, EPOCHS, PATIENCE, BS = 320, 1e-4, 40, 8, 16
STABLE16 = {f"cover3_{i:02d}" for i in [1,2,3,4,5,6,7,8,9,10,12,16,17,18,19,20]}
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

def _crop(img):
    w, h = img.size
    return img.crop((int(CROP[0]*w), int(CROP[1]*h), int(CROP[2]*w), int(CROP[3]*h)))
train_tf = transforms.Compose([transforms.Lambda(_crop), transforms.Resize((RES,RES)),
    transforms.RandomHorizontalFlip(), transforms.ColorJitter(0.2,0.2,0.2),
    transforms.ToTensor(), transforms.Normalize(IMAGENET_MEAN, IMAGENET_STD)])
eval_tf = transforms.Compose([transforms.Lambda(_crop), transforms.Resize((RES,RES)),
    transforms.ToTensor(), transforms.Normalize(IMAGENET_MEAN, IMAGENET_STD)])

base = CoverageFolder(DATA); classes = base.classes; n = len(classes); samples = base.samples
c3 = classes.index("cover3")
print(f"device={device.type} classes={classes} crop={CROP} res={RES} seeds={SEEDS}", flush=True)

def macro_f1(preds, trues):
    conf = [[0]*n for _ in range(n)]
    for p, t in zip(preds, trues): conf[t][p] += 1
    f1s = []
    for c in range(n):
        tp = conf[c][c]; fp = sum(conf[r][c] for r in range(n))-tp; fn = sum(conf[c])-tp
        pr = tp/(tp+fp) if tp+fp else 0.0; rc = tp/(tp+fn) if tp+fn else 0.0
        f1s.append(2*pr*rc/(pr+rc) if pr+rc else 0.0)
    return sum(f1s)/n, f1s

def train_seed(seed, train_idx, val_idx):
    torch.manual_seed(seed)
    tl = DataLoader(Subset(CoverageFolder(DATA, transform=train_tf), train_idx), batch_size=BS, shuffle=True)
    vl = DataLoader(Subset(CoverageFolder(DATA, transform=eval_tf), val_idx), batch_size=BS, shuffle=False)
    model = build_model(n, pretrained=True, unfreeze=True).to(device)
    opt = torch.optim.Adam([p for p in model.parameters() if p.requires_grad], lr=LR)
    lossf = nn.CrossEntropyLoss()
    best_f1, best_state, since = -1.0, None, 0
    for _ in range(EPOCHS):
        model.train()
        for x, y in tl:
            x, y = x.to(device), y.to(device)
            opt.zero_grad(); lossf(model(x), y).backward(); opt.step()
        _, f1, _, _ = evaluate(model, vl, device, n)
        if f1 > best_f1:
            best_f1, best_state, since = f1, {k: v.cpu().clone() for k, v in model.state_dict().items()}, 0
        else:
            since += 1
            if since >= PATIENCE: break
    model.load_state_dict(best_state)
    return model

def val_logits(model, val_idx):
    ds = CoverageFolder(DATA, transform=eval_tf); model.eval()
    L, T, C = [], [], []
    with torch.no_grad():
        for idx in val_idx:
            path, t = samples[idx]
            cid = "_".join(Path(path).stem.split("_")[:2])
            x, _ = ds[idx]
            L.append(model(x.unsqueeze(0).to(device))[0].cpu())
            T.append(t); C.append(cid)
    return torch.stack(L), T, C

single = {s: [] for s in SEEDS}; single_pc = {s: [[] for _ in range(n)] for s in SEEDS}
ens_f1s = []; ens_pc = [[] for _ in range(n)]
clip_votes = defaultdict(Counter)

for fi, ho in enumerate(FOLDS, 1):
    tr, va = clip_level_split(samples, ho)
    seed_logits = None; T = C = None
    for seed in SEEDS:
        m = train_seed(seed, tr, va)
        L, T, C = val_logits(m, va)
        sp = L.argmax(1).tolist()
        mf, pc = macro_f1(sp, T); single[seed].append(mf)
        for c in range(n): single_pc[seed][c].append(pc[c])
        seed_logits = L if seed_logits is None else seed_logits + L
    ensL = seed_logits / len(SEEDS)                 # averaged logits
    ep = ensL.argmax(1).tolist()
    mf, pc = macro_f1(ep, T); ens_f1s.append(mf)
    for c in range(n): ens_pc[c].append(pc[c])
    for pred, cid in zip(ep, C): clip_votes[cid][pred] += 1
    print(f"fold {fi} {sorted(ho)}: single{[round(single[s][-1],3) for s in SEEDS]}  ENSEMBLE={mf:.3f}", flush=True)

def ms(xs): return statistics.mean(xs), (statistics.pstdev(xs) if len(xs) > 1 else 0.0)
print("\n===== MACRO-F1 =====")
for s in SEEDS:
    print(f"  single seed {s}: mean={ms(single[s])[0]:.3f}  folds={[round(x,3) for x in single[s]]}")
sm = statistics.mean([ms(single[s])[0] for s in SEEDS])
em, es = ms(ens_f1s)
print(f"  single-seed AVG-of-means: {sm:.3f}")
print(f"  ENSEMBLE (avg logits):    mean={em:.3f} +/- {es:.3f}  folds={[round(x,3) for x in ens_f1s]}")
print("  ensemble per-class F1:", {classes[c]: round(ms(ens_pc[c])[0],3) for c in range(n)})

print("\n===== ENSEMBLE per-clip cover3 (val) =====")
stable_ok = True
for cid in sorted(k for k in clip_votes if k.startswith("cover3")):
    v = clip_votes[cid]; maj = v.most_common(1)[0][0]
    vb = ", ".join(f"{classes[k]}:{v[k]}" for k in range(n) if v[k])
    ok = maj == c3; tag = ""
    if cid in STABLE16 and not ok: stable_ok = False; tag = "  <-- STABLE-16 REGRESSED!"
    if cid in {"cover3_11","cover3_13","cover3_14","cover3_15"}: tag += "  (residual clip)"
    print(f"  {'OK' if ok else 'XX'} {cid}: ens_pred={classes[maj]:7s} [{vb}]{tag}")

print(f"\n16-STABLE all correct under ensemble? {stable_ok}")
v11 = clip_votes["cover3_11"]; maj11 = v11.most_common(1)[0][0]
top2 = v11.most_common(2)
margin = top2[0][1] - (top2[1][1] if len(top2) > 1 else 0)
print(f"cover3_11 ensemble: pred={classes[maj11]}  votes=[{', '.join(f'{classes[k]}:{v11[k]}' for k in range(n) if v11[k])}]  margin={margin}")
