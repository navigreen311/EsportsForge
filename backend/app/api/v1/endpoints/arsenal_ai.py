"""ArsenalAI endpoints — discover (Claude web_search), trigger, recommendations."""

from __future__ import annotations

import time
from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import get_current_user
from app.db.base import get_db
from app.models.secret_weapon import SecretWeapon, UserArsenal
from app.models.user import User
from app.schemas.secret_weapon import WeaponResponse
from app.services.arsenal_ai import (
    build_discover_system,
    build_trigger_system,
    call_claude,
    parse_json_array,
    parse_json_object,
)

router = APIRouter()


# ---------------------------------------------------------------------------
# In-memory caches (per process — fine for dev)
# ---------------------------------------------------------------------------

_discover_cache: dict[str, tuple[float, list[str]]] = {}
_trigger_cache: dict[str, tuple[float, dict[str, Any]]] = {}


# ---------------------------------------------------------------------------
# Discover
# ---------------------------------------------------------------------------

class DiscoverBody(BaseModel):
    query: str
    title_id: str
    patch_version: str | None = None


@router.post("/discover", response_model=list[WeaponResponse])
async def discover(
    body: DiscoverBody,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> list[WeaponResponse]:
    """Run a Claude web_search and persist any new SecretWeapon rows."""
    cache_key = f"{body.title_id}::{body.query.lower().strip()}"
    cached = _discover_cache.get(cache_key)
    if cached and time.time() - cached[0] < 60 * 60 * 24:  # 24h
        weapon_ids: list[str] = cached[1]
        rows = (
            await db.execute(
                select(SecretWeapon).where(SecretWeapon.id.in_(weapon_ids))
            )
        ).scalars().all()
        return [_to_response(r) for r in rows]

    system = build_discover_system(body.title_id, body.patch_version)
    raw = await call_claude(
        system=system,
        user_content=body.query,
        max_tokens=3000,
        tools=[{"type": "web_search_20250305", "name": "web_search"}],
    )
    if not raw:
        raise HTTPException(
            status_code=503,
            detail="ArsenalAI is unavailable — ANTHROPIC_API_KEY not configured",
        )

    items = parse_json_array(raw)

    saved: list[SecretWeapon] = []
    for item in items[:6]:
        try:
            weapon = SecretWeapon(
                user_id=None,
                title_id=body.title_id,
                name=str(item.get("name", "Unnamed weapon"))[:200],
                category=str(item.get("category", "Situational")),
                formation=item.get("formation"),
                play_name=item.get("play_name") or item.get("playName"),
                description=str(item.get("description", "")),
                instructions=list(item.get("instructions", []) or []),
                setup_steps=list(
                    item.get("setup_steps", []) or item.get("setupSteps", []) or []
                ),
                when_to_use=str(
                    item.get("when_to_use") or item.get("whenToUse") or ""
                ),
                trigger_conditions=item.get("trigger_conditions")
                or item.get("triggerConditions")
                or {},
                difficulty=item.get("difficulty", "medium"),
                source_type="web-discovery",
                source_url=item.get("source_url") or item.get("sourceUrl"),
                tags=list(item.get("tags", []) or []),
                verified=False,
            )
            db.add(weapon)
            saved.append(weapon)
        except Exception:
            continue

    if saved:
        await db.commit()
        for w in saved:
            await db.refresh(w)

    _discover_cache[cache_key] = (time.time(), [w.id for w in saved])
    return [_to_response(w) for w in saved]


# ---------------------------------------------------------------------------
# Trigger
# ---------------------------------------------------------------------------

class TriggerBody(BaseModel):
    title_id: str
    game_state: dict[str, Any]
    session_id: str | None = None


@router.post("/trigger")
async def trigger(
    body: TriggerBody,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """Evaluate the player's saved weapons against current game state."""
    cache_key = f"{current_user.id}::{body.session_id or '_'}::{body.title_id}"
    cached = _trigger_cache.get(cache_key)
    if cached and time.time() - cached[0] < 90:
        return cached[1]

    saved_rows = (
        await db.execute(
            select(SecretWeapon)
            .join(UserArsenal, UserArsenal.weapon_id == SecretWeapon.id)
            .where(
                UserArsenal.user_id == current_user.id,
                SecretWeapon.title_id == body.title_id,
            )
        )
    ).scalars().all()

    if not saved_rows:
        result = {"trigger": False, "reason": "No saved weapons for this title"}
        _trigger_cache[cache_key] = (time.time(), result)
        return result

    saved_payload = [
        {
            "id": w.id,
            "name": w.name,
            "category": w.category,
            "when_to_use": w.when_to_use,
            "trigger_conditions": w.trigger_conditions or {},
            "difficulty": w.difficulty,
        }
        for w in saved_rows
    ]

    system = build_trigger_system(body.title_id, saved_payload, body.game_state)
    raw = await call_claude(
        system=system,
        user_content=f"Current {body.title_id} game state: {body.game_state}",
        max_tokens=500,
    )
    if not raw:
        result = {"trigger": False, "reason": "ArsenalAI offline"}
        _trigger_cache[cache_key] = (time.time(), result)
        return result

    parsed = parse_json_object(raw) or {}
    if not isinstance(parsed.get("trigger"), bool):
        parsed = {"trigger": False}

    if parsed.get("trigger"):
        weapon_id = parsed.get("weapon_id") or parsed.get("weaponId")
        weapon = next((w for w in saved_rows if w.id == weapon_id), None)
        if weapon:
            parsed["weapon"] = {
                "id": weapon.id,
                "name": weapon.name,
                "category": weapon.category,
                "title_id": weapon.title_id,
            }
            parsed["weapon_id"] = weapon.id

    _trigger_cache[cache_key] = (time.time(), parsed)
    return parsed


# ---------------------------------------------------------------------------
# Recommendations (simple deterministic synthesis from saved weapons)
# ---------------------------------------------------------------------------

@router.get("/recommendations")
async def recommendations(
    title_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> list[dict[str, Any]]:
    rows = (
        await db.execute(
            select(SecretWeapon)
            .join(UserArsenal, UserArsenal.weapon_id == SecretWeapon.id)
            .where(
                UserArsenal.user_id == current_user.id,
                SecretWeapon.title_id == title_id,
            )
            .order_by(SecretWeapon.community_rating.desc())
            .limit(3)
        )
    ).scalars().all()

    return [
        {
            "id": f"arsenal-rec-{w.id}",
            "agent": "arsenal-ai",
            "weapon_id": w.id,
            "title_id": w.title_id,
            "headline": f"{w.name} — {w.category}",
            "body": w.when_to_use,
        }
        for w in rows
    ]


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _to_response(w: SecretWeapon) -> WeaponResponse:
    return WeaponResponse(
        id=w.id,
        user_id=w.user_id,
        title_id=w.title_id,
        name=w.name,
        category=w.category,
        sub_category=w.sub_category,
        formation=w.formation,
        play_name=w.play_name,
        description=w.description,
        instructions=w.instructions or [],
        setup_steps=w.setup_steps or [],
        when_to_use=w.when_to_use,
        trigger_conditions=w.trigger_conditions or {},
        difficulty=w.difficulty,  # type: ignore[arg-type]
        title_specific_data=w.title_specific_data or {},
        patch_version=w.patch_version,
        source_type=w.source_type,  # type: ignore[arg-type]
        source_url=w.source_url,
        video_url=w.video_url,
        thumbnail_url=w.thumbnail_url,
        tags=w.tags or [],
        verified=w.verified,
        success_rate=w.success_rate,
        times_used=w.times_used,
        community_rating=w.community_rating,
        community_votes=w.community_votes,
        saved=False,
        created_at=w.created_at,
        updated_at=w.updated_at,
    )
