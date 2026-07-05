"""Rotated clip-level cross-validation for the coverage probe — HONEST baseline.

Runs the CURRENT frozen-ResNet18 linear-probe setup (NO model changes) across 5
rotated clip-level holdouts so every clip lands in validation exactly once, and
no clip is ever in train+val within a fold. Reports per-fold macro-F1 + val
accuracy, then mean +/- std across folds, plus per-class F1 mean +/- std. A
single split is too noisy (val swung 0.24-0.48); this is the stable baseline.

REAL runs only — offline training, nothing wired into the adapter.

Run (VAF venv or the GPU box):
    python agents/capture/crossval_coverage.py --data /abs/.../coverage_dataset
Smoke (1 fold, 2 epochs):
    python agents/capture/crossval_coverage.py --data <dir> --max-folds 1 --epochs 2
"""
from __future__ import annotations

import argparse
import statistics
import sys
from pathlib import Path

import torch
import torch.nn as nn
from torch.utils.data import DataLoader, Subset
from torchvision import transforms

sys.path.insert(0, str(Path(__file__).resolve().parent))
from train_coverage import (  # noqa: E402  (local module, path set above)
    IMAGENET_MEAN,
    IMAGENET_STD,
    CoverageFolder,
    build_model,
    clip_level_split,
    evaluate,
)

# 5-fold rotation: each clip number is held out exactly once; every fold mixes
# batch-1 (01-06, per-clip snap) and batch-2 (07+). cover1/3 span 01-15,
# cover2/4 span 01-20, so a number absent for a class is simply skipped.
FOLDS = [
    {"01", "06", "11", "16"},
    {"02", "07", "12", "17"},
    {"03", "08", "13", "18"},
    {"04", "09", "14", "19"},
    {"05", "10", "15", "20"},
]


def train_one_fold(data, holdout, n_classes, epochs, patience, lr, bs, seed, device, unfreeze=False):
    torch.manual_seed(seed)
    train_tf = transforms.Compose([
        transforms.Resize((224, 224)), transforms.RandomHorizontalFlip(),
        transforms.ColorJitter(0.2, 0.2, 0.2), transforms.ToTensor(),
        transforms.Normalize(IMAGENET_MEAN, IMAGENET_STD),
    ])
    eval_tf = transforms.Compose([
        transforms.Resize((224, 224)), transforms.ToTensor(),
        transforms.Normalize(IMAGENET_MEAN, IMAGENET_STD),
    ])
    samples = CoverageFolder(str(data)).samples
    train_idx, val_idx = clip_level_split(samples, holdout)
    train_ld = DataLoader(Subset(CoverageFolder(str(data), transform=train_tf), train_idx),
                          batch_size=bs, shuffle=True)
    val_ld = DataLoader(Subset(CoverageFolder(str(data), transform=eval_tf), val_idx),
                        batch_size=bs, shuffle=False)

    model = build_model(n_classes, pretrained=True, unfreeze=unfreeze).to(device)
    opt = torch.optim.Adam([p for p in model.parameters() if p.requires_grad], lr=lr)
    lossf = nn.CrossEntropyLoss()

    best, best_f1, since = None, -1.0, 0
    for _epoch in range(1, epochs + 1):
        model.train()
        for x, y in train_ld:
            x, y = x.to(device), y.to(device)
            opt.zero_grad()
            lossf(model(x), y).backward()
            opt.step()
        val_acc, val_f1, per, _conf = evaluate(model, val_ld, device, n_classes)
        if val_f1 > best_f1:
            best_f1, best, since = val_f1, (val_acc, val_f1, per), 0
        else:
            since += 1
            if since >= patience:
                break
    return best, len(train_idx), len(val_idx)


def main() -> int:
    ap = argparse.ArgumentParser(description="Rotated clip-level cross-val (frozen probe).")
    ap.add_argument("--data", type=Path, required=True)
    ap.add_argument("--epochs", type=int, default=30)
    ap.add_argument("--patience", type=int, default=8)
    ap.add_argument("--lr", type=float, default=1e-3)
    ap.add_argument("--batch-size", type=int, default=16)
    ap.add_argument("--seed", type=int, default=1337)
    ap.add_argument("--max-folds", type=int, default=0, help="0 = all folds (smoke: 1)")
    ap.add_argument("--unfreeze", action="store_true",
                    help="fine-tune: unfreeze layer4 + fc (default frozen probe). Use lower --lr.")
    args = ap.parse_args()

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    classes = CoverageFolder(str(args.data)).classes
    n = len(classes)
    folds = FOLDS if args.max_folds <= 0 else FOLDS[: args.max_folds]
    mode = "FINE-TUNE (layer4+fc)" if args.unfreeze else "frozen linear probe (fc only)"
    print(f"device={device.type}  classes={classes}  folds={len(folds)}  epochs={args.epochs}  "
          f"lr={args.lr}  mode={mode}", flush=True)

    accs, f1s = [], []
    per_class_f1: dict[int, list[float]] = {c: [] for c in range(n)}
    for i, ho in enumerate(folds, 1):
        (val_acc, val_f1, per), ntr, nval = train_one_fold(
            args.data, ho, n, args.epochs, args.patience, args.lr, args.batch_size, args.seed, device,
            unfreeze=args.unfreeze)
        accs.append(val_acc)
        f1s.append(val_f1)
        for c in range(n):
            per_class_f1[c].append(per[c][2])
        pf = ", ".join(f"{classes[c]}={per[c][2]:.2f}" for c in range(n))
        print(f"fold {i} holdout={sorted(ho)} (train={ntr}/val={nval}): "
              f"val_acc={val_acc:.3f}  macroF1={val_f1:.3f}  [{pf}]", flush=True)

    def ms(xs):
        return statistics.mean(xs), (statistics.pstdev(xs) if len(xs) > 1 else 0.0)

    ma, sa = ms(accs)
    mf, sf = ms(f1s)
    print(f"\n===== CROSS-VAL BASELINE (ResNet18, {mode}) =====")
    print(f"val_acc  : mean={ma:.3f} +/- {sa:.3f}   folds={[round(a, 3) for a in accs]}")
    print(f"macro-F1 : mean={mf:.3f} +/- {sf:.3f}   folds={[round(f, 3) for f in f1s]}")
    print("per-class F1 (mean +/- std across folds):")
    for c in range(n):
        m, s = ms(per_class_f1[c])
        print(f"  {classes[c]:8s} {m:.3f} +/- {s:.3f}   folds={[round(v, 2) for v in per_class_f1[c]]}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
