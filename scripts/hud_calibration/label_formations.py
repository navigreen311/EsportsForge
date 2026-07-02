"""Keyboard-only Madden 26 formation labeling tool (M5c sub-task 2).

Labels the MATCHUP-clip pre-snap candidates emitted by
sample_pre_snap_candidates.py. (Practice-clip candidates are auto-labelled by
that script from the filename formation and never reach this tool.)

Design target: <= 20 seconds per frame. No mouse, no typing of class names,
no separate viewer — one keypress labels and advances.

Keymap (single keypress = immediate CSV write + advance):

    1  shotgun_trips      5  singleback_ace
    2  shotgun_bunch      6  pistol_strong
    3  shotgun_empty      7  shotgun_doubles
    4  i_form_pro         8  singleback_wing

    SPACE   skip this frame (recorded as label_quality=skip; not training data)
    m       toggle MEDIUM-quality mode — the next numeric label is flagged
            'medium' (ambiguous formation) instead of 'high'
    j / <-  back up one frame (re-label the previous frame)
    l / ->  skip ahead one frame WITHOUT recording anything
    q       save and quit

Writes incrementally to agents/capture/fixtures/real/formation_labels.csv
(one row appended per label keypress — a crash loses at most one frame). On
restart it loads existing labels and resumes at the first unlabelled candidate.

CSV schema:
    clip,frame_idx,ts_sec,formation_class,label_quality

Run (from repo root, with services/visionaudioforge/.venv active):

    python scripts/hud_calibration/label_formations.py
    python scripts/hud_calibration/label_formations.py --check   # no-GUI self-test
"""

from __future__ import annotations

import argparse
import csv
import sys
from pathlib import Path

import cv2

REPO_ROOT = Path(__file__).resolve().parents[2]
SERVICE_ROOT = REPO_ROOT / "services" / "visionaudioforge"
sys.path.insert(0, str(SERVICE_ROOT))

from app.adapters.madden26.formation_detector import TOP_8_FORMATIONS  # noqa: E402

FIXTURES_DIR = REPO_ROOT / "agents" / "capture" / "fixtures" / "real"
CANDIDATES_PATH = FIXTURES_DIR / "formation_candidates.json"
LABELS_PATH = FIXTURES_DIR / "formation_labels.csv"
CSV_FIELDS = ["clip", "frame_idx", "ts_sec", "formation_class", "label_quality"]

# Key '1'..'8' -> formation (TOP_8 order).
KEY_TO_FORMATION = {str(i + 1): f for i, f in enumerate(TOP_8_FORMATIONS)}
# Arrow-key extended codes vary by platform; letters j/l are the portable path.
LEFT_CODES = {2424832, 65361, 81}    # win / gtk / qt left
RIGHT_CODES = {2555904, 65363, 83}   # win / gtk / qt right
DISPLAY_SIZE = (960, 540)


def load_existing_labels() -> set[tuple[str, int]]:
    done: set[tuple[str, int]] = set()
    if LABELS_PATH.exists():
        with LABELS_PATH.open(newline="") as f:
            for row in csv.DictReader(f):
                done.add((row["clip"], int(row["frame_idx"])))
    return done


def append_label(row: dict) -> None:
    new_file = not LABELS_PATH.exists()
    with LABELS_PATH.open("a", newline="") as f:
        w = csv.DictWriter(f, fieldnames=CSV_FIELDS)
        if new_file:
            w.writeheader()
        w.writerow(row)


def load_matchup_candidates() -> list[dict]:
    import json
    data = json.loads(CANDIDATES_PATH.read_text())
    return [c for c in data["candidates"] if c["kind"] == "matchup" and not c.get("auto_label")]


def preload_frames(cands: list[dict]) -> list[dict]:
    """Read + downsample each candidate frame once (grouped by clip)."""
    by_clip: dict[str, list[dict]] = {}
    for c in cands:
        by_clip.setdefault(c["clip"], []).append(c)
    loaded: list[dict] = []
    for clip, items in sorted(by_clip.items()):
        cap = cv2.VideoCapture(str(FIXTURES_DIR / clip))
        if not cap.isOpened():
            print(f"WARN could not open {clip}; skipping its {len(items)} frames")
            continue
        for c in sorted(items, key=lambda x: x["frame_idx"]):
            cap.set(cv2.CAP_PROP_POS_FRAMES, c["frame_idx"])
            ok, frame = cap.read()
            if not ok or frame is None:
                continue
            loaded.append({**c, "img": cv2.resize(frame, DISPLAY_SIZE)})
        cap.release()
        print(f"  loaded {clip}")
    return loaded


def _overlay(img, idx: int, total: int, c: dict, medium: bool, labeled: int):
    canvas = img.copy()
    W, H = DISPLAY_SIZE
    # Top status bar.
    top = canvas.copy()
    cv2.rectangle(top, (0, 0), (W, 70), (0, 0, 0), -1)
    cv2.addWeighted(top, 0.55, canvas, 0.45, 0, canvas)
    cv2.putText(canvas, f"[{idx+1}/{total}] {c['clip']}  f{c['frame_idx']} ({c['ts_sec']}s)",
                (8, 22), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (255, 255, 255), 1, cv2.LINE_AA)
    mode = "MEDIUM (next label)" if medium else "high"
    qcol = (0, 165, 255) if medium else (0, 255, 255)
    cv2.putText(canvas, f"labeled this session: {labeled}    quality: {mode}",
                (8, 48), cv2.FONT_HERSHEY_SIMPLEX, 0.5, qcol, 1, cv2.LINE_AA)
    # Bottom legend: which number labels which formation + the control keys.
    bot = canvas.copy()
    cv2.rectangle(bot, (0, H - 78), (W, H), (0, 0, 0), -1)
    cv2.addWeighted(bot, 0.6, canvas, 0.4, 0, canvas)
    col_w = W // 4
    for i, formation in enumerate(TOP_8_FORMATIONS):
        row, col = divmod(i, 4)
        x = 8 + col * col_w
        y = H - 54 + row * 22
        cv2.putText(canvas, f"{i+1} {formation}", (x, y),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.45, (120, 255, 120), 1, cv2.LINE_AA)
    cv2.putText(canvas, "SPACE skip   m medium   j/l (or <-/->) nav   q save+quit",
                (8, H - 8), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (200, 200, 255), 1, cv2.LINE_AA)
    return canvas


def run() -> int:
    if not CANDIDATES_PATH.exists():
        print(f"No candidates file at {CANDIDATES_PATH}. Run "
              f"sample_pre_snap_candidates.py first.")
        return 1
    cands = load_matchup_candidates()
    done = load_existing_labels()
    todo = [c for c in cands if (c["clip"], c["frame_idx"]) not in done]
    print(f"{len(cands)} matchup candidates, {len(done)} already labeled, "
          f"{len(todo)} to go. Loading frames into memory…")
    frames = preload_frames(todo)
    if not frames:
        print("Nothing to label. Done.")
        return 0

    win = "label_formations"
    cv2.namedWindow(win, cv2.WINDOW_NORMAL)
    cv2.setWindowProperty(win, cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_FULLSCREEN)

    i = 0
    medium = False
    labeled = 0
    while 0 <= i < len(frames):
        c = frames[i]
        cv2.imshow(win, _overlay(c["img"], i, len(frames), c, medium, labeled))
        key = cv2.waitKeyEx(0)
        ch = chr(key & 0xFF) if 0 <= (key & 0xFF) < 256 else ""

        if ch == "q":
            break
        if ch in KEY_TO_FORMATION:
            append_label({"clip": c["clip"], "frame_idx": c["frame_idx"],
                          "ts_sec": c["ts_sec"], "formation_class": KEY_TO_FORMATION[ch],
                          "label_quality": "medium" if medium else "high"})
            labeled += 1
            medium = False
            i += 1
        elif ch == " ":
            append_label({"clip": c["clip"], "frame_idx": c["frame_idx"],
                          "ts_sec": c["ts_sec"], "formation_class": "skip",
                          "label_quality": "skip"})
            i += 1
        elif ch == "m":
            medium = not medium
        elif ch in ("j",) or key in LEFT_CODES:
            i = max(0, i - 1)
        elif ch in ("l",) or key in RIGHT_CODES:
            i += 1
        # any other key: ignore, re-show same frame

    cv2.destroyAllWindows()
    print(f"\nSaved {labeled} labels this session -> {LABELS_PATH}")
    return 0


def check() -> int:
    """No-GUI self-test: candidates load, frames decode, CSV round-trips."""
    assert CANDIDATES_PATH.exists(), f"missing {CANDIDATES_PATH}"
    cands = load_matchup_candidates()
    print(f"matchup candidates needing labels: {len(cands)}")
    assert len(KEY_TO_FORMATION) == 8 and set(KEY_TO_FORMATION.values()) == set(TOP_8_FORMATIONS)
    # decode the first candidate frame to prove preload works
    if cands:
        sample = preload_frames(cands[:2])
        assert sample and sample[0]["img"].shape[:2] == (DISPLAY_SIZE[1], DISPLAY_SIZE[0])
        print(f"frame preload OK ({sample[0]['img'].shape})")
    done = load_existing_labels()
    print(f"existing labels: {len(done)}; resume target: "
          f"{len([c for c in cands if (c['clip'], c['frame_idx']) not in done])}")
    print("check OK")
    return 0


def smoke() -> int:
    """GUI smoke test: open the fullscreen window, render the first candidate
    frame for ~1.5 s, then close. Confirms cv2 GUI (opencv-python, not
    -headless) works end-to-end without starting a real labeling session."""
    cands = load_matchup_candidates()
    if not cands:
        print("no candidates to smoke-test")
        return 1
    frames = preload_frames(cands[:1])
    if not frames:
        print("could not load first candidate frame")
        return 1
    win = "label_formations"
    cv2.namedWindow(win, cv2.WINDOW_NORMAL)
    cv2.setWindowProperty(win, cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_FULLSCREEN)
    cv2.imshow(win, _overlay(frames[0]["img"], 0, len(cands), frames[0], False, 0))
    cv2.waitKey(1500)
    cv2.destroyAllWindows()
    cv2.waitKey(1)  # flush destroy on some backends
    print("smoke OK — window opened and first frame rendered cleanly")
    return 0


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--check", action="store_true", help="no-GUI self-test")
    p.add_argument("--smoke", action="store_true",
                   help="GUI smoke test: open window + render first frame, then close")
    args = p.parse_args()
    if args.check:
        return check()
    if args.smoke:
        return smoke()
    return run()


if __name__ == "__main__":
    raise SystemExit(main())
