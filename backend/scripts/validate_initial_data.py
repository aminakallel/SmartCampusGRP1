"""Validate provisional SA-18 business fixtures without connecting to a database."""

import json
from datetime import date, datetime
from decimal import Decimal
from pathlib import Path
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, ValidationError, field_validator, model_validator

FIXTURE_PATH = Path(__file__).resolve().parents[1] / "seed_data" / "initial_data.json"

LOAD_ORDER = (
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

IDENTITY_RESOLUTION_KEYS = {
    "formations_parcours.etablissement_id",
    "criteres_admission.parcours_id",
    "documents_catalogue_rag.parcours_id",
    "profil_candidat.utilisateur_id",
    "resultat_scolaire.profil_id",
    "profil_interet.profil_id",
    "profil_interet.interet_id",
}


class InitialDataError(ValueError):
    """Safe, concise error for an unreadable or invalid SA-18 fixture."""


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True, populate_by_name=True)


class ProvisionalModel(StrictModel):
    provisional: Literal[True]


class SeedEntity(ProvisionalModel):
    seed_key: str = Field(min_length=1)


class EstablishmentData(StrictModel):
    code: str = Field(min_length=1, max_length=20)
    nom: str = Field(min_length=1, max_length=150)
    ville: str = Field(min_length=1, max_length=100)
    site_web: str | None = Field(default=None, max_length=255)
    est_actif: bool


class EstablishmentRecord(SeedEntity):
    data: EstablishmentData


class ProgramData(StrictModel):
    code_parcours: str = Field(min_length=1, max_length=40)
    type_parcours: str = Field(min_length=1, max_length=30)
    titre: str = Field(min_length=1, max_length=200)
    duree_semestres: int = Field(gt=0, le=32767)
    resume: str = Field(min_length=1)
    objectifs_pedagogiques: str | None = None
    debouches: str | None = None
    modalite: str = Field(min_length=1, max_length=50)
    langue_enseignement: str = Field(min_length=1, max_length=50)
    tags_interets: list[str] = Field(min_length=1)
    statut: Literal["BROUILLON", "PUBLIE", "ARCHIVE"]
    source_reference: str = Field(min_length=1, max_length=255)
    source_url: str | None = Field(default=None, max_length=255)
    derniere_synchro_at: datetime | None = None


class ProgramRecord(SeedEntity):
    etablissement_code_ref: str = Field(min_length=1, max_length=20)
    data: ProgramData


class AdmissionCriteriaData(StrictModel):
    niveau_requis: str = Field(min_length=1, max_length=100)
    filieres_acceptees: list[str] = Field(min_length=1)
    score_ou_moyenne_min: Decimal | None = Field(default=None, max_digits=5, decimal_places=2)
    prerequis_matieres: str | None = None
    modalites_admission: str | None = None
    priorite: int = Field(ge=-32768, le=32767)


class AdmissionCriteriaRecord(SeedEntity):
    parcours_code_ref: str = Field(min_length=1, max_length=40)
    data: AdmissionCriteriaData


class CatalogueRAGData(StrictModel):
    type_source: Literal["PROGRAMME", "CONDITIONS", "FAQ", "BROCHURE"]
    titre_source: str = Field(min_length=1, max_length=200)
    extrait_url_ou_ref: str = Field(min_length=1, max_length=255)
    contenu_chunk: str = Field(min_length=1)
    embedding: list[float] | None = Field(default=None, min_length=1536, max_length=1536)


class CatalogueRAGRecord(SeedEntity):
    parcours_code_ref: str = Field(min_length=1, max_length=40)
    data: CatalogueRAGData


class UserData(StrictModel):
    id: UUID
    nom: str = Field(min_length=1, max_length=100)
    prenom: str = Field(min_length=1, max_length=100)
    email: str = Field(min_length=1, max_length=255, pattern=r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
    role: Literal["candidat", "admin"]
    langue_preferee: Literal["fr", "tunisien", "arabizi"]
    est_actif: bool
    derniere_connexion: datetime | None

    @field_validator("id")
    @classmethod
    def require_uuid_v4(cls, value: UUID) -> UUID:
        if value.version != 4:
            raise ValueError("SA-13 user IDs must be UUID version 4")
        return value


class UserRecord(ProvisionalModel):
    data: UserData


class CandidateProfileData(StrictModel):
    id: UUID
    telephone: str | None = Field(default=None, max_length=20, pattern=r"^\+?[0-9]{8,15}$")
    date_naissance: date | None
    ville: str | None = Field(default=None, max_length=100)
    gouvernorat: str | None = Field(default=None, max_length=50)
    pays: str = Field(min_length=1, max_length=60)
    adresse: str | None = None
    niveau_etudes: str | None = Field(default=None, max_length=100)
    serie_bac: str | None = Field(default=None, max_length=60)
    etablissement_origine: str | None = Field(default=None, max_length=150)
    annee_obtention: int | None = Field(default=None, ge=1990, le=2100)
    moyenne_generale: Decimal | None = Field(default=None, ge=0, le=20, max_digits=4, decimal_places=2)
    objectifs: str | None = None
    etablissement_prefere: Literal["IIT", "ISB", "indifferent"]
    mode_contact_prefere: Literal["email", "telephone"]

    @field_validator("id")
    @classmethod
    def require_uuid_v4(cls, value: UUID) -> UUID:
        if value.version != 4:
            raise ValueError("SA-13 profile IDs must be UUID version 4")
        return value

    @field_validator("date_naissance")
    @classmethod
    def reject_future_birth_date(cls, value: date | None) -> date | None:
        if value is not None and value > date.today():
            raise ValueError("birth date cannot be in the future")
        return value


class CandidateProfileRecord(ProvisionalModel):
    utilisateur_id_ref: UUID
    data: CandidateProfileData

    @field_validator("utilisateur_id_ref")
    @classmethod
    def require_uuid_v4(cls, value: UUID) -> UUID:
        if value.version != 4:
            raise ValueError("SA-13 user references must be UUID version 4")
        return value


class SchoolResultData(StrictModel):
    id: UUID
    matiere: str = Field(min_length=1, max_length=100)
    periode: str = Field(min_length=1, max_length=50)
    note: Decimal = Field(ge=0, le=20, max_digits=4, decimal_places=2)
    coefficient: Decimal = Field(gt=0, max_digits=4, decimal_places=2)

    @field_validator("id")
    @classmethod
    def require_uuid_v4(cls, value: UUID) -> UUID:
        if value.version != 4:
            raise ValueError("SA-13 result IDs must be UUID version 4")
        return value


class SchoolResultRecord(ProvisionalModel):
    profil_id_ref: UUID
    data: SchoolResultData

    @field_validator("profil_id_ref")
    @classmethod
    def require_uuid_v4(cls, value: UUID) -> UUID:
        if value.version != 4:
            raise ValueError("SA-13 profile references must be UUID version 4")
        return value


class InterestData(StrictModel):
    id: UUID
    libelle: str = Field(min_length=1, max_length=100)
    categorie: str | None = Field(default=None, max_length=60)

    @field_validator("id")
    @classmethod
    def require_uuid_v4(cls, value: UUID) -> UUID:
        if value.version != 4:
            raise ValueError("SA-13 interest IDs must be UUID version 4")
        return value


class InterestRecord(ProvisionalModel):
    data: InterestData


class ProfileInterestData(StrictModel):
    ajoute_le: datetime


class ProfileInterestRecord(ProvisionalModel):
    profil_id_ref: UUID
    interet_id_ref: UUID
    data: ProfileInterestData

    @field_validator("profil_id_ref", "interet_id_ref")
    @classmethod
    def require_uuid_v4(cls, value: UUID) -> UUID:
        if value.version != 4:
            raise ValueError("SA-13 relationship references must be UUID version 4")
        return value


class FixtureMetadata(StrictModel):
    task: Literal["SA-18"]
    purpose: str = Field(min_length=1)
    status: Literal["provisional_not_ready_for_database_insert"]
    notes: list[str] = Field(min_length=1)
    required_before_database_insert: list[str] = Field(min_length=1)
    load_order: list[str]
    identity_resolution: dict[str, str]

    @model_validator(mode="after")
    def validate_load_order(self) -> "FixtureMetadata":
        if tuple(self.load_order) != LOAD_ORDER:
            raise ValueError("load_order must respect SA-12/SA-13 foreign-key dependencies")
        if set(self.identity_resolution) != IDENTITY_RESOLUTION_KEYS:
            raise ValueError("identity_resolution must define every fixture foreign-key mapping")
        return self


class InitialDataDocument(StrictModel):
    metadata: FixtureMetadata = Field(alias="_metadata")
    etablissements: list[EstablishmentRecord] = Field(min_length=2)
    formations_parcours: list[ProgramRecord] = Field(min_length=1)
    criteres_admission: list[AdmissionCriteriaRecord] = Field(min_length=1)
    documents_catalogue_rag: list[CatalogueRAGRecord] = Field(default_factory=list)
    utilisateur: UserRecord
    profil_candidat: CandidateProfileRecord
    resultat_scolaire: list[SchoolResultRecord] = Field(min_length=1)
    interet: list[InterestRecord] = Field(min_length=1)
    profil_interet: list[ProfileInterestRecord] = Field(min_length=1)

    @model_validator(mode="after")
    def validate_references_and_uniqueness(self) -> "InitialDataDocument":
        seed_keys = [
            *(item.seed_key for item in self.etablissements),
            *(item.seed_key for item in self.formations_parcours),
            *(item.seed_key for item in self.criteres_admission),
            *(item.seed_key for item in self.documents_catalogue_rag),
        ]
        if len(seed_keys) != len(set(seed_keys)):
            raise ValueError("fixture seed keys must be unique")

        establishment_codes = [item.data.code for item in self.etablissements]
        if len(establishment_codes) != len(set(establishment_codes)):
            raise ValueError("establishment codes must be unique")
        if set(establishment_codes) != {"IIT", "ISB"}:
            raise ValueError("fixture must contain exactly the IIT and ISB establishments")

        program_codes = [item.data.code_parcours for item in self.formations_parcours]
        if len(program_codes) != len(set(program_codes)):
            raise ValueError("program codes must be unique")
        establishment_code_set = set(establishment_codes)
        for program in self.formations_parcours:
            if program.etablissement_code_ref not in establishment_code_set:
                raise ValueError("program references an unknown establishment code")

        for criteria in self.criteres_admission:
            if criteria.parcours_code_ref not in set(program_codes):
                raise ValueError("admission criteria reference an unknown program code")
        for document in self.documents_catalogue_rag:
            if document.parcours_code_ref not in set(program_codes):
                raise ValueError("catalogue RAG document references an unknown program code")

        user_id = self.utilisateur.data.id
        profile_id = self.profil_candidat.data.id
        if self.utilisateur.data.role != "candidat":
            raise ValueError("the seeded SA-18 account must have the candidate role")
        if self.profil_candidat.utilisateur_id_ref != user_id:
            raise ValueError("candidate profile must reference the seeded user UUID")

        result_keys: list[tuple[UUID, str, str]] = []
        for result in self.resultat_scolaire:
            if result.profil_id_ref != profile_id:
                raise ValueError("school result references an unknown candidate profile")
            result_keys.append((result.profil_id_ref, result.data.matiere, result.data.periode))
        if len(result_keys) != len(set(result_keys)):
            raise ValueError("school result profile/subject/period keys must be unique")

        interest_ids = [item.data.id for item in self.interet]
        interest_labels = [item.data.libelle for item in self.interet]
        if len(interest_ids) != len(set(interest_ids)) or len(interest_labels) != len(set(interest_labels)):
            raise ValueError("interest IDs and labels must be unique")

        links = [(item.profil_id_ref, item.interet_id_ref) for item in self.profil_interet]
        if len(links) != len(set(links)):
            raise ValueError("profile-interest links must be unique")
        valid_interest_ids = set(interest_ids)
        for profile_ref, interest_ref in links:
            if profile_ref != profile_id or interest_ref not in valid_interest_ids:
                raise ValueError("profile-interest link references an unknown profile or interest")
        return self


def validate_initial_data(payload: object) -> InitialDataDocument:
    """Validate a fixture and its cross-references without accessing PostgreSQL."""
    try:
        return InitialDataDocument.model_validate(payload)
    except ValidationError as exc:
        raise InitialDataError(
            f"Initial SA-18 fixture validation failed ({exc.error_count()} error(s))."
        ) from None


def read_initial_data(path: Path = FIXTURE_PATH) -> InitialDataDocument:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        raise InitialDataError("Initial SA-18 fixture file is missing.") from None
    except (OSError, UnicodeError):
        raise InitialDataError("Initial SA-18 fixture file could not be read.") from None
    except json.JSONDecodeError:
        raise InitialDataError("Initial SA-18 fixture is not valid JSON.") from None
    return validate_initial_data(payload)


def main() -> None:
    try:
        fixture = read_initial_data()
    except InitialDataError as exc:
        raise SystemExit(str(exc)) from None
    print(
        "Validated provisional SA-18 fixture without database access: "
        f"{len(fixture.etablissements)} establishments, "
        f"{len(fixture.formations_parcours)} programs, "
        f"{len(fixture.criteres_admission)} admission criteria, "
        f"{len(fixture.documents_catalogue_rag)} RAG document(s), "
        "1 candidate, 1 profile, "
        f"{len(fixture.resultat_scolaire)} school result(s), "
        f"{len(fixture.interet)} interest(s), "
        f"{len(fixture.profil_interet)} profile-interest link(s)."
    )


if __name__ == "__main__":
    main()
