"""SA-21 checks against the checked-in, provisional catalogue JSON dataset."""

import json

import pytest
from fastapi.testclient import TestClient

from app.catalogue_consultation.repository import MockCatalogueRepository, get_repository
from app.main import app


BASE = "/api/v1/catalogue/programmes"


def test_default_catalogue_dataset_is_loadable_and_contains_both_institutions():
    repository = MockCatalogueRepository()
    records = repository.find_all(None, None, None)

    assert records
    assert {record.etablissement for record in records} == {"IIT", "ISB"}
    assert all(record.statut == "PUBLIE" for record in records)


def test_default_catalogue_search_is_case_and_accent_insensitive():
    with TestClient(app) as client:
        response = client.get(BASE, params={"q": "MECATRONIQUE"})

    assert response.status_code == 200
    assert any("Mécatronique" in item["nom"] for item in response.json())


def test_default_catalogue_public_detail_matches_list_record():
    with TestClient(app) as client:
        response = client.get(BASE)
        assert response.status_code == 200
        record = response.json()[0]
        detail = client.get(f"{BASE}/{record['slug']}")

    assert detail.status_code == 200
    assert detail.json() == record
    assert "statut" not in detail.json()


@pytest.mark.parametrize(
    ("filters", "expected_ids"),
    [
        ({"etablissement": "IIT"}, {"iit-licence", "iit-master"}),
        ({"niveau": "Licence"}, {"iit-licence", "isb-licence"}),
        ({"etablissement": "ISB", "niveau": "Master"}, {"isb-master"}),
    ],
    ids=["establishment", "level", "combined"],
)
def test_catalogue_filters_return_matching_records(
    tmp_path, monkeypatch, filters, expected_ids
):
    records = [
        {"id": "iit-licence", "slug": "iit-licence", "nom": "Licence IIT",
         "etablissement": "IIT", "niveau": "Licence", "duree": "3 ans",
         "description": "Exemple", "statut": "PUBLIE"},
        {"id": "iit-master", "slug": "iit-master", "nom": "Master IIT",
         "etablissement": "IIT", "niveau": "Master", "duree": "2 ans",
         "description": "Exemple", "statut": "PUBLIE"},
        {"id": "isb-licence", "slug": "isb-licence", "nom": "Licence ISB",
         "etablissement": "ISB", "niveau": "Licence", "duree": "3 ans",
         "description": "Exemple", "statut": "PUBLIE"},
        {"id": "isb-master", "slug": "isb-master", "nom": "Master ISB",
         "etablissement": "ISB", "niveau": "Master", "duree": "2 ans",
         "description": "Exemple", "statut": "PUBLIE"},
    ]
    data_file = tmp_path / "programmes.json"
    data_file.write_text(json.dumps(records), encoding="utf-8")
    repository = MockCatalogueRepository(data_file)
    monkeypatch.setitem(app.dependency_overrides, get_repository, lambda: repository)

    with TestClient(app) as client:
        response = client.get(BASE, params=filters)

    assert response.status_code == 200
    assert {item["id"] for item in response.json()} == expected_ids
