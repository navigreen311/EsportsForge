"""Tiny mock AnimaForge for dev — accepts render requests and returns an
immediately-completed job that points at a publicly hosted sample MP4. Lets
you exercise the full Gameplan / Arsenal / Drill / Share-Win Watch flows
without needing the real AnimaForge renderer.

Run alongside the EsportsForge backend::

    cd backend
    ./venv/Scripts/python.exe ../scripts/mock_animaforge.py

Then in `backend/.env` (already the default)::

    ANIMAFORGE_API_URL=http://localhost:3001
    ANIMAFORGE_API_KEY=dev-animaforge-key

Endpoints implemented:
  - GET  /health                  → 200 {"ok": true}
  - POST /api/v1/render           → returns {job_id, estimated_seconds:0,
                                    video_url, thumbnail_url, status:"complete"}
  - GET  /api/v1/jobs/{job_id}    → returns the cached job row

The mock always returns the same sample video so renders are predictable.
Override with $ESF_MOCK_VIDEO_URL / $ESF_MOCK_THUMB_URL if you have your own
asset to point at.
"""

from __future__ import annotations

import os
import time
import uuid
from typing import Any

from fastapi import FastAPI
from pydantic import BaseModel
import uvicorn


SAMPLE_VIDEO_URL = os.environ.get(
    "ESF_MOCK_VIDEO_URL",
    "https://samplelib.com/lib/preview/mp4/sample-5s.mp4",
)
SAMPLE_THUMB_URL = os.environ.get(
    "ESF_MOCK_THUMB_URL",
    "https://samplelib.com/lib/preview/jpg/sample-1.jpg",
)
PORT = int(os.environ.get("ESF_MOCK_PORT", "3001"))


app = FastAPI(title="EsportsForge mock AnimaForge", version="0.0.1")

# In-memory store. Keyed by job_id.
_JOBS: dict[str, dict[str, Any]] = {}


@app.get("/health")
def health() -> dict[str, Any]:
    return {"ok": True, "mock": True}


class RenderRequest(BaseModel):
    type: str | None = None
    title_id: str | None = None
    spec: dict[str, Any] | None = None
    user_id: str | None = None
    webhook_url: str | None = None


@app.post("/api/v1/render")
def render(req: RenderRequest) -> dict[str, Any]:
    job_id = f"mock-{uuid.uuid4().hex[:12]}"
    job = {
        "job_id": job_id,
        "status": "complete",
        "video_url": SAMPLE_VIDEO_URL,
        "thumbnail_url": SAMPLE_THUMB_URL,
        "completed_at": time.time(),
        "type": req.type,
        "title_id": req.title_id,
    }
    _JOBS[job_id] = job
    print(
        f"[mock-animaforge] render type={req.type} title_id={req.title_id} -> {job_id}"
    )
    return {
        "job_id": job_id,
        "estimated_seconds": 0,
        "status": "complete",
        "video_url": SAMPLE_VIDEO_URL,
        "thumbnail_url": SAMPLE_THUMB_URL,
    }


@app.get("/api/v1/jobs/{job_id}")
def job_status(job_id: str) -> dict[str, Any]:
    job = _JOBS.get(job_id)
    if not job:
        return {
            "job_id": job_id,
            "status": "pending",
            "progress": 50,
        }
    return job


if __name__ == "__main__":
    print(
        f"[mock-animaforge] listening on http://127.0.0.1:{PORT} — "
        f"video={SAMPLE_VIDEO_URL}"
    )
    uvicorn.run(app, host="127.0.0.1", port=PORT, log_level="warning")
