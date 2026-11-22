import json

from fastapi.testclient import TestClient

from app.catalogue_consultation.repository import MockCatalogueRepository, get_repository
from app.main import app

client = TestClient(app)
BASE = "/api/catalogue/programmes"


def test_liste_renvoie_des_formations_sans_statut():
    response = client.get(BASE)
    assert response.status_code == 200
    data = response.json()
    assert len(data) > 0
    assert "statut" not in data[0]


def test_filtre_par_etablissement():
    total = len(client.get(BASE).json())
    iit = client.get(BASE, params={"etablissement": "IIT"}).json()
    isb = client.get(BASE, params={"etablissement": "ISB"}).json()
    assert len(iit) > 0 and len(isb) > 0
    assert all(p["etablissement"] == "IIT" for p in iit)
    assert all(p["etablissement"] == "ISB" for p in isb)
    assert len(iit) + len(isb) == total


def test_filtre_par_niveau():
    data = client.get(BASE, params={"niveau": "Master"}).json()
    assert len(data) > 0
    assert all(p["niveau"] == "Master" for p in data)


def test_filtres_combines():
    data = client.get(BASE, params={"etablissement": "ISB", "niveau": "Master"}).json()
    assert len(data) > 0
    assert all(p["etablissement"] == "ISB" and p["niveau"] == "Master" for p in data)


def test_recherche_sans_accents_ni_majuscules():
    data = client.get(BASE, params={"q": "MECATRONIQUE"}).json()
    assert any("Mécatronique" in p["nom"] for p in data)


def test_recherche_sans_resultat_renvoie_liste_vide():
    response = client.get(BASE, params={"q": "zzzzzz"})
    assert response.status_code == 200
    assert response.json() == []


def test_recherche_trop_courte_est_refusee():
    assert client.get(BASE, params={"q": "a"}).status_code == 422


def test_filtre_invalide_est_refuse():
    assert client.get(BASE, params={"etablissement": "XYZ"}).status_code == 422


def test_detail_existant():
    slug = client.get(BASE).json()[0]["slug"]
    response = client.get(f"{BASE}/{slug}")
    assert response.status_code == 200
    assert response.json()["slug"] == slug


def test_detail_introuvable():
    response = client.get(f"{BASE}/formation-qui-n-existe-pas")
    assert response.status_code == 404
    assert response.json()["detail"] == "Formation introuvable."


def test_les_brouillons_sont_invisibles(tmp_path):
    draft = {
        "id": "x", "slug": "brouillon-test", "nom": "Brouillon", "etablissement": "IIT",
        "niveau": "Licence", "duree": "3 ans", "description": "Formation non publiée.",
        "statut": "brouillon",
    }
    file = tmp_path / "p.json"
    file.write_text(json.dumps([draft]), encoding="utf-8")
    app.dependency_overrides[get_repository] = lambda: MockCatalogueRepository(file)
    try:
        assert client.get(BASE).json() == []
        assert client.get(f"{BASE}/brouillon-test").status_code == 404
    finally:
        app.dependency_overrides.clear()