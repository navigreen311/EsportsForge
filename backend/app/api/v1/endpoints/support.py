"""Support ticket & feedback endpoints."""

from __future__ import annotations

from datetime import datetime
from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import get_current_user
from app.db.base import get_db
from app.models.support_ticket import SupportTicket
from app.models.user import User

router = APIRouter(tags=["Support"])


# ---------------------------------------------------------------------------
# Schemas
# ---------------------------------------------------------------------------

class TicketCreateRequest(BaseModel):
    subject: str = Field(..., min_length=1, max_length=500)
    category: Literal["billing", "bug", "account", "feature", "other"] = "other"
    body: str = Field(..., min_length=1, max_length=5000)


class TicketOut(BaseModel):
    id: str
    user_id: str
    email: str
    subject: str
    body: str
    category: str
    priority: str
    status: str
    admin_notes: str | None = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class TicketListOut(BaseModel):
    tickets: list[TicketOut]
    total: int
    page: int
    page_size: int


class FeedbackRequest(BaseModel):
    rating: Literal["good", "okay", "bad"]
    message: str | None = Field(None, max_length=2000)
    page: str = Field(..., max_length=500)


class FeedbackOut(BaseModel):
    id: str
    message: str


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@router.post("/tickets", response_model=TicketOut, status_code=status.HTTP_201_CREATED)
async def create_ticket(
    payload: TicketCreateRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Create a new support ticket."""
    ticket = SupportTicket(
        user_id=current_user.id,
        email=current_user.email,
        subject=payload.subject,
        category=payload.category,
        body=payload.body,
    )
    db.add(ticket)
    await db.flush()
    await db.refresh(ticket)
    return ticket


@router.get("/tickets", response_model=TicketListOut)
async def list_tickets(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List the current user's support tickets with pagination."""
    base = select(SupportTicket).where(SupportTicket.user_id == current_user.id)

    total_result = await db.execute(select(func.count()).select_from(base.subquery()))
    total = total_result.scalar() or 0

    query = (
        base
        .order_by(SupportTicket.created_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    )
    result = await db.execute(query)
    tickets = result.scalars().all()

    return TicketListOut(tickets=tickets, total=total, page=page, page_size=page_size)


@router.get("/tickets/{ticket_id}", response_model=TicketOut)
async def get_ticket(
    ticket_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get a single support ticket (must belong to the current user)."""
    result = await db.execute(
        select(SupportTicket).where(
            SupportTicket.id == ticket_id,
            SupportTicket.user_id == current_user.id,
        )
    )
    ticket = result.scalar_one_or_none()
    if not ticket:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Ticket not found")
    return ticket


@router.post("/feedback", response_model=FeedbackOut, status_code=status.HTTP_201_CREATED)
async def submit_feedback(
    payload: FeedbackRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Quick feedback submission — stored as a support ticket with category='feedback'."""
    body = f"Rating: {payload.rating}\nPage: {payload.page}"
    if payload.message:
        body += f"\n\n{payload.message}"

    ticket = SupportTicket(
        user_id=current_user.id,
        email=current_user.email,
        subject=f"Feedback — {payload.rating}",
        body=body,
        category="feedback",
        priority="low",
    )
    db.add(ticket)
    await db.flush()
    await db.refresh(ticket)
    return FeedbackOut(id=ticket.id, message="Thank you for your feedback!")
