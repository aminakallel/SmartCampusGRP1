from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field, field_serializer


class CritereAdmissionCreate(BaseModel):
    model_config = ConfigDict(
        str_strip_whitespace=True,
        json_schema_extra={
            "example": {
                "niveau_requis": "BAC",
                "filieres_acceptees": ["Mathématiques", "Sciences expérimentales"],
                "score_ou_moyenne_min": 12.5,
                "prerequis_matieres": "Mathématiques",
                "modalites_admission": "Étude de dossier et entretien",
                "priorite": 1,
            }
        },
    )

    niveau_requis: str = Field(min_length=1, max_length=100)
    filieres_acceptees: list[str] = Field(default_factory=list)
    score_ou_moyenne_min: Decimal | None = Field(default=None, ge=0, le=999.99)
    prerequis_matieres: str | None = None
    modalites_admission: str | None = None
    priorite: int = Field(default=1, ge=1, le=32767)


class CritereAdmissionUpdate(BaseModel):
    """Modification partielle : seuls les champs envoyés sont modifiés."""

    model_config = ConfigDict(str_strip_whitespace=True)

    niveau_requis: str | None = Field(default=None, min_length=1, max_length=100)
    filieres_acceptees: list[str] | None = None
    score_ou_moyenne_min: Decimal | None = Field(default=None, ge=0, le=999.99)
    prerequis_matieres: str | None = None
    modalites_admission: str | None = None
    priorite: int | None = Field(default=None, ge=1, le=32767)


class CritereAdmissionOut(CritereAdmissionCreate):
    model_config = ConfigDict(from_attributes=True)

    id: int
    parcours_id: int

    @field_serializer("score_ou_moyenne_min")
    def _score_en_nombre(self, value: Decimal | None) -> float | None:
        # Renvoyer 12.5 (nombre) plutôt que "12.50" (chaîne).
        return float(value) if value is not None else None
