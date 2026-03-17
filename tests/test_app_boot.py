from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI
from sqlmodel import text

from app.db import get_engine, init_db
from app.main import app, create_app


def test_app_import_exposes_fastapi_instance() -> None:
    assert isinstance(app, FastAPI)


def test_app_factory_returns_fastapi_instance() -> None:
    assert isinstance(create_app(), FastAPI)


def test_database_engine_initializes_local_sqlite_file(tmp_path: Path) -> None:
    database_file = tmp_path / "phase0.db"
    database_url = f"sqlite:///{database_file}"

    init_db(database_url)

    assert database_file.exists()
    with get_engine(database_url).connect() as connection:
        connection.execute(text("SELECT 1"))