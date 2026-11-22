"""FastAPI application entry point."""

import logging

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from starlette.middleware.cors import CORSMiddleware

from app.api.routes.health import router as health_router
from app.api.v1.formations import router as formations_router
from app.api.v1.formations import criteria_router
from app.api.v1.etablissements import router as etablissements_router
from app.core.errors import register_error_handlers
from app.core.config import Settings, get_settings
from app.catalogue_consultation.router import router as catalogue_consultation_router


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
    application.include_router(catalogue_consultation_router)

    application.include_router(etablissements_router, prefix="/api/v1")
    application.include_router(formations_router, prefix="/api/v1")
    application.include_router(criteria_router, prefix="/api/v1")

    register_error_handlers(application)

    if app_settings.allowed_origins:
        application.add_middleware(
            CORSMiddleware,
            allow_origins=app_settings.allowed_origins,
            allow_credentials=False,
            allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
            allow_headers=["Authorization", "Content-Type"],
        )

    @application.exception_handler(Exception)
    async def unexpected_error_handler(request: Request, exc: Exception) -> JSONResponse:
        logging.getLogger(__name__).error(
            "Unhandled request error (%s)", type(exc).__name__
        )
        return JSONResponse(
            status_code=500,
            content={"detail": "Internal server error"},
        )

    return application


app = create_app()
