"""Build the match-level-disjoint train/val/test split (M5c sub-task 3).

Split is BY CLIP (never by frame — consecutive frames within a play are nearly
identical and would leak). Design, given the dataset's shape:

  * The 8 practice clips are each a single formation. They go entirely to
    TRAIN so the model LEARNS every class from clean, balanced labels. Putting
    a single-formation practice clip in val/test would either test only one
    class or starve train of that class.
  * VAL and TEST are held-out MATCHUP clips — real-game frames, the realistic
    evaluation surface. They are chosen to spread class coverage as much as the
    thin matchup data allows.

Hard data limit (documented, not hidden): CPU-vs-CPU footage is sparse and
uneven for the rare formations — pistol_strong has only 15 matchup labels
total, and empty/i_form/ace/doubles are also thin — so the plan's "≥15 per
class per split" is NOT achievable in val/test for those classes. Per-class
support is emitted so sub-task 5 can caveat low-support F1 numbers.

Output: agents/capture/fixtures/real/formation_split.json
"""

from __future__ import annotations

import csv
import json
from collections import Counter, defaultdict
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
FX = REPO_ROOT / "agents" / "capture" / "fixtures" / "real"
LABELS = FX / "formation_labels.csv"
OUT = FX / "formation_split.json"

TOP8 = ["shotgun_trips", "shotgun_bunch", "shotgun_empty", "i_form_pro",
        "singleback_ace", "pistol_strong", "shotgun_doubles", "singleback_wing"]

# Held-out matchup clips. Chosen so val and test each span all 8 classes as far
# as the data allows (buf carries ace/pistol/i_form; lac carries doubles; chi
# carries doubles/wing; kc carries empty/i_form/ace). Everything else trains.
VAL_CLIPS = ["madden26_buf_vs_mia_q1.mp4", "madden26_lac_vs_sea_q4.mp4"]
TEST_CLIPS = ["madden26_chi_vs_hou_q4.mp4", "madden26_kc_vs_phi._q1.mp4"]


def main() -> int:
    rows = [r for r in csv.DictReader(LABELS.open(newline=""))
            if r["formation_class"] != "skip"]
    clips = sorted({r["clip"] for r in rows})
    practice = [c for c in clips if "practice" in c]
    matchup = [c for c in clips if "practice" not in c]
    held = set(VAL_CLIPS) | set(TEST_CLIPS)
    assert held <= set(matchup), f"held-out clips not all matchup: {held - set(matchup)}"

    train_clips = sorted([c for c in clips if c not in held])  # all practice + remaining matchup
    split_of = {c: "train" for c in train_clips}
    split_of.update({c: "val" for c in VAL_CLIPS})
    split_of.update({c: "test" for c in TEST_CLIPS})

    counts = {s: Counter() for s in ("train", "val", "test")}
    for r in rows:
        counts[split_of[r["clip"]]][r["formation_class"]] += 1

    per_split = {s: {f: counts[s][f] for f in TOP8} for s in ("train", "val", "test")}
    split = {
        "version": "1.0.0",
        "milestone": "M5c sub-task 3",
        "method": "match-level disjoint, by clip (never by frame)",
        "design": ("8 practice clips (single-formation) -> train so the model learns "
                   "every class; val/test are held-out MATCHUP clips for real-game eval"),
        "train_clips": train_clips,
        "val_clips": VAL_CLIPS,
        "test_clips": TEST_CLIPS,
        "clip_counts": {"train": len(train_clips), "val": len(VAL_CLIPS), "test": len(TEST_CLIPS),
                        "train_practice": len([c for c in train_clips if "practice" in c]),
                        "train_matchup": len([c for c in train_clips if "practice" not in c])},
        "per_split_class_counts": per_split,
        "per_split_totals": {s: sum(per_split[s].values()) for s in per_split},
        "low_support_warning": {
            "threshold": 15,
            "note": ("matchup footage is sparse/uneven for rare formations; "
                     "val/test cannot hit >=15 for these. Caveat low-support F1 in sub-task 5."),
            "below_15": {s: [f for f in TOP8 if per_split[s][f] < 15 and s in ("val", "test")]
                         for s in ("val", "test")},
        },
    }
    OUT.write_text(json.dumps(split, indent=2))

    # Console report.
    print(f"clips: {len(train_clips)} train ({split['clip_counts']['train_practice']} practice "
          f"+ {split['clip_counts']['train_matchup']} matchup), "
          f"{len(VAL_CLIPS)} val, {len(TEST_CLIPS)} test")
    print(f"\n{'formation':18}{'train':>8}{'val':>6}{'test':>6}")
    for f in TOP8:
        print(f"{f:18}{per_split['train'][f]:>8}{per_split['val'][f]:>6}{per_split['test'][f]:>6}")
    print(f"{'TOTAL':18}{split['per_split_totals']['train']:>8}"
          f"{split['per_split_totals']['val']:>6}{split['per_split_totals']['test']:>6}")
    print(f"\nval classes <15:  {split['low_support_warning']['below_15']['val']}")
    print(f"test classes <15: {split['low_support_warning']['below_15']['test']}")
    print(f"\n-> {OUT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
