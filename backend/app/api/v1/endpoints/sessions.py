"""Game session endpoints — CRUD for match/session records."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field

router = APIRouter(tags=["Sessions"])


# ---------------------------------------------------------------------------
# Schemas
# ---------------------------------------------------------------------------

class SessionCreate(BaseModel):
    """Payload for creating a new game session."""

    user_id: uuid.UUID
    title: str = Field(max_length=100, description="Game title slug, e.g. 'madden26'.")
    mode: str = Field(description="Game mode: ranked | tournament | training.")
    opponent_id: uuid.UUID | None = None


class SessionUpdate(BaseModel):
    """Payload for updating an existing session (add result, stats)."""

    result: str | None = Field(default=None, description="Outcome: win | loss | draw.")
    stats: dict[str, Any] | None = None
    session_duration: int | None = Field(default=None, description="Duration in seconds.")
    recommendations_followed: dict[str, Any] | None = None


class SessionOut(BaseModel):
    """Response schema for a game session."""

    id: uuid.UUID
    user_id: uuid.UUID
    title: str
    mode: str
    opponent_id: uuid.UUID | None = None
    result: str | None = None
    stats: dict[str, Any] | None = None
    recommendations_followed: dict[str, Any] | None = None
    session_duration: int | None = None
    played_at: datetime
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class SessionListOut(BaseModel):
    """Paginated list of sessions."""

    items: list[SessionOut]
    total: int
    page: int
    page_size: int


# ---------------------------------------------------------------------------
# Mock store
# ---------------------------------------------------------------------------

_sessions: dict[uuid.UUID, dict] = {}


def _make_session(data: dict) -> dict:
    """Stamp a session dict with id and timestamps."""
    now = datetime.now(timezone.utc)
    return {
        "id": uuid.uuid4(),
        "created_at": now,
        "updated_at": now,
        "played_at": now,
        "result": None,
        "stats": None,
        "recommendations_followed": None,
        "session_duration": None,
        **data,
    }


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@router.post(
    "",
    response_model=SessionOut,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new game session",
)
async def create_session(payload: SessionCreate) -> SessionOut:
    """Record a new game session / match."""
    session = _make_session(payload.model_dump())
    _sessions[session["id"]] = session
    return SessionOut(**session)


@router.get(
    "",
    response_model=SessionListOut,
    summary="List sessions with filtering",
)
async def list_sessions(
    title: str | None = Query(default=None, description="Filter by game title."),
    mode: str | None = Query(default=None, description="Filter by game mode."),
    played_after: datetime | None = Query(default=None, description="Sessions played after this date."),
    played_before: datetime | None = Query(default=None, description="Sessions played before this date."),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
) -> SessionListOut:
    """Return a paginated, filterable list of game sessions."""
    items = list(_sessions.values())

    if title:
        items = [s for s in items if s["title"] == title]
    if mode:
        items = [s for s in items if s["mode"] == mode]
    if played_after:
        items = [s for s in items if s["played_at"] >= played_after]
    if played_before:
        items = [s for s in items if s["played_at"] <= played_before]

    total = len(items)
    start = (page - 1) * page_size
    page_items = items[start : start + page_size]

    return SessionListOut(
        items=[SessionOut(**s) for s in page_items],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.get(
    "/{session_id}",
    response_model=SessionOut,
    summary="Get session detail",
)
async def get_session(session_id: uuid.UUID) -> SessionOut:
    """Retrieve a single game session by ID."""
    session = _sessions.get(session_id)
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found.",
        )
    return SessionOut(**session)


@router.patch(
    "/{session_id}",
    response_model=SessionOut,
    summary="Update a session (add result, stats)",
)
async def update_session(session_id: uuid.UUID, payload: SessionUpdate) -> SessionOut:
    """Update an existing session with result, stats, or duration."""
    session = _sessions.get(session_id)
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found.",
        )

    update_data = payload.model_dump(exclude_unset=True)
    session.update(update_data)
    session["updated_at"] = datetime.now(timezone.utc)
    return SessionOut(**session)
