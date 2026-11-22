from tests.conftest import ADMIN, CANDIDAT, FORMATION

URL = "/api/v1/formations"


def create(client, headers=ADMIN, **overrides):
    return client.post(URL, json={**FORMATION, **overrides}, headers=headers)


def test_create_ok(client):
    response = create(client)
    assert response.status_code == 201
    assert response.json()["code_parcours"] == FORMATION["code_parcours"]
    assert response.json()["titre"] == FORMATION["titre"]
    assert response.json()["etablissement_id"] == 1


def test_create_refused_for_non_admin_or_missing_role(client):
    assert create(client, headers=CANDIDAT).status_code == 403
    assert create(client, headers={}).status_code == 403


def test_create_invalid_duration_status_and_missing_field(client):
    invalid_duration = create(client, duree_semestres=0)
    assert invalid_duration.status_code == 422
    assert invalid_duration.json()["error"]["code"] == "VALIDATION_ERROR"
    assert "supérieur ou égal à 1" in invalid_duration.json()["error"]["message"]

    invalid_status = create(client, statut="INCONNU")
    assert invalid_status.status_code == 422
    assert invalid_status.json()["error"]["code"] == "VALIDATION_ERROR"

    invalid_type = create(client, type_parcours="Licence")
    assert invalid_type.status_code == 422
    assert "majuscules" in invalid_type.json()["error"]["message"]

    missing_code = {key: value for key, value in FORMATION.items() if key != "code_parcours"}
    missing = client.post(URL, json=missing_code, headers=ADMIN)
    assert missing.status_code == 422
    assert set(missing.json()) == {"error"}


def test_duplicate_code_parcours_returns_409(client):
    create(client)
    duplicate = create(client, titre="Autre titre")
    assert duplicate.status_code == 409
    assert duplicate.json()["error"]["code"] == "DUPLICATE"


def test_unknown_or_inactive_etablissement(client, repo):
    unknown = create(client, etablissement_id=999)
    assert unknown.status_code == 404
    assert unknown.json()["error"]["code"] == "NOT_FOUND"

    inactif = repo.add_etablissement("INACTIF", "Inactif", "Sfax", est_actif=False)
    inactive = create(client, etablissement_id=inactif.id)
    assert inactive.status_code == 422
    assert inactive.json()["error"]["code"] == "VALIDATION_ERROR"


def test_public_visibility_and_admin_status_filter(client):
    create(client, statut="BROUILLON")
    create(client, code_parcours="IIT-INFO-ARCH", statut="ARCHIVE")
    create(client, code_parcours="IIT-INFO-PUB", statut="PUBLIE")

    assert [item["statut"] for item in client.get(URL).json()] == ["PUBLIE"]
    assert client.get(f"{URL}/1").status_code == 404
    assert client.get(URL, headers=ADMIN).status_code == 200
    assert len(client.get(URL, headers=ADMIN).json()) == 3
    assert len(client.get(URL, params={"statut": "BROUILLON"}, headers=ADMIN).json()) == 1


def test_public_cannot_filter_by_status(client):
    response = client.get(URL, params={"statut": "PUBLIE"})
    assert response.status_code == 403
    assert response.json()["error"]["code"] == "FORBIDDEN"


def test_list_filters_and_pagination(client):
    create(client, statut="PUBLIE")
    create(
        client,
        etablissement_id=2,
        code_parcours="ISB-MGMT",
        type_parcours="INGENIERIE",
        statut="PUBLIE",
    )
    response = client.get(
        URL,
        params={"etablissement": "ISB", "type_parcours": "INGENIERIE", "limit": 1},
    )
    assert response.status_code == 200
    assert len(response.json()) == 1
    assert response.json()[0]["code_parcours"] == "ISB-MGMT"


def test_get_not_found_and_patch_partial(client):
    assert client.get(f"{URL}/999").status_code == 404
    create(client)
    response = client.patch(
        f"{URL}/1", json={"duree_semestres": 8}, headers=ADMIN
    )
    assert response.status_code == 200
    assert response.json()["duree_semestres"] == 8
    assert response.json()["titre"] == FORMATION["titre"]
    null_required = client.patch(f"{URL}/1", json={"titre": None}, headers=ADMIN)
    assert null_required.status_code == 422


def test_patch_refused_for_non_admin(client):
    create(client)
    response = client.patch(
        f"{URL}/1", json={"duree_semestres": 8}, headers=CANDIDAT
    )
    assert response.status_code == 403


def test_delete_archives_idempotently(client):
    create(client, statut="PUBLIE")
    assert client.delete(f"{URL}/1", headers=ADMIN).status_code == 204
    assert client.get(f"{URL}/1", headers=ADMIN).json()["statut"] == "ARCHIVE"
    assert client.get(f"{URL}/1").status_code == 404
    assert client.delete(f"{URL}/1", headers=ADMIN).status_code == 204


def test_delete_not_found_and_refused_for_non_admin(client):
    assert client.delete(f"{URL}/999", headers=ADMIN).status_code == 404
    create(client)
    assert client.delete(f"{URL}/1", headers=CANDIDAT).status_code == 403


def test_criteria_create_update_delete_and_errors(client):
    create(client, statut="PUBLIE")
    criteria_url = f"{URL}/1/criteres"
    payload = {
        "niveau_requis": "Baccalauréat",
        "filieres_acceptees": ["Sciences"],
        "score_ou_moyenne_min": 12.5,
        "priorite": 1,
    }
    created = client.post(criteria_url, json=payload, headers=ADMIN)
    assert created.status_code == 201
    critere_id = created.json()["id"]

    public_list = client.get(criteria_url)
    assert public_list.status_code == 200
    assert len(public_list.json()) == 1
    assert public_list.json()[0]["niveau_requis"] == "Baccalauréat"
    assert client.patch(
        f"/api/v1/criteres/{critere_id}",
        json={"priorite": 2},
        headers=ADMIN,
    ).json()["priorite"] == 2
    assert (
        client.patch(
            f"/api/v1/criteres/{critere_id}",
            json={"priorite": 3},
            headers=CANDIDAT,
        ).status_code
        == 403
    )
    assert client.delete(
        f"/api/v1/criteres/{critere_id}", headers=ADMIN
    ).status_code == 204
    assert client.get(f"/api/v1/criteres/{critere_id}").status_code == 404
    assert client.delete("/api/v1/criteres/999", headers=ADMIN).status_code == 404


def test_criteria_routes_enforce_admin_and_missing_parent(client):
    assert (
        client.post(
            f"{URL}/999/criteres",
            json={"niveau_requis": "Bac"},
            headers=ADMIN,
        ).status_code
        == 404
    )
    assert (
        client.post(
            f"{URL}/1/criteres",
            json={"niveau_requis": "Bac"},
            headers=CANDIDAT,
        ).status_code
        == 403
    )


def test_archiving_keeps_criteria_for_admin_and_hides_them_from_public(client):
    create(client, statut="PUBLIE")
    client.post(
        f"{URL}/1/criteres",
        json={"niveau_requis": "Baccalauréat"},
        headers=ADMIN,
    )
    assert len(client.get(f"{URL}/1/criteres").json()) == 1

    client.delete(f"{URL}/1", headers=ADMIN)
    assert len(client.get(f"{URL}/1/criteres", headers=ADMIN).json()) == 1
    assert client.get(f"{URL}/1/criteres").status_code == 404


def test_etablissements_are_read_only(client):
    response = client.get("/api/v1/etablissements")
    assert response.status_code == 200
    assert {item["code"] for item in response.json()} == {"IIT", "ISB"}
    assert client.post("/api/v1/etablissements", json={}).status_code == 405


def test_openapi_documents_common_error_response(client):
    schemas = client.get("/openapi.json").json()["components"]["schemas"]
    error_response = schemas["ErrorResponse"]
    assert "error" in error_response["properties"]
    operation = client.get("/openapi.json").json()["paths"]["/api/v1/formations"]["post"]
    assert "403" in operation["responses"]
    assert "404" in operation["responses"]
    assert "409" in operation["responses"]
    assert "422" in operation["responses"]
    assert (
        operation["responses"]["422"]["content"]["application/json"]["schema"]["$ref"]
        == "#/components/schemas/ErrorResponse"
    )


def test_create_requires_mandatory_sa12_fields(client):
    for field in ("resume", "modalite", "langue_enseignement", "source_reference"):
        body = {key: value for key, value in FORMATION.items() if key != field}
        response = client.post(URL, json=body, headers=ADMIN)
        assert response.status_code == 422, field
        assert response.json()["error"]["code"] == "VALIDATION_ERROR"


def test_patch_cannot_null_mandatory_fields(client):
    create(client)
    for field in ("resume", "modalite", "langue_enseignement", "tags_interets"):
        response = client.patch(f"{URL}/1", json={field: None}, headers=ADMIN)
        assert response.status_code == 422, field


def test_criteria_score_is_a_number_and_defaults(client):
    create(client)
    response = client.post(
        f"{URL}/1/criteres",
        json={"niveau_requis": "BAC", "score_ou_moyenne_min": 12.5},
        headers=ADMIN,
    )
    assert response.status_code == 201
    assert response.json()["score_ou_moyenne_min"] == 12.5
    assert response.json()["filieres_acceptees"] == []
    assert response.json()["priorite"] == 1


def test_criteria_score_out_of_range(client):
    create(client)
    response = client.post(
        f"{URL}/1/criteres",
        json={"niveau_requis": "BAC", "score_ou_moyenne_min": 1000},
        headers=ADMIN,
    )
    assert response.status_code == 422
