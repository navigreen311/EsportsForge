"""FormationDataset + frame-cache extraction (M5c sub-task 4).

The labeled frames live inside the gitignored capture clips at specific frame
indices. Seeking the multi-GB clips per sample per epoch would be hopelessly
slow, so frames are extracted ONCE to a gitignored on-disk cache (the formation
crop, resized to CACHE_SIZE) and the dataset loads from there.

Input region: a fixed central crop of the play area (the offense lines up in the
upper-centre under Madden's behind-offense camera), resized square. This focuses
the classifier on the on-field formation and drops crowd / sky / HUD. It is a
deliberate, documented choice — the first thing to revisit if accuracy is poor.
"""

from __future__ import annotations

import csv
import json
from pathlib import Path

import cv2
import numpy as np
import torch
from torch.utils.data import Dataset

REPO_ROOT = Path(__file__).resolve().parents[3]
FX = REPO_ROOT / "agents" / "capture" / "fixtures" / "real"
LABELS = FX / "formation_labels.csv"
SPLIT = FX / "formation_split.json"
CACHE = Path(__file__).resolve().parent / ".frame_cache"   # gitignored

# Central play-area crop (x0, y0, x1, y1) on the 1920x1080 frame, then square-resized.
CROP = (240, 80, 1520, 680)
CACHE_SIZE = 256          # cached square size; transforms crop/resize to 224
INPUT_SIZE = 224

TOP8 = ("shotgun_trips", "shotgun_bunch", "shotgun_empty", "i_form_pro",
        "singleback_ace", "pistol_strong", "shotgun_doubles", "singleback_wing")
CLASS_TO_IDX = {c: i for i, c in enumerate(TOP8)}
IMAGENET_MEAN = np.array([0.485, 0.456, 0.406], dtype=np.float32)
IMAGENET_STD = np.array([0.229, 0.224, 0.225], dtype=np.float32)


def _cache_name(clip: str, frame_idx: int) -> str:
    return f"{Path(clip).stem}_f{frame_idx:06d}.jpg"


def build_cache(verbose: bool = True) -> int:
    """Extract every labeled (non-skip) frame's crop to the cache. Idempotent."""
    CACHE.mkdir(parents=True, exist_ok=True)
    rows = [r for r in csv.DictReader(LABELS.open(newline="")) if r["formation_class"] != "skip"]
    by_clip: dict[str, list[dict]] = {}
    for r in rows:
        by_clip.setdefault(r["clip"], []).append(r)
    x0, y0, x1, y1 = CROP
    written = 0
    for clip, items in sorted(by_clip.items()):
        todo = [r for r in items if not (CACHE / _cache_name(clip, int(r["frame_idx"]))).exists()]
        if not todo:
            continue
        cap = cv2.VideoCapture(str(FX / clip))
        for r in sorted(todo, key=lambda r: int(r["frame_idx"])):
            idx = int(r["frame_idx"])
            cap.set(cv2.CAP_PROP_POS_FRAMES, idx)
            ok, frame = cap.read()
            if not ok or frame is None:
                continue
            crop = cv2.resize(frame[y0:y1, x0:x1], (CACHE_SIZE, CACHE_SIZE))
            cv2.imwrite(str(CACHE / _cache_name(clip, idx)), crop, [cv2.IMWRITE_JPEG_QUALITY, 92])
            written += 1
        cap.release()
        if verbose:
            print(f"  cached {clip}")
    if verbose:
        print(f"cache ready: {written} new frames -> {CACHE}")
    return written


def _load_split() -> dict:
    return json.loads(SPLIT.read_text())


def split_clip_sets() -> dict[str, set]:
    s = _load_split()
    return {"train": set(s["train_clips"]), "val": set(s["val_clips"]), "test": set(s["test_clips"])}


def class_weights(split: str = "train") -> torch.Tensor:
    """Inverse-frequency class weights from the split's per-class train counts."""
    counts = _load_split()["per_split_class_counts"][split]
    freq = np.array([counts[c] for c in TOP8], dtype=np.float32)
    w = freq.sum() / (len(TOP8) * np.maximum(freq, 1.0))
    return torch.tensor(w, dtype=torch.float32)


class FormationDataset(Dataset):
    def __init__(self, split: str, transform=None):
        self.transform = transform
        clip_set = split_clip_sets()[split]
        rows = [r for r in csv.DictReader(LABELS.open(newline=""))
                if r["formation_class"] != "skip" and r["clip"] in clip_set]
        self.items = [(_cache_name(r["clip"], int(r["frame_idx"])),
                       CLASS_TO_IDX[r["formation_class"]],
                       r["label_quality"]) for r in rows]

    def __len__(self) -> int:
        return len(self.items)

    def __getitem__(self, i):
        name, label, _q = self.items[i]
        img = cv2.cvtColor(cv2.imread(str(CACHE / name)), cv2.COLOR_BGR2RGB)
        if self.transform is not None:
            img = self.transform(img)            # augment: np.uint8 HxWx3 -> np.uint8
        img = cv2.resize(img, (INPUT_SIZE, INPUT_SIZE)).astype(np.float32) / 255.0
        img = (img - IMAGENET_MEAN) / IMAGENET_STD
        tensor = torch.from_numpy(img.transpose(2, 0, 1).copy())
        return tensor, label


if __name__ == "__main__":
    build_cache()
