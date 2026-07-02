"""Training augmentation for the formation classifier (M5c sub-task 4).

NO horizontal flip — formation orientation is left/right-meaningful (trips-left
vs trips-right, strong-side). Augments operate on uint8 RGB HxWx3 arrays so they
compose with the cv2-based FormationDataset. Deterministic given a seeded RNG.
"""

from __future__ import annotations

import cv2
import numpy as np


class TrainAugment:
    """Rotation +-5 deg, brightness +-15%, mild colour jitter. No h-flip."""

    def __init__(self, seed: int = 42):
        self.rng = np.random.default_rng(seed)

    def __call__(self, img: np.ndarray) -> np.ndarray:
        h, w = img.shape[:2]
        # rotation +-5 degrees about centre
        angle = float(self.rng.uniform(-5, 5))
        m = cv2.getRotationMatrix2D((w / 2, h / 2), angle, 1.0)
        img = cv2.warpAffine(img, m, (w, h), borderMode=cv2.BORDER_REFLECT)
        # brightness +-15%
        img = np.clip(img.astype(np.float32) * float(self.rng.uniform(0.85, 1.15)), 0, 255)
        # mild per-channel colour jitter +-5%
        jitter = self.rng.uniform(0.95, 1.05, size=3).astype(np.float32)
        img = np.clip(img * jitter, 0, 255)
        return img.astype(np.uint8)


class NoAugment:
    """Identity — val/test see the cached crop unchanged."""

    def __call__(self, img: np.ndarray) -> np.ndarray:
        return img
