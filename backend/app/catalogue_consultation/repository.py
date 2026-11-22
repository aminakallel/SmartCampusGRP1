import json
import unicodedata
from functools import lru_cache
from pathlib import Path
from typing import Protocol

from app.catalogue_consultation.schemas import Programme

DATA_FILE = Path(__file__).resolve().parent / "data" / "programmes.json"


def _normalize(text: str) -> str:
    """Minuscules et sans accents : 'Mécatronique' devient 'mecatronique'."""
    decomposed = unicodedata.normalize("NFD", text.lower())
    return "".join(c for c in decomposed if unicodedata.category(c) != "Mn")


class CatalogueRepository(Protocol):
    def find_all(
        self, etablissement: str | None, niveau: str | None, q: str | None
    ) -> list[Programme]: ...

    def find_by_slug(self, slug: str) -> Programme | None: ...


class MockCatalogueRepository:
    """Lit programmes.json (provisoire).

    À remplacer par un dépôt SQL (même deux méthodes) quand les tables du
    catalogue (SA-12) existeront : seul get_repository() changera.
    """

    def __init__(self, data_file: Path = DATA_FILE) -> None:
        raw = json.loads(data_file.read_text(encoding="utf-8"))
        self._items = [Programme.model_validate(item) for item in raw]

    def _published(self) -> list[Programme]:
        return [p for p in self._items if p.statut == "publiee"]

    def find_all(
        self, etablissement: str | None, niveau: str | None, q: str | None
    ) -> list[Programme]:
        result = self._published()
        if etablissement:
            result = [p for p in result if p.etablissement == etablissement]
        if niveau:
            result = [p for p in result if p.niveau == niveau]
        if q:
            needle = _normalize(q.strip())
            result = [
                p
                for p in result
                if needle in _normalize(" ".join([p.nom, p.description, *p.motsCles]))
            ]
        return result

    def find_by_slug(self, slug: str) -> Programme | None:
        return next((p for p in self._published() if p.slug == slug), None)


@lru_cache
def get_repository() -> CatalogueRepository:
    return MockCatalogueRepository()