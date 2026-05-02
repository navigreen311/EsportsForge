"""Certifications endpoints — skill-based player certifications."""

from __future__ import annotations


from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import get_current_user
from app.db.base import get_db
from app.models.certification import Certification
from app.models.user import User

router = APIRouter(tags=["Certifications"])


# ---------------------------------------------------------------------------
# Schemas
# ---------------------------------------------------------------------------

class CertificationResponse(BaseModel):
    id: str
    title_id: str
    skill_dimension: str
    percentile: int
    awarded_at: str


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@router.get("", response_model=list[CertificationResponse])
async def list_certifications(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List all certifications for the current user."""
    result = await db.execute(
        select(Certification)
        .where(Certification.user_id == str(current_user.id))
        .order_by(Certification.awarded_at.desc())
    )
    certs = result.scalars().all()

    return [
        CertificationResponse(
            id=c.id,
            title_id=c.title_id,
            skill_dimension=c.skill_dimension,
            percentile=c.percentile,
            awarded_at=c.awarded_at.isoformat(),
        )
        for c in certs
    ]


@router.get("/{cert_id}", response_model=CertificationResponse)
async def get_certification(
    cert_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get a specific certification by ID."""
    result = await db.execute(
        select(Certification)
        .where(Certification.id == cert_id)
        .where(Certification.user_id == str(current_user.id))
    )
    cert = result.scalar_one_or_none()

    if not cert:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Certification not found.",
        )

    return CertificationResponse(
        id=cert.id,
        title_id=cert.title_id,
        skill_dimension=cert.skill_dimension,
        percentile=cert.percentile,
        awarded_at=cert.awarded_at.isoformat(),
    )
