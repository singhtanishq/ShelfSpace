"""Centralized exception handlers producing a consistent error envelope."""

from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from sqlalchemy.exc import IntegrityError, OperationalError
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.core.logging import get_logger
from app.utils.exceptions import AppError

logger = get_logger(__name__)


def error_response(status_code: int, code: str, message: str, details=None) -> JSONResponse:
    payload = {"error": {"code": code, "message": message}}
    if details:
        payload["error"]["details"] = details
    return JSONResponse(status_code=status_code, content=payload)


def register_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(AppError)
    async def app_error_handler(request: Request, exc: AppError):
        return error_response(exc.status_code, exc.code, exc.message, exc.details)

    @app.exception_handler(RequestValidationError)
    async def request_validation_handler(request: Request, exc: RequestValidationError):
        details = []
        for err in exc.errors():
            details.append(
                {"field": ".".join(str(part) for part in err.get("loc", [])[1:]), "message": err.get("msg", "")}
            )
        return error_response(
            status.HTTP_422_UNPROCESSABLE_ENTITY,
            "validation_error",
            "The submitted data is invalid.",
            details,
        )

    @app.exception_handler(IntegrityError)
    async def integrity_error_handler(request: Request, exc: IntegrityError):
        logger.warning("IntegrityError on %s: %s", request.url.path, exc.orig)
        return error_response(
            status.HTTP_409_CONFLICT, "conflict", "The request conflicts with existing data."
        )

    @app.exception_handler(OperationalError)
    async def db_error_handler(request: Request, exc: OperationalError):
        logger.error("Database failure on %s: %s", request.url.path, exc.orig)
        return error_response(
            status.HTTP_503_SERVICE_UNAVAILABLE,
            "database_unavailable",
            "The service is temporarily unavailable. Please try again.",
        )

    @app.exception_handler(StarletteHTTPException)
    async def http_exception_handler(request: Request, exc: StarletteHTTPException):
        code = {404: "not_found", 401: "unauthorized", 403: "permission_denied", 405: "method_not_allowed"}.get(
            exc.status_code, "http_error"
        )
        return error_response(exc.status_code, code, str(exc.detail))

    @app.exception_handler(Exception)
    async def unhandled_exception_handler(request: Request, exc: Exception):
        logger.exception("Unhandled error on %s", request.url.path)
        message = (
            "An unexpected error occurred." if not settings_debug() else f"Unexpected error: {exc}"
        )
        return error_response(status.HTTP_500_INTERNAL_SERVER_ERROR, "internal_error", message)


def settings_debug() -> bool:
    from app.core.config import settings

    return settings.DEBUG
