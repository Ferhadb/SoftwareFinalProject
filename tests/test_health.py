from sqlalchemy.exc import OperationalError

from app.core.db import get_db
from app.main import app


def test_health_ok(client):
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json() == {"status": "ok", "db": "ok", "version": "0.1.0"}


def test_health_degraded_when_db_down(client):
    class BrokenDb:
        def execute(self, *_):
            raise OperationalError("SELECT 1", {}, Exception("db down"))

    app.dependency_overrides[get_db] = lambda: BrokenDb()
    r = client.get("/health")
    assert r.status_code == 503
    assert r.json()["db"] == "down"


def test_startup_creates_tables(tmp_path, monkeypatch):
    from fastapi.testclient import TestClient
    from sqlalchemy import create_engine, inspect

    from app import main

    eng = create_engine(f"sqlite:///{tmp_path}/t.db")
    monkeypatch.setattr(main, "engine", eng)
    with TestClient(main.app):
        pass
    assert {"users", "expenses", "budgets", "alerts"} <= set(
        inspect(eng).get_table_names()
    )
