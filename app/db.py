"""Database setup and session management."""

from collections.abc import Generator
from pathlib import Path

from sqlalchemy import Engine
from sqlmodel import Session, SQLModel, create_engine, text

from app.config import get_settings

_engines: dict[str, Engine] = {}


def _prepare_sqlite_path(database_url: str) -> None:
    prefix = "sqlite:///"
    if not database_url.startswith(prefix):
        return
    db_path = Path(database_url.removeprefix(prefix))
    if db_path.parent != Path(""):
        db_path.parent.mkdir(parents=True, exist_ok=True)


def get_engine(database_url: str | None = None) -> Engine:
    settings = get_settings()
    resolved_url = database_url or settings.database_url
    if resolved_url not in _engines:
        _prepare_sqlite_path(resolved_url)
        connect_args = {"check_same_thread": False} if resolved_url.startswith("sqlite") else {}
        _engines[resolved_url] = create_engine(resolved_url, connect_args=connect_args)
    return _engines[resolved_url]


def _migrate_schema(database_url: str) -> None:
    """Apply lightweight schema migrations for pre-existing databases.

    SQLModel's create_all does not ALTER existing tables when new columns are
    added to a model.  This function back-fills columns that were introduced
    after the initial schema so that databases created by earlier versions
    continue to work.  It is safe to run repeatedly (idempotent).
    """
    engine = get_engine(database_url)
    with engine.connect() as conn:
        # Check if the projects table exists before trying to migrate it
        result = conn.execute(
            text("SELECT name FROM sqlite_master WHERE type='table' AND name='projects'")
        )
        if result.fetchone() is None:
            return
        # Add completed_at column if missing
        columns = [row[1] for row in conn.execute(text("PRAGMA table_info(projects)"))]
        if "completed_at" not in columns:
            conn.execute(text("ALTER TABLE projects ADD COLUMN completed_at DATETIME"))
            conn.commit()
        # Add notes and due_date columns if missing
        if "notes" not in columns:
            conn.execute(text("ALTER TABLE projects ADD COLUMN notes TEXT"))
            conn.commit()
        if "due_date" not in columns:
            conn.execute(text("ALTER TABLE projects ADD COLUMN due_date DATE"))
            conn.commit()


def init_db(database_url: str | None = None) -> None:
    settings = get_settings()
    resolved_url = database_url or settings.database_url
    engine = get_engine(resolved_url)
    SQLModel.metadata.create_all(engine)
    _migrate_schema(resolved_url)


def get_session() -> Generator[Session, None, None]:
    with Session(get_engine()) as session:
        yield session