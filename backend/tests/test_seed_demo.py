import json

import pytest
from sqlalchemy.sql.elements import TextClause

from scripts.seed_demo import (
    FIXTURE_PATH,
    SeedDataError,
    read_fixtures,
    upsert_records,
    validate_fixture_payload,
)


class RecordingConnection:
    def __init__(self) -> None:
        self.statements: list[tuple[str, dict | None]] = []

    def execute(self, statement: TextClause, parameters: dict | None = None) -> None:
        self.statements.append((str(statement), parameters))


def test_demo_fixture_records_are_fictional_and_provisional() -> None:
    records = read_fixtures()
    assert records
    assert all(record["provisional"] is True for record in records)
    assert {record["kind"] for record in records} >= {"establishment", "program", "user"}


def test_seed_rejects_missing_program_fields() -> None:
    payload = json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))
    del payload["records"][2]["duration"]
    with pytest.raises(SeedDataError, match="validation failed"):
        validate_fixture_payload(payload)


def test_seed_rejects_duplicate_ids() -> None:
    payload = json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))
    payload["records"][1]["id"] = payload["records"][0]["id"]
    with pytest.raises(SeedDataError, match="validation failed"):
        validate_fixture_payload(payload)


def test_seed_rejects_non_provisional_records() -> None:
    payload = json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))
    payload["records"][0]["provisional"] = False
    with pytest.raises(SeedDataError, match="validation failed"):
        validate_fixture_payload(payload)


def test_seed_reports_invalid_json_without_dumping_file_contents(tmp_path) -> None:
    fixture = tmp_path / "invalid.json"
    fixture.write_text('{"password":"sensitive"', encoding="utf-8")
    with pytest.raises(SeedDataError, match="not valid JSON") as error:
        read_fixtures(fixture)
    assert "sensitive" not in str(error.value)


def test_seed_uses_idempotent_upsert_for_each_record() -> None:
    records = read_fixtures()
    connection = RecordingConnection()

    upsert_records(connection, records)
    upsert_records(connection, records)

    assert len(connection.statements) == len(records) * 2
    for index, (statement, params) in enumerate(connection.statements):
        assert "ON CONFLICT (id) DO UPDATE" in statement
        assert params is not None
        assert params["id"] == records[index % len(records)]["id"]
