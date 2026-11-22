from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query

from app.catalogue_consultation.repository import CatalogueRepository, get_repository
from app.catalogue_consultation.schemas import Etablissement, Niveau, ProgrammePublic

# Lecture seule (SA-21). La gestion (création, modification, suppression) est SA-20.
router = APIRouter(prefix="/api/catalogue", tags=["Catalogue (consultation)"])
Repo = Annotated[CatalogueRepository, Depends(get_repository)]


@router.get(
    "/programmes",
    response_model=list[ProgrammePublic],
    summary="Lister les formations publiées",
)
def list_programmes(
    repo: Repo,
    etablissement: Etablissement | None = None,
    niveau: Niveau | None = None,
    q: Annotated[
        str | None,
        Query(min_length=2, max_length=100, description="Recherche texte, sans accents ni majuscules"),
    ] = None,
):
    return repo.find_all(etablissement, niveau, q)


@router.get(
    "/programmes/{slug}",
    response_model=ProgrammePublic,
    summary="Détail d'une formation publiée",
    responses={404: {"description": "Formation introuvable"}},
)
def get_programme(slug: str, repo: Repo):
    programme = repo.find_by_slug(slug)
    if programme is None:
        raise HTTPException(status_code=404, detail="Formation introuvable.")
    return programme