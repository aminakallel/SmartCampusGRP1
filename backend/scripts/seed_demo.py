"""Idempotently load fictional fixtures into an isolated staging table."""

import json
from pathlib import Path
from typing import Annotated, Literal, Union

from pydantic import BaseModel, ConfigDict, Field, ValidationError, model_validator
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

from app.db.database import engine

FIXTURE_PATH = Path(__file__).resolve().parents[1] / "seed_data" / "demo_records.json"
UPSERT_RECORD = text("""
    INSERT INTO smartcampus_demo.seed_records (id, kind, payload)
    VALUES (:id, :kind, CAST(:payload AS JSONB))
    ON CONFLICT (id) DO UPDATE
    SET kind = EXCLUDED.kind, payload = EXCLUDED.payload
""")


class SeedDataError(ValueError):
    """Safe, concise error for malformed or unavailable demo fixtures."""


class DemoRecordBase(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    id: str = Field(min_length=1)
    provisional: Literal[True]


class EstablishmentRecord(DemoRecordBase):
    kind: Literal["establishment"]
    institution: Literal["IIT", "ISB"]
    name: str = Field(min_length=1)


class ProgramRecord(DemoRecordBase):
    kind: Literal["program"]
    institution: Literal["IIT", "ISB"]
    name: str = Field(min_length=1)
    level: str = Field(min_length=1)
    duration: str = Field(min_length=1)
    admission_conditions: str = Field(min_length=1)
    career_opportunities: list[str] = Field(min_length=1)


class DemoUserRecord(DemoRecordBase):
    kind: Literal["user"]
    username: str = Field(min_length=1)
    display_name: str = Field(min_length=1)
    email: str = Field(pattern=r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


DemoRecord = Annotated[
    Union[EstablishmentRecord, ProgramRecord, DemoUserRecord],
    Field(discriminator="kind"),
]


class SeedDocument(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    notice: str = Field(min_length=1)
    records: list[DemoRecord] = Field(min_length=1)

    @model_validator(mode="after")
    def validate_unique_ids(self) -> "SeedDocument":
        ids = [record.id for record in self.records]
        if len(ids) != len(set(ids)):
            raise ValueError("record IDs must be unique")
        return self


def validate_fixture_payload(payload: object) -> list[dict[str, object]]:
    try:
        document = SeedDocument.model_validate(payload)
    except ValidationError as exc:
        raise SeedDataError(f"Seed fixture validation failed ({exc.error_count()} error(s)).") from None
    return [record.model_dump() for record in document.records]


def read_fixtures(path: Path = FIXTURE_PATH) -> list[dict[str, object]]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        raise SeedDataError("Seed fixture file is missing.") from None
    except (OSError, UnicodeError):
        raise SeedDataError("Seed fixture file could not be read.") from None
    except json.JSONDecodeError:
        raise SeedDataError("Seed fixture file is not valid JSON.") from None
    return validate_fixture_payload(payload)


def prepare_demo_table(connection) -> None:
    connection.execute(text("CREATE SCHEMA IF NOT EXISTS smartcampus_demo"))
    connection.execute(text("""
        CREATE TABLE IF NOT EXISTS smartcampus_demo.seed_records (
            id TEXT PRIMARY KEY, kind TEXT NOT NULL, payload JSONB NOT NULL
        )
    """))


def upsert_records(connection, records: list[dict[str, object]]) -> None:
    """Insert or update fixture IDs, making repeated runs safe."""
    for record in records:
        connection.execute(UPSERT_RECORD, {
            "id": record["id"],
            "kind": record["kind"],
            "payload": json.dumps(record),
        })


def main() -> None:
    try:
        records = read_fixtures()
    except SeedDataError as exc:
        raise SystemExit(str(exc)) from None
    try:
        with engine.begin() as connection:
            prepare_demo_table(connection)
            upsert_records(connection, records)
    except SQLAlchemyError:
        raise SystemExit(
            "Could not load demo fixtures. Verify PostgreSQL availability and DATABASE_URL; "
            "database details were omitted to protect credentials."
        ) from None
    print(f"Loaded {len(records)} fictional records into smartcampus_demo.seed_records")


if __name__ == "__main__":
    main()
