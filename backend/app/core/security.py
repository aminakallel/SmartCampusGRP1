"""Sécurité TEMPORAIRE pour SA-20.

Le rôle est lu dans l'en-tête X-Role (visiteur, candidat, admin).
À remplacer par la vérification du JWT quand SA-28 sera prête :
seule la fonction get_current_role() devra changer.
"""
from fastapi import Depends, Header

from app.core.errors import AppError


def get_current_role(x_role: str | None = Header(default=None)) -> str:
    return x_role or "visiteur"


def require_admin(role: str = Depends(get_current_role)) -> None:
    if role != "admin":
        raise AppError(403, "FORBIDDEN", "Accès refusé : rôle admin requis")
