import pandas as pd


def analyze_data_quality(df: pd.DataFrame) -> dict:
    """Detect potential data quality issues and generate insights."""

    insights = []
    rows, columns = df.shape

    # 1. Missing values
    for column in df.columns:
        missing_count = int(df[column].isna().sum())

        if missing_count > 0:
            missing_percentage = round((missing_count / rows) * 100, 2)

            insights.append({
                "type": "warning",
                "category": "missing_values",
                "column": str(column),
                "message": (
                    f"'{column}' contains {missing_count} missing values "
                    f"({missing_percentage}% of rows)."
                ),
                "count": missing_count,
            })

    # 2. Duplicate rows
    duplicate_count = int(df.duplicated().sum())

    if duplicate_count > 0:
        insights.append({
            "type": "warning",
            "category": "duplicates",
            "column": None,
            "message": f"The dataset contains {duplicate_count} duplicate rows.",
            "count": duplicate_count,
        })

    # 3. Constant columns
    for column in df.columns:
        unique_count = int(df[column].nunique(dropna=True))

        if rows > 1 and unique_count <= 1:
            insights.append({
                "type": "info",
                "category": "constant_column",
                "column": str(column),
                "message": (
                    f"'{column}' contains only {unique_count} distinct "
                    "non-null value. It may not be useful for analysis."
                ),
                "count": unique_count,
            })

    # 4. Potential identifier columns
    for column in df.columns:
        unique_count = int(df[column].nunique(dropna=True))

        if rows >= 10 and unique_count / rows >= 0.9:
            insights.append({
                "type": "info",
                "category": "potential_identifier",
                "column": str(column),
                "message": (
                    f"'{column}' has {unique_count} unique values across "
                    f"{rows} rows. It may be an identifier column."
                ),
                "count": unique_count,
            })

    # 5. Potential numeric outliers (IQR method)
    numeric_columns = df.select_dtypes(include="number").columns

    for column in numeric_columns:
        series = df[column].dropna()

        if len(series) < 5 or series.nunique() < 4:
            continue

        q1 = series.quantile(0.25)
        q3 = series.quantile(0.75)
        iqr = q3 - q1

        if iqr == 0:
            continue

        lower_bound = q1 - (1.5 * iqr)
        upper_bound = q3 + (1.5 * iqr)

        outlier_count = int(
            ((series < lower_bound) | (series > upper_bound)).sum()
        )

        if outlier_count > 0:
            insights.append({
                "type": "info",
                "category": "potential_outliers",
                "column": str(column),
                "message": (
                    f"'{column}' contains {outlier_count} potential outliers "
                    "based on the IQR method. These values may be valid."
                ),
                "count": outlier_count,
            })

    # 6. Overall quality summary
    warning_count = sum(
        1 for insight in insights if insight["type"] == "warning"
    )
    info_count = sum(
        1 for insight in insights if insight["type"] == "info"
    )

    if warning_count > 0:
        status = "issues_found"
    elif info_count > 0:
        status = "review_recommended"
    else:
        status = "clean"

    if not insights:
        insights.append({
            "type": "success",
            "category": "overall",
            "column": None,
            "message": "No common data quality issues detected.",
            "count": 0,
        })

    return {
        "status": status,
        "total_issues": warning_count + info_count,
        "warning_count": warning_count,
        "info_count": info_count,
        "insights": insights,
    }