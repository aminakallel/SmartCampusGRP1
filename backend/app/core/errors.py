"""Format d'erreur unique : {"error": {"code": ..., "message": ...}}"""
from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse


class AppError(Exception):
    def __init__(self, status_code: int, code: str, message: str):
        self.status_code = status_code
        self.code = code
        self.message = message
        super().__init__(message)


def error_body(code: str, message: str) -> dict:
    return {"error": {"code": code, "message": message}}


def validation_message(error: dict) -> str:
    error_type = error.get("type")
    context = error.get("ctx") or {}
    if error_type == "missing":
        return "Champ obligatoire"
    if error_type == "enum":
        return "Valeur non autorisée"
    if error_type in {"greater_than", "greater_than_equal"}:
        bound = context.get("gt", context.get("ge"))
        return f"Doit être supérieur{' ou égal' if error_type.endswith('equal') else ''} à {bound}"
    if error_type in {"less_than", "less_than_equal"}:
        bound = context.get("lt", context.get("le"))
        return f"Doit être inférieur{' ou égal' if error_type.endswith('equal') else ''} à {bound}"
    if error_type == "string_too_short":
        return f"Doit contenir au moins {context.get('min_length')} caractère(s)"
    if error_type == "string_too_long":
        return f"Ne doit pas dépasser {context.get('max_length')} caractère(s)"
    if error_type in {"int_parsing", "int_type"}:
        return "Doit être un entier"
    if error_type == "string_type":
        return "Doit être une chaîne de caractères"
    if error_type == "list_type":
        return "Doit être une liste"
    if error_type == "value_error":
        return str(context.get("error", "Valeur invalide"))
    return "Valeur invalide"


def register_error_handlers(app: FastAPI) -> None:
    @app.exception_handler(AppError)
    async def handle_app_error(request: Request, exc: AppError):
        return JSONResponse(
            status_code=exc.status_code,
            content=error_body(exc.code, exc.message),
        )

    @app.exception_handler(RequestValidationError)
    async def handle_validation_error(request: Request, exc: RequestValidationError):
        details = "; ".join(
            ".".join(str(p) for p in e["loc"] if p != "body")
            + ": "
            + validation_message(e)
            for e in exc.errors()
        )
        return JSONResponse(
            status_code=422,
            content=error_body("VALIDATION_ERROR", details),
        )
