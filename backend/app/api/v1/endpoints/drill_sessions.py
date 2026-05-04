"""Drill execution session endpoints — start a drill, log each rep, complete.

The vision/monitor sub-route lives here too (added in a later commit).
"""

from __future__ import annotations

import json
import logging
import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import get_current_user
from app.db.base import get_db
from app.models.drill_session import DrillRep, DrillSession
from app.models.user import User
from app.services.ai.claude_client import ClaudeClient

logger = logging.getLogger(__name__)
_claude = ClaudeClient()

router = APIRouter(tags=["DrillSessions"])


# ---------------------------------------------------------------------------
# Schemas
# ---------------------------------------------------------------------------


class DrillSessionStartRequest(BaseModel):
    drill_id: str
    drill_type: str | None = None
    title_id: str
    total_reps: int = Field(gt=0, le=100)


class DrillRepOut(BaseModel):
    rep_number: int
    success: bool
    auto_detected: bool
    confidence: float | None
    reason: str | None

    model_config = {"from_attributes": True}


class DrillSessionOut(BaseModel):
    id: str
    drill_id: str
    drill_type: str | None
    title_id: str
    total_reps: int
    completed_reps: int
    success_reps: int
    fail_reps: int
    success_rate: float
    auto_detected: bool
    status: str
    started_at: datetime
    completed_at: datetime | None
    reps: list[DrillRepOut] = []

    model_config = {"from_attributes": True}


class DrillRepRequest(BaseModel):
    rep_number: int = Field(ge=1)
    success: bool
    auto_detected: bool = False
    confidence: float | None = Field(default=None, ge=0.0, le=1.0)
    reason: str | None = Field(default=None, max_length=500)


class DrillSessionRepUpdate(BaseModel):
    completed_reps: int
    success_reps: int
    fail_reps: int
    success_rate: float


class DrillDebrief(BaseModel):
    """Mock-formulaic LoopAI debrief returned when a session completes.

    Pure deterministic math right now — no Claude call. Real LoopAI insight
    can be wired in when an ANTHROPIC_API_KEY is configured by replacing the
    body of :func:`_build_debrief`.
    """

    success_rate: float
    success_reps: int
    fail_reps: int
    total_reps: int
    auto_detected_pct: float
    skill_update: str
    player_twin_note: str
    loop_ai_insight: str
    mastery_change: int
    difficulty_recommendation: str
    next_drill_hint: str | None


class DrillSessionCompleteOut(BaseModel):
    session: DrillSessionOut
    debrief: DrillDebrief


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


async def _load_session(
    session_id: str,
    user: User,
    db: AsyncSession,
) -> DrillSession:
    """Fetch a session owned by the current user, or 404."""
    try:
        uuid.UUID(session_id)
    except ValueError:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Invalid session id.")

    result = await db.execute(
        select(DrillSession).where(
            DrillSession.id == session_id,
            DrillSession.user_id == user.id,
        )
    )
    sess = result.scalar_one_or_none()
    if sess is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Drill session not found.")
    return sess


def _recalc(sess: DrillSession) -> None:
    sess.completed_reps = sess.success_reps + sess.fail_reps
    sess.success_rate = (
        sess.success_reps / sess.completed_reps if sess.completed_reps else 0.0
    )


def _build_debrief(sess: DrillSession) -> DrillDebrief:
    """Deterministic post-session insight — replaces a real LoopAI call."""
    rate = sess.success_rate
    auto_count = sum(1 for r in sess.reps if r.auto_detected)
    auto_pct = (auto_count / sess.completed_reps) if sess.completed_reps else 0.0

    if rate >= 0.9:
        difficulty = "increase"
        mastery_change = 3
        skill_update = "Mastery climbing — challenge level raised."
        loop_insight = (
            "Strong, consistent execution. PlayerTwin baseline raised; "
            "next session adds two reps at the higher tier."
        )
    elif rate <= 0.5:
        difficulty = "decrease"
        mastery_change = -1
        skill_update = "Foundation rebuild — difficulty dialled back."
        loop_insight = (
            "Tough session. Dropping difficulty by one tier and reducing "
            "rep count to rebuild rhythm before pushing again."
        )
    else:
        difficulty = "hold"
        mastery_change = 1
        skill_update = "Steady gains — same difficulty until 90% hit."
        loop_insight = (
            "Solid session. Stay at this tier; once you hit 90% the "
            "difficulty advances automatically."
        )

    return DrillDebrief(
        success_rate=round(rate, 3),
        success_reps=sess.success_reps,
        fail_reps=sess.fail_reps,
        total_reps=sess.total_reps,
        auto_detected_pct=round(auto_pct, 3),
        skill_update=skill_update,
        player_twin_note=(
            f"PlayerTwin updated for {sess.title_id} / {sess.drill_id}. "
            "Confirm transfer with 3 ranked sessions."
        ),
        loop_ai_insight=loop_insight,
        mastery_change=mastery_change,
        difficulty_recommendation=difficulty,
        next_drill_hint=None,
    )


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------


@router.post("/start", status_code=status.HTTP_201_CREATED, response_model=DrillSessionOut)
async def start_drill_session(
    payload: DrillSessionStartRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> DrillSession:
    sess = DrillSession(
        user_id=current_user.id,
        drill_id=payload.drill_id,
        drill_type=payload.drill_type,
        title_id=payload.title_id,
        total_reps=payload.total_reps,
        started_at=datetime.now(timezone.utc),
    )
    db.add(sess)
    await db.flush()
    await db.refresh(sess)
    return sess


@router.post("/{session_id}/rep", response_model=DrillSessionRepUpdate)
async def record_rep(
    session_id: str,
    payload: DrillRepRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> DrillSessionRepUpdate:
    sess = await _load_session(session_id, current_user, db)
    if sess.status != "active":
        raise HTTPException(status.HTTP_409_CONFLICT, "Session is not active.")
    if payload.rep_number > sess.total_reps:
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST,
            f"rep_number {payload.rep_number} exceeds total_reps {sess.total_reps}.",
        )

    rep = DrillRep(
        drill_session_id=sess.id,
        rep_number=payload.rep_number,
        success=payload.success,
        auto_detected=payload.auto_detected,
        confidence=payload.confidence,
        reason=payload.reason,
    )
    db.add(rep)

    if payload.success:
        sess.success_reps += 1
    else:
        sess.fail_reps += 1
    if payload.auto_detected:
        sess.auto_detected = True
    _recalc(sess)
    await db.flush()

    return DrillSessionRepUpdate(
        completed_reps=sess.completed_reps,
        success_reps=sess.success_reps,
        fail_reps=sess.fail_reps,
        success_rate=round(sess.success_rate, 3),
    )


@router.post("/{session_id}/complete", response_model=DrillSessionCompleteOut)
async def complete_drill_session(
    session_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> DrillSessionCompleteOut:
    sess = await _load_session(session_id, current_user, db)
    if sess.status == "complete":
        # Idempotent — return current state.
        return DrillSessionCompleteOut(
            session=DrillSessionOut.model_validate(sess),
            debrief=_build_debrief(sess),
        )

    sess.status = "complete"
    sess.completed_at = datetime.now(timezone.utc)
    _recalc(sess)
    await db.flush()
    await db.refresh(sess)

    return DrillSessionCompleteOut(
        session=DrillSessionOut.model_validate(sess),
        debrief=_build_debrief(sess),
    )


@router.get("/{session_id}", response_model=DrillSessionOut)
async def get_drill_session(
    session_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> DrillSession:
    return await _load_session(session_id, current_user, db)


# ---------------------------------------------------------------------------
# Vision monitor — Claude vision per frame
# ---------------------------------------------------------------------------


class VisionFrameRequest(BaseModel):
    drill_type: str
    title_id: str
    image_base64: str = Field(min_length=100)
    watch_for: list[str]
    success_criteria: str
    fail_criteria: str


class VisionFrameResponse(BaseModel):
    rep_in_progress: bool = False
    rep_completed: bool = False
    success: bool = False
    confidence: float = 0.0
    reason: str | None = None
    mode: str = "vision"


_VISION_SYSTEM = (
    "You are an esports drill coach watching a single video frame from a "
    "player's game. Decide whether a drill rep just completed in this frame, "
    "and if so whether it was a success or a fail. "
    "Respond with strict JSON only — no markdown, no commentary."
)


def _build_vision_prompt(req: VisionFrameRequest) -> str:
    return json.dumps(
        {
            "title": req.title_id,
            "drill_type": req.drill_type,
            "watch_for": req.watch_for,
            "success_criteria": req.success_criteria,
            "fail_criteria": req.fail_criteria,
            "instructions": (
                "Inspect the attached frame. "
                "Return: rep_in_progress (bool), rep_completed (bool), "
                "success (bool — only meaningful when rep_completed), "
                "confidence (0..1), reason (short string)."
            ),
        }
    )


@router.post("/vision/monitor", response_model=VisionFrameResponse)
async def vision_monitor(
    payload: VisionFrameRequest,
    _user: User = Depends(get_current_user),
) -> VisionFrameResponse:
    if not _claude.is_available:
        return VisionFrameResponse(mode="unavailable", reason="no_anthropic_key")

    try:
        response = await _claude._client.messages.create(  # noqa: SLF001
            model=_claude._model,  # noqa: SLF001
            max_tokens=200,
            temperature=0.1,
            system=_VISION_SYSTEM,
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "image",
                            "source": {
                                "type": "base64",
                                "media_type": "image/jpeg",
                                "data": payload.image_base64,
                            },
                        },
                        {"type": "text", "text": _build_vision_prompt(payload)},
                    ],
                }
            ],
        )
    except Exception as exc:  # noqa: BLE001
        logger.warning("vision_monitor: claude call failed: %s", exc)
        return VisionFrameResponse(mode="unavailable", reason="claude_error")

    text = response.content[0].text.strip()
    if text.startswith("```"):
        text = "\n".join(
            ln for ln in text.split("\n") if not ln.strip().startswith("```")
        )
    try:
        data = json.loads(text)
    except json.JSONDecodeError:
        logger.info("vision_monitor: non-JSON response: %s", text[:200])
        return VisionFrameResponse(mode="vision", reason="parse_error")

    return VisionFrameResponse(
        rep_in_progress=bool(data.get("rep_in_progress", False)),
        rep_completed=bool(data.get("rep_completed", False)),
        success=bool(data.get("success", False)),
        confidence=float(data.get("confidence", 0.0) or 0.0),
        reason=data.get("reason"),
        mode="vision",
    )
