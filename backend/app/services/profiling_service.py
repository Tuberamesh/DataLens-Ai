
import pandas as pd
from app.services.quality_service import analyze_data_quality

def profile_dataset(df: pd.DataFrame) -> dict:
    """Generate a structured profile of an uploaded dataset."""

    rows, columns = df.shape

    column_profiles = []

    for column in df.columns:
        series = df[column]

        column_profiles.append({
            "name": str(column),
            "data_type": str(series.dtype),
            "missing_values": int(series.isna().sum()),
            "missing_percentage": round(
                float(series.isna().mean() * 100), 2
            ),
            "unique_values": int(series.nunique()),
        })

    numeric_columns = [
        str(column)
        for column in df.select_dtypes(include="number").columns
    ]

    categorical_columns = [
        str(column)
        for column in df.select_dtypes(
            include=["object", "category", "bool"]
        ).columns
    ]

    numeric_summary = {}

    if numeric_columns:
        numeric_summary = (
            df[numeric_columns]
            .describe()
            .replace({float("nan"): None})
            .to_dict()
        )

        return {
        "row_count": int(rows),
        "column_count": int(columns),
        "columns": column_profiles,
        "numeric_columns": numeric_columns,
        "categorical_columns": categorical_columns,
        "duplicate_rows": int(df.duplicated().sum()),
        "total_missing_values": int(df.isna().sum().sum()),
        "numeric_summary": numeric_summary,

        # NEW: Data quality analysis
        "data_quality": analyze_data_quality(df),

        "preview": (
            df.head(5)
            .astype(object)
            .where(pd.notna(df.head(5)), None)
            .to_dict(orient="records")
        ),
    }