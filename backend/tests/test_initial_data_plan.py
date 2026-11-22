"""Database-independent tests for the SA-18 load plan."""

from uuid import UUID

import pytest

from scripts.plan_initial_data import (
    InitialDataConflict,
    build_initial_data_plan,
    ensure_interest_label_available,
)
from scripts.validate_initial_data import CatalogueRAGRecord, read_initial_data


class FakeInterestRepository:
    """Read-only stand-in for an existing SA-13 interest table."""

    def __init__(self, labels: dict[str, UUID]) -> None:
        self.labels = labels

    def find_interest_id_by_label(self, label: str) -> UUID | None:
        return self.labels.get(label)


def test_plan_is_descriptive_only_and_does_not_claim_to_be_executable() -> None:
    plan = build_initial_data_plan()

    assert plan.executable is False
    assert "documents_catalogue_rag" in plan.empty_tables
    assert any("SA-12 migration" in blocker for blocker in plan.blockers)


def test_catalogue_plan_uses_business_codes_and_database_generated_serials() -> None:
    plan = build_initial_data_plan()
    establishments = [item for item in plan.writes if item.table == "etablissements"]
    programs = [item for item in plan.writes if item.table == "formations_parcours"]

    assert len(establishments) == 2
    assert all(item.conflict_columns == ("code",) for item in establishments)
    assert all("id" not in item.values and "id" in item.generated_columns for item in establishments)
    assert all(item.conflict_columns == ("code_parcours",) for item in programs)
    assert all("id" not in item.values and "id" in item.generated_columns for item in programs)
    assert programs[0].foreign_key_lookups["etablissement_id"].target_column == "code"
    assert programs[0].foreign_key_lookups["etablissement_id"].fixture_value == "IIT"


def test_criteria_and_rag_plan_never_invents_unique_keys() -> None:
    plan = build_initial_data_plan()
    criteria = [item for item in plan.writes if item.table == "criteres_admission"]
    rag = [item for item in plan.writes if item.table == "documents_catalogue_rag"]

    assert len(criteria) == 2
    assert not rag
    assert all(item.conflict_columns == () for item in criteria)
    assert all(item.strategy == "insert_requires_idempotency_decision" for item in criteria)
    assert all("UNIQUE key" in item.blockers[0] for item in criteria)
    assert all("id" not in item.values and "id" in item.generated_columns for item in criteria)


def test_rag_record_plan_resolves_program_by_business_code_and_keeps_serial_generated() -> None:
    fixture = read_initial_data()
    rag_record = CatalogueRAGRecord.model_validate({
        "seed_key": "rag_plan_test",
        "parcours_code_ref": "DEMO-IIT-INFO-LIC",
        "provisional": True,
        "data": {
            "type_source": "PROGRAMME",
            "titre_source": "Fixture de test",
            "extrait_url_ou_ref": "source-test",
            "contenu_chunk": "Contenu synthétique de test uniquement.",
            "embedding": None,
        },
    })
    fixture = fixture.model_copy(update={"documents_catalogue_rag": [rag_record]})

    plan = build_initial_data_plan(fixture)
    item = next(entry for entry in plan.writes if entry.table == "documents_catalogue_rag")

    assert item.conflict_columns == ()
    assert "id" not in item.values
    assert "id" in item.generated_columns
    lookup = item.foreign_key_lookups["parcours_id"]
    assert lookup.target_column == "code_parcours"
    assert lookup.fixture_value == "DEMO-IIT-INFO-LIC"


def test_candidate_and_dependents_are_blocked_without_auth_hash() -> None:
    plan = build_initial_data_plan()
    user = next(item for item in plan.writes if item.table == "utilisateur")
    profile = next(item for item in plan.writes if item.table == "profil_candidat")

    assert "mot_de_passe_hash" not in user.values
    assert user.blockers
    assert profile.blockers


def test_plan_keeps_foreign_key_lookups_explicit() -> None:
    plan = build_initial_data_plan()
    criteria = next(item for item in plan.writes if item.table == "criteres_admission")

    lookup = criteria.foreign_key_lookups["parcours_id"]
    assert lookup.target_table == "formations_parcours"
    assert lookup.target_column == "code_parcours"
    assert lookup.fixture_value == "DEMO-IIT-INFO-LIC"


def test_interest_label_collision_with_another_uuid_is_detected_by_fake_repository() -> None:
    interest = read_initial_data().interet[0].data
    other_id = UUID("5c8cdb0a-a393-4f17-b2ac-4d73b7e9d4e0")
    repository = FakeInterestRepository({interest.libelle: other_id})

    with pytest.raises(InitialDataConflict, match="different UUID"):
        ensure_interest_label_available(interest, repository)


def test_interest_with_same_uuid_and_label_is_not_a_collision() -> None:
    interest = read_initial_data().interet[0].data
    repository = FakeInterestRepository({interest.libelle: interest.id})

    assert ensure_interest_label_available(interest, repository) is None


def test_interest_without_existing_label_is_available() -> None:
    interest = read_initial_data().interet[0].data
    repository = FakeInterestRepository({})

    assert ensure_interest_label_available(interest, repository) is None
