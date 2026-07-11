"""Standalone evaluation harness for digit_reader.py — reproduces the held-out
game-clock-seconds result banked in docs/phase-completions/digit-ocr-reader-result.md.

NOT a unit test and NOT wired into anything. Run manually:

    python -m app.adapters.madden26.digit_reader_eval

Requires the target-style capture frames, which live OUTSIDE the repo per the
`~/madden-recal-refs` convention (524 x 1080p PNGs, ~145 MB). Set CAMPAIGN_DIR if
they live elsewhere. Ground-truth clock-seconds labels ship in
digit_templates/gcsec_labels.json (frame index -> 2-char value); distance GT is the
folder name (ts_<down>_and_<distance>).

Split is DISJOINT BY VIEW: consecutive same-value frames form one "view" (a single
clock reading, whose frames are near-duplicates); whole views go to train / val /
eval by index % 3, so no near-duplicate leaks across the split. Thresholds are frozen
on the validation split before the held-out eval is scored.
"""

from __future__ import annotations

import glob
import json
import os
import statistics

import cv2
import numpy as np

from .digit_reader import (
    GCSEC,
    DigitReader,
    field_present,
    is_corrupt,
    segment,
    vec,
)

CAMPAIGN_DIR = os.environ.get(
    "DIGIT_CAMPAIGN_DIR", r"C:/Users/ivann/madden-recal-refs/digit-campaign"
)
HERE = os.path.dirname(__file__)
LABELS = os.path.join(HERE, "digit_templates", "gcsec_labels.json")
CLK = os.path.join(CAMPAIGN_DIR, "ts_clock_run")


def _fp(idx: int) -> str:
    return os.path.join(CLK, f"ts_clock_run_{idx:03d}.png")


def _views(frame_gt: dict[str, str]) -> list[list[int]]:
    """Group consecutive same-value frames into views (one clock reading each)."""
    idxs = sorted(int(k) for k in frame_gt)
    views: list[list[int]] = []
    cur: list[int] = []
    for i in idxs:
        if cur and (i - cur[-1] > 2 or frame_gt[str(i)] != frame_gt[str(cur[-1])]):
            views.append(cur)
            cur = []
        cur.append(i)
    if cur:
        views.append(cur)
    return views


def _collect(view_list, frame_gt):
    items = []
    for view in view_list:
        for m in view:
            im = cv2.imread(_fp(m))
            if im is None or is_corrupt(im, GCSEC):
                continue
            gs = segment(im, GCSEC)
            if gs is None:
                continue
            for g, d in zip(gs, frame_gt[str(m)]):
                items.append((vec(g), d, m))
    return items


def main() -> None:
    frame_gt = json.load(open(LABELS))
    views = _views(frame_gt)
    train_v = [v for i, v in enumerate(views) if i % 3 == 2]
    val_v = [v for i, v in enumerate(views) if i % 3 == 1]
    eval_v = [v for i, v in enumerate(views) if i % 3 == 0]
    train, valset, evalset = (
        _collect(train_v, frame_gt),
        _collect(val_v, frame_gt),
        _collect(eval_v, frame_gt),
    )
    reader = DigitReader(GCSEC)
    reader.build([(v, d) for v, d, _ in train])

    # reject frames: gcsec field genuinely absent/corrupt
    reject = []
    for f in sorted(glob.glob(f"{CLK}/*.png")):
        idx = int(os.path.basename(f).split("_")[-1].split(".")[0])
        if str(idx) in frame_gt:
            continue
        im = cv2.imread(f)
        if im.mean() < 60 or is_corrupt(im, GCSEC) or not field_present(im, GCSEC):
            reject.append(f)
    for folder in glob.glob(f"{CAMPAIGN_DIR}/ts_*_and_*"):
        for f in glob.glob(f"{folder}/*.png"):
            if is_corrupt(cv2.imread(f), GCSEC):
                reject.append(f)

    # freeze thresholds on validation (never-fabricate-first)
    def score(items, tau, delta):
        c = t = 0
        for v, d, _ in items:
            r = reader.classify(v)
            if r.best < tau or r.margin < delta:
                continue
            t += 1
            c += r.digit == d
        return c, t

    def abstains(im, tau, delta):
        if im is None or is_corrupt(im, GCSEC) or not field_present(im, GCSEC):
            return True
        gs = segment(im, GCSEC)
        if gs is None:
            return True
        for g in gs:
            r = reader.classify(vec(g))
            if r.best < tau or r.margin < delta:
                return True
        return False

    rej_ims = [cv2.imread(f) for f in reject]
    best = None
    for tau in [0.55, 0.60, 0.65, 0.70, 0.75, 0.80]:
        for delta in [0.02, 0.05, 0.10]:
            c, t = score(valset, tau, delta)
            leaks = sum(1 for im in rej_ims if not abstains(im, tau, delta))
            key = (-(t - c), -leaks, t)
            if best is None or key > best[0]:
                best = (key, tau, delta)
    assert best is not None  # both loops run >=1 iteration, so best is always set
    _, TAU, DELTA = best
    reader.tau, reader.delta = TAU, DELTA
    print(f"views: train={len(train_v)} val={len(val_v)} eval={len(eval_v)}")
    print(f"FROZEN tau={TAU} delta={DELTA}")

    # held-out 1-vs-7
    ones = [v for v, d, _ in evalset if d == "1"]
    sevens = [v for v, d, _ in evalset if d == "7"]
    c17 = sum(1 for v in ones if reader.classify(v).digit == "7")
    c71 = sum(1 for v in sevens if reader.classify(v).digit == "1")
    print("\n=== gcsec 1-vs-7 (HELD-OUT) ===")
    print(f"  true-1 read as 7: {c17}/{len(ones)}   (M={len(ones)})")
    print(f"  true-7 read as 1: {c71}/{len(sevens)}   (N={len(sevens)})")
    if sevens:
        t7 = [float(np.dot(v, reader.means["7"])) for v in sevens]
        t1 = [float(np.dot(v, reader.means["1"])) for v in sevens]
        print(f"  held-out 7s NCC: vs 7-tmpl={statistics.mean(t7):.2f} vs 1-tmpl={statistics.mean(t1):.2f}")

    # per-digit
    per: dict[str, list[int]] = {}
    for v, d, _ in evalset:
        r = reader.classify(v)
        ab = r.best < TAU or r.margin < DELTA
        per.setdefault(d, [0, 0, 0])
        if ab:
            per[d][2] += 1
        elif r.digit == d:
            per[d][0] += 1
        else:
            per[d][1] += 1
    print("\n=== per-digit (HELD-OUT): correct | wrong | abstain ===")
    for d in "0123456789":
        if d in per:
            print(f"  {d}: {per[d][0]} | {per[d][1]} | {per[d][2]}")
    tot = [sum(x) for x in zip(*per.values())]
    print(f"  OVERALL: {tot[0]} correct | {tot[1]} wrong | {tot[2]} abstain")

    # reject
    leaks = sum(1 for im in rej_ims if reader.read(im)[0] is not None)
    print(f"\n=== reject set: {len(reject) - leaks}/{len(reject)} abstained ({leaks} leaks) ===")


if __name__ == "__main__":
    main()
