"""Two-Factor Authentication endpoints using TOTP (RFC 6238)."""

import base64
import io

import pyotp
import qrcode
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import get_current_user
from app.db.base import get_db
from app.models.user import User

router = APIRouter()


# ---------------------------------------------------------------------------
# Schemas
# ---------------------------------------------------------------------------

class TOTPCodeRequest(BaseModel):
    code: str


class SetupResponse(BaseModel):
    secret: str
    qr_code: str  # base64-encoded PNG


class StatusResponse(BaseModel):
    enabled: bool


class MessageResponse(BaseModel):
    message: str


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@router.post("/setup", response_model=SetupResponse)
async def setup_2fa(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Generate a TOTP secret and return a QR code for authenticator apps."""
    if current_user.two_factor_enabled:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="2FA is already enabled. Disable it first to re-setup.",
        )

    secret = pyotp.random_base32()
    current_user.two_factor_secret = secret
    await db.commit()

    totp = pyotp.TOTP(secret)
    provisioning_uri = totp.provisioning_uri(
        name=current_user.email,
        issuer_name="EsportsForge",
    )

    # Generate QR code as base64 PNG
    img = qrcode.make(provisioning_uri)
    buffer = io.BytesIO()
    img.save(buffer, format="PNG")
    qr_b64 = base64.b64encode(buffer.getvalue()).decode("utf-8")

    return SetupResponse(secret=secret, qr_code=qr_b64)


@router.post("/verify", response_model=MessageResponse)
async def verify_2fa(
    body: TOTPCodeRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Verify a TOTP code and enable 2FA on success."""
    if current_user.two_factor_enabled:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="2FA is already enabled.",
        )
    if not current_user.two_factor_secret:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Call /setup first to generate a secret.",
        )

    totp = pyotp.TOTP(current_user.two_factor_secret)
    if not totp.verify(body.code):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid TOTP code.",
        )

    current_user.two_factor_enabled = True
    await db.commit()
    return MessageResponse(message="2FA has been enabled successfully.")


@router.post("/disable", response_model=MessageResponse)
async def disable_2fa(
    body: TOTPCodeRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Disable 2FA. Requires a valid TOTP code for confirmation."""
    if not current_user.two_factor_enabled:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="2FA is not enabled.",
        )

    assert current_user.two_factor_secret is not None
    totp = pyotp.TOTP(current_user.two_factor_secret)
    if not totp.verify(body.code):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid TOTP code.",
        )

    current_user.two_factor_enabled = False
    current_user.two_factor_secret = None
    await db.commit()
    return MessageResponse(message="2FA has been disabled.")


@router.get("/status", response_model=StatusResponse)
async def get_2fa_status(
    current_user: User = Depends(get_current_user),
):
    """Return whether 2FA is enabled for the current user."""
    return StatusResponse(enabled=current_user.two_factor_enabled)
