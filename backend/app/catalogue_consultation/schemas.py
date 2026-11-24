"""Catalogue response and query types derived from the SA-21 candidate.

The public resource remains slug-addressed pending coordination with the SA-12
SERIAL identifier contract for the shared ``/api/v1/formations`` API.
"""

from typing import Literal

from pydantic import BaseModel, Field

Etablissement = Literal["IIT", "ISB"]
Niveau = Literal["Licence", "Préparatoire", "Ingénierie", "Master", "Architecture"]
Statut = Literal["BROUILLON", "PUBLIE", "ARCHIVE"]


class ProgrammePublic(BaseModel):
    """Public fields; internal lifecycle status is intentionally omitted."""

    id: str
    slug: str
    nom: str
    etablissement: Etablissement
    niveau: Niveau
    duree: str
    description: str
    prerequis: list[str] = Field(default_factory=list)
    debouches: list[str] = Field(default_factory=list)
    motsCles: list[str] = Field(default_factory=list)
    lien: str | None = None


class Programme(ProgrammePublic):
    """Internal JSON-backed record, including the SA-12 publication status."""

    statut: Statut = "PUBLIE"
