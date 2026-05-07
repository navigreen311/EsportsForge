# VisionAudioForge (VAF) — Core Service

Per-title vision/audio adapter pipeline. Receives JPEG frame batches from the capture agent, dispatches per-frame to the active title's adapter, emits structured `EventEnvelope` events to subscribers (EsportsForge backend webhook + future WebSocket fan-out).

- **Spec:** [docs/specs/02-visionaudioforge-core.md](../../docs/specs/02-visionaudioforge-core.md)
- **Madden adapter spec:** [docs/specs/04-madden26-adapter-spec.md](../../docs/specs/04-madden26-adapter-spec.md)
- **Architecture:** [docs/FORGE_ARCHITECTURE_PATTERN.md](../../docs/FORGE_ARCHITECTURE_PATTERN.md)
- **Phase status:** [docs/phase-completions/0-vaf-foundation.md](../../docs/phase-completions/0-vaf-foundation.md) (Phase 0 in progress, 5 of 8 acceptance criteria pending real-footage validation)
- **Default ports:** core service `:8100`; webhook target (EsportsForge backend) `:8002` (per [ADR 0011](../../docs/adr/0011-dev-backend-port-correction.md)).

## Local development

The service has its own venv. **Do not install dependencies into the EsportsForge backend venv** — they have different dependency floors (e.g., FastAPI version, NumPy ABI for OpenCV).

### One-time venv setup

Requires Python 3.12 (matches CI; 3.13+ has not been validated).

#### Windows (PowerShell)

```powershell
cd services\visionaudioforge
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
```

If PowerShell blocks the activate script, run once per machine:

```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

#### Windows (Git Bash / cmd)

```bash
cd services/visionaudioforge
python -m venv .venv
source .venv/Scripts/activate     # Git Bash
# OR
.venv\Scripts\activate.bat        # cmd
python -m pip install --upgrade pip
pip install -r requirements.txt
```

#### Linux / macOS (future ECS deploy + macOS dev)

```bash
cd services/visionaudioforge
python3.12 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
pip install -r requirements.txt
```

The service is platform-neutral per [ADR 0009](../../docs/adr/0009-core-service-platform-neutral.md) — no `import win32*`, no `\\` literals, no Windows-only file paths.

### Running the service

With venv active:

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8100 --reload
```

Environment variables (read from `os.environ` at process start):

| Variable | Default | Purpose |
|---|---|---|
| `ESF_BACKEND_URL` | `http://127.0.0.1:8002` | EsportsForge backend webhook target. See ADR 0011 for the `:8001` → `:8002` change. |
| `AWS_REGION` | `us-east-1` | CloudWatch metric publish region (only used when boto3 + creds are present). |
| `VAF_METRICS_DISABLED` | unset (enabled) | Set to `1` to skip CloudWatch metric publishing entirely. Useful in CI. |

### Running the tests

```bash
# With venv active:
pytest tests/ -v
```

The test suite uses `services/visionaudioforge/tests/conftest.py` to put the service root on `sys.path`, so `pytest` works from any cwd as long as the venv is active.

Pinned versions:
- `pytest==8.3.3` (matches CI floor)
- `pytest-asyncio==0.24.0`

If your `pytest --version` reports anything other than `8.3.3`, you have an environment-version mismatch — recreate the venv. The mismatched version was the trigger for adding this README.

### Real-footage validation harness

Independent of the FastAPI service. Bypasses the websocket transport and feeds real frames directly into `Dispatcher.process_frame`:

```bash
python ../../agents/capture/real_footage_harness.py \
  --video ../../agents/capture/fixtures/real/madden26.mp4 \
  --max-frames 200 \
  --frame-stride 5 \
  --report ../../agents/capture/fixtures/real/report_runN.json
```

The fixture `madden26.mp4` is gitignored (large binary). Regenerate via the `yt-dlp` command in [docs/phase-completions/0-real-footage-validation.md §Reproduction](../../docs/phase-completions/0-real-footage-validation.md).

## Dependency notes

- **EasyOCR** replaces Tesseract (Tesseract install blocked without admin on the dev workstation). Per-frame cost is being addressed by the OCR cadence reform milestone — see [Phase 0 remaining milestones](../../docs/phase-completions/0-vaf-remaining-milestones.md).
- **boto3** is intentionally not pinned. `app/core/metrics.py` lazy-imports it and no-ops when absent or when `VAF_METRICS_DISABLED=1`. Production deploys add it via the deployment `Dockerfile` overlay.
- **PyTorch** comes in transitively via EasyOCR. CPU-only wheel; ~2 GB install footprint. The first OCR call has a ~5 s cold start (model download + load).

## Service layout

```
services/visionaudioforge/
├── app/
│   ├── main.py               # FastAPI entry on :8100
│   ├── api/                  # /sessions, /ingest, /health endpoints
│   ├── adapters/             # registry + per-title adapters (madden26 only in Phase 0)
│   ├── core/                 # session, dispatcher, title_detector, integrity_gate, webhook, metrics, envelope
│   └── schemas/              # EventEnvelope + payload + wire shapes
├── tests/                    # pytest test suite
├── requirements.txt          # pinned runtime + test deps
└── README.md                 # this file
```

See the [Phase 0 status doc](../../docs/phase-completions/0-vaf-foundation.md) for the current acceptance-criteria status and what remains.
