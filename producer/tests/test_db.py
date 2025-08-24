import os
import pytest
from sqlalchemy import text
from app.db import engine, get_db

def test_database_url_format():
    database_url = os.getenv("DATABASE_URL")
    assert database_url is not None
    assert database_url.startswith("postgresql://") or database_url.startswith("postgresql+psycopg2://")

def test_engine_connection():
    with engine.connect() as connection:
        result = connection.execute(text("SELECT 1"))
        assert result.scalar() == 1

def test_get_db_yields_session():
    gen = get_db()
    db = next(gen)
    assert db is not None
    db.close()
    with pytest.raises(StopIteration):
        next(gen)


def test_engine_echo_off():
    assert engine.echo in (False, None)

def test_get_db_can_execute_query():
    gen = get_db()
    db = next(gen)
    result = db.execute(text("SELECT version()"))
    assert "PostgreSQL" in result.scalar()
    db.close()
    with pytest.raises(StopIteration):
        next(gen)


def test_multiple_get_db_calls_yield_new_sessions():
    gen1 = get_db()
    gen2 = get_db()
    db1 = next(gen1)
    db2 = next(gen2)
    assert db1 != db2
    db1.close()
    db2.close()
    with pytest.raises(StopIteration):
        next(gen1)
    with pytest.raises(StopIteration):
        next(gen2)



# Test error handling for incomplete environment configuration in app.db
def test_get_db_handles_incomplete_env(monkeypatch):
    monkeypatch.delenv("DATABASE_URL", raising=False)
    monkeypatch.delenv("POSTGRES_USER", raising=False)
    monkeypatch.delenv("POSTGRES_PASSWORD", raising=False)
    monkeypatch.delenv("POSTGRES_DB", raising=False)

    with pytest.raises(RuntimeError, match="Database configuration is incomplete"):
        import importlib
        import app.db
        importlib.reload(app.db)
