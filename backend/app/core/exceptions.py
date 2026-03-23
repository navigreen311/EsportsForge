"""Centralized exception hierarchy and global exception handlers for EsportsForge.

All API errors return a consistent JSON shape::

    {
        "error": "<error_code>",
        "message": "<human-readable message>",
        "detail": { ... },  // optional structured context
        "request_id": "<X-Request-ID if available>"
    }
"""

from __future__ import annotations

import logging
import traceback
from typing import Any

from fastapi import FastAPI, HTTPException, Request, status
from fastapi.responses import JSONResponse

logger = logging.getLogger("esportsforge.exceptions")


# ---------------------------------------------------------------------------
# Base exception
# ---------------------------------------------------------------------------

class ForgeException(Exception):
    """Base exception for all EsportsForge domain errors."""

    status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR
    error_code: str = "forge_error"
    message: str = "An unexpected error occurred."

    def __init__(
        self,
        message: str | None = None,
        *,
        detail: dict[str, Any] | None = None,
        status_code: int | None = None,
    ) -> None:
        self.message = message or self.__class__.message
        self.detail = detail or {}
        if status_code is not None:
            self.status_code = status_code
        super().__init__(self.message)


# ---------------------------------------------------------------------------
# Domain-specific exceptions
# ---------------------------------------------------------------------------

class AgentError(ForgeException):
    """Raised when an AI agent fails to produce a valid result."""

    status_code = status.HTTP_502_BAD_GATEWAY
    error_code = "agent_error"
    message = "AI agent encountered an error."


class DataFabricError(ForgeException):
    """Raised when ForgeData Fabric cannot retrieve or validate data."""

    status_code = status.HTTP_503_SERVICE_UNAVAILABLE
    error_code = "data_fabric_error"
    message = "Data fabric is unavailable or returned invalid data."


class IntegrityViolation(ForgeException):
    """Raised when an action violates IntegrityMode compliance rules."""

    status_code = status.HTTP_403_FORBIDDEN
    error_code = "integrity_violation"
    message = "Action blocked by IntegrityMode compliance rules."


class TierAccessDenied(ForgeException):
    """Raised when a user's tier does not permit access to a resource."""

    status_code = status.HTTP_403_FORBIDDEN
    error_code = "tier_access_denied"
    message = "Your subscription tier does not include this feature."

    def __init__(
        self,
        message: str | None = None,
        *,
        required_tier: str | None = None,
        current_tier: str | None = None,
        feature: str | None = None,
        detail: dict[str, Any] | None = None,
    ) -> None:
        extra = {}
        if required_tier:
            extra["required_tier"] = required_tier
        if current_tier:
            extra["current_tier"] = current_tier
        if feature:
            extra["feature"] = feature
        extra["upgrade_url"] = "/api/v1/subscription/upgrade"
        combined = {**(detail or {}), **extra}
        super().__init__(message, detail=combined)


class ValidationError(ForgeException):
    """Raised when request data fails domain-level validation."""

    status_code = status.HTTP_422_UNPROCESSABLE_ENTITY
    error_code = "validation_error"
    message = "Request data failed validation."


class NotFoundError(ForgeException):
    """Raised when a requested resource is not found."""

    status_code = status.HTTP_404_NOT_FOUND
    error_code = "not_found"
    message = "Requested resource not found."


class RateLimitExceeded(ForgeException):
    """Raised when a user exceeds their tier's rate limit."""

    status_code = status.HTTP_429_TOO_MANY_REQUESTS
    error_code = "rate_limit_exceeded"
    message = "Rate limit exceeded. Please try again later."


# ---------------------------------------------------------------------------
# Global exception handlers
# ---------------------------------------------------------------------------

def _build_error_body(
    error_code: str,
    message: str,
    detail: dict[str, Any] | None = None,
    request_id: str | None = None,
) -> dict[str, Any]:
    """Build the standard error JSON shape."""
    body: dict[str, Any] = {
        "error": error_code,
        "message": message,
    }
    if detail:
        body["detail"] = detail
    if request_id:
        body["request_id"] = request_id
    return body


async def forge_exception_handler(request: Request, exc: ForgeException) -> JSONResponse:
    """Handle all ForgeException subclasses."""
    request_id = getattr(request.state, "request_id", None)
    logger.warning(
        "ForgeException: %s | code=%s | request_id=%s",
        exc.message,
        exc.error_code,
        request_id,
    )
    return JSONResponse(
        status_code=exc.status_code,
        content=_build_error_body(
            error_code=exc.error_code,
            message=exc.message,
            detail=exc.detail,
            request_id=request_id,
        ),
    )


async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
    """Handle FastAPI HTTPException with consistent shape."""
    request_id = getattr(request.state, "request_id", None)
    # HTTPException.detail can be str or dict
    if isinstance(exc.detail, dict):
        error_code = exc.detail.get("error", "http_error")
        message = exc.detail.get("message", str(exc.detail))
        detail = exc.detail
    else:
        error_code = "http_error"
        message = str(exc.detail)
        detail = None

    return JSONResponse(
        status_code=exc.status_code,
        content=_build_error_body(
            error_code=error_code,
            message=message,
            detail=detail,
            request_id=request_id,
        ),
    )


async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Catch-all for unhandled exceptions — log full traceback."""
    request_id = getattr(request.state, "request_id", None)
    logger.error(
        "Unhandled exception: %s | request_id=%s\n%s",
        exc,
        request_id,
        traceback.format_exc(),
    )
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=_build_error_body(
            error_code="internal_error",
            message="An unexpected error occurred.",
            request_id=request_id,
        ),
    )


def register_exception_handlers(app: FastAPI) -> None:
    """Register all global exception handlers on the FastAPI app."""
    app.add_exception_handler(ForgeException, forge_exception_handler)  # type: ignore[arg-type]
    app.add_exception_handler(HTTPException, http_exception_handler)  # type: ignore[arg-type]
    app.add_exception_handler(Exception, unhandled_exception_handler)
