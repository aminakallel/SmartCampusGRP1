from __future__ import annotations

from app.core.errors import AppError
from app.domain.models import CritereAdmission, Etablissement, FormationParcours
from app.repositories.formation_repository import InMemoryCatalogueRepository
from app.schemas.critere import CritereAdmissionCreate, CritereAdmissionUpdate
from app.schemas.formation import (
    FormationCreate,
    FormationUpdate,
    StatutFormation,
)

DUPLICATE_MSG = "Le code_parcours existe déjà"

# Champs obligatoires d'une formation (SA-12) : ils ne peuvent pas être mis à null.
REQUIRED_FORMATION_FIELDS = (
    "etablissement_id",
    "code_parcours",
    "type_parcours",
    "titre",
    "duree_semestres",
    "resume",
    "modalite",
    "langue_enseignement",
    "tags_interets",
    "statut",
    "source_reference",
)
REQUIRED_CRITERE_FIELDS = ("niveau_requis", "filieres_acceptees", "priorite")


class FormationService:
    def __init__(self, repo: InMemoryCatalogueRepository) -> None:
        self.repo = repo

    # ---------------- helpers ----------------
    def _formation_or_404(self, formation_id: int) -> FormationParcours:
        formation = self.repo.get(formation_id)
        if formation is None:
            raise AppError(404, "NOT_FOUND", f"Formation {formation_id} introuvable")
        return formation

    def _critere_or_404(self, critere_id: int) -> CritereAdmission:
        critere = self.repo.get_critere(critere_id)
        if critere is None:
            raise AppError(404, "NOT_FOUND", f"Critère {critere_id} introuvable")
        return critere

    def _require_active_etablissement(self, etablissement_id: int) -> Etablissement:
        etablissement = self.repo.get_etablissement(etablissement_id)
        if etablissement is None:
            raise AppError(
                404, "NOT_FOUND", f"Établissement {etablissement_id} introuvable"
            )
        if not etablissement.est_actif:
            raise AppError(
                422, "VALIDATION_ERROR", f"L'établissement {etablissement.code} est inactif"
            )
        return etablissement

    def _is_public(self, formation: FormationParcours) -> bool:
        etablissement = self.repo.get_etablissement(formation.etablissement_id)
        return (
            formation.statut == "PUBLIE"
            and etablissement is not None
            and etablissement.est_actif
        )

    # ---------------- formations ----------------
    def list(
        self,
        role: str,
        etablissement_code: str | None = None,
        type_parcours: str | None = None,
        statut: StatutFormation | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> list[FormationParcours]:
        is_admin = role == "admin"
        if statut is not None and not is_admin:
            raise AppError(403, "FORBIDDEN", "Le filtre statut est réservé à l'admin")
        return self.repo.list(
            etablissement_code=etablissement_code,
            type_parcours=type_parcours,
            statut=statut.value if statut else None,
            public_only=not is_admin,
            limit=limit,
            offset=offset,
        )

    def get(self, formation_id: int, role: str) -> FormationParcours:
        formation = self._formation_or_404(formation_id)
        if role != "admin" and not self._is_public(formation):
            # Une formation non publique est présentée comme introuvable.
            raise AppError(404, "NOT_FOUND", f"Formation {formation_id} introuvable")
        return formation

    def create(self, data: FormationCreate) -> FormationParcours:
        self._require_active_etablissement(data.etablissement_id)
        if self.repo.find_by_code(data.code_parcours) is not None:
            raise AppError(409, "DUPLICATE", DUPLICATE_MSG)
        return self.repo.create(data)

    def update(self, formation_id: int, data: FormationUpdate) -> FormationParcours:
        current = self._formation_or_404(formation_id)
        changes = data.model_dump(exclude_unset=True)
        if any(changes.get(field, "non-null") is None for field in REQUIRED_FORMATION_FIELDS):
            raise AppError(
                422,
                "VALIDATION_ERROR",
                "Les champs obligatoires d'une formation ne peuvent pas être nuls",
            )
        if "etablissement_id" in changes:
            self._require_active_etablissement(changes["etablissement_id"])
        new_code = changes.get("code_parcours", current.code_parcours)
        other = self.repo.find_by_code(new_code)
        if other is not None and other.id != formation_id:
            raise AppError(409, "DUPLICATE", DUPLICATE_MSG)
        return self.repo.update(current, changes)

    def archive(self, formation_id: int) -> None:
        formation = self._formation_or_404(formation_id)
        if formation.statut != "ARCHIVE":
            self.repo.archive(formation)

    # ---------------- critères d'admission ----------------
    def list_criteres(self, formation_id: int, role: str) -> list[CritereAdmission]:
        self.get(formation_id, role)  # 404 si introuvable ou non visible
        return self.repo.list_criteres(formation_id)

    def get_critere(self, critere_id: int, role: str) -> CritereAdmission:
        critere = self._critere_or_404(critere_id)
        self.get(critere.parcours_id, role)
        return critere

    def create_critere(
        self, formation_id: int, data: CritereAdmissionCreate
    ) -> CritereAdmission:
        self._formation_or_404(formation_id)
        return self.repo.create_critere(formation_id, data)

    def update_critere(
        self, critere_id: int, data: CritereAdmissionUpdate
    ) -> CritereAdmission:
        critere = self._critere_or_404(critere_id)
        changes = data.model_dump(exclude_unset=True)
        if any(changes.get(field, "non-null") is None for field in REQUIRED_CRITERE_FIELDS):
            raise AppError(
                422,
                "VALIDATION_ERROR",
                "niveau_requis, filieres_acceptees et priorite ne peuvent pas être nuls",
            )
        return self.repo.update_critere(critere, changes)

    def delete_critere(self, critere_id: int) -> None:
        critere = self._critere_or_404(critere_id)
        self.repo.delete_critere(critere)

    # ---------------- établissements ----------------
    def list_etablissements(self) -> list[Etablissement]:
        return self.repo.list_etablissements()
