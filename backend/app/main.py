"""FastAPI application entry point."""

import logging
from http import HTTPStatus

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.middleware.cors import CORSMiddleware
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.api.routes.health import router as health_router
from app.catalogue_consultation.router import router as catalogue_router
from app.core.config import Settings, get_settings


ERROR_CODES = {
    400: "BAD_REQUEST",
    401: "UNAUTHORIZED",
    403: "FORBIDDEN",
    404: "NOT_FOUND",
    405: "METHOD_NOT_ALLOWED",
    422: "VALIDATION_ERROR",
    500: "INTERNAL_SERVER_ERROR",
    503: "SERVICE_UNAVAILABLE",
}


def error_response(
    status_code: int,
    message: str,
    *,
    details: dict | list | None = None,
    headers: dict[str, str] | None = None,
) -> JSONResponse:
    """Return errors using the shared SA-5 JSON envelope."""
    return JSONResponse(
        status_code=status_code,
        content={
            "error": {
                "code": ERROR_CODES.get(status_code, f"HTTP_{status_code}"),
                "message": message,
                "details": details if details is not None else {},
            }
        },
        headers=headers,
    )


def create_app(settings: Settings | None = None) -> FastAPI:
    """Build the API using explicit settings, including a restrictive CORS policy."""
    app_settings = settings or get_settings()
    logging.basicConfig(level=app_settings.log_level.upper())
    application = FastAPI(
        title=app_settings.app_name,
        version=app_settings.app_version,
        description="Backend foundation for the SmartCampus AI orientation platform.",
        docs_url="/docs",
        redoc_url="/redoc",
    )
    application.include_router(health_router)
    application.include_router(catalogue_router)

    if app_settings.allowed_origins:
        application.add_middleware(
            CORSMiddleware,
            allow_origins=app_settings.allowed_origins,
            allow_credentials=False,
            allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
            allow_headers=["Authorization", "Content-Type"],
        )

    @application.exception_handler(StarletteHTTPException)
    async def http_error_handler(_request: Request, exc: StarletteHTTPException) -> JSONResponse:
        if exc.status_code >= 500 and exc.status_code != 503:
            message = "Internal server error"
        elif isinstance(exc.detail, str):
            message = exc.detail
        else:
            message = HTTPStatus(exc.status_code).phrase
        return error_response(exc.status_code, message, headers=exc.headers)

    @application.exception_handler(RequestValidationError)
    async def validation_error_handler(
        _request: Request, exc: RequestValidationError
    ) -> JSONResponse:
        # Omit submitted input/context: validation errors can contain passwords or tokens.
        details = [
            {"loc": list(error["loc"]), "msg": error["msg"], "type": error["type"]}
            for error in exc.errors()
        ]
        return error_response(422, "Request validation failed", details=details)

    @application.exception_handler(Exception)
    async def unexpected_error_handler(_request: Request, exc: Exception) -> JSONResponse:
        # Do not log exception text or request URLs; either may contain user-supplied secrets.
        logging.getLogger(__name__).error("Unhandled request error (%s)", type(exc).__name__)
        return error_response(500, "Internal server error")

    return application


app = create_app()
