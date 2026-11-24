"""SA-21 public, read-only catalogue endpoints."""

from typing import Annotated

from fastapi import APIRouter, Depends, Query
from pydantic import BeforeValidator, StringConstraints

from app.catalogue_consultation.repository import CatalogueRepository, get_repository
from app.catalogue_consultation.schemas import Etablissement, Niveau, ProgrammePublic

router = APIRouter(prefix="/api/v1/catalogue", tags=["Catalogue (consultation)"])
RepositoryDependency = Annotated[CatalogueRepository, Depends(get_repository)]


def _strip_search_query(value: str | None) -> str | None:
    """Trim optional search input before enforcing its normalized length."""
    return value.strip() if value is not None else None


SearchTerm = Annotated[
    str,
    BeforeValidator(_strip_search_query),
    StringConstraints(
        min_length=2,
        max_length=100,
    ),
]


@router.get(
    "/programmes",
    response_model=list[ProgrammePublic],
    summary="Lister les formations publiées",
)
def list_programmes(
    repo: RepositoryDependency,
    etablissement: Etablissement | None = None,
    niveau: Niveau | None = None,
    q: Annotated[SearchTerm | None, Query(
        description="Recherche dans le catalogue (2 à 100 caractères après trim)."
    )] = None,
) -> list[ProgrammePublic]:
    return repo.find_all(etablissement, niveau, q)


@router.get(
    "/programmes/{slug}",
    response_model=ProgrammePublic,
    summary="Détail d'une formation publiée",
    responses={404: {"description": "Formation introuvable"}},
)
def get_programme(slug: str, repo: RepositoryDependency) -> ProgrammePublic:
    programme = repo.find_by_slug(slug)
    if programme is None:
        from fastapi import HTTPException

        raise HTTPException(status_code=404, detail="Formation introuvable.")
    return programme
