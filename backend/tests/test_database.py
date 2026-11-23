from app.db import database


def test_get_db_closes_session_when_dependency_finishes(monkeypatch) -> None:
    class FakeSession:
        closed = False

        def close(self) -> None:
            self.closed = True

    session = FakeSession()
    monkeypatch.setattr(database, "SessionLocal", lambda: session)

    dependency = database.get_db()
    assert next(dependency) is session
    dependency.close()
    assert session.closed is True
