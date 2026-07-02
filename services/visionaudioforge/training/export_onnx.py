"""Export the trained formation classifier to ONNX with a parity check.

Loads the best PyTorch checkpoint, exports to ONNX (opset 17, static shape),
then runs both on 50 random test-set frames and asserts max abs logit
divergence < 1e-4. Divergence > tolerance FAILS hard (per the plan's
silent-divergence guard) — common causes: BatchNorm in train mode at export,
dynamic-shape issues, opset mismatch.

Output: services/visionaudioforge/app/adapters/madden26/models/formation_v0_1.onnx
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import torch
from torch.utils.data import DataLoader

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
from training.dataset import FormationDataset, INPUT_SIZE  # noqa: E402
from training.train_formation import build_model, CKPT, MODELS_DIR  # noqa: E402

ONNX_PATH = MODELS_DIR / "formation_v0_1.onnx"
TOL = 1e-4
N_PARITY = 50


def main() -> int:
    model = build_model()
    model.load_state_dict(torch.load(CKPT, map_location="cpu"))
    model.eval()

    dummy = torch.randn(1, 3, INPUT_SIZE, INPUT_SIZE)
    torch.onnx.export(
        model, dummy, str(ONNX_PATH), opset_version=17,
        input_names=["input"], output_names=["logits"],
        dynamic_axes=None, do_constant_folding=True,
    )
    size_mb = ONNX_PATH.stat().st_size / 1e6
    print(f"exported {ONNX_PATH.name} ({size_mb:.1f} MB)")

    import onnxruntime as ort
    sess = ort.InferenceSession(str(ONNX_PATH), providers=["CPUExecutionProvider"])

    test = FormationDataset("test", transform=None)
    n = min(N_PARITY, len(test))
    dl = DataLoader(test, batch_size=1, shuffle=False)
    max_div = 0.0
    with torch.no_grad():
        for i, (x, _) in enumerate(dl):
            if i >= n:
                break
            pt = model(x).numpy()
            on = sess.run(["logits"], {"input": x.numpy()})[0]
            max_div = max(max_div, float(np.max(np.abs(pt - on))))
    ok = max_div < TOL
    print(f"parity over {n} frames: max abs logit divergence {max_div:.2e} "
          f"(tol {TOL:.0e}) -> {'PASS' if ok else 'FAIL'}")
    if not ok:
        print("FAIL: PyTorch/ONNX divergence exceeds tolerance — not shipping this ONNX.")
        return 1
    print(f"\nonnx -> {ONNX_PATH}  size {size_mb:.1f} MB  (Git LFS: {'yes' if size_mb>25 else 'no'})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
