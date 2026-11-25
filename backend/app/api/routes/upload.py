from io import BytesIO

import pandas as pd
from fastapi import APIRouter, File, HTTPException, UploadFile

from app.core.config import settings
from app.services.database_service import (
    get_dataset_metadata,
    register_dataset,
)
from app.services.profiling_service import profile_dataset
from app.services.storage_service import (
    load_dataset_from_storage,
    save_uploaded_file,
)

router = APIRouter()


@router.post("/upload")
async def upload_dataset(file: UploadFile = File(...)):
    filename = file.filename or ""
    extension = "." + filename.rsplit(".", 1)[-1].lower() if "." in filename else ""

    # Validate file extension
    if extension not in settings.ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail="Only CSV and XLSX files are supported.",
        )

    # Read file, allowing one extra byte to detect oversized uploads
    content = await file.read(settings.MAX_FILE_SIZE + 1)

    if not content:
        raise HTTPException(
            status_code=400,
            detail="The uploaded file is empty.",
        )

    # Validate file size
    if len(content) > settings.MAX_FILE_SIZE:
        max_size_mib = settings.MAX_FILE_SIZE / (1024 * 1024)

        raise HTTPException(
            status_code=413,
            detail=f"File exceeds the {max_size_mib:g} MiB upload limit.",
        )

    try:
        # Read file into a DataFrame
        if extension == ".csv":
            df = pd.read_csv(BytesIO(content))
        else:
            df = pd.read_excel(BytesIO(content), engine="openpyxl")

        # Validate dataset contents
        if df.empty:
            raise HTTPException(
                status_code=400,
                detail="The dataset contains no rows.",
            )

        if len(df.columns) == 0:
            raise HTTPException(
                status_code=400,
                detail="The dataset contains no columns.",
            )

        # Normalize column names
        df.columns = [str(column) for column in df.columns]

        # Generate profile and quality report
        profile = profile_dataset(df)

    except HTTPException:
        raise

    except Exception:
        raise HTTPException(
            status_code=400,
            detail="Could not process the file. Please check its format and contents.",
        )

    # Save original file
    try:
        storage_metadata = save_uploaded_file(content, filename)

    except Exception:
        raise HTTPException(
            status_code=500,
            detail="The dataset could not be saved.",
        )

    # Register metadata in SQLite
    try:
        register_dataset(storage_metadata, profile)

    except Exception:
        raise HTTPException(
            status_code=500,
            detail="The dataset file was saved, but database registration failed.",
        )

    return {
        "success": True,
        "dataset_id": storage_metadata["dataset_id"],
        "filename": filename,
        "file_size_bytes": len(content),
        "profile": profile,
    }


@router.get("/datasets/{dataset_id}")
def retrieve_dataset(dataset_id: str):
    """Retrieve a saved dataset's metadata and profile using its ID."""

    # Find dataset metadata in SQLite
    metadata = get_dataset_metadata(dataset_id)

    if metadata is None:
        raise HTTPException(
            status_code=404,
            detail="Dataset not found.",
        )

    # Load original file from storage
    try:
        df = load_dataset_from_storage(metadata)

        # Generate profile from the loaded dataset
        profile = profile_dataset(df)

    except FileNotFoundError:
        raise HTTPException(
            status_code=500,
            detail="Dataset metadata exists, but the stored file is missing.",
        )

    except Exception:
        raise HTTPException(
            status_code=500,
            detail="Could not retrieve the stored dataset.",
        )

    return {
        "success": True,
        "dataset": {
            "dataset_id": metadata["dataset_id"],
            "filename": metadata["original_filename"],
            "file_size_bytes": metadata["file_size_bytes"],
            "row_count": metadata["row_count"],
            "column_count": metadata["column_count"],
            "uploaded_at": metadata["uploaded_at"],
        },
        "profile": profile,
    }