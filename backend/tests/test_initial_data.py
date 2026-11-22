"""Offline structural and referential tests for provisional SA-18 data."""

import json
from decimal import Decimal

import pytest

from scripts.validate_initial_data import (
    FIXTURE_PATH,
    InitialDataError,
    read_initial_data,
    validate_initial_data,
)


def _payload() -> dict:
    return json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))


def test_initial_fixture_has_expected_fictional_entities_and_valid_references() -> None:
    fixture = read_initial_data()

    assert {item.data.code for item in fixture.etablissements} == {"IIT", "ISB"}
    assert len(fixture.formations_parcours) == 2
    assert len(fixture.criteres_admission) == 2
    assert fixture.utilisateur.data.role == "candidat"
    assert fixture.profil_candidat.utilisateur_id_ref == fixture.utilisateur.data.id
    assert all(result.profil_id_ref == fixture.profil_candidat.data.id for result in fixture.resultat_scolaire)
    assert all(link.profil_id_ref == fixture.profil_candidat.data.id for link in fixture.profil_interet)
    assert all(link.interet_id_ref in {item.data.id for item in fixture.interet} for link in fixture.profil_interet)
    assert all(
        item.provisional is True
        for item in (
            *fixture.etablissements,
            *fixture.formations_parcours,
            *fixture.criteres_admission,
            fixture.utilisateur,
            fixture.profil_candidat,
            *fixture.resultat_scolaire,
            *fixture.interet,
            *fixture.profil_interet,
        )
    )
    assert fixture.metadata.status == "provisional_not_ready_for_database_insert"


def test_candidate_average_matches_the_weighted_fictional_results() -> None:
    fixture = read_initial_data()
    weighted_total = sum(
        (result.data.note * result.data.coefficient for result in fixture.resultat_scolaire),
        Decimal("0"),
    )
    total_coefficient = sum(
        (result.data.coefficient for result in fixture.resultat_scolaire), Decimal("0")
    )

    assert weighted_total / total_coefficient == fixture.profil_candidat.data.moyenne_generale


def test_candidate_interests_match_the_iit_demo_program_tags() -> None:
    fixture = read_initial_data()
    iit_program = next(
        program for program in fixture.formations_parcours
        if program.etablissement_code_ref == "IIT"
    )
    interest_labels = {interest.data.libelle.casefold() for interest in fixture.interet}

    assert fixture.profil_candidat.data.etablissement_prefere == "IIT"
    assert set(iit_program.data.tags_interets).issubset(interest_labels)


def test_fixture_declares_dependency_order_without_serial_ids() -> None:
    fixture = read_initial_data()

    assert fixture.metadata.load_order == [
        "etablissements",
        "formations_parcours",
        "criteres_admission",
        "documents_catalogue_rag",
        "utilisateur",
        "profil_candidat",
        "resultat_scolaire",
        "interet",
        "profil_interet",
    ]
    assert all("id" not in record.data.model_dump() for record in fixture.etablissements)
    assert all("id" not in record.data.model_dump() for record in fixture.formations_parcours)
    assert all("id" not in record.data.model_dump() for record in fixture.criteres_admission)
    assert fixture.documents_catalogue_rag == []
    assert set(fixture.metadata.identity_resolution) == {
        "formations_parcours.etablissement_id",
        "criteres_admission.parcours_id",
        "documents_catalogue_rag.parcours_id",
        "profil_candidat.utilisateur_id",
        "resultat_scolaire.profil_id",
        "profil_interet.profil_id",
        "profil_interet.interet_id",
    }


@pytest.mark.parametrize("secret_field", ["password", "mot_de_passe", "mot_de_passe_hash"])
def test_fixture_rejects_password_or_hash_fields(secret_field: str) -> None:
    payload = _payload()
    payload["utilisateur"]["data"][secret_field] = "must-not-be-in-fixture"

    with pytest.raises(InitialDataError, match="validation failed") as error:
        validate_initial_data(payload)
    assert "must-not-be-in-fixture" not in str(error.value)


@pytest.mark.parametrize(
    ("collection", "record_index"),
    [("etablissements", 0), ("formations_parcours", 0), ("criteres_admission", 0)],
)
def test_fixture_rejects_serial_id_in_catalogue_record(collection: str, record_index: int) -> None:
    payload = _payload()
    payload[collection][record_index]["data"]["id"] = 123

    with pytest.raises(InitialDataError, match="validation failed"):
        validate_initial_data(payload)


def test_fixture_rejects_dangling_program_establishment_reference() -> None:
    payload = _payload()
    payload["formations_parcours"][0]["etablissement_code_ref"] = "UNKNOWN"

    with pytest.raises(InitialDataError, match="validation failed"):
        validate_initial_data(payload)


def test_fixture_rejects_dangling_admission_criteria_reference() -> None:
    payload = _payload()
    payload["criteres_admission"][0]["parcours_code_ref"] = "UNKNOWN"

    with pytest.raises(InitialDataError, match="validation failed"):
        validate_initial_data(payload)


def test_fixture_rejects_profile_that_references_another_user() -> None:
    payload = _payload()
    payload["profil_candidat"]["utilisateur_id_ref"] = "96b10948-98fa-4d2d-b640-21e80864b992"

    with pytest.raises(InitialDataError, match="validation failed"):
        validate_initial_data(payload)


def test_fixture_rejects_broken_load_order() -> None:
    payload = _payload()
    payload["_metadata"]["load_order"][0] = "formations_parcours"

    with pytest.raises(InitialDataError, match="validation failed"):
        validate_initial_data(payload)


def test_fixture_rejects_malformed_json_without_echoing_contents(tmp_path) -> None:
    invalid_fixture = tmp_path / "invalid_initial_data.json"
    invalid_fixture.write_text('{"password":"fixture-secret"', encoding="utf-8")

    with pytest.raises(InitialDataError, match="not valid JSON") as error:
        read_initial_data(invalid_fixture)
    assert "fixture-secret" not in str(error.value)


def test_fixture_rejects_duplicate_program_code() -> None:
    payload = _payload()
    payload["formations_parcours"][1]["data"]["code_parcours"] = payload["formations_parcours"][0]["data"]["code_parcours"]

    with pytest.raises(InitialDataError, match="validation failed"):
        validate_initial_data(payload)


def test_fixture_rejects_duplicate_establishment_code() -> None:
    payload = _payload()
    payload["etablissements"][1]["data"]["code"] = payload["etablissements"][0]["data"]["code"]

    with pytest.raises(InitialDataError, match="validation failed"):
        validate_initial_data(payload)


def test_fixture_rejects_duplicate_school_result_business_key() -> None:
    payload = _payload()
    duplicate = json.loads(json.dumps(payload["resultat_scolaire"][0]))
    duplicate["data"]["id"] = "477fd9fb-85a8-4c84-9f15-9f5f34f6caa7"
    payload["resultat_scolaire"].append(duplicate)

    with pytest.raises(InitialDataError, match="validation failed"):
        validate_initial_data(payload)


def test_fixture_rejects_duplicate_interest_label() -> None:
    payload = _payload()
    payload["interet"][1]["data"]["libelle"] = payload["interet"][0]["data"]["libelle"]

    with pytest.raises(InitialDataError, match="validation failed"):
        validate_initial_data(payload)


def test_fixture_rejects_duplicate_profile_interest_pair() -> None:
    payload = _payload()
    payload["profil_interet"].append(json.loads(json.dumps(payload["profil_interet"][0])))

    with pytest.raises(InitialDataError, match="validation failed"):
        validate_initial_data(payload)


def test_fixture_rejects_duplicate_seed_key() -> None:
    payload = _payload()
    payload["formations_parcours"][0]["seed_key"] = payload["etablissements"][0]["seed_key"]

    with pytest.raises(InitialDataError, match="validation failed"):
        validate_initial_data(payload)


def test_fixture_rejects_school_result_outside_sa13_grade_range() -> None:
    payload = _payload()
    payload["resultat_scolaire"][0]["data"]["note"] = 20.01

    with pytest.raises(InitialDataError, match="validation failed"):
        validate_initial_data(payload)


@pytest.mark.parametrize("field", ["modalite", "langue_enseignement"])
@pytest.mark.parametrize("bad_value", [None, ""])
def test_fixture_rejects_missing_required_sa12_program_fields(field: str, bad_value: str | None) -> None:
    payload = _payload()
    payload["formations_parcours"][0]["data"][field] = bad_value

    with pytest.raises(InitialDataError, match="validation failed"):
        validate_initial_data(payload)


def _sample_rag_record() -> dict:
    return {
        "seed_key": "rag_demo_iit_programme",
        "parcours_code_ref": "DEMO-IIT-INFO-LIC",
        "provisional": True,
        "data": {
            "type_source": "PROGRAMME",
            "titre_source": "Extrait de démonstration (source à fournir)",
            "extrait_url_ou_ref": "reference-fictive-SA18",
            "contenu_chunk": "Contenu factice de test, absent des données livrées.",
            "embedding": None,
        },
    }


def test_fixture_can_validate_a_schema_shaped_rag_record_without_serial_id() -> None:
    payload = _payload()
    payload["documents_catalogue_rag"] = [_sample_rag_record()]

    fixture = validate_initial_data(payload)

    assert fixture.documents_catalogue_rag[0].parcours_code_ref == "DEMO-IIT-INFO-LIC"
    assert "id" not in fixture.documents_catalogue_rag[0].data.model_dump()


def test_fixture_rejects_rag_document_with_unknown_program_reference() -> None:
    payload = _payload()
    record = _sample_rag_record()
    record["parcours_code_ref"] = "UNKNOWN"
    payload["documents_catalogue_rag"] = [record]

    with pytest.raises(InitialDataError, match="validation failed"):
        validate_initial_data(payload)


@pytest.mark.parametrize("dimension", [1535, 1537])
def test_fixture_rejects_rag_embedding_with_wrong_dimension(dimension: int) -> None:
    payload = _payload()
    record = _sample_rag_record()
    record["data"]["embedding"] = [0.0] * dimension
    payload["documents_catalogue_rag"] = [record]

    with pytest.raises(InitialDataError, match="validation failed"):
        validate_initial_data(payload)


def test_fixture_accepts_rag_embedding_with_exactly_1536_dimensions() -> None:
    payload = _payload()
    record = _sample_rag_record()
    record["data"]["embedding"] = [0.0] * 1536
    payload["documents_catalogue_rag"] = [record]

    fixture = validate_initial_data(payload)

    assert len(fixture.documents_catalogue_rag[0].data.embedding) == 1536
