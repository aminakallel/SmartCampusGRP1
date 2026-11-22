from pydantic import BaseModel, ConfigDict, Field


class EtablissementOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    code: str
    nom: str
    ville: str
    site_web: str | None
    est_actif: bool


class EtablissementCreate(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    code: str = Field(min_length=1, max_length=20)
    nom: str = Field(min_length=1, max_length=150)
    ville: str = Field(min_length=1, max_length=100)
    site_web: str | None = Field(default=None, max_length=255)
    est_actif: bool = True
