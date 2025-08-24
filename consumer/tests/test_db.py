import os
import pytest
import logging
from unittest.mock import patch, MagicMock
from sqlalchemy.exc import SQLAlchemyError
from app.db import get_db, SessionLocal, engine

@patch("app.db.SessionLocal")
def test_get_db_success(mock_session):
    mock_db = MagicMock()
    mock_session.return_value = mock_db

    with get_db() as db:
        assert db == mock_db
    mock_db.close.assert_called_once()

@patch("app.db.SessionLocal", side_effect=SQLAlchemyError("Session error"))
def test_get_db_exception_logs_and_raises(mock_session, caplog):
    caplog.set_level(logging.ERROR)
    with pytest.raises(SQLAlchemyError):
        with get_db():
            pass
    assert "Database session error" in caplog.text

def test_engine_creation_and_url_masking(monkeypatch):
    monkeypatch.setenv("POSTGRES_USER", "testuser")
    monkeypatch.setenv("POSTGRES_PASSWORD", "secret")
    monkeypatch.setenv("POSTGRES_HOST", "localhost")
    monkeypatch.setenv("POSTGRES_PORT", "5432")
    monkeypatch.setenv("POSTGRES_DB", "testdb")

    from importlib import reload
    import app.db as db_module
    reload(db_module)

    assert db_module.engine is not None
    assert "secret" not in db_module.safe_url
    assert "***" in db_module.safe_url