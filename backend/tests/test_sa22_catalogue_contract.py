"""SA-22 contract coverage for the read-only SA-21 catalogue API.

Each test owns an isolated JSON-backed mock repository; no database is used.
"""

import json

import pytest
from fastapi.testclient import TestClient

from app.catalogue_consultation.repository import MockCatalogueRepository, get_repository
from app.catalogue_consultation.schemas import ProgrammePublic
from app.main import app


BASE = "/api/v1/catalogue/programmes"


def _programme(
    *,
    id: str = "iit-licence-1",
    slug: str = "iit-licence-1",
    nom: str = "Licence informatique",
    etablissement: str = "IIT",
    niveau: str = "Licence",
    description: str = "Parcours de démonstration.",
    mots_cles: list[str] | None = None,
    statut: str = "PUBLIE",
) -> dict[str, object]:
    return {
        "id": id,
        "slug": slug,
        "nom": nom,
        "etablissement": etablissement,
        "niveau": niveau,
        "duree": "3 ans",
        "description": description,
        "prerequis": ["Baccalauréat"],
        "debouches": ["Exemple fictif"],
        "motsCles": mots_cles or [],
        "lien": None,
        "statut": statut,
    }


def _write_catalogue(path, records: list[dict[str, object]]) -> None:
    path.write_text(json.dumps(records, ensure_ascii=False), encoding="utf-8")


@pytest.fixture
def catalogue_client_factory(monkeypatch):
    """Override only the catalogue dependency; each test owns its data file."""

    def make_client(data_file):
        repository = MockCatalogueRepository(data_file)
        monkeypatch.setitem(app.dependency_overrides, get_repository, lambda: repository)
        return TestClient(app)

    return make_client


def test_cat01_valid_filters_without_matches_return_empty_list(tmp_path, catalogue_client_factory):
    data_file = tmp_path / "programmes.json"
    _write_catalogue(data_file, [_programme()])

    with catalogue_client_factory(data_file) as client:
        response = client.get(BASE, params={"etablissement": "ISB", "niveau": "Master"})

    assert response.status_code == 200
    assert response.json() == []


def test_cat02_unknown_level_is_rejected(tmp_path, catalogue_client_factory):
    data_file = tmp_path / "programmes.json"
    _write_catalogue(data_file, [_programme()])

    with catalogue_client_factory(data_file) as client:
        response = client.get(BASE, params={"niveau": "Niveau inconnu"})

    assert response.status_code == 422


@pytest.mark.parametrize("query_length", [1, 101])
def test_cat03_search_outside_normalized_length_range_is_rejected(
    tmp_path, catalogue_client_factory, query_length
):
    data_file = tmp_path / "programmes.json"
    _write_catalogue(data_file, [_programme()])

    with catalogue_client_factory(data_file) as client:
        response = client.get(BASE, params={"q": f" {'x' * query_length} "})

    assert response.status_code == 422
    _assert_common_validation_error(response)


@pytest.mark.parametrize("query_length", [2, 100])
def test_cat04_search_length_boundaries_are_accepted(
    tmp_path, catalogue_client_factory, query_length
):
    data_file = tmp_path / "programmes.json"
    _write_catalogue(data_file, [_programme()])

    with catalogue_client_factory(data_file) as client:
        response = client.get(BASE, params={"q": f" {'x' * query_length} "})

    assert response.status_code == 200
    assert isinstance(response.json(), list)


def _assert_common_validation_error(response) -> None:
    body = response.json()
    assert set(body) == {"error"}
    assert set(body["error"]) == {"code", "message", "details"}
    assert body["error"]["code"] == "VALIDATION_ERROR"
    assert body["error"]["message"] == "Request validation failed"
    assert body["error"]["details"]


@pytest.mark.parametrize(
    ("record", "query"),
    [
        (_programme(description="Cloud computing académique."), "cloud computing"),
        (_programme(mots_cles=["robotique avancée"]), "robotique avancée"),
    ],
    ids=["description", "keywords"],
)
def test_cat05_search_matches_description_and_keywords(
    tmp_path, catalogue_client_factory, record, query
):
    data_file = tmp_path / "programmes.json"
    _write_catalogue(data_file, [record])

    with catalogue_client_factory(data_file) as client:
        response = client.get(BASE, params={"q": query})

    assert response.status_code == 200
    assert [item["slug"] for item in response.json()] == [record["slug"]]


def test_cat06_empty_catalogue_returns_empty_list(tmp_path, catalogue_client_factory):
    data_file = tmp_path / "programmes.json"
    _write_catalogue(data_file, [])

    with catalogue_client_factory(data_file) as client:
        response = client.get(BASE)

    assert response.status_code == 200
    assert response.json() == []


def test_cat07_every_list_item_matches_public_schema(tmp_path, catalogue_client_factory):
    data_file = tmp_path / "programmes.json"
    records = [
        _programme(),
        _programme(
            id="isb-master-1",
            slug="isb-master-1",
            nom="Master gestion",
            etablissement="ISB",
            niveau="Master",
        ),
    ]
    _write_catalogue(data_file, records)

    with catalogue_client_factory(data_file) as client:
        response = client.get(BASE)

    assert response.status_code == 200
    items = response.json()
    assert len(items) == 2
    expected_fields = set(ProgrammePublic.model_fields)
    for item in items:
        assert set(item) == expected_fields
        assert "statut" not in item
        ProgrammePublic.model_validate(item)


def test_cat08_detail_payload_matches_the_full_list_item(tmp_path, catalogue_client_factory):
    data_file = tmp_path / "programmes.json"
    _write_catalogue(
        data_file,
        [
            _programme(),
            _programme(
                id="isb-master-1",
                slug="isb-master-1",
                nom="Master gestion",
                etablissement="ISB",
                niveau="Master",
            ),
        ],
    )

    with catalogue_client_factory(data_file) as client:
        list_response = client.get(BASE)
        assert list_response.status_code == 200
        for list_item in list_response.json():
            detail_response = client.get(f"{BASE}/{list_item['slug']}")
            assert detail_response.status_code == 200
            assert detail_response.json() == list_item


def test_cat09_archived_programmes_are_hidden_from_list_and_detail(
    tmp_path, catalogue_client_factory
):
    data_file = tmp_path / "programmes.json"
    archived = _programme(id="archived", slug="archived", statut="ARCHIVE")
    published = _programme(id="published", slug="published")
    _write_catalogue(data_file, [archived, published])

    with catalogue_client_factory(data_file) as client:
        listing = client.get(BASE)
        detail = client.get(f"{BASE}/archived")

    assert listing.status_code == 200
    assert [item["slug"] for item in listing.json()] == ["published"]
    assert detail.status_code == 404
    assert detail.json() == {
        "error": {"code": "NOT_FOUND", "message": "Formation introuvable.", "details": {}}
    }


def test_cat18_unknown_programme_slug_returns_common_not_found_error(
    tmp_path, catalogue_client_factory
):
    data_file = tmp_path / "programmes.json"
    _write_catalogue(data_file, [_programme()])

    with catalogue_client_factory(data_file) as client:
        response = client.get(f"{BASE}/slug-inexistant")

    assert response.status_code == 404
    assert response.json() == {
        "error": {
            "code": "NOT_FOUND",
            "message": "Formation introuvable.",
            "details": {},
        }
    }


def test_cat10_draft_programmes_remain_hidden(tmp_path, catalogue_client_factory):
    data_file = tmp_path / "programmes.json"
    _write_catalogue(data_file, [_programme(statut="BROUILLON")])

    with catalogue_client_factory(data_file) as client:
        assert client.get(BASE).json() == []


def test_cat11_inactive_establishments_are_not_public(tmp_path, monkeypatch):
    data_file = tmp_path / "programmes.json"
    _write_catalogue(data_file, [_programme(etablissement="IIT"), _programme(
        id="isb", slug="isb", etablissement="ISB"
    )])
    repository = MockCatalogueRepository(data_file, active_establishments={"ISB"})
    monkeypatch.setitem(app.dependency_overrides, get_repository, lambda: repository)

    with TestClient(app) as client:
        response = client.get(BASE)

    assert response.status_code == 200
    assert [item["etablissement"] for item in response.json()] == ["ISB"]


def test_cat12_invalid_filter_uses_shared_validation_error_envelope(
    tmp_path, catalogue_client_factory
):
    data_file = tmp_path / "programmes.json"
    _write_catalogue(data_file, [_programme()])

    with catalogue_client_factory(data_file) as client:
        response = client.get(BASE, params={"etablissement": "XYZ"})

    assert response.status_code == 422
    assert response.json()["error"]["code"] == "VALIDATION_ERROR"
    assert response.json()["error"]["details"]


def test_cat13_public_catalogue_is_readable_without_authentication(
    tmp_path, catalogue_client_factory
):
    data_file = tmp_path / "programmes.json"
    _write_catalogue(data_file, [_programme()])

    with catalogue_client_factory(data_file) as client:
        response = client.get(BASE)

    assert response.status_code == 200


def test_cat14_repository_failure_returns_sanitized_500(monkeypatch):
    secret = "catalogue-private-diagnostic"

    class BrokenRepository:
        def find_all(self, *_args):
            raise RuntimeError(secret)

        def find_by_slug(self, _slug):
            raise RuntimeError(secret)

    monkeypatch.setitem(app.dependency_overrides, get_repository, lambda: BrokenRepository())
    with TestClient(app, raise_server_exceptions=False) as client:
        response = client.get(BASE)

    assert response.status_code == 500
    assert response.json() == {
        "error": {
            "code": "INTERNAL_SERVER_ERROR",
            "message": "Internal server error",
            "details": {},
        }
    }
    assert secret not in response.text


def test_cat15_missing_search_query_is_optional(tmp_path, catalogue_client_factory):
    data_file = tmp_path / "programmes.json"
    _write_catalogue(data_file, [_programme()])

    with catalogue_client_factory(data_file) as client:
        response = client.get(BASE)

    assert response.status_code == 200
    assert [item["slug"] for item in response.json()] == ["iit-licence-1"]


@pytest.mark.parametrize("query", ["", "   "], ids=["empty", "whitespace-only"])
def test_cat16_empty_or_whitespace_search_is_rejected(
    tmp_path, catalogue_client_factory, query
):
    data_file = tmp_path / "programmes.json"
    _write_catalogue(data_file, [_programme()])

    with catalogue_client_factory(data_file) as client:
        response = client.get(BASE, params={"q": query})

    assert response.status_code == 422
    _assert_common_validation_error(response)


def test_cat17_search_trims_surrounding_spaces_before_matching(
    tmp_path, catalogue_client_factory
):
    data_file = tmp_path / "programmes.json"
    record = _programme(description="Cloud computing académique.")
    _write_catalogue(data_file, [record])

    with catalogue_client_factory(data_file) as client:
        response = client.get(BASE, params={"q": "  cloud computing  "})

    assert response.status_code == 200
    assert [item["slug"] for item in response.json()] == [record["slug"]]
