from __future__ import annotations

from collections.abc import Generator
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session

from app.config import get_settings
from app.db import get_engine, init_db
from app.main import create_app


@pytest.fixture
def sqlite_database_url(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> str:
    get_settings.cache_clear()
    database_url = f"sqlite:///{tmp_path / 'test.db'}"
    monkeypatch.setenv("DATABASE_URL", database_url)
    monkeypatch.setenv("AUTH_DISABLED", "true")
    return database_url


@pytest.fixture
def client(sqlite_database_url: str) -> TestClient:
    app = create_app()
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture
def db_session(sqlite_database_url: str) -> Generator[Session, None, None]:
    """Provide a database session with tables created."""
    init_db(sqlite_database_url)
    engine = get_engine(sqlite_database_url)
    with Session(engine) as session:
        yield session