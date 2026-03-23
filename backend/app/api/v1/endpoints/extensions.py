"""API endpoints for the API & Extension Layer / SDK."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException

from app.services.backbone import api_extension

router = APIRouter(prefix="/extensions", tags=["Extensions & SDK"])


@router.get("/")
async def get_available_extensions():
    """List all registered community extensions."""
    return api_extension.get_available_extensions()


@router.post("/register")
async def register_extension(payload: dict[str, Any]):
    """Register a new community extension."""
    name = payload.get("name")
    version = payload.get("version")
    author = payload.get("author")
    description = payload.get("description")

    if not all([name, version, author, description]):
        raise HTTPException(
            status_code=400,
            detail="name, version, author, and description are required",
        )
    try:
        return api_extension.register_extension(payload)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc))


@router.post("/validate")
async def validate_extension(payload: dict[str, Any]):
    """Validate an extension manifest without registering it."""
    return api_extension.validate_extension(payload)


@router.get("/sdk-docs")
async def get_sdk_documentation():
    """Retrieve SDK documentation for extension developers."""
    return api_extension.get_sdk_documentation()
