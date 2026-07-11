"""Style-aware patch-NCC digit reader for the Madden 26 broadcast bar.

STANDALONE — deliberately NOT wired into ocr_pipeline. Built to evaluate whether
target-style templates can resolve the ADR-0019 `1<->7` symptom on the fields that
fail today (game-clock-seconds and single-digit distance).

TWO per-field readers, not one shared set: game-clock-seconds and distance render
at different scale/stroke weight (gcsec ~21px/2-3px, distance ~34px/5px), so a
template built on one field does not transfer to the other at native scale
(cross-field NCC ~0.3). Each reader carries its own per-field template set. This
mirrors the original play-clock cross-style mismatch (ADR 0020) — style, not
technique, is the constraint.

Method: patch-NCC with abstain-over-guess (never-fabricate, ADR 0017/0019).
Pipeline per field:
    crop zone -> reject corrupt (colour-saturation; green-static HDMI glitch)
    -> require field present -> 8x upscale -> Otsu -> strip full-width chrome rows
    -> split into N column slots -> per-slot LARGEST-connected-component tight crop
    -> 40x56 -> zero-mean unit-norm -> max NCC over per-digit templates
    -> abstain if best < tau OR (best - second) < delta.

The largest-connected-component tight crop is load-bearing: a loose row-threshold
crop leaves the glyph un-normalised in scale/position and collapses cross-instance
NCC to ~0.1. Tight-crop restores same-digit NCC to ~0.8.
"""

from __future__ import annotations

from dataclasses import dataclass

import cv2
import numpy as np

# Normalised glyph canvas.
GH, GW = 56, 40


@dataclass(frozen=True)
class FieldSpec:
    """A broadcast-bar numeric field: pixel zone + expected digit-slot count."""

    name: str
    bbox: tuple[int, int, int, int]  # x, y, w, h on the 1920x1080 frame
    n_slots: int


# Zones calibrated on the live PS5 feed (v2.3.0-live bar). The distance zone is
# x=1693 (not the doc's ~1686 nor the Phase-1 1700): the ruler showed the '&'
# ampersand ends ~x=1690 and the single digit sits ~1695-1720, so 1693..1726
# isolates the digit and excludes the '&'.
GCSEC = FieldSpec("gcsec", (1383, 1013, 68, 40), 2)
DIST = FieldSpec("dist", (1693, 1010, 33, 44), 1)


def _crop(frame: np.ndarray, spec: FieldSpec) -> np.ndarray:
    x, y, w, h = spec.bbox
    return frame[y : y + h, x : x + w]


# ---------------------------------------------------------------------------
# Two entry styles. Patch-based `*_patch` functions operate on an ALREADY-CROPPED
# field patch — this is the pipeline contract (ocr_pipeline crops the zone via
# hud_regions + its own _crop, then hands the reader the patch; the reader never
# touches the full frame). The frame+spec wrappers below just crop and delegate,
# and are what the standalone eval/gate harness uses.
# ---------------------------------------------------------------------------


def sat_mean_patch(patch: np.ndarray) -> float:
    """Mean per-pixel colour saturation of a field patch. Clean HUD box is
    near-grey (~low); a green-static HDMI-glitch frame is highly saturated."""
    roi = patch.astype(np.int16)
    b, g, r = roi[..., 0], roi[..., 1], roi[..., 2]
    hi = np.maximum(np.maximum(b, g), r)
    lo = np.minimum(np.minimum(b, g), r)
    return float((hi - lo).mean())


def is_corrupt_patch(patch: np.ndarray, thresh: float = 28.0) -> bool:
    return sat_mean_patch(patch) >= thresh


def field_present_patch(patch: np.ndarray) -> bool:
    """White-on-dark digits present in the patch: it must hold both dark box
    background and bright ink. Rejects blank/menu (all-dark) and field cutaways
    (all-bright, which pass a plain brightness check but have no bar)."""
    g = cv2.cvtColor(patch, cv2.COLOR_BGR2GRAY)
    return (g < 60).mean() > 0.15 and (g > 180).mean() > 0.08


def segment_patch(patch: np.ndarray, n_slots: int) -> list[np.ndarray] | None:
    """Segment an already-cropped field patch into normalised GHxGW glyphs, or
    None if it can't be cleanly segmented (caller abstains)."""
    g = cv2.cvtColor(patch, cv2.COLOR_BGR2GRAY)
    g = cv2.resize(g, None, fx=8, fy=8, interpolation=cv2.INTER_CUBIC)
    _, bw = cv2.threshold(g, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    bw = cv2.morphologyEx(bw, cv2.MORPH_OPEN, np.ones((3, 3), np.uint8))
    H, W = bw.shape
    bw[(bw > 0).sum(1) / W > 0.85, :] = 0  # strip full-width chrome rows
    cols = np.where((bw > 0).sum(0) > 0)[0]
    if len(cols) < 3:
        return None
    bw = bw[:, cols[0] : cols[-1] + 1]
    g = g[:, cols[0] : cols[-1] + 1]
    Wc = bw.shape[1]
    out: list[np.ndarray] = []
    for k in range(n_slots):
        a, b = k * Wc // n_slots, (k + 1) * Wc // n_slots
        sub, subg = bw[:, a:b], g[:, a:b]
        num, lab, stats, _ = cv2.connectedComponentsWithStats(
            (sub > 0).astype(np.uint8), 8
        )
        if num <= 1:
            return None
        big = 1 + int(np.argmax(stats[1:, cv2.CC_STAT_AREA]))
        xs = np.where((lab == big).any(0))[0]
        ys = np.where((lab == big).any(1))[0]
        glyph = subg[ys[0] : ys[-1] + 1, xs[0] : xs[-1] + 1]
        out.append(cv2.resize(glyph, (GW, GH), interpolation=cv2.INTER_CUBIC))
    return out


# Frame+spec wrappers (crop, then delegate) — used by the standalone eval/gate.
def sat_mean(frame: np.ndarray, spec: FieldSpec) -> float:
    return sat_mean_patch(_crop(frame, spec))


def is_corrupt(frame: np.ndarray, spec: FieldSpec, thresh: float = 28.0) -> bool:
    return is_corrupt_patch(_crop(frame, spec), thresh)


def field_present(frame: np.ndarray, spec: FieldSpec) -> bool:
    return field_present_patch(_crop(frame, spec))


def segment(frame: np.ndarray, spec: FieldSpec) -> list[np.ndarray] | None:
    return segment_patch(_crop(frame, spec), spec.n_slots)


def vec(glyph: np.ndarray) -> np.ndarray:
    """Zero-mean unit-norm feature vector for NCC (dot product)."""
    v = glyph.astype(np.float32).ravel()
    v -= v.mean()
    n = np.linalg.norm(v)
    return v / n if n > 0 else v


@dataclass
class SlotResult:
    digit: str | None
    best: float
    margin: float


class DigitReader:
    """Per-field patch-NCC reader with frozen abstain thresholds."""

    def __init__(self, spec: FieldSpec, tau: float = 0.60, delta: float = 0.05):
        self.spec = spec
        self.tau = tau
        self.delta = delta
        self.templates: dict[str, list[np.ndarray]] = {str(d): [] for d in range(10)}
        self.means: dict[str, np.ndarray] = {}

    def add(self, digit: str, glyph_vec: np.ndarray) -> None:
        self.templates[digit].append(glyph_vec)
        self._finalize()

    def build(self, items: list[tuple[np.ndarray, str]]) -> None:
        for v, d in items:
            self.templates[d].append(v)
        self._finalize()

    def _finalize(self) -> None:
        """Collapse each digit's exemplars to ONE mean (renormalised) template.

        Classifying against a per-digit mean — not max-NCC over every exemplar —
        is essential: max-over-N inflates the score of digits with many exemplars
        (gcsec `9` has ~84, `7` has 2), so with raw max a glyph spuriously matches
        the high-count digit at ~1.0 and margins collapse. The mean gives every
        digit one fair representative and restores true shape discrimination.
        """
        means = {}
        for d, ts in self.templates.items():
            if ts:
                m = np.mean(ts, axis=0)
                n = np.linalg.norm(m)
                means[d] = m / n if n > 0 else m
        self.means = means

    def classify(self, v: np.ndarray) -> SlotResult:
        scores = {d: float(np.dot(v, m)) for d, m in self.means.items()}
        if not scores:
            return SlotResult(None, -2.0, 0.0)
        ranked = sorted(scores.items(), key=lambda kv: -kv[1])
        (d1, s1) = ranked[0]
        s2 = ranked[1][1] if len(ranked) > 1 else -2.0
        return SlotResult(d1, s1, s1 - s2)

    def save(self, path: str) -> None:
        """Persist the frozen thresholds + per-digit mean templates to an .npz."""
        np.savez(
            path,
            tau=self.tau,
            delta=self.delta,
            spec_name=self.spec.name,
            **{f"tmpl_{d}": m for d, m in self.means.items()},
        )

    @classmethod
    def load(cls, path: str, spec: FieldSpec) -> "DigitReader":
        z = np.load(path)
        r = cls(spec, float(z["tau"]), float(z["delta"]))
        r.means = {k[len("tmpl_"):]: z[k] for k in z.files if k.startswith("tmpl_")}
        return r

    def read_patch(
        self, patch: np.ndarray, n_slots: int | None = None
    ) -> tuple[str | None, list[SlotResult]]:
        """PIPELINE ENTRY: read an ALREADY-CROPPED field patch (the pipeline crops
        the zone via hud_regions + _crop and hands it here). `n_slots` overrides the
        spec's slot count — so the shared white-on-dark template set reads a
        1-digit field (quarter/down/minutes) or a 2-digit one (seconds). Returns
        (digit string, per-slot detail) or (None, ...) on abstain. Abstains on:
        corruption, absent field, failed segmentation, or any slot below tau /
        margin. A null beats a wrong digit (never-fabricate)."""
        if patch is None or patch.size == 0:
            return None, []
        if is_corrupt_patch(patch) or not field_present_patch(patch):
            return None, []
        glyphs = segment_patch(patch, n_slots if n_slots is not None else self.spec.n_slots)
        if glyphs is None:
            return None, []
        results = [self.classify(vec(g)) for g in glyphs]
        if any(r.best < self.tau or r.margin < self.delta for r in results):
            return None, results
        return "".join(r.digit for r in results), results

    def read(self, frame: np.ndarray) -> tuple[str | None, list[SlotResult]]:
        """Frame entry (standalone eval/gate): crop the reader's zone, then read."""
        return self.read_patch(_crop(frame, self.spec))
