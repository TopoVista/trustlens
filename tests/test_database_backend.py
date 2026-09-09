"""Portable database backend behavior that does not need a live Postgres server."""
import sys
from pathlib import Path
from types import SimpleNamespace

BACKEND = Path(__file__).resolve().parents[1] / "backend"
if str(BACKEND) not in sys.path:
    sys.path.insert(0, str(BACKEND))

from app.knowledge import db


class _FakeCursor:
    def __init__(self):
        self.executed = None
        self.description = [SimpleNamespace(name="id"), SimpleNamespace(name="title")]

    def execute(self, query, params):
        self.executed = (query, params)

    def fetchone(self):
        return ("doc_123", "Saved Document")

    def fetchall(self):
        return [("doc_123", "Saved Document")]


class _FakeConnection:
    def __init__(self):
        self.cursor_instance = _FakeCursor()

    def cursor(self):
        return self.cursor_instance

    def commit(self):
        pass

    def rollback(self):
        pass

    def close(self):
        pass


def test_database_url_uses_postgres_adapter_with_sqlite_compatible_queries(monkeypatch):
    fake_raw_connection = _FakeConnection()
    fake_psycopg = SimpleNamespace(connect=lambda url, connect_timeout: fake_raw_connection)
    monkeypatch.setenv("DATABASE_URL", "postgresql://example/trustlens")
    monkeypatch.setitem(sys.modules, "psycopg", fake_psycopg)

    conn = db.get_db_connection("ignored-for-postgres.db")
    cursor = conn.execute("SELECT id, title FROM documents WHERE id = ?", ("doc_123",))

    assert db.using_postgres() is True
    assert fake_raw_connection.cursor_instance.executed == (
        "SELECT id, title FROM documents WHERE id = %s", ("doc_123",)
    )
    row = cursor.fetchone()
    assert row[0] == "doc_123"
    assert row["title"] == "Saved Document"
    assert dict(row) == {"id": "doc_123", "title": "Saved Document"}
