"""Train the Madden 26 formation classifier (M5c sub-task 4).

MobileNetV3-Small (ImageNet-pretrained) -> 8-way head. Features frozen for the
first FREEZE_EPOCHS, then fine-tuned. Class-weighted CrossEntropy (the rare
classes are <100 in train). Adam + ReduceLROnPlateau on val macro-F1. Early
stop on val-macro-F1 plateau. Reproducible (seeds + deterministic algorithms).

Outputs:
  services/visionaudioforge/app/adapters/madden26/models/formation_v0_1.pt  (best ckpt)
  agents/capture/fixtures/real/train_log.json                               (metrics)
"""

from __future__ import annotations

import json
import platform
import random
import sys
import time
from pathlib import Path

import numpy as np
import torch
import torch.nn as nn
from torch.utils.data import DataLoader
from torchvision.models import mobilenet_v3_small, MobileNet_V3_Small_Weights

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))  # services/visionaudioforge on path
from training.dataset import (FormationDataset, build_cache, class_weights,  # noqa: E402
                              TOP8, INPUT_SIZE)
from training.augment import TrainAugment, NoAugment  # noqa: E402

REPO_ROOT = HERE.parents[2]
MODELS_DIR = REPO_ROOT / "services" / "visionaudioforge" / "app" / "adapters" / "madden26" / "models"
CKPT = MODELS_DIR / "formation_v0_1.pt"
LOG = REPO_ROOT / "agents" / "capture" / "fixtures" / "real" / "train_log.json"

SEED = 42
BATCH = 32
LR = 1e-3
MAX_EPOCHS = 30
FREEZE_EPOCHS = 5
PATIENCE = 6


def seed_everything():
    random.seed(SEED); np.random.seed(SEED); torch.manual_seed(SEED)
    torch.use_deterministic_algorithms(True, warn_only=True)


def build_model() -> nn.Module:
    m = mobilenet_v3_small(weights=MobileNet_V3_Small_Weights.IMAGENET1K_V1)
    in_f = m.classifier[3].in_features
    m.classifier[3] = nn.Linear(in_f, len(TOP8))
    return m


def macro_f1(conf: np.ndarray) -> tuple[float, list[dict]]:
    per = []
    f1s = []
    for i in range(len(TOP8)):
        tp = conf[i, i]
        fp = conf[:, i].sum() - tp
        fn = conf[i, :].sum() - tp
        p = tp / (tp + fp) if tp + fp else 0.0
        r = tp / (tp + fn) if tp + fn else 0.0
        f1 = 2 * p * r / (p + r) if p + r else 0.0
        f1s.append(f1)
        per.append({"class": TOP8[i], "precision": round(p, 3), "recall": round(r, 3),
                    "f1": round(f1, 3), "support": int(conf[i, :].sum())})
    return float(np.mean(f1s)), per


@torch.no_grad()
def evaluate(model, loader, device) -> tuple[float, np.ndarray, float]:
    model.eval()
    conf = np.zeros((len(TOP8), len(TOP8)), dtype=np.int64)
    loss_sum, n = 0.0, 0
    crit = nn.CrossEntropyLoss()
    for x, y in loader:
        x, y = x.to(device), y.to(device)
        out = model(x)
        loss_sum += crit(out, y).item() * len(y); n += len(y)
        for t, p in zip(y.cpu().numpy(), out.argmax(1).cpu().numpy()):
            conf[t, p] += 1
    mf1, _ = macro_f1(conf)
    return mf1, conf, loss_sum / max(n, 1)


def main() -> int:
    t0 = time.monotonic()
    seed_everything()
    device = torch.device("cpu")
    print("ensuring frame cache…")
    build_cache(verbose=True)

    train_ds = FormationDataset("train", transform=TrainAugment(SEED))
    val_ds = FormationDataset("val", transform=NoAugment())
    test_ds = FormationDataset("test", transform=NoAugment())
    print(f"train {len(train_ds)}  val {len(val_ds)}  test {len(test_ds)}")
    train_dl = DataLoader(train_ds, batch_size=BATCH, shuffle=True, num_workers=0, drop_last=False)
    val_dl = DataLoader(val_ds, batch_size=BATCH, num_workers=0)
    test_dl = DataLoader(test_ds, batch_size=BATCH, num_workers=0)

    model = build_model().to(device)
    weights = class_weights("train").to(device)
    crit = nn.CrossEntropyLoss(weight=weights)
    opt = torch.optim.Adam(model.parameters(), lr=LR)
    sched = torch.optim.lr_scheduler.ReduceLROnPlateau(opt, mode="max", factor=0.5, patience=3)

    history, best_f1, best_state, bad = [], -1.0, None, 0
    for epoch in range(1, MAX_EPOCHS + 1):
        if epoch <= FREEZE_EPOCHS:
            model.features.requires_grad_(False)
        else:
            model.features.requires_grad_(True)
        model.train()
        tl, n = 0.0, 0
        for x, y in train_dl:
            x, y = x.to(device), y.to(device)
            opt.zero_grad()
            loss = crit(model(x), y)
            loss.backward(); opt.step()
            tl += loss.item() * len(y); n += len(y)
        train_loss = tl / max(n, 1)
        val_f1, _, val_loss = evaluate(model, val_dl, device)
        sched.step(val_f1)
        lr_now = opt.param_groups[0]["lr"]
        history.append({"epoch": epoch, "train_loss": round(train_loss, 4),
                        "val_loss": round(val_loss, 4), "val_macro_f1": round(val_f1, 4),
                        "lr": lr_now, "frozen": epoch <= FREEZE_EPOCHS})
        print(f"epoch {epoch:2d}  train_loss {train_loss:.4f}  val_loss {val_loss:.4f}  "
              f"val_macroF1 {val_f1:.4f}  lr {lr_now:.1e}{'  [frozen]' if epoch<=FREEZE_EPOCHS else ''}")
        if val_f1 > best_f1:
            best_f1 = val_f1
            best_state = {k: v.cpu().clone() for k, v in model.state_dict().items()}
            bad = 0
        else:
            bad += 1
            if bad >= PATIENCE:
                print(f"early stop (no val improvement in {PATIENCE} epochs)")
                break

    model.load_state_dict(best_state)
    MODELS_DIR.mkdir(parents=True, exist_ok=True)
    torch.save(best_state, CKPT)
    test_f1, test_conf, test_loss = evaluate(model, test_dl, device)
    val_f1, val_conf, _ = evaluate(model, val_dl, device)
    _, test_per = macro_f1(test_conf)
    _, val_per = macro_f1(val_conf)

    log = {
        "milestone": "M5c sub-task 4",
        "model": "mobilenet_v3_small (ImageNet pretrained, 8-way head)",
        "hyperparams": {"seed": SEED, "batch": BATCH, "lr": LR, "max_epochs": MAX_EPOCHS,
                        "freeze_epochs": FREEZE_EPOCHS, "patience": PATIENCE,
                        "input_size": INPUT_SIZE, "class_weighted_loss": True,
                        "augment": "rot+-5,bright+-15%,jitter+-5%,no-hflip"},
        "environment": {"python": platform.python_version(), "torch": torch.__version__,
                        "torchvision": __import__("torchvision").__version__, "device": "cpu"},
        "epochs_run": len(history), "best_val_macro_f1": round(best_f1, 4),
        "history": history,
        "final": {"val_macro_f1": round(val_f1, 4), "test_macro_f1": round(test_f1, 4),
                  "test_loss": round(test_loss, 4),
                  "test_per_class": test_per, "val_per_class": val_per,
                  "test_confusion": test_conf.tolist()},
        "elapsed_sec": round(time.monotonic() - t0, 1),
        "checkpoint": str(CKPT.relative_to(REPO_ROOT)).replace("\\", "/"),
    }
    LOG.write_text(json.dumps(log, indent=2))
    print(f"\nBEST val macro-F1 {best_f1:.4f} | TEST macro-F1 {test_f1:.4f}")
    print("test per-class:")
    for pc in test_per:
        print(f"  {pc['class']:18} P {pc['precision']:.2f} R {pc['recall']:.2f} "
              f"F1 {pc['f1']:.2f}  (support {pc['support']})")
    print(f"\nckpt -> {CKPT}\nlog  -> {LOG}\nelapsed {log['elapsed_sec']}s")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
