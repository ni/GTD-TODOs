"""Application configuration."""

import os
from dataclasses import dataclass
from pathlib import Path

DEFAULT_DATA_DIR = Path("/data")
DEFAULT_DB_FILENAME = "todo.db"


@dataclass(slots=True)
class Settings:
    app_name: str = "GTD TODOs"
    app_env: str = "development"
    host: str = "0.0.0.0"
    port: int = 8080
    database_url: str = f"sqlite:///{DEFAULT_DATA_DIR / DEFAULT_DB_FILENAME}"

    @property
    def sqlite_path(self) -> Path | None:
        prefix = "sqlite:///"
        if not self.database_url.startswith(prefix):
            return None
        return Path(self.database_url.removeprefix(prefix))


def get_settings() -> Settings:
    return Settings(
        app_name=os.getenv("APP_NAME", "GTD TODOs"),
        app_env=os.getenv("APP_ENV", "development"),
        host=os.getenv("APP_HOST", "0.0.0.0"),
        port=int(os.getenv("APP_PORT", "8080")),
        database_url=os.getenv(
            "DATABASE_URL",
            f"sqlite:///{DEFAULT_DATA_DIR / DEFAULT_DB_FILENAME}",
        ),
    )