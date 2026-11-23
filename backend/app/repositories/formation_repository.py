"""Repository en mémoire (aucune base de données).

Les données disparaissent à l'arrêt du serveur. Les établissements IIT et ISB
sont créés au démarrage. Plus tard, une autre classe avec les mêmes méthodes
pourra stocker les données dans une vraie base sans changer les routes.
"""

from __future__ import annotations

from app.domain.models import CritereAdmission, Etablissement, FormationParcours
from app.schemas.critere import CritereAdmissionCreate
from app.schemas.formation import FormationCreate


class InMemoryCatalogueRepository:
    def __init__(self) -> None:
        self._etablissements: dict[int, Etablissement] = {}
        self._formations: dict[int, FormationParcours] = {}
        self._criteres: dict[int, CritereAdmission] = {}
        self._next_etablissement_id = 1
        self._next_formation_id = 1
        self._next_critere_id = 1
        # Données de référence
        self.add_etablissement("IIT", "Institut International de Technologie", "Sfax")
        self.add_etablissement("ISB", "ISB (nom officiel à compléter)", "Sfax")

    # ---------------- établissements ----------------
    def add_etablissement(
        self,
        code: str,
        nom: str,
        ville: str,
        site_web: str | None = None,
        est_actif: bool = True,
    ) -> Etablissement:
        etablissement = Etablissement(
            id=self._next_etablissement_id,
            code=code,
            nom=nom,
            ville=ville,
            site_web=site_web,
            est_actif=est_actif,
        )
        self._etablissements[etablissement.id] = etablissement
        self._next_etablissement_id += 1
        return etablissement

    def get_etablissement(self, etablissement_id: int) -> Etablissement | None:
        return self._etablissements.get(etablissement_id)

    def get_etablissement_by_code(self, code: str) -> Etablissement | None:
        for etablissement in self._etablissements.values():
            if etablissement.code == code:
                return etablissement
        return None

    def list_etablissements(self) -> list[Etablissement]:
        return [e for e in self._etablissements.values() if e.est_actif]

    # ---------------- formations ----------------
    def list(
        self,
        etablissement_code: str | None = None,
        type_parcours: str | None = None,
        statut: str | None = None,
        public_only: bool = True,
        limit: int = 50,
        offset: int = 0,
    ) -> list[FormationParcours]:
        items = sorted(self._formations.values(), key=lambda f: f.id)
        result = []
        for formation in items:
            etablissement = self._etablissements.get(formation.etablissement_id)
            if etablissement is None:
                continue
            if public_only and (formation.statut != "PUBLIE" or not etablissement.est_actif):
                continue
            if etablissement_code is not None and etablissement.code != etablissement_code:
                continue
            if type_parcours is not None and formation.type_parcours != type_parcours:
                continue
            if statut is not None and formation.statut != statut:
                continue
            result.append(formation)
        return result[offset : offset + limit]

    def get(self, formation_id: int) -> FormationParcours | None:
        return self._formations.get(formation_id)

    def find_by_code(self, code_parcours: str) -> FormationParcours | None:
        for formation in self._formations.values():
            if formation.code_parcours == code_parcours:
                return formation
        return None

    def create(self, data: FormationCreate) -> FormationParcours:
        formation = FormationParcours(
            id=self._next_formation_id,
            **data.model_dump(exclude={"statut"}),
            statut=data.statut.value,
        )
        self._formations[formation.id] = formation
        self._next_formation_id += 1
        return formation

    def update(self, formation: FormationParcours, changes: dict) -> FormationParcours:
        for key, value in changes.items():
            if key == "statut" and value is not None:
                value = value.value if hasattr(value, "value") else value
            setattr(formation, key, value)
        return formation

    def archive(self, formation: FormationParcours) -> None:
        formation.statut = "ARCHIVE"

    # ---------------- critères d'admission ----------------
    def list_criteres(self, parcours_id: int) -> list[CritereAdmission]:
        items = [c for c in self._criteres.values() if c.parcours_id == parcours_id]
        return sorted(items, key=lambda c: (c.priorite, c.id))

    def get_critere(self, critere_id: int) -> CritereAdmission | None:
        return self._criteres.get(critere_id)

    def create_critere(
        self, parcours_id: int, data: CritereAdmissionCreate
    ) -> CritereAdmission:
        critere = CritereAdmission(
            id=self._next_critere_id,
            parcours_id=parcours_id,
            **data.model_dump(),
        )
        self._criteres[critere.id] = critere
        self._next_critere_id += 1
        return critere

    def update_critere(self, critere: CritereAdmission, changes: dict) -> CritereAdmission:
        for key, value in changes.items():
            setattr(critere, key, value)
        return critere

    def delete_critere(self, critere: CritereAdmission) -> None:
        self._criteres.pop(critere.id, None)
