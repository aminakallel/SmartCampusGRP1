"""Build a database-free SA-18 load plan; this module never emits or executes SQL."""

from dataclasses import dataclass
from typing import Literal, Protocol
from uuid import UUID

from pydantic import BaseModel

from scripts.validate_initial_data import InitialDataDocument, InterestData, read_initial_data


class InitialDataConflict(ValueError):
    """A fixture identity conflicts with an existing row found by a read-only lookup."""


class InterestLookup(Protocol):
    """Minimal read-only lookup required to check the SA-13 unique interest label."""

    def find_interest_id_by_label(self, label: str) -> UUID | None: ...


def ensure_interest_label_available(interest: InterestData, lookup: InterestLookup) -> None:
    """Reject a label owned by another UUID; does not write data or generate SQL."""
    existing_id = lookup.find_interest_id_by_label(interest.libelle)
    if existing_id is not None and existing_id != interest.id:
        raise InitialDataConflict(
            "interest label is already assigned to a different UUID"
        )


@dataclass(frozen=True)
class ForeignKeyLookup:
    target_table: str
    target_column: str
    fixture_value: str


@dataclass(frozen=True)
class PlannedWrite:
    table: str
    fixture_key: str
    strategy: str
    values: dict[str, object]
    conflict_columns: tuple[str, ...] = ()
    generated_columns: tuple[str, ...] = ()
    foreign_key_lookups: dict[str, ForeignKeyLookup] | None = None
    blockers: tuple[str, ...] = ()

    @property
    def idempotent(self) -> bool:
        return bool(self.conflict_columns) and not self.blockers


@dataclass(frozen=True)
class InitialDataPlan:
    writes: tuple[PlannedWrite, ...]
    empty_tables: tuple[str, ...]
    blockers: tuple[str, ...]
    executable: Literal[False] = False


def _values(model: BaseModel) -> dict[str, object]:
    return model.model_dump(mode="json")


def build_initial_data_plan(
    fixture: InitialDataDocument | None = None,
) -> InitialDataPlan:
    """Describe row writes and FK lookups without touching a database."""
    data = fixture or read_initial_data()
    writes: list[PlannedWrite] = []

    for record in data.etablissements:
        writes.append(PlannedWrite(
            table="etablissements",
            fixture_key=record.seed_key,
            strategy="upsert_by_business_code",
            values=_values(record.data),
            conflict_columns=("code",),
            generated_columns=("id",),
        ))

    for record in data.formations_parcours:
        writes.append(PlannedWrite(
            table="formations_parcours",
            fixture_key=record.seed_key,
            strategy="upsert_by_business_code",
            values=_values(record.data),
            conflict_columns=("code_parcours",),
            generated_columns=("id",),
            foreign_key_lookups={
                "etablissement_id": ForeignKeyLookup(
                    target_table="etablissements",
                    target_column="code",
                    fixture_value=record.etablissement_code_ref,
                )
            },
        ))

    for record in data.criteres_admission:
        writes.append(PlannedWrite(
            table="criteres_admission",
            fixture_key=record.seed_key,
            strategy="insert_requires_idempotency_decision",
            values=_values(record.data),
            generated_columns=("id",),
            foreign_key_lookups={
                "parcours_id": ForeignKeyLookup(
                    target_table="formations_parcours",
                    target_column="code_parcours",
                    fixture_value=record.parcours_code_ref,
                )
            },
            blockers=(
                "SA-12 defines no UNIQUE key for criteria; a repeatable UPSERT key is not approved.",
            ),
        ))

    for record in data.documents_catalogue_rag:
        writes.append(PlannedWrite(
            table="documents_catalogue_rag",
            fixture_key=record.seed_key,
            strategy="insert_requires_idempotency_decision",
            values=_values(record.data),
            generated_columns=("id",),
            foreign_key_lookups={
                "parcours_id": ForeignKeyLookup(
                    target_table="formations_parcours",
                    target_column="code_parcours",
                    fixture_value=record.parcours_code_ref,
                )
            },
            blockers=(
                "SA-12 defines no UNIQUE key for RAG documents; a repeatable UPSERT key is not approved.",
            ),
        ))

    user_hash_blocker = (
        "mot_de_passe_hash is required by SA-13 but is intentionally absent; wait for the approved auth hash provider.",
    )
    writes.append(PlannedWrite(
        table="utilisateur",
        fixture_key="candidate_user",
        strategy="upsert_by_uuid_blocked_until_auth_hash_available",
        values=_values(data.utilisateur.data),
        conflict_columns=("id",),
        blockers=user_hash_blocker,
    ))

    profile_id = str(data.profil_candidat.data.id)
    writes.append(PlannedWrite(
        table="profil_candidat",
        fixture_key="candidate_profile",
        strategy="upsert_by_uuid",
        values=_values(data.profil_candidat.data),
        conflict_columns=("id",),
        foreign_key_lookups={
            "utilisateur_id": ForeignKeyLookup(
                target_table="utilisateur",
                target_column="id",
                fixture_value=str(data.profil_candidat.utilisateur_id_ref),
            )
        },
        blockers=("Depends on a candidate user whose required password hash is not yet available.",),
    ))

    for index, record in enumerate(data.resultat_scolaire, start=1):
        writes.append(PlannedWrite(
            table="resultat_scolaire",
            fixture_key=f"school_result_{index}",
            strategy="upsert_by_uuid",
            values=_values(record.data),
            conflict_columns=("id",),
            foreign_key_lookups={
                "profil_id": ForeignKeyLookup(
                    target_table="profil_candidat",
                    target_column="id",
                    fixture_value=str(record.profil_id_ref),
                )
            },
            blockers=("Depends on the candidate profile.",),
        ))

    for record in data.interet:
        writes.append(PlannedWrite(
            table="interet",
            fixture_key=f"interest_{record.data.id}",
            strategy="upsert_by_uuid_with_label_collision_check",
            values=_values(record.data),
            conflict_columns=("id",),
        ))

    for index, record in enumerate(data.profil_interet, start=1):
        writes.append(PlannedWrite(
            table="profil_interet",
            fixture_key=f"profile_interest_{index}",
            strategy="upsert_by_composite_primary_key",
            values=_values(record.data),
            conflict_columns=("profil_id", "interet_id"),
            foreign_key_lookups={
                "profil_id": ForeignKeyLookup(
                    target_table="profil_candidat",
                    target_column="id",
                    fixture_value=str(record.profil_id_ref),
                ),
                "interet_id": ForeignKeyLookup(
                    target_table="interet",
                    target_column="id",
                    fixture_value=str(record.interet_id_ref),
                ),
            },
            blockers=("Depends on the candidate profile.",),
        ))

    all_tables = (
        "etablissements",
        "formations_parcours",
        "criteres_admission",
        "documents_catalogue_rag",
        "utilisateur",
        "profil_candidat",
        "resultat_scolaire",
        "interet",
        "profil_interet",
    )
    planned_tables = {write.table for write in writes}
    blockers = (
        "Plan only: no SQL is generated or executed by this module.",
        "SA-12 migration and its PostgreSQL schema must be available and validated before catalogue writes.",
        "The candidate account needs the approved mot_de_passe_hash provider.",
        "Criteria and RAG records need team-approved idempotency keys before a reusable seed can write them.",
    )
    return InitialDataPlan(
        writes=tuple(writes),
        empty_tables=tuple(table for table in all_tables if table not in planned_tables),
        blockers=blockers,
    )


def main() -> None:
    plan = build_initial_data_plan()
    print(f"Prepared database-free SA-18 plan: {len(plan.writes)} row(s); executable={plan.executable}.")
    print(f"Empty fixture tables: {', '.join(plan.empty_tables) or 'none'}")
    for blocker in plan.blockers:
        print(f"Pending: {blocker}")


if __name__ == "__main__":
    main()
