import uuid
import pandas as pd
from io import BytesIO 
from pathlib import Path

from app.core.config import settings


def save_uploaded_file(content: bytes, original_filename: str) -> dict:
    """Save an uploaded file using a unique internal dataset ID."""

    dataset_id = str(uuid.uuid4())

    extension = Path(original_filename).suffix.lower()

    storage_dir = settings.UPLOAD_DIR
    storage_dir.mkdir(parents=True, exist_ok=True)

    stored_filename = f"{dataset_id}{extension}"
    file_path = storage_dir / stored_filename

    file_path.write_bytes(content)

    return {
        "dataset_id": dataset_id,
        "original_filename": original_filename,
        "stored_filename": stored_filename,
        "file_path": str(file_path),
        "file_size_bytes": len(content),
    }


def load_dataset_from_storage(dataset_metadata: dict) -> pd.DataFrame:
    """Load a previously uploaded dataset into a Pandas DataFrame."""

    stored_filename = dataset_metadata["stored_filename"]
    file_path = settings.UPLOAD_DIR / stored_filename

    # Ensure the file path stays inside our uploads directory
    storage_dir = settings.UPLOAD_DIR.resolve()
    resolved_path = file_path.resolve()

    if not resolved_path.is_relative_to(storage_dir):
        raise ValueError("Invalid dataset file path.")

    if not resolved_path.exists():
        raise FileNotFoundError("Dataset file not found in storage.")

    content = resolved_path.read_bytes()

    extension = resolved_path.suffix.lower()

    if extension == ".csv":
        df = pd.read_csv(BytesIO(content))

    elif extension == ".xlsx":
        df = pd.read_excel(BytesIO(content), engine="openpyxl")

    else:
        raise ValueError("Unsupported dataset format.")

    df.columns = [str(column) for column in df.columns]

    return df