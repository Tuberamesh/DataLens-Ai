from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


# Backend directory
BASE_DIR = Path(__file__).resolve().parents[2]

# Project root directory
PROJECT_ROOT = BASE_DIR.parent


class Settings(BaseSettings):
    """Central application configuration."""

    UPLOAD_DIR: Path = PROJECT_ROOT / "storage" / "uploads"
    DATABASE_PATH: Path = PROJECT_ROOT / "storage" / "datalens.db"

    MAX_FILE_SIZE: int = 10 * 1024 * 1024  # 20 MB

    ALLOWED_EXTENSIONS: set[str] = {".csv", ".xlsx"}

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


settings = Settings()