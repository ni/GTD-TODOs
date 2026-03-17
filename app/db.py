"""Database setup and session management."""

from collections.abc import Generator
from pathlib import Path

from sqlmodel import Session, SQLModel, create_engine

from app.config import get_settings

_engines: dict[str, object] = {}


def _prepare_sqlite_path(database_url: str) -> None:
    prefix = "sqlite:///"
    if not database_url.startswith(prefix):
        return
    db_path = Path(database_url.removeprefix(prefix))
    if db_path.parent != Path(""):
        db_path.parent.mkdir(parents=True, exist_ok=True)


def get_engine(database_url: str | None = None):
    settings = get_settings()
    resolved_url = database_url or settings.database_url
    if resolved_url not in _engines:
        _prepare_sqlite_path(resolved_url)
        connect_args = {"check_same_thread": False} if resolved_url.startswith("sqlite") else {}
        _engines[resolved_url] = create_engine(resolved_url, connect_args=connect_args)
    return _engines[resolved_url]


def init_db(database_url: str | None = None) -> None:
    engine = get_engine(database_url)
    SQLModel.metadata.create_all(engine)


def get_session() -> Generator[Session, None, None]:
    with Session(get_engine()) as session:
        yield session