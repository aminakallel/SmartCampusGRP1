from fastapi import FastAPI

from app.api.v1 import etablissements, formations
from app.core.errors import register_error_handlers

app = FastAPI(title="SmartCampus AI : API du catalogue", version="0.3.0")
register_error_handlers(app)
app.include_router(formations.router, prefix="/api/v1")
app.include_router(formations.criteria_router, prefix="/api/v1")
app.include_router(etablissements.router, prefix="/api/v1")
