from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from uuid import UUID


class UserRole(str, Enum):
    CANDIDAT = "candidat"
    ADMIN = "admin"


@dataclass(frozen=True, slots=True)
class UserAccount:
    """SA-13 `utilisateur` row shape shared by SQL and test repositories."""

    id: UUID
    nom: str
    prenom: str
    email: str
    mot_de_passe_hash: str
    role: UserRole
    langue_preferee: str
    est_actif: bool
    derniere_connexion: datetime | None
    cree_le: datetime
    modifie_le: datetime
