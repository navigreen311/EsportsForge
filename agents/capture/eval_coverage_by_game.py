"""By-game (group-held-out) eval for the coverage OCR reader (`read_coverage`).

Runs the REAL `OCRPipeline.read_coverage` over labeled coach-cam clips grouped by
GAME, and reports per-game / held-out accuracy, a confusion matrix, and held-out
macro-F1 — the group-held-out check the shipped OCR reader has never had. It was
tuned + validated on ONE ~44-min session (`cov_cc_*`); robustness across games is
unestablished (see docs/phase-completions/coverage-ocr-playcall-pivot.md and the
[[feedback_ml_eval_hygiene]] rule: reproduce a metric with a GROUP-held-out split
before building on it). ADR 0010 gates Phase 1c on held-out macro-F1 >= 0.85.

Each clip is one committed coverage (one play); the shipped adapter mode-votes the
coverage across the pre-snap window into one COVERAGE_LOCKED, so the honest unit is
the CLIP: predict = the mode of the clip's non-null frame reads (abstain if all null).

Layout expected under --root:
    cov_<game>_<coverage>/<clip>.mp4        (e.g. cov_g1_cover3/cov_g1_cover3.mp4)
    cov_<game>_<coverage>/frame_*.png       (pre-extracted frames also accepted)
Game "cc" is the tuning session (in-sample) by default; the held-out report EXCLUDES
it. Dirs whose <coverage> suffix isn't mapped below are SKIPPED and listed (never
silently dropped).

Run from services/visionaudioforge with that venv so `app` imports resolve:
    cd services/visionaudioforge
    PYTHONPATH="$PWD" .venv/Scripts/python.exe \
        ../../agents/capture/eval_coverage_by_game.py \
        --root C:/Users/ivann/madden-recal-refs/digit-campaign [--tuning-game cc]
"""

from __future__ import annotations

import argparse
import sys
from collections import Counter, defaultdict
from dataclasses import dataclass
from pathlib import Path

import cv2

from app.adapters.madden26.ocr_pipeline import OCRPipeline


@dataclass
class ClipResult:
    game: str
    label: str
    pred: str | None
    n_frames: int
    n_read: int
    dirname: str


# <coverage> dir-suffix -> canonical coverage the classifier is expected to emit.
# Tampa 2 and Cover 2-Invert fold to "Cover 2" by design (ADR 0017 — label-identical
# to Cover 2 without route geometry); "c3slimpress" is a Cover 3 family member.
LABEL_MAP = {
    "cover0": "Cover 0", "cover1": "Cover 1", "cover2": "Cover 2",
    "cover2man": "Cover 2-Man", "cover3": "Cover 3",
    "cover4": "Cover 4 (Quarters)",  # classifier's exact canonical for the 4-deep shell
    "cover6": "Cover 6", "cover9": "Cover 9",
    "tampa2": "Cover 2", "cover2invert": "Cover 2", "cover2invert_b": "Cover 2",
    "c3slimpress": "Cover 3", "rec2": "Cover 2",
}


def _label_for(suffix: str) -> str | None:
    return LABEL_MAP.get(suffix)


def _parse_dir(name: str) -> tuple[str, str] | None:
    """'cov_g1_cover3' -> ('g1', 'cover3'); None if not a cov_<game>_<cov> dir."""
    if not name.startswith("cov_"):
        return None
    rest = name[len("cov_"):]
    game, _, cov = rest.partition("_")
    if not game or not cov:
        return None
    return game, cov


def _frames(clip_dir: Path, stride_s: float, cap: int) -> list["cv2.typing.MatLike"]:
    """Sample frames from the clip's mp4 (every stride_s), or read its PNGs."""
    pngs = sorted(clip_dir.glob("frame_*.png")) or sorted(clip_dir.glob("*.png"))
    if pngs:
        imgs = [cv2.imread(str(p)) for p in pngs[:cap]]
        return [im for im in imgs if im is not None]
    mp4s = sorted(clip_dir.glob("*.mp4"))
    if not mp4s:
        return []
    cap_v = cv2.VideoCapture(str(mp4s[0]))
    fps = cap_v.get(cv2.CAP_PROP_FPS) or 30.0
    step = max(1, int(round(fps * stride_s)))
    out: list = []
    i = 0
    while len(out) < cap:
        ok, fr = cap_v.read()
        if not ok:
            break
        if i % step == 0:
            out.append(fr)
        i += 1
    cap_v.release()
    return out


def _clip_pred(ocr: OCRPipeline, frames) -> tuple[str | None, int]:
    """Mode of non-null read_coverage predictions over the clip's frames.
    Returns (predicted_coverage_or_None, n_frames_that_read)."""
    reads = []
    for fr in frames:
        r = ocr.read_coverage(fr)
        if r is not None and r.coverage is not None:
            reads.append(r.coverage)
    if not reads:
        return None, 0
    return Counter(reads).most_common(1)[0][0], len(reads)


def _f1_macro(pairs: list[tuple[str, str | None]]) -> float:
    """Macro-F1 over the label set from (true, pred) pairs (pred None = miss)."""
    labels = sorted({t for t, _ in pairs})
    f1s = []
    for lab in labels:
        tp = sum(1 for t, p in pairs if t == lab and p == lab)
        fp = sum(1 for t, p in pairs if t != lab and p == lab)
        fn = sum(1 for t, p in pairs if t == lab and p != lab)
        prec = tp / (tp + fp) if (tp + fp) else 0.0
        rec = tp / (tp + fn) if (tp + fn) else 0.0
        f1s.append(2 * prec * rec / (prec + rec) if (prec + rec) else 0.0)
    return sum(f1s) / len(f1s) if f1s else 0.0


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", required=True, help="dir of cov_<game>_<coverage> subdirs")
    ap.add_argument("--tuning-game", default="cc",
                    help="game id treated as in-sample (excluded from held-out report)")
    ap.add_argument("--stride-s", type=float, default=2.0, help="seconds between sampled frames")
    ap.add_argument("--max-frames", type=int, default=10, help="max frames scored per clip")
    args = ap.parse_args()

    root = Path(args.root)
    clips = sorted(d for d in root.iterdir() if d.is_dir() and d.name.startswith("cov_"))
    if not clips:
        print(f"no cov_* dirs under {root}", file=sys.stderr)
        return 2

    print("constructing OCRPipeline (warms EasyOCR ~2s)...", file=sys.stderr)
    ocr = OCRPipeline()
    ocr.warmup()

    skipped: list[tuple[str, str]] = []
    rows: list[ClipResult] = []
    for d in clips:
        parsed = _parse_dir(d.name)
        if parsed is None:
            skipped.append((d.name, "unparseable name"))
            continue
        game, cov_suffix = parsed
        label = _label_for(cov_suffix)
        if label is None:
            skipped.append((d.name, f"unmapped coverage '{cov_suffix}'"))
            continue
        frames = _frames(d, args.stride_s, args.max_frames)
        if not frames:
            skipped.append((d.name, "no frames"))
            continue
        pred, n_read = _clip_pred(ocr, frames)
        rows.append(ClipResult(game=game, label=label, pred=pred,
                               n_frames=len(frames), n_read=n_read, dirname=d.name))
        mark = "OK " if pred == label else ("--?" if pred is None else "XX ")
        print(f"  {mark} {d.name:28s} label={label:11s} pred={str(pred):11s} "
              f"({n_read}/{len(frames)} frames read)")

    if not rows:
        print("\nno scorable clips.", file=sys.stderr)
        return 1

    # Per-game accuracy.
    by_game: dict[str, list[ClipResult]] = defaultdict(list)
    for r in rows:
        by_game[r.game].append(r)
    print("\n=== per-game (clip-level; abstain counts as wrong) ===")
    for game in sorted(by_game):
        rs = by_game[game]
        correct = sum(1 for r in rs if r.pred == r.label)
        abstain = sum(1 for r in rs if r.pred is None)
        tag = "  (tuning/in-sample)" if game == args.tuning_game else ""
        print(f"  {game:4s}  {correct}/{len(rs)} correct  ({abstain} abstain){tag}")

    # Held-out (all games except the tuning game) — the honest generalization number.
    held = [r for r in rows if r.game != args.tuning_game]
    print(f"\n=== HELD-OUT (games != '{args.tuning_game}') — {len(held)} clips ===")
    if held:
        correct = sum(1 for r in held if r.pred == r.label)
        abstain = sum(1 for r in held if r.pred is None)
        pairs = [(r.label, r.pred) for r in held]
        print(f"  accuracy      : {correct}/{len(held)} = {correct / len(held):.2f}")
        decided = [r for r in held if r.pred is not None]
        if decided:
            dc = sum(1 for r in decided if r.pred == r.label)
            print(f"  decided acc   : {dc}/{len(decided)} = {dc / len(decided):.2f} "
                  f"(excludes {abstain} abstains)")
        print(f"  macro-F1      : {_f1_macro(pairs):.2f}   (ADR 0010 gate: >= 0.85)")
        print("  per-coverage  :")
        for lab in sorted({r.label for r in held}):
            ls = [r for r in held if r.label == lab]
            c = sum(1 for r in ls if r.pred == lab)
            print(f"    {lab:12s} {c}/{len(ls)}")
        print("  confusion (label -> pred):")
        conf = Counter((r.label, str(r.pred)) for r in held)
        for (lab, pred), n in sorted(conf.items()):
            if lab != pred:
                print(f"    {lab:12s} -> {pred:12s} x{n}")
    else:
        print("  (no held-out games — capture cov_g<N>_* clips across multiple games)")

    if skipped:
        print(f"\n=== SKIPPED {len(skipped)} dirs (not silently dropped) ===")
        for name, why in skipped:
            print(f"  {name}: {why}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
