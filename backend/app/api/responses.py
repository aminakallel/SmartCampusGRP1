from app.schemas.error import ErrorResponse


def error_response(code: str, message: str, description: str) -> dict:
    return {
        "model": ErrorResponse,
        "description": description,
        "content": {"application/json": {"example": {"error": {"code": code, "message": message}}}},
    }


RESP_403 = error_response("FORBIDDEN", "Accès refusé : rôle admin requis", "Rôle admin requis")
RESP_404 = error_response("NOT_FOUND", "Formation 999 introuvable", "Ressource introuvable")
RESP_409 = error_response(
    "DUPLICATE",
    "Le code_parcours existe déjà",
    "code_parcours déjà utilisé",
)
RESP_422 = error_response(
    "VALIDATION_ERROR",
    "duree_semestres: La durée doit être comprise entre 1 et 20 semestres",
    "Données invalides",
)