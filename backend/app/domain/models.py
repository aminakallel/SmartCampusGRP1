"""Entités du catalogue (modèle SA-12), sans base de données.

Seules les 3 entités gérées par SA-20 sont représentées. La table
documents_catalogue_rag (corpus RAG / pgvector) est hors périmètre.
"""
from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal


@dataclass
class Etablissement:
    id: int
    code: str
    nom: str
    ville: str
    site_web: str | None = None
    est_actif: bool = True


@dataclass
class FormationParcours:
    id: int
    etablissement_id: int
    code_parcours: str
    type_parcours: str
    titre: str
    duree_semestres: int
    resume: str
    modalite: str
    langue_enseignement: str
    source_reference: str
    objectifs_pedagogiques: str | None = None
    debouches: str | None = None
    tags_interets: list[str] = field(default_factory=list)
    statut: str = "BROUILLON"  # BROUILLON | PUBLIE | ARCHIVE
    source_url: str | None = None
    derniere_synchro_at: datetime | None = None


@dataclass
class CritereAdmission:
    id: int
    parcours_id: int
    niveau_requis: str
    filieres_acceptees: list[str] = field(default_factory=list)
    score_ou_moyenne_min: Decimal | None = None
    prerequis_matieres: str | None = None
    modalites_admission: str | None = None
    priorite: int = 1
