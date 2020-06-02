"""Domain exceptions mapped to HTTP responses by app.utils.handlers."""

from typing import Any, Dict, Optional


class AppError(Exception):
    """Base class for all expected application errors."""

    status_code = 400
    code = "bad_request"

    def __init__(self, message: str, *, details: Optional[Dict[str, Any]] = None):
        super().__init__(message)
        self.message = message
        self.details = details or {}


class ValidationError(AppError):
    status_code = 400
    code = "validation_error"


class NotFoundError(AppError):
    status_code = 404
    code = "not_found"


class AuthError(AppError):
    """Authentication failures (bad credentials, expired/invalid tokens)."""

    status_code = 401
    code = "unauthorized"


class PermissionDeniedError(AppError):
    status_code = 403
    code = "permission_denied"


class ConflictError(AppError):
    """Duplicate resources / state conflicts."""

    status_code = 409
    code = "conflict"


class BusinessRuleError(AppError):
    """Valid request that violates a business rule (e.g. invalid state transition)."""

    status_code = 422
    code = "business_rule_violation"


class RateLimitError(AppError):
    status_code = 429
    code = "rate_limited"
