"""VisionAudioForge drill-monitoring endpoint.

Receives a single frame from the client, runs it through Claude with the
detection config, and returns a structured `FrameAnalysis`. When
`ANTHROPIC_API_KEY` is not configured the route returns a deterministic
"no-op" analysis so the polling loop continues to operate (UI surfaces
the missing-key state via a low-confidence indicator + manual override).
"""

from __future__ import annotations

import json
from typing import Any

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

import anthropic

from app.core.config import settings
from app.core.security import get_current_user
from app.db.base import get_db
from app.models.user import User

router = APIRouter()


# ---------------------------------------------------------------------------
# Schemas
# ---------------------------------------------------------------------------

class DetectionPayload(BaseModel):
    type: str
    watch_for: list[str] = []
    success_criteria: dict[str, Any] = {}
    fail_criteria: dict[str, Any] = {}
    prompt_context: str


class MonitorBody(BaseModel):
    frame: str  # base64-encoded JPEG, no data: prefix
    mode: str  # 'simlab' | 'arsenal-practice' | 'drill-lab'
    title_id: str
    scenario_id: str | None = None
    weapon_id: str | None = None
    weapon_name: str | None = None
    formation: str | None = None
    play_name: str | None = None
    detection: DetectionPayload


class FrameAnalysis(BaseModel):
    playInProgress: bool = False
    repCompleted: bool = False
    success: bool | None = None
    coverageDetected: str | None = None
    playDetected: str | None = None
    executionQuality: str | None = None  # 'clean' | 'poor'
    confidence: int = 0
    reason: str = ""


# ---------------------------------------------------------------------------
# Endpoint
# ---------------------------------------------------------------------------

@router.post("/monitor", response_model=FrameAnalysis)
async def monitor_frame(
    body: MonitorBody,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> FrameAnalysis:
    """Analyse a single frame against the supplied detection config."""
    # Without an API key we return a benign no-op so the polling loop and
    # UI continue to function. The client renders this as 'low confidence'
    # and the manual override stays visible.
    if not settings.anthropic_api_key:
        return FrameAnalysis(
            playInProgress=False,
            repCompleted=False,
            success=None,
            confidence=0,
            reason="ANTHROPIC_API_KEY not configured — manual override only.",
        )

    client = anthropic.AsyncAnthropic(api_key=settings.anthropic_api_key)

    user_text = (
        f"You are watching a {body.title_id} game screen.\n"
        f"Mode: {body.mode}\n"
        f"Scenario: {body.scenario_id or 'custom'}\n"
        + (f"Secret weapon: {body.weapon_name}\n" if body.weapon_name else "")
        + (f"Formation: {body.formation}\n" if body.formation else "")
        + (f"Play: {body.play_name}\n" if body.play_name else "")
        + f"\n{body.detection.prompt_context}\n\n"
        "Analyse this frame and decide:\n"
        "1. Is a play currently being executed? (yes/no)\n"
        "2. Has a rep just completed? (yes/no)\n"
        "3. If completed: was it successful? (yes/no/unclear)\n"
        "   What coverage/defense did opponent show?\n"
        "   What play was called?\n"
        "   Did execution match the scenario objective?\n"
        "4. Confidence (0-100).\n\n"
        "Return ONLY JSON:\n"
        "{\n"
        '  "playInProgress": bool,\n'
        '  "repCompleted": bool,\n'
        '  "success": bool | null,\n'
        '  "coverageDetected": string | null,\n'
        '  "playDetected": string | null,\n'
        '  "executionQuality": "clean" | "poor" | null,\n'
        '  "confidence": number,\n'
        '  "reason": string\n'
        "}"
    )

    try:
        response = await client.messages.create(
            model=settings.claude_model,
            max_tokens=400,
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "image",
                            "source": {
                                "type": "base64",
                                "media_type": "image/jpeg",
                                "data": body.frame,
                            },
                        },
                        {"type": "text", "text": user_text},
                    ],
                }
            ],
        )
    except anthropic.APIError as exc:
        return FrameAnalysis(
            playInProgress=False,
            repCompleted=False,
            success=None,
            confidence=0,
            reason=f"VisionAudioForge upstream error: {exc}",
        )

    text = "".join(
        getattr(b, "text", "") for b in response.content if getattr(b, "type", None) == "text"
    ).strip()
    text = _strip_fence(text)

    try:
        parsed = json.loads(text)
    except json.JSONDecodeError:
        return FrameAnalysis(
            playInProgress=False,
            repCompleted=False,
            success=None,
            confidence=0,
            reason="VisionAudioForge returned non-JSON response — ignored.",
        )

    return FrameAnalysis(
        playInProgress=bool(parsed.get("playInProgress", False)),
        repCompleted=bool(parsed.get("repCompleted", False)),
        success=parsed.get("success"),
        coverageDetected=parsed.get("coverageDetected"),
        playDetected=parsed.get("playDetected"),
        executionQuality=parsed.get("executionQuality"),
        confidence=int(parsed.get("confidence", 0) or 0),
        reason=str(parsed.get("reason", "")),
    )


def _strip_fence(text: str) -> str:
    if text.startswith("```"):
        text = text.strip("`")
        if text.startswith("json"):
            text = text[4:]
    return text.strip()
