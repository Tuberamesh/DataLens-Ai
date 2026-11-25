
from io import BytesIO

import pandas as pd
from fastapi import APIRouter, File, HTTPException, UploadFile

from app.services.profiling_service import profile_dataset

router = APIRouter()

ALLOWED_EXTENSIONS = {".csv", ".xlsx"}
MAX_FILE_SIZE = 20 * 1024 * 1024  # 20 MB


@router.post("/upload")
async def upload_dataset(file: UploadFile = File(...)):
    filename = file.filename or ""
    extension = "." + filename.rsplit(".", 1)[-1].lower() if "." in filename else ""

    if extension not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail="Only CSV and XLSX files are supported.",
        )

    content = await file.read(MAX_FILE_SIZE + 1)

    if not content:
        raise HTTPException(
            status_code=400,
            detail="The uploaded file is empty.",
        )

    if len(content) > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=413,
            detail="File exceeds the 20 MB upload limit.",
        )

    try:
        if extension == ".csv":
            df = pd.read_csv(BytesIO(content))
        else:
            df = pd.read_excel(BytesIO(content), engine="openpyxl")

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

        df.columns = [str(column) for column in df.columns]

        profile = profile_dataset(df)

        return {
            "success": True,
            "filename": filename,
            "file_size_bytes": len(content),
            "profile": profile,
        }

    except HTTPException:
        raise

    except Exception as error:
        raise HTTPException(
            status_code=400,
            detail=f"Could not process the uploaded file: {str(error)}",
        )

    finally:
        await file.close()
