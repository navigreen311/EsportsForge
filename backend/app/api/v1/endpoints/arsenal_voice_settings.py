"""Arsenal voice coaching settings endpoints.

GET  /users/me/arsenal-voice-settings  — return current settings (defaults if empty)
PATCH /users/me/arsenal-voice-settings — partial merge update
"""

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import get_current_user
from app.db.base import get_db
from app.models.identity_profile import IdentityProfile
from app.models.user import User
from app.schemas.arsenal_voice_settings import (
    ArsenalVoiceSettingsPatch,
    ArsenalVoiceSettingsRead,
)

router = APIRouter()

_DEFAULTS: dict = {
    "enabled": True,
    "guidedPractice": True,
    "postDebrief": True,
    "preExecBrief": True,
    "tone": "standard",
}


async def _get_or_create_profile(user: User, db: AsyncSession) -> IdentityProfile:
    result = await db.execute(
        select(IdentityProfile).where(IdentityProfile.user_id == str(user.id))
    )
    profile = result.scalar_one_or_none()
    if profile is None:
        profile = IdentityProfile(user_id=str(user.id))
        db.add(profile)
        await db.flush()
    return profile


@router.get("/users/me/arsenal-voice-settings", response_model=ArsenalVoiceSettingsRead)
async def get_arsenal_voice_settings(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ArsenalVoiceSettingsRead:
    profile = await _get_or_create_profile(current_user, db)
    stored: dict = profile.arsenal_voice_settings or {}
    merged = {**_DEFAULTS, **stored}
    return ArsenalVoiceSettingsRead(**merged)


@router.patch("/users/me/arsenal-voice-settings", response_model=ArsenalVoiceSettingsRead)
async def patch_arsenal_voice_settings(
    payload: ArsenalVoiceSettingsPatch,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ArsenalVoiceSettingsRead:
    profile = await _get_or_create_profile(current_user, db)
    stored: dict = dict(profile.arsenal_voice_settings or {})
    patch = payload.model_dump(exclude_unset=True)
    stored.update(patch)
    profile.arsenal_voice_settings = stored
    await db.flush()
    merged = {**_DEFAULTS, **stored}
    return ArsenalVoiceSettingsRead(**merged)
