from datetime import datetime
from enum import Enum

from pydantic import BaseModel, ConfigDict, Field, field_validator


class StatutFormation(str, Enum):
    BROUILLON = "BROUILLON"
    PUBLIE = "PUBLIE"
    ARCHIVE = "ARCHIVE"


def _check_majuscules(value: str | None) -> str | None:
    if value is not None and value != value.upper():
        raise ValueError("type_parcours doit être en majuscules")
    return value


class FormationCreate(BaseModel):
    model_config = ConfigDict(
        str_strip_whitespace=True,
        json_schema_extra={
            "example": {
                "etablissement_id": 1,
                "code_parcours": "IIT-INFO-LIC",
                "type_parcours": "LICENCE",
                "titre": "Licence en Informatique",
                "duree_semestres": 6,
                "resume": "Formation en informatique.",
                "objectifs_pedagogiques": "Maîtriser les fondamentaux.",
                "debouches": "Développeur, analyste de données",
                "modalite": "Présentiel",
                "langue_enseignement": "Français",
                "tags_interets": ["informatique", "programmation"],
                "statut": "BROUILLON",
                "source_reference": "Catalogue officiel IIT",
                "source_url": "https://example.edu/formations",
            }
        },
    )

    etablissement_id: int = Field(gt=0)
    code_parcours: str = Field(min_length=1, max_length=40)
    type_parcours: str = Field(min_length=2, max_length=30)
    titre: str = Field(min_length=2, max_length=200)
    duree_semestres: int = Field(ge=1, le=20)
    resume: str = Field(min_length=1)
    objectifs_pedagogiques: str | None = None
    debouches: str | None = None
    modalite: str = Field(min_length=1, max_length=50)
    langue_enseignement: str = Field(min_length=1, max_length=50)
    tags_interets: list[str] = Field(default_factory=list)
    statut: StatutFormation = StatutFormation.BROUILLON
    source_reference: str = Field(min_length=1, max_length=255)
    source_url: str | None = Field(default=None, max_length=255)

    @field_validator("type_parcours")
    @classmethod
    def type_parcours_en_majuscules(cls, value: str) -> str:
        return _check_majuscules(value)


class FormationUpdate(BaseModel):
    """Modification partielle : seuls les champs envoyés sont modifiés."""

    model_config = ConfigDict(str_strip_whitespace=True)

    etablissement_id: int | None = Field(default=None, gt=0)
    code_parcours: str | None = Field(default=None, min_length=1, max_length=40)
    type_parcours: str | None = Field(default=None, min_length=2, max_length=30)
    titre: str | None = Field(default=None, min_length=2, max_length=200)
    duree_semestres: int | None = Field(default=None, ge=1, le=20)
    resume: str | None = Field(default=None, min_length=1)
    objectifs_pedagogiques: str | None = None
    debouches: str | None = None
    modalite: str | None = Field(default=None, min_length=1, max_length=50)
    langue_enseignement: str | None = Field(default=None, min_length=1, max_length=50)
    tags_interets: list[str] | None = None
    statut: StatutFormation | None = None
    source_reference: str | None = Field(default=None, min_length=1, max_length=255)
    source_url: str | None = Field(default=None, max_length=255)

    @field_validator("type_parcours")
    @classmethod
    def type_parcours_en_majuscules(cls, value: str | None) -> str | None:
        return _check_majuscules(value)


class FormationOut(FormationCreate):
    model_config = ConfigDict(from_attributes=True)

    id: int
    derniere_synchro_at: datetime | None
