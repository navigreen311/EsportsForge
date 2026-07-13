"""Player-detection → player-relative framing for All-22 frames (coverage by-game work).

Offline/experimental. Built during the coverage v0.3 by-game validation to make frame
crops **field-position invariant**: a fixed-fraction crop (top-40%) only lands on the
defensive backfield in one camera framing; across stadiums/field-positions it grabs the
endzone instead (that broke the by-game validation — see
docs/phase-completions/coverage-v0.3-modeling-plan.md "BY-GAME VALIDATION").

This locates the on-field players with a pretrained detector (COCO person, feet-on-grass
filter to drop crowd/sideline) and crops relative to them. The framing works; the caveat
(documented in the modeling plan) is that frozen-ResNet features on these crops still do
NOT read the 1-vs-2-safety shell — robust coverage-from-vision remains a research arc, and
the shipped path is OCR-of-play-call (coverage-ocr-playcall-pivot.md). Kept as reusable
infrastructure if the opponent-coverage vision arc is ever revisited.

Needs torch/torchvision (the training venv, not CI). CPU ~0.8s/frame.

    python player_crop.py   # renders player-bbox crops for a few capture clips
"""

from __future__ import annotations

import cv2
import numpy as np
import torch
from torchvision.models.detection import (
    FasterRCNN_ResNet50_FPN_Weights,
    fasterrcnn_resnet50_fpn,
)

_DET = fasterrcnn_resnet50_fpn(weights=FasterRCNN_ResNet50_FPN_Weights.DEFAULT).eval()


def _is_grass(frame, x, y):
    h, w = frame.shape[:2]
    x = min(max(x, 0), w - 1)
    y = min(max(y, 0), h - 1)
    b, g, r = frame[y, x].astype(int)
    return g > r + 8 and g > b + 8 and 50 < g < 200


def onfield_players(frame, conf=0.5):
    """Return person boxes (x1,y1,x2,y2) whose feet are on grass — i.e. field players,
    excluding crowd/sideline."""
    rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    t = torch.tensor(rgb).permute(2, 0, 1).float() / 255
    with torch.no_grad():
        o = _DET([t])[0]
    box, lab, sc = o["boxes"].numpy(), o["labels"].numpy(), o["scores"].numpy()
    ppl = box[(lab == 1) & (sc > conf)]
    keep = [bx for bx in ppl if _is_grass(frame, int((bx[0] + bx[2]) / 2), int(bx[3] - 3))]
    return np.array(keep)


def player_bbox_crop(frame, pad=0.03):
    """Crop the frame to the bounding box of on-field players (field-position invariant).
    Returns (crop, n_players) or None if too few players (not a usable alignment frame)."""
    p = onfield_players(frame)
    if len(p) < 8:
        return None
    h, w = frame.shape[:2]
    x1 = max(0, int(p[:, 0].min() - pad * w))
    x2 = min(w, int(p[:, 2].max() + pad * w))
    y1 = max(0, int(p[:, 1].min() - pad * h))
    y2 = min(h, int(p[:, 3].max() + pad * h))
    return frame[y1:y2, x1:x2], len(p)


if __name__ == "__main__":
    import glob

    d = r"C:/Users/ivann/madden-recal-refs/digit-campaign"
    rows = []
    for clip, frac in [("cov_g1_cover1", 0.5), ("cov_g4_cover1", 0.85)]:
        paths = sorted(glob.glob(f"{d}/{clip}/{clip}.mp4*"))
        if not paths:
            continue
        cap = cv2.VideoCapture(paths[0])
        n = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        cap.set(cv2.CAP_PROP_POS_FRAMES, int(n * frac))
        ok, f = cap.read()
        cap.release()
        if ok:
            res = player_bbox_crop(f)
            if res:
                rows.append(cv2.resize(res[0], (600, 200)))
    if rows:
        cv2.imwrite("player_crop_demo.png", np.vstack(rows))
        print("saved player_crop_demo.png")
