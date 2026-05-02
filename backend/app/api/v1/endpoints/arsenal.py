"""Secret Weapon Arsenal — CRUD + saved-weapon + usage-log endpoints."""

from __future__ import annotations

import uuid
from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy import and_, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import get_current_user
from app.db.base import get_db
from app.models.secret_weapon import SecretWeapon, UserArsenal, WeaponUsageLog
from app.models.user import User
from app.schemas.secret_weapon import (
    UsageLogCreate,
    UsageLogResponse,
    WeaponCreate,
    WeaponRateBody,
    WeaponResponse,
    WeaponUpdate,
)

router = APIRouter()


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

async def _saved_ids_for(db: AsyncSession, user_id: str) -> set[str]:
    rows = (
        await db.execute(
            select(UserArsenal.weapon_id).where(UserArsenal.user_id == user_id)
        )
    ).scalars().all()
    return set(rows)


def _to_response(weapon: SecretWeapon, saved_ids: set[str]) -> WeaponResponse:
    return WeaponResponse(
        id=weapon.id,
        user_id=weapon.user_id,
        title_id=weapon.title_id,
        name=weapon.name,
        category=weapon.category,
        sub_category=weapon.sub_category,
        formation=weapon.formation,
        play_name=weapon.play_name,
        description=weapon.description,
        instructions=weapon.instructions or [],
        setup_steps=weapon.setup_steps or [],
        when_to_use=weapon.when_to_use,
        trigger_conditions=weapon.trigger_conditions or {},
        difficulty=weapon.difficulty,  # type: ignore[arg-type]
        title_specific_data=weapon.title_specific_data or {},
        patch_version=weapon.patch_version,
        source_type=weapon.source_type,  # type: ignore[arg-type]
        source_url=weapon.source_url,
        video_url=weapon.video_url,
        thumbnail_url=weapon.thumbnail_url,
        tags=weapon.tags or [],
        verified=weapon.verified,
        success_rate=weapon.success_rate,
        times_used=weapon.times_used,
        community_rating=weapon.community_rating,
        community_votes=weapon.community_votes,
        saved=weapon.id in saved_ids,
        created_at=weapon.created_at,
        updated_at=weapon.updated_at,
    )


# ---------------------------------------------------------------------------
# Weapon library
# ---------------------------------------------------------------------------

@router.get("/weapons", response_model=list[WeaponResponse])
async def list_weapons(
    title_id: str = Query(..., min_length=1),
    category: str | None = None,
    difficulty: Literal["easy", "medium", "hard"] | None = None,
    source: Literal["platform", "community", "my-uploads"] | None = None,
    situation: str | None = None,
    sort: Literal[
        "most-used", "highest-rated", "most-recent", "easiest"
    ] = "most-recent",
    q: str | None = None,
    saved_only: bool = False,
    limit: int = Query(60, ge=1, le=200),
    offset: int = Query(0, ge=0),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> list[WeaponResponse]:
    """Filtered list of weapons for a title."""
    stmt = select(SecretWeapon).where(SecretWeapon.title_id == title_id)

    if category:
        stmt = stmt.where(SecretWeapon.category == category)
    if difficulty:
        stmt = stmt.where(SecretWeapon.difficulty == difficulty)
    if source == "platform":
        stmt = stmt.where(SecretWeapon.source_type == "platform")
    elif source == "community":
        stmt = stmt.where(SecretWeapon.source_type.in_(["web-discovery", "user-upload"]))
        stmt = stmt.where(SecretWeapon.user_id != current_user.id)
    elif source == "my-uploads":
        stmt = stmt.where(SecretWeapon.user_id == current_user.id)

    if q:
        like = f"%{q.lower()}%"
        stmt = stmt.where(
            or_(
                SecretWeapon.name.ilike(like),
                SecretWeapon.description.ilike(like),
                SecretWeapon.when_to_use.ilike(like),
            )
        )

    if saved_only:
        saved_ids = await _saved_ids_for(db, current_user.id)
        if not saved_ids:
            return []
        stmt = stmt.where(SecretWeapon.id.in_(saved_ids))

    if sort == "most-used":
        stmt = stmt.order_by(SecretWeapon.times_used.desc())
    elif sort == "highest-rated":
        stmt = stmt.order_by(SecretWeapon.community_rating.desc())
    elif sort == "easiest":
        # custom ordering: easy < medium < hard
        diff_order = {"easy": 0, "medium": 1, "hard": 2}
        rows = (await db.execute(stmt)).scalars().all()
        rows = sorted(rows, key=lambda w: diff_order.get(w.difficulty, 3))
        rows = rows[offset: offset + limit]
        saved_ids = await _saved_ids_for(db, current_user.id)
        return [_to_response(r, saved_ids) for r in rows]
    else:  # most-recent
        stmt = stmt.order_by(SecretWeapon.created_at.desc())

    stmt = stmt.offset(offset).limit(limit)
    rows = (await db.execute(stmt)).scalars().all()

    saved_ids = await _saved_ids_for(db, current_user.id)
    if situation:
        # situation is a free-form pill — match against tags or trigger_conditions
        sit = situation.lower()
        rows = [
            r
            for r in rows
            if sit in [t.lower() for t in (r.tags or [])]
            or sit in (r.when_to_use or "").lower()
        ]

    return [_to_response(r, saved_ids) for r in rows]


@router.get("/weapons/{weapon_id}", response_model=WeaponResponse)
async def get_weapon(
    weapon_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> WeaponResponse:
    weapon = await db.get(SecretWeapon, weapon_id)
    if not weapon:
        raise HTTPException(status_code=404, detail="Weapon not found")
    saved_ids = await _saved_ids_for(db, current_user.id)
    return _to_response(weapon, saved_ids)


@router.post(
    "/weapons", response_model=WeaponResponse, status_code=status.HTTP_201_CREATED
)
async def create_weapon(
    body: WeaponCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> WeaponResponse:
    weapon = SecretWeapon(
        user_id=current_user.id,
        title_id=body.title_id,
        name=body.name,
        category=body.category,
        sub_category=body.sub_category,
        formation=body.formation,
        play_name=body.play_name,
        description=body.description,
        instructions=body.instructions,
        setup_steps=body.setup_steps,
        when_to_use=body.when_to_use,
        trigger_conditions=body.trigger_conditions,
        difficulty=body.difficulty,
        title_specific_data=body.title_specific_data,
        patch_version=body.patch_version,
        source_type=body.source_type or "user-upload",
        source_url=body.source_url,
        video_url=body.video_url,
        thumbnail_url=body.thumbnail_url,
        tags=body.tags,
        verified=False,
    )
    db.add(weapon)
    await db.commit()
    await db.refresh(weapon)
    return _to_response(weapon, set())


@router.patch("/weapons/{weapon_id}", response_model=WeaponResponse)
async def update_weapon(
    weapon_id: str,
    body: WeaponUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> WeaponResponse:
    weapon = await db.get(SecretWeapon, weapon_id)
    if not weapon:
        raise HTTPException(status_code=404, detail="Weapon not found")
    if weapon.user_id and weapon.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Can only edit your own weapons")

    for field, value in body.model_dump(exclude_unset=True).items():
        setattr(weapon, field, value)
    await db.commit()
    await db.refresh(weapon)
    saved_ids = await _saved_ids_for(db, current_user.id)
    return _to_response(weapon, saved_ids)


@router.delete("/weapons/{weapon_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_weapon(
    weapon_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Response:
    weapon = await db.get(SecretWeapon, weapon_id)
    if not weapon:
        raise HTTPException(status_code=404, detail="Weapon not found")
    if weapon.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Can only delete your own weapons")
    await db.delete(weapon)
    await db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)


# ---------------------------------------------------------------------------
# My Arsenal (saved weapons)
# ---------------------------------------------------------------------------

@router.get("/my-arsenal", response_model=list[WeaponResponse])
async def list_my_arsenal(
    title_id: str | None = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> list[WeaponResponse]:
    stmt = (
        select(SecretWeapon, UserArsenal)
        .join(UserArsenal, UserArsenal.weapon_id == SecretWeapon.id)
        .where(UserArsenal.user_id == current_user.id)
    )
    if title_id:
        stmt = stmt.where(SecretWeapon.title_id == title_id)
    stmt = stmt.order_by(UserArsenal.saved_at.desc())
    rows = (await db.execute(stmt)).all()
    saved_ids = {r[0].id for r in rows}
    return [_to_response(r[0], saved_ids) for r in rows]


@router.post(
    "/my-arsenal/{weapon_id}",
    response_model=WeaponResponse,
    status_code=status.HTTP_201_CREATED,
)
async def save_weapon(
    weapon_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> WeaponResponse:
    weapon = await db.get(SecretWeapon, weapon_id)
    if not weapon:
        raise HTTPException(status_code=404, detail="Weapon not found")

    existing = (
        await db.execute(
            select(UserArsenal).where(
                and_(
                    UserArsenal.user_id == current_user.id,
                    UserArsenal.weapon_id == weapon_id,
                )
            )
        )
    ).scalar_one_or_none()
    if not existing:
        link = UserArsenal(
            id=str(uuid.uuid4()),
            user_id=current_user.id,
            weapon_id=weapon_id,
            title_id=weapon.title_id,
        )
        db.add(link)
        await db.commit()

    saved_ids = await _saved_ids_for(db, current_user.id)
    return _to_response(weapon, saved_ids)


@router.delete("/my-arsenal/{weapon_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_from_arsenal(
    weapon_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Response:
    link = (
        await db.execute(
            select(UserArsenal).where(
                and_(
                    UserArsenal.user_id == current_user.id,
                    UserArsenal.weapon_id == weapon_id,
                )
            )
        )
    ).scalar_one_or_none()
    if link:
        await db.delete(link)
        await db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)


# ---------------------------------------------------------------------------
# Usage logging
# ---------------------------------------------------------------------------

@router.post(
    "/usage-log", response_model=UsageLogResponse, status_code=status.HTTP_201_CREATED
)
async def log_usage(
    body: UsageLogCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> UsageLogResponse:
    weapon = await db.get(SecretWeapon, body.weapon_id)
    if not weapon:
        raise HTTPException(status_code=404, detail="Weapon not found")

    # outcome shorthand wins over `worked` if provided.
    worked = body.worked
    if body.outcome == "yes":
        worked = True
    elif body.outcome == "no":
        worked = False
    elif body.outcome == "not-used":
        worked = None

    log = WeaponUsageLog(
        user_id=current_user.id,
        weapon_id=body.weapon_id,
        session_id=body.session_id,
        title_id=body.title_id,
        game_state=body.game_state,
        deployed=body.deployed,
        worked=worked,
        opponent_adjusted=body.opponent_adjusted,
        notes=body.notes,
    )
    db.add(log)

    # Update success_rate / times_used on actual deployments.
    if body.deployed:
        weapon.times_used = (weapon.times_used or 0) + 1
        if worked is not None:
            # running average: new_rate = ((old_rate * (n-1)) + (1 if worked else 0)) / n
            n = weapon.times_used
            old = weapon.success_rate or 0.0
            new_rate = ((old * (n - 1)) + (1.0 if worked else 0.0)) / n
            weapon.success_rate = round(new_rate, 4)

    await db.commit()
    await db.refresh(log)
    return UsageLogResponse.model_validate(log)


# ---------------------------------------------------------------------------
# Rating
# ---------------------------------------------------------------------------

@router.post("/weapons/{weapon_id}/rate", response_model=WeaponResponse)
async def rate_weapon(
    weapon_id: str,
    body: WeaponRateBody,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> WeaponResponse:
    weapon = await db.get(SecretWeapon, weapon_id)
    if not weapon:
        raise HTTPException(status_code=404, detail="Weapon not found")

    n = (weapon.community_votes or 0) + 1
    old = weapon.community_rating or 0.0
    new_rating = ((old * (n - 1)) + body.stars) / n
    weapon.community_rating = round(new_rating, 3)
    weapon.community_votes = n
    await db.commit()
    await db.refresh(weapon)
    saved_ids = await _saved_ids_for(db, current_user.id)
    return _to_response(weapon, saved_ids)
