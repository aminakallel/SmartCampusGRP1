"""Read-only repository used until the SA-12 SQL migration/repository exists.

This JSON adapter is deliberately replaceable and has no database side effects.
"""

import json
import unicodedata
from functools import lru_cache
from pathlib import Path
from typing import Protocol

from app.catalogue_consultation.schemas import Programme

DATA_FILE = Path(__file__).resolve().parent / "data" / "programmes.json"


def _normalize(text: str) -> str:
    decomposed = unicodedata.normalize("NFD", text.casefold())
    return "".join(char for char in decomposed if unicodedata.category(char) != "Mn")


class CatalogueRepository(Protocol):
    def find_all(self, etablissement: str | None, niveau: str | None, q: str | None) -> list[Programme]: ...
    def find_by_slug(self, slug: str) -> Programme | None: ...


class MockCatalogueRepository:
    """In-memory view of candidate catalogue JSON; no SQL or SERIAL IDs."""

    def __init__(
        self,
        data_file: Path = DATA_FILE,
        *,
        active_establishments: set[str] | None = None,
    ) -> None:
        raw = json.loads(data_file.read_text(encoding="utf-8-sig"))
        # The source candidate used lowercase French status labels. Convert only
        # those known labels to the canonical SA-12 enum names.
        for item in raw:
            item["statut"] = {
                "publiee": "PUBLIE",
                "brouillon": "BROUILLON",
                "archive": "ARCHIVE",
            }.get(item.get("statut"), item.get("statut", "PUBLIE"))
        self._items = [Programme.model_validate(item) for item in raw]
        # Candidate demo institutions are provisionally treated as active.
        # Production must obtain this set from ``etablissements.est_actif``.
        self._active_establishments = (
            {"IIT", "ISB"} if active_establishments is None else set(active_establishments)
        )

    def _public(self) -> list[Programme]:
        return [
            row for row in self._items
            if row.statut == "PUBLIE" and row.etablissement in self._active_establishments
        ]

    def find_all(self, etablissement: str | None, niveau: str | None, q: str | None) -> list[Programme]:
        result = self._public()
        if etablissement:
            result = [row for row in result if row.etablissement == etablissement]
        if niveau:
            result = [row for row in result if row.niveau == niveau]
        if q:
            needle = _normalize(q.strip())
            result = [
                row for row in result
                if needle in _normalize(" ".join([row.nom, row.description, *row.motsCles]))
            ]
        return result

    def find_by_slug(self, slug: str) -> Programme | None:
        return next((row for row in self._public() if row.slug == slug), None)


@lru_cache
def get_repository() -> CatalogueRepository:
    return MockCatalogueRepository()
