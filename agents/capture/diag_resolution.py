"""Option-A evaluation: rotated 5-fold clip-level cross-val (SAME config as
crossval_coverage.py --unfreeze --lr 1e-4 --epochs 40, seed 1337) PLUS the
per-clip Cover-3 confusion breakdown (C3->C4 count) — the Option-A answer.

Reproduces the canonical crossval metrics exactly AND reports which held-out
Cover-3 clips are misclassified and as what. One run = headline + diagnosis.

Run on the 5080:
    .venv-cu128/Scripts/python.exe agents/capture/diag_option_a.py \
        --data agents/capture/coverage_dataset
"""
import argparse
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

FOLDS = [{"01","06","11","16"}, {"02","07","12","17"}, {"03","08","13","18"},
         {"04","09","14","19"}, {"05","10","15","20"}]

ap = argparse.ArgumentParser()
ap.add_argument("--data", type=Path, required=True)
ap.add_argument("--epochs", type=int, default=40)
ap.add_argument("--lr", type=float, default=1e-4)
ap.add_argument("--patience", type=int, default=8)
ap.add_argument("--batch-size", type=int, default=16)
ap.add_argument("--seed", type=int, default=1337)
ap.add_argument("--resize", type=int, default=320, help="input square resolution (baseline=224, Variant A=320/384)")
args = ap.parse_args()
RES = args.resize

device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
train_tf = transforms.Compose([transforms.Resize((RES,RES)), transforms.RandomHorizontalFlip(),
                               transforms.ColorJitter(0.2,0.2,0.2), transforms.ToTensor(),
                               transforms.Normalize(IMAGENET_MEAN, IMAGENET_STD)])
eval_tf = transforms.Compose([transforms.Resize((RES,RES)), transforms.ToTensor(),
                              transforms.Normalize(IMAGENET_MEAN, IMAGENET_STD)])
base = CoverageFolder(str(args.data)); classes = base.classes; n = len(classes); samples = base.samples
c3 = classes.index("cover3")
print(f"device={device.type}  classes={classes}  mode=FINE-TUNE (layer4+fc)  "
      f"lr={args.lr}  epochs={args.epochs}  seed={args.seed}  INPUT_RES={RES}", flush=True)

accs, f1s = [], []
per_class_f1 = {c: [] for c in range(n)}
allwrong = []; conf_dir = Counter()

for fi, ho in enumerate(FOLDS, 1):
    torch.manual_seed(args.seed)
    tr, va = clip_level_split(samples, ho)
    train_ld = DataLoader(Subset(CoverageFolder(str(args.data), transform=train_tf), tr), batch_size=args.batch_size, shuffle=True)
    val_ld = DataLoader(Subset(CoverageFolder(str(args.data), transform=eval_tf), va), batch_size=args.batch_size, shuffle=False)
    model = build_model(n, pretrained=True, unfreeze=True).to(device)
    opt = torch.optim.Adam([p for p in model.parameters() if p.requires_grad], lr=args.lr)
    lossf = nn.CrossEntropyLoss()
    best_f1, best_state, since = -1.0, None, 0
    for _ in range(1, args.epochs + 1):
        model.train()
        for x, y in train_ld:
            x, y = x.to(device), y.to(device)
            opt.zero_grad(); lossf(model(x), y).backward(); opt.step()
        acc, f1, per, _ = evaluate(model, val_ld, device, n)
        if f1 > best_f1:
            best_f1, best_state, since = f1, {k: v.cpu().clone() for k, v in model.state_dict().items()}, 0
        else:
            since += 1
            if since >= args.patience:
                break
    model.load_state_dict(best_state); model.eval()
    acc, f1, per, _ = evaluate(model, val_ld, device, n)
    accs.append(acc); f1s.append(f1)
    for c in range(n):
        per_class_f1[c].append(per[c][2])
    # per-clip Cover-3 predictions
    val_ds = CoverageFolder(str(args.data), transform=eval_tf)
    clip_votes = defaultdict(Counter)
    with torch.no_grad():
        for idx in va:
            path, t = samples[idx]
            cid = "_".join(Path(path).stem.split("_")[:2])
            if not cid.startswith("cover3"):
                continue
            p = int(model(val_ds[idx][0].unsqueeze(0).to(device)).argmax(1).item())
            clip_votes[cid][p] += 1
    pf = ", ".join(f"{classes[c]}={per[c][2]:.2f}" for c in range(n))
    print(f"\nfold {fi} holdout={sorted(ho)}: val_acc={acc:.3f} macroF1={f1:.3f} [{pf}]", flush=True)
    for cid in sorted(clip_votes):
        votes = clip_votes[cid]; maj = votes.most_common(1)[0][0]
        vb = ", ".join(f"{classes[k]}:{votes[k]}" for k in range(n) if votes[k])
        ok = maj == c3
        print(f"    {'OK' if ok else 'XX'} {cid}: pred={classes[maj]:7s} [{vb}]", flush=True)
        if not ok:
            allwrong.append((cid, classes[maj])); conf_dir[classes[maj]] += 1

def ms(xs): return statistics.mean(xs), (statistics.pstdev(xs) if len(xs) > 1 else 0.0)
mf, sf = ms(f1s); ma, sa = ms(accs)
print("\n===== CROSS-VAL (ResNet18 fine-tune, 5-fold clip-level) =====")
print(f"val_acc  : mean={ma:.3f} +/- {sa:.3f}  folds={[round(a,3) for a in accs]}")
print(f"macro-F1 : mean={mf:.3f} +/- {sf:.3f}  folds={[round(f,3) for f in f1s]}")
print("per-class F1 (mean +/- std):")
for c in range(n):
    m, s = ms(per_class_f1[c])
    print(f"  {classes[c]:8s} {m:.3f} +/- {s:.3f}  folds={[round(v,2) for v in per_class_f1[c]]}")
print("\n===== COVER-3 CONFUSION (the Option-A answer) =====")
print(f"misclassified cover3 clips ({len(allwrong)} of 20 held-out):")
for cid, pred in sorted(allwrong):
    print(f"  {cid} -> {pred}")
print(f"confusion-direction tally: {dict(conf_dir)}")
print(f">>> C3->C4: {conf_dir['cover4']} of {len(allwrong)} misses   (PRIOR round-3: 4 of 7)")
