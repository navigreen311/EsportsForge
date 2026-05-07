# Capture-agent test fixtures

`synthetic.mp4` is generated locally on demand. Not committed because
it's a binary.

To generate the synthetic fixture for the Phase 0 smoke test:

```bash
cd <repo-root>
source backend/venv/Scripts/activate    # or your VAF venv
python -c "
import cv2, numpy as np
out = 'agents/capture/fixtures/synthetic.mp4'
fourcc = cv2.VideoWriter_fourcc(*'mp4v')
vw = cv2.VideoWriter(out, fourcc, 12.0, (1920, 1080))
for i in range(60):
    img = np.full((1080, 1920, 3), (i*4 % 256, 100, 200), dtype=np.uint8)
    cv2.putText(img, f'frame {i}', (50, 100), cv2.FONT_HERSHEY_SIMPLEX, 2, (255,255,255), 3)
    vw.write(img)
vw.release()
print('wrote', out)
"
```

Real Madden gameplay clips (for adapter-correctness testing) live
under `services/visionaudioforge/app/adapters/madden26/tests/fixtures/`
when curated; those go through Git LFS.
