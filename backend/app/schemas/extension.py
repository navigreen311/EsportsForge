"""Pydantic schemas for the API & Extension Layer."""

from __future__ import annotations

from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------

class ExtensionStatus(str, Enum):
    """Lifecycle status of a registered extension."""
    ACTIVE = "active"
    DISABLED = "disabled"
    PENDING_REVIEW = "pending_review"
    REJECTED = "rejected"


# ---------------------------------------------------------------------------
# Extension Manifest & Registration
# ---------------------------------------------------------------------------

class ExtensionManifest(BaseModel):
    """Manifest submitted when registering an extension."""
    name: str = Field(..., min_length=1, max_length=128, description="Extension name")
    version: str = Field(..., description="Semver version string, e.g. '1.0.0'")
    author: str = Field(..., description="Author email or handle")
    description: str = Field(..., description="Short description of the extension")
    hooks: list[str] = Field(default_factory=list, description="Hook points to attach to")
    permissions: list[str] = Field(default_factory=list, description="Requested permissions")
    settings: dict[str, Any] = Field(default_factory=dict, description="Extension settings")
    icon_url: str = Field("", description="URL to extension icon")


class ExtensionSummary(BaseModel):
    """Summary view of a registered extension."""
    extension_id: str
    name: str
    version: str
    author: str
    description: str
    status: str = Field("active")
    hooks: list[str] = Field(default_factory=list)


class ExtensionListResponse(BaseModel):
    """Response containing list of extensions."""
    extensions: list[ExtensionSummary] = Field(default_factory=list)
    total: int = Field(0, ge=0)
    retrieved_at: str = Field("")


class ExtensionRegistration(BaseModel):
    """Result of registering an extension."""
    extension_id: str
    name: str
    status: str = Field("active")
    registered_at: str = Field("")
    warnings: list[str] = Field(default_factory=list)


# ---------------------------------------------------------------------------
# Validation
# ---------------------------------------------------------------------------

class ValidationResult(BaseModel):
    """Result of manifest validation."""
    valid: bool
    errors: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    validated_at: str = Field("")


# ---------------------------------------------------------------------------
# SDK Documentation
# ---------------------------------------------------------------------------

class PermissionInfo(BaseModel):
    """Description of an available permission."""
    name: str
    description: str


class SDKDocumentation(BaseModel):
    """SDK documentation for extension developers."""
    sdk_version: str
    base_url: str
    authentication: str
    hook_points: list[str] = Field(default_factory=list)
    available_permissions: list[PermissionInfo] = Field(default_factory=list)
    manifest_schema: dict[str, Any] = Field(default_factory=dict)
    example_manifest: dict[str, Any] = Field(default_factory=dict)
    rate_limits: dict[str, Any] = Field(default_factory=dict)
