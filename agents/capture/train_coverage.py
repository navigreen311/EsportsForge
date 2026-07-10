"""Coverage-classifier PROBE — transfer learning off ResNet18 on the small
post-snap coverage frame dataset.

PURPOSE: answer "is coverage learnable from this footage + rough trajectory",
NOT ship a production classifier. The dataset is tiny (~6-7 frames x 24 clips),
so this is a signal check, not a finished model. Watch the train/val gap —
overfitting is the default failure mode at this size.

NOT wired into the adapter / detect_coverage / COVERAGE_LOCKED — offline
training only, separate from the pipeline.

Approach (right-sized for a tiny set):
  - Pretrained ResNet18 backbone, FROZEN; only the final fc (512->4) is trained.
    Freezing is deliberate — fine-tuning a full CNN on ~150 images overfits
    instantly. Transfer the ImageNet features, learn only the linear head.
  - Stratified ~80/20 train/val split (per-class), seeded/reproducible.
  - Light train-time aug (h-flip + mild jitter). H-flip is defensible here:
    zone shells (Cover 2/3/4) are largely left/right symmetric; it doubles
    effective data. Remove it if you consider a coverage L/R-asymmetric.
  - Reports REAL metrics: val accuracy, per-class precision/recall/F1,
    macro-F1 (the 0.85 target), a confusion matrix, and the train/val gap.

RUN ON THE GPU BOX (RTX 5080):
    python agents/capture/train_coverage.py \
        --data /path/to/agents/capture/coverage_dataset --epochs 30
  GOTCHA: the RTX 5080 is Blackwell (sm_120) — it needs a recent CUDA torch
  build (cu128 / torch>=2.7). A stock cu121 wheel may fail with "no kernel
  image is available for execution on the device". Install e.g.:
    pip install torch torchvision --index-url https://download.pytorch.org/whl/cu128

Plumbing check only (no training, no GPU needed):
    python agents/capture/train_coverage.py --data <dir> --dry-run
"""

from __future__ import annotations

import argparse
import os
import random
from pathlib import Path

import torch
import torch.nn as nn
from torch.utils.data import DataLoader, Subset
from torchvision import datasets, models, transforms

IMAGENET_MEAN = [0.485, 0.456, 0.406]
IMAGENET_STD = [0.229, 0.224, 0.225]

# Only these are coverage classes. Anything else under the dataset root (e.g.
# the _contactsheets/ labeling aid) is NOT a class and must be ignored, or it
# poisons the label space. Caught by the dry-run when ImageFolder grabbed
# _contactsheets as a phantom 5th class.
CLASS_ALLOW = {"cover1", "cover2", "cover3", "cover4"}


class CoverageFolder(datasets.ImageFolder):
    """ImageFolder restricted to the cover1..4 classes (ignores stray dirs)."""

    def find_classes(self, directory):
        classes = sorted(
            d.name for d in os.scandir(directory) if d.is_dir() and d.name in CLASS_ALLOW
        )
        if not classes:
            raise RuntimeError(f"no cover1..4 class dirs found under {directory}")
        return classes, {c: i for i, c in enumerate(classes)}


def stratified_split(targets: list[int], val_frac: float, seed: int):
    by_class: dict[int, list[int]] = {}
    for idx, t in enumerate(targets):
        by_class.setdefault(t, []).append(idx)
    rng = random.Random(seed)
    train_idx, val_idx = [], []
    for _t, idxs in sorted(by_class.items()):
        idxs = idxs[:]
        rng.shuffle(idxs)
        n_val = max(1, round(len(idxs) * val_frac))
        val_idx += idxs[:n_val]
        train_idx += idxs[n_val:]
    return sorted(train_idx), sorted(val_idx)


def clip_level_split(samples, holdout_nums: set[str]):
    """Hold out ENTIRE clips for val so no clip appears in both sets.

    The ONLY honest split for this data: 6 frames/clip are near-identical, so a
    frame-level split leaks a play's visual signature into val and the model
    scores ~100% by memorizing plays, not learning coverage. holdout_nums like
    {"05","06"} sends cover*_05 and cover*_06 to val, the rest to train.
    """
    train_idx, val_idx = [], []
    for idx, (path, _t) in enumerate(samples):
        num = Path(path).stem.split("_")[1]  # cover3_04_f02 -> "04"
        (val_idx if num in holdout_nums else train_idx).append(idx)
    return sorted(train_idx), sorted(val_idx)


def build_model(num_classes: int, pretrained: bool, unfreeze: bool = False) -> nn.Module:
    weights = models.ResNet18_Weights.IMAGENET1K_V1 if pretrained else None
    model = models.resnet18(weights=weights)
    for p in model.parameters():        # freeze backbone
        p.requires_grad = False
    model.fc = nn.Linear(model.fc.in_features, num_classes)  # trainable head (always)
    if unfreeze:                        # fine-tune: also train the top conv block
        for p in model.layer4.parameters():
            p.requires_grad = True
    return model


@torch.no_grad()
def evaluate(model, loader, device, num_classes):
    model.eval()
    conf = [[0] * num_classes for _ in range(num_classes)]
    correct = total = 0
    for x, y in loader:
        x, y = x.to(device), y.to(device)
        pred = model(x).argmax(1)
        for t, p in zip(y.tolist(), pred.tolist()):
            conf[t][p] += 1
        correct += (pred == y).sum().item()
        total += y.numel()
    acc = correct / total if total else 0.0
    # per-class precision/recall/F1
    per = {}
    f1s = []
    for c in range(num_classes):
        tp = conf[c][c]
        fp = sum(conf[r][c] for r in range(num_classes)) - tp
        fn = sum(conf[c]) - tp
        prec = tp / (tp + fp) if tp + fp else 0.0
        rec = tp / (tp + fn) if tp + fn else 0.0
        f1 = 2 * prec * rec / (prec + rec) if prec + rec else 0.0
        per[c] = (prec, rec, f1)
        f1s.append(f1)
    macro_f1 = sum(f1s) / len(f1s) if f1s else 0.0
    return acc, macro_f1, per, conf


def main() -> int:
    ap = argparse.ArgumentParser(description="Coverage-classifier probe (transfer learning).")
    ap.add_argument("--data", type=Path, required=True, help="coverage_dataset/ (cover1..4 subdirs)")
    ap.add_argument("--epochs", type=int, default=30)
    ap.add_argument("--batch-size", type=int, default=16)
    ap.add_argument("--lr", type=float, default=1e-3)
    ap.add_argument("--val-frac", type=float, default=0.2)
    ap.add_argument("--seed", type=int, default=1337)
    ap.add_argument("--patience", type=int, default=8, help="early-stop patience on val macro-F1")
    ap.add_argument("--split", choices=["clip", "frame"], default="clip",
                    help="clip = hold out whole clips (HONEST); frame = stratified frames (LEAKS)")
    ap.add_argument("--holdout", default="05,06", help="clip numbers held out for val (clip split)")
    ap.add_argument("--unfreeze", action="store_true",
                    help="fine-tune: unfreeze layer4 + fc (default is frozen linear probe). "
                         "Use a LOWER --lr (e.g. 1e-4) and more --epochs.")
    ap.add_argument("--dry-run", action="store_true", help="load+split+one forward pass, no training")
    args = ap.parse_args()

    torch.manual_seed(args.seed)
    random.seed(args.seed)
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

    train_tf = transforms.Compose([
        transforms.Resize((224, 224)),
        transforms.RandomHorizontalFlip(),
        transforms.ColorJitter(0.2, 0.2, 0.2),
        transforms.ToTensor(),
        transforms.Normalize(IMAGENET_MEAN, IMAGENET_STD),
    ])
    eval_tf = transforms.Compose([
        transforms.Resize((224, 224)),
        transforms.ToTensor(),
        transforms.Normalize(IMAGENET_MEAN, IMAGENET_STD),
    ])

    # Two views of the same folder so train/val get different transforms.
    base = CoverageFolder(str(args.data))
    classes = base.classes
    samples = base.samples
    targets = [y for _, y in samples]

    if args.split == "clip":
        holdout = {h.strip() for h in args.holdout.split(",")}
        train_idx, val_idx = clip_level_split(samples, holdout)
        val_clips = sorted({Path(samples[i][0]).stem.rsplit("_", 1)[0] for i in val_idx})
        split_desc = f"CLIP-LEVEL, holdout=*_{{{args.holdout}}} -> val clips {val_clips}"
    else:
        train_idx, val_idx = stratified_split(targets, args.val_frac, args.seed)
        split_desc = f"FRAME-LEVEL stratified val_frac={args.val_frac} (LEAKS clips across split)"

    train_ds = Subset(CoverageFolder(str(args.data), transform=train_tf), train_idx)
    val_ds = Subset(CoverageFolder(str(args.data), transform=eval_tf), val_idx)
    train_ld = DataLoader(train_ds, batch_size=args.batch_size, shuffle=True)
    val_ld = DataLoader(val_ds, batch_size=args.batch_size, shuffle=False)

    print(f"device={device.type}  classes={classes}")
    print(f"split: {split_desc}")
    print(f"total={len(targets)}  train={len(train_idx)}  val={len(val_idx)}")
    per_class_val = {c: 0 for c in range(len(classes))}
    for i in val_idx:
        per_class_val[targets[i]] += 1
    print("val per-class:", {classes[c]: n for c, n in per_class_val.items()})

    print(f"mode: {'FINE-TUNE (layer4+fc)' if args.unfreeze else 'frozen linear probe (fc only)'}  lr={args.lr}")
    if args.dry_run:
        model = build_model(len(classes), pretrained=False, unfreeze=args.unfreeze).to(device)
        x, y = next(iter(train_ld))
        with torch.no_grad():
            out = model(x.to(device))
        print(f"[dry-run] batch x={tuple(x.shape)} logits={tuple(out.shape)} y={y.tolist()}")
        print("[dry-run] plumbing OK - data loads, split works, forward pass runs. NO training performed.")
        return 0

    model = build_model(len(classes), pretrained=True, unfreeze=args.unfreeze).to(device)
    opt = torch.optim.Adam([p for p in model.parameters() if p.requires_grad], lr=args.lr)
    lossf = nn.CrossEntropyLoss()

    best_f1, best_state, best_epoch, since = -1.0, None, -1, 0
    for epoch in range(1, args.epochs + 1):
        model.train()
        tr_correct = tr_total = 0
        for x, y in train_ld:
            x, y = x.to(device), y.to(device)
            opt.zero_grad()
            out = model(x)
            loss = lossf(out, y)
            loss.backward()
            opt.step()
            tr_correct += (out.argmax(1) == y).sum().item()
            tr_total += y.numel()
        tr_acc = tr_correct / tr_total
        val_acc, val_f1, per, conf = evaluate(model, val_ld, device, len(classes))
        print(f"epoch {epoch:2d}  train_acc={tr_acc:.3f}  val_acc={val_acc:.3f}  "
              f"val_macroF1={val_f1:.3f}  gap={tr_acc - val_acc:+.3f}")
        if val_f1 > best_f1:
            best_f1, best_epoch, since = val_f1, epoch, 0
            best_state = (val_acc, val_f1, per, conf, tr_acc)
        else:
            since += 1
            if since >= args.patience:
                print(f"early stop (no val macro-F1 gain for {args.patience} epochs)")
                break

    val_acc, val_f1, per, conf, tr_acc = best_state
    print("\n===== BEST (val macro-F1) =====")
    print(f"epoch {best_epoch}:  val_acc={val_acc:.3f}  val_macroF1={val_f1:.3f}  "
          f"train_acc={tr_acc:.3f}  train/val gap={tr_acc - val_acc:+.3f}")
    print("\nper-class (precision / recall / F1):")
    for c, name in enumerate(classes):
        p, r, f = per[c]
        print(f"  {name:8s}  P={p:.3f}  R={r:.3f}  F1={f:.3f}")
    print("\nconfusion matrix (rows=true, cols=pred):")
    print("            " + "  ".join(f"{n:>8s}" for n in classes))
    for c, name in enumerate(classes):
        print(f"  {name:8s}  " + "  ".join(f"{conf[c][k]:8d}" for k in range(len(classes))))
    print("\nPROBE — tiny val set; treat as signal + trajectory, not a final metric.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
