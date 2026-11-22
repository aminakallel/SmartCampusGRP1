import pytest
from fastapi.testclient import TestClient

from app.api.dependencies import get_repository
from app.main import app
from app.repositories.formation_repository import InMemoryCatalogueRepository

ADMIN = {"X-Role": "admin"}
CANDIDAT = {"X-Role": "candidat"}

FORMATION = {
    "etablissement_id": 1,
    "code_parcours": "IIT-INFO-LIC",
    "type_parcours": "LICENCE",
    "titre": "Licence en Informatique",
    "duree_semestres": 6,
    "resume": "Formation en informatique",
    "objectifs_pedagogiques": "Maîtriser les fondamentaux",
    "debouches": "Développeur",
    "modalite": "Présentiel",
    "langue_enseignement": "Français",
    "tags_interets": ["informatique"],
    "statut": "BROUILLON",
    "source_reference": "Catalogue officiel",
}


@pytest.fixture
def repo():
    # Un catalogue neuf (IIT = 1, ISB = 2) pour chaque test.
    return InMemoryCatalogueRepository()


@pytest.fixture
def client(repo):
    app.dependency_overrides[get_repository] = lambda: repo
    yield TestClient(app)
    app.dependency_overrides.clear()
