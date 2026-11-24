"""FastAPI entry point for the SA-25 guest-session service."""

import logging
from http import HTTPStatus

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.api.routes.guest_sessions import router as guest_sessions_router
from app.api.routes.conversation_attachment import router as conversation_attachment_router
from app.auth.router import router as auth_router
from app.conversation_memory.router import router as memory_router


ERROR_CODES = {
    400: "BAD_REQUEST",
    401: "UNAUTHORIZED",
    403: "FORBIDDEN",
    404: "NOT_FOUND",
    405: "METHOD_NOT_ALLOWED",
    409: "CONFLICT",
    422: "VALIDATION_ERROR",
    500: "INTERNAL_SERVER_ERROR",
    503: "SERVICE_UNAVAILABLE",
}


def create_app() -> FastAPI:
    application = FastAPI(
        title="SmartCampus AI API",
        version="0.1.0",
        description="Temporary anonymous visitor sessions.",
    )
    application.include_router(guest_sessions_router)
    application.include_router(memory_router, prefix="/api/v1")
    application.include_router(conversation_attachment_router)
    application.include_router(auth_router)

    @application.get("/health", tags=["health"])
    def health() -> dict[str, str]:
        return {"status": "ok"}

    @application.exception_handler(StarletteHTTPException)
    async def http_error_handler(_request: Request, exc: StarletteHTTPException) -> JSONResponse:
        if exc.status_code >= 500:
            message = "Internal server error"
        elif isinstance(exc.detail, str):
            message = exc.detail
        else:
            message = HTTPStatus(exc.status_code).phrase
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "error": {
                    "code": ERROR_CODES.get(exc.status_code, f"HTTP_{exc.status_code}"),
                    "message": message,
                    "details": {},
                }
            },
            headers=exc.headers,
        )

    @application.exception_handler(RequestValidationError)
    async def validation_error_handler(
        _request: Request, exc: RequestValidationError
    ) -> JSONResponse:
        details = [
            {"loc": list(error["loc"]), "msg": error["msg"], "type": error["type"]}
            for error in exc.errors()
        ]
        return JSONResponse(
            status_code=422,
            content={
                "error": {
                    "code": "VALIDATION_ERROR",
                    "message": "Request validation failed",
                    "details": details,
                }
            },
        )

    @application.exception_handler(Exception)
    async def unexpected_error_handler(_request: Request, exc: Exception) -> JSONResponse:
        logging.getLogger(__name__).error(
            "Unhandled request error (%s)", type(exc).__name__
        )
        return JSONResponse(
            status_code=500,
            content={
                "error": {
                    "code": "INTERNAL_SERVER_ERROR",
                    "message": "Internal server error",
                    "details": {},
                }
            },
        )

    return application


app = create_app()
