from functools import lru_cache

from fastapi import Depends

from app.repositories.formation_repository import InMemoryCatalogueRepository
from app.services.formation_service import FormationService


@lru_cache
def get_repository() -> InMemoryCatalogueRepository:
    return InMemoryCatalogueRepository()


def get_service(
    repo: InMemoryCatalogueRepository = Depends(get_repository),
) -> FormationService:
    return FormationService(repo)
