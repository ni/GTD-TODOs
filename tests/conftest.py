from __future__ import annotations

from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.main import create_app


@pytest.fixture
def sqlite_database_url(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> str:
    database_url = f"sqlite:///{tmp_path / 'test.db'}"
    monkeypatch.setenv("DATABASE_URL", database_url)
    return database_url


@pytest.fixture
def client(sqlite_database_url: str) -> TestClient:
    app = create_app()
    with TestClient(app) as test_client:
        yield test_client