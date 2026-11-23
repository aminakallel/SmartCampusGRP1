from typing import Literal

from pydantic import BaseModel, Field

Etablissement = Literal["IIT", "ISB"]
Niveau = Literal["Licence", "Préparatoire", "Ingénierie", "Master", "Architecture"]
Statut = Literal["publiee", "brouillon"]


class ProgrammePublic(BaseModel):
    """Ce que l'API de consultation renvoie (sans le statut interne)."""

    id: str
    slug: str
    nom: str
    etablissement: Etablissement
    niveau: Niveau
    duree: str
    description: str
    prerequis: list[str] = Field(default_factory=list)
    debouches: list[str] = Field(default_factory=list)
    motsCles: list[str] = Field(default_factory=list)  # même nom que le frontend
    lien: str | None = None


class Programme(ProgrammePublic):
    """Version complète avec le statut (usage interne)."""

    statut: Statut = "publiee"