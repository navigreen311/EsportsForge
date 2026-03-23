"""API & Extension Layer — community extension registry and SDK support.

Manages registration, validation, and discovery of community-built
extensions. Provides SDK documentation endpoint for third-party developers.
"""

from __future__ import annotations

import logging
import uuid
from datetime import datetime, timezone
from typing import Any

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# In-memory stores (replaced by DB in production)
# ---------------------------------------------------------------------------

_extensions: dict[str, dict[str, Any]] = {}  # extension_id -> manifest
_extension_index: dict[str, str] = {}  # name -> extension_id


def reset_store() -> None:
    """Clear all in-memory state (for testing)."""
    _extensions.clear()
    _extension_index.clear()


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _now() -> datetime:
    return datetime.now(timezone.utc)


def _generate_id() -> str:
    return uuid.uuid4().hex[:12]


# ---------------------------------------------------------------------------
# Validation
# ---------------------------------------------------------------------------

_REQUIRED_MANIFEST_FIELDS = {"name", "version", "author", "description"}
_VALID_HOOK_POINTS = {
    "pre_analysis",
    "post_analysis",
    "pre_gameplan",
    "post_gameplan",
    "on_session_start",
    "on_session_end",
    "on_rating_change",
    "custom_overlay",
}


def validate_extension(manifest: dict[str, Any]) -> dict[str, Any]:
    """Validate an extension manifest against the SDK spec.

    Parameters
    ----------
    manifest : dict
        Extension manifest to validate.

    Returns
    -------
    dict with ``valid`` (bool), ``errors`` (list), and ``warnings`` (list).
    """
    errors: list[str] = []
    warnings: list[str] = []

    # Check required fields
    for field in _REQUIRED_MANIFEST_FIELDS:
        if field not in manifest or not manifest[field]:
            errors.append(f"Missing required field: '{field}'")

    # Validate version format
    version = manifest.get("version", "")
    if version and not all(p.isdigit() for p in version.split(".")):
        warnings.append(f"Version '{version}' does not follow semver format")

    # Validate hook points
    hooks = manifest.get("hooks", [])
    if hooks:
        for hook in hooks:
            if hook not in _VALID_HOOK_POINTS:
                errors.append(f"Invalid hook point: '{hook}'")
    else:
        warnings.append("No hook points declared — extension will have limited integration")

    # Check permissions
    permissions = manifest.get("permissions", [])
    valid_permissions = {"read_session", "read_gameplan", "read_stats", "write_overlay"}
    for perm in permissions:
        if perm not in valid_permissions:
            errors.append(f"Invalid permission: '{perm}'")

    # Name uniqueness check
    name = manifest.get("name", "")
    if name and name in _extension_index:
        errors.append(f"Extension name '{name}' is already registered")

    return {
        "valid": len(errors) == 0,
        "errors": errors,
        "warnings": warnings,
        "validated_at": _now().isoformat(),
    }


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def get_available_extensions() -> dict[str, Any]:
    """List all registered community extensions.

    Returns
    -------
    dict with ``extensions`` list and ``total``.
    """
    extensions_list = [
        {
            "extension_id": ext_id,
            "name": ext.get("name"),
            "version": ext.get("version"),
            "author": ext.get("author"),
            "description": ext.get("description"),
            "status": ext.get("status", "active"),
            "hooks": ext.get("hooks", []),
        }
        for ext_id, ext in _extensions.items()
    ]

    return {
        "extensions": extensions_list,
        "total": len(extensions_list),
        "retrieved_at": _now().isoformat(),
    }


def register_extension(manifest: dict[str, Any]) -> dict[str, Any]:
    """Register a new community extension.

    Parameters
    ----------
    manifest : dict
        Extension manifest containing name, version, author,
        description, hooks, and permissions.

    Returns
    -------
    dict with registration result including ``extension_id``.

    Raises
    ------
    ValueError
        If the manifest fails validation.
    """
    validation = validate_extension(manifest)
    if not validation["valid"]:
        raise ValueError(
            f"Invalid extension manifest: {'; '.join(validation['errors'])}"
        )

    extension_id = _generate_id()
    name = manifest["name"]

    registered = {
        **manifest,
        "extension_id": extension_id,
        "status": "active",
        "registered_at": _now().isoformat(),
    }

    _extensions[extension_id] = registered
    _extension_index[name] = extension_id

    logger.info("Extension '%s' registered with ID %s", name, extension_id)

    return {
        "extension_id": extension_id,
        "name": name,
        "status": "active",
        "registered_at": registered["registered_at"],
        "warnings": validation.get("warnings", []),
    }


def get_sdk_documentation() -> dict[str, Any]:
    """Return SDK documentation for extension developers.

    Returns
    -------
    dict with SDK version, available hook points, permissions,
    manifest schema, and example manifest.
    """
    return {
        "sdk_version": "1.0.0-beta",
        "base_url": "/api/v1/extensions",
        "authentication": "Bearer token required for all SDK endpoints",
        "hook_points": sorted(_VALID_HOOK_POINTS),
        "available_permissions": [
            {"name": "read_session", "description": "Read user session data"},
            {"name": "read_gameplan", "description": "Read gameplan recommendations"},
            {"name": "read_stats", "description": "Read player statistics"},
            {"name": "write_overlay", "description": "Write to broadcast overlay"},
        ],
        "manifest_schema": {
            "required_fields": sorted(_REQUIRED_MANIFEST_FIELDS),
            "optional_fields": ["hooks", "permissions", "settings", "icon_url"],
        },
        "example_manifest": {
            "name": "my-extension",
            "version": "1.0.0",
            "author": "developer@example.com",
            "description": "A sample community extension",
            "hooks": ["post_analysis", "on_session_end"],
            "permissions": ["read_session", "read_stats"],
        },
        "rate_limits": {
            "requests_per_minute": 60,
            "webhook_timeout_seconds": 10,
        },
    }
