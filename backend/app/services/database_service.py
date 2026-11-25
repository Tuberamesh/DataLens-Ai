import sqlite3
from datetime import datetime, timezone
from contextlib import contextmanager 
from collections.abc import Iterator

from app.core.config import settings


@contextmanager
def get_connection() -> Iterator[sqlite3.Connection]:
    """Provide a SQLite connection and close it after use."""

    settings.DATABASE_PATH.parent.mkdir(parents=True, exist_ok=True)

    connection = sqlite3.connect(settings.DATABASE_PATH)
    connection.row_factory = sqlite3.Row

    try:
        yield connection
        connection.commit()
    except Exception:
        connection.rollback()
        raise
    finally:
        connection.close()


def initialize_database() -> None:
    """Create the datasets table if it doesn't already exist."""

    with get_connection() as connection:
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS datasets (
                dataset_id TEXT PRIMARY KEY,
                original_filename TEXT NOT NULL,
                stored_filename TEXT NOT NULL,
                file_size_bytes INTEGER NOT NULL,
                row_count INTEGER NOT NULL,
                column_count INTEGER NOT NULL,
                uploaded_at TEXT NOT NULL
            )
            """
        )

def register_dataset(storage_metadata: dict, profile: dict) -> None:
    """Register an uploaded dataset and its profile metadata in SQLite."""

    uploaded_at = datetime.now(timezone.utc).isoformat()

    with get_connection() as connection:
        connection.execute(
            """
            INSERT INTO datasets (
                dataset_id,
                original_filename,
                stored_filename,
                file_size_bytes,
                row_count,
                column_count,
                uploaded_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                storage_metadata["dataset_id"],
                storage_metadata["original_filename"],
                storage_metadata["stored_filename"],
                storage_metadata["file_size_bytes"],
                profile["row_count"],
                profile["column_count"],
                uploaded_at,
            ),
        )

def get_dataset_metadata(dataset_id: str) -> dict | None:
    """Retrieve dataset metadata from SQLite using its dataset ID."""

    with get_connection() as connection:
        row = connection.execute(
            "SELECT * FROM datasets WHERE dataset_id = ?",
            (dataset_id,),
        ).fetchone()

        return dict(row) if row else None