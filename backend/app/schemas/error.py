from pydantic import BaseModel, Field


class ErrorDetail(BaseModel):
    code: str = Field(examples=["NOT_FOUND"])
    message: str = Field(examples=["Formation 999 introuvable"])


class ErrorResponse(BaseModel):
    error: ErrorDetail