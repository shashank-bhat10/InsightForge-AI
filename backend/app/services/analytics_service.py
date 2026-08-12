import math
import pandas as pd

from app.services.dataset_service import load_dataset


def _safe_float(value):
    """
    Convert numeric values to JSON-safe floats.

    Pandas can produce NaN or infinity values when a column
    contains missing or invalid numeric data. JSON does not
    allow these values, so convert them to None.
    """

    if pd.isna(value):
        return None

    value = float(value)

    if not math.isfinite(value):
        return None

    return value


def get_dataset_summary(file_path: str):
    df = load_dataset(file_path)

    return {
        "rows": len(df),
        "columns": len(df.columns),
        "column_names": list(df.columns),
        "data_types": {
            column: str(dtype)
            for column, dtype in df.dtypes.items()
        },
        "missing_values": {
            column: int(count)
            for column, count in df.isnull().sum().items()
        }
    }


def get_dataset_statistics(file_path: str):
    df = load_dataset(file_path)

    numeric_df = df.select_dtypes(include="number")

    statistics = {}

    for column in numeric_df.columns:
        statistics[column] = {
            "count": int(numeric_df[column].count()),
            "mean": _safe_float(numeric_df[column].mean()),
            "median": _safe_float(numeric_df[column].median()),
            "min": _safe_float(numeric_df[column].min()),
            "max": _safe_float(numeric_df[column].max()),
            "std": (
                _safe_float(numeric_df[column].std())
                if numeric_df[column].count() > 1
                else 0.0
            )
        }

    return {
        "rows": len(df),
        "columns": len(df.columns),
        "numeric_columns": statistics
    }


def get_dataset_insights(file_path: str):
    df = load_dataset(file_path)

    insights = []

    insights.append(
        f"Dataset contains {len(df)} rows and {len(df.columns)} columns."
    )

    missing = df.isnull().sum().sum()

    if missing == 0:
        insights.append("No missing values detected.")
    else:
        insights.append(
            f"Dataset contains {int(missing)} missing values."
        )

    numeric_df = df.select_dtypes(include="number")

    if len(numeric_df.columns) == 0:
        insights.append("No numeric columns found.")
    else:
        insights.append(
            f"Found {len(numeric_df.columns)} numeric columns."
        )

        for column in numeric_df.columns:
            minimum = _safe_float(numeric_df[column].min())
            maximum = _safe_float(numeric_df[column].max())
            average = _safe_float(numeric_df[column].mean())

            insights.append(
                f"{column}: min={minimum}, "
                f"max={maximum}, "
                f"average={round(average, 2) if average is not None else None}"
            )

    return {
        "insights": insights
    }


def get_grouped_analysis(file_path: str):
    df = load_dataset(file_path)

    numeric_columns = df.select_dtypes(include="number").columns

    categorical_columns = df.select_dtypes(
        include=["object", "category"]
    ).columns

    grouped_analysis = {}

    for categorical_column in categorical_columns:

        if df[categorical_column].nunique(dropna=True) > 50:
            continue

        for numeric_column in numeric_columns:

            grouped = (
                df.groupby(
                    categorical_column,
                    dropna=False
                )[numeric_column]
                .agg(["count", "mean", "sum"])
                .reset_index()
            )

            grouped = grouped.sort_values(
                by="sum",
                ascending=False
            )

            records = []

            for _, row in grouped.head(20).iterrows():

                category_value = row[categorical_column]

                if pd.isna(category_value):
                    category_value = "Missing"

                average = _safe_float(row["mean"])
                total = _safe_float(row["sum"])

                records.append({
                    "category": str(category_value),
                    "count": int(row["count"]),
                    "average": (
                        round(average, 4)
                        if average is not None
                        else None
                    ),
                    "total": (
                        round(total, 4)
                        if total is not None
                        else None
                    )
                })

            grouped_analysis[
                f"{categorical_column}_by_{numeric_column}"
            ] = records

    return grouped_analysis


def get_dataset_quality(file_path: str):
    """
    Analyze the overall quality of an uploaded dataset.

    Includes:
    - Missing values
    - Duplicate rows
    - Unique values
    - Constant columns
    - Categorical inconsistencies
    - Numeric outliers using the IQR method
    - Overall quality score
    """

    df = load_dataset(file_path)

    total_rows = len(df)
    total_columns = len(df.columns)

    # ---------------------------------------------------------
    # Missing values
    # ---------------------------------------------------------

    missing_values = {}

    for column in df.columns:
        count = int(df[column].isna().sum())

        missing_values[column] = {
            "count": count,
            "percentage": round(
                (count / total_rows) * 100,
                2
            ) if total_rows > 0 else 0.0
        }

    total_missing = int(df.isna().sum().sum())

    # ---------------------------------------------------------
    # Duplicate rows
    # ---------------------------------------------------------

    duplicate_rows = int(df.duplicated().sum())

    duplicate_percentage = round(
        (duplicate_rows / total_rows) * 100,
        2
    ) if total_rows > 0 else 0.0

    # ---------------------------------------------------------
    # Column information
    # ---------------------------------------------------------

    column_details = {}

    for column in df.columns:
        series = df[column]

        column_details[column] = {
            "data_type": str(series.dtype),
            "unique_values": int(series.nunique(dropna=True)),
            "missing_values": int(series.isna().sum()),
            "missing_percentage": round(
                (series.isna().sum() / total_rows) * 100,
                2
            ) if total_rows > 0 else 0.0,
            "is_constant": bool(
                series.nunique(dropna=True) <= 1
            )
        }

    # ---------------------------------------------------------
    # Constant columns
    # ---------------------------------------------------------

    constant_columns = []

    for column in df.columns:
        if df[column].nunique(dropna=True) <= 1:
            constant_columns.append(column)

    # ---------------------------------------------------------
    # Categorical inconsistencies
    # ---------------------------------------------------------

    categorical_inconsistencies = {}

    categorical_columns = df.select_dtypes(
        include=["object", "category"]
    ).columns

    for column in categorical_columns:
        series = df[column].dropna()

        if len(series) == 0:
            continue

        original_values = {}

        for value in series.astype(str).unique():
            normalized = value.strip().lower()

            original_values.setdefault(
                normalized,
                []
            ).append(value)

        inconsistent_groups = []

        for normalized_value, original_values_list in original_values.items():
            unique_originals = sorted(
                set(original_values_list)
            )

            if len(unique_originals) > 1:
                inconsistent_groups.append({
                    "normalized_value": normalized_value,
                    "variants": unique_originals
                })

        if inconsistent_groups:
            categorical_inconsistencies[column] = (
                inconsistent_groups
            )

    # ---------------------------------------------------------
    # Numeric outliers
    # ---------------------------------------------------------

    numeric_columns = df.select_dtypes(
        include="number"
    ).columns

    outliers = {}

    for column in numeric_columns:
        series = df[column].dropna()

        if len(series) < 4:
            outliers[column] = {
                "count": 0,
                "percentage": 0.0
            }
            continue

        q1 = series.quantile(0.25)
        q3 = series.quantile(0.75)

        iqr = q3 - q1

        lower_bound = q1 - (1.5 * iqr)
        upper_bound = q3 + (1.5 * iqr)

        outlier_mask = (
            (series < lower_bound)
            | (series > upper_bound)
        )

        outlier_count = int(outlier_mask.sum())

        outliers[column] = {
            "count": outlier_count,
            "percentage": round(
                (outlier_count / len(series)) * 100,
                2
            ),
            "lower_bound": _safe_float(lower_bound),
            "upper_bound": _safe_float(upper_bound)
        }

    # ---------------------------------------------------------
    # Quality score
    # ---------------------------------------------------------

    score = 100.0

    if total_rows > 0 and total_columns > 0:

        missing_percentage = (
            total_missing
            / (total_rows * total_columns)
        ) * 100

        # Missing data penalty
        score -= min(
            missing_percentage * 0.8,
            30
        )

        # Duplicate penalty
        score -= min(
            duplicate_percentage * 0.5,
            15
        )

        # Constant-column penalty
        constant_percentage = (
            len(constant_columns)
            / total_columns
        ) * 100

        score -= min(
            constant_percentage * 0.5,
            10
        )

        # Categorical inconsistency penalty
        inconsistent_column_count = len(
            categorical_inconsistencies
        )

        inconsistency_percentage = (
            inconsistent_column_count
            / total_columns
        ) * 100

        score -= min(
            inconsistency_percentage * 0.5,
            10
        )

        # Outlier penalty
        columns_with_outliers = sum(
            1
            for value in outliers.values()
            if value["count"] > 0
        )

        outlier_percentage = (
            columns_with_outliers
            / len(numeric_columns)
        ) * 100 if len(numeric_columns) > 0 else 0

        score -= min(
            outlier_percentage * 0.2,
            10
        )

    score = max(
        0.0,
        min(100.0, score)
    )

    if score >= 90:
        quality_level = "Excellent"
    elif score >= 75:
        quality_level = "Good"
    elif score >= 60:
        quality_level = "Fair"
    else:
        quality_level = "Needs Attention"

    # ---------------------------------------------------------
    # Recommendations
    # ---------------------------------------------------------

    recommendations = []

    if total_missing > 0:
        recommendations.append(
            "Review and handle missing values before modeling."
        )

    if duplicate_rows > 0:
        recommendations.append(
            "Review duplicate rows and remove them if they "
            "represent duplicate records."
        )

    if constant_columns:
        recommendations.append(
            "Consider removing constant columns because they "
            "do not provide analytical information."
        )

    if categorical_inconsistencies:
        recommendations.append(
            "Standardize categorical values with inconsistent "
            "capitalization or whitespace."
        )

    if any(
        value["count"] > 0
        for value in outliers.values()
    ):
        recommendations.append(
            "Review detected numeric outliers before using "
            "the data for statistical analysis or modeling."
        )

    if not recommendations:
        recommendations.append(
            "No major data-quality issues were detected."
        )

    return {
        "quality_score": round(score, 2),
        "quality_level": quality_level,
        "rows": total_rows,
        "columns": total_columns,
        "total_missing_values": total_missing,
        "duplicate_rows": duplicate_rows,
        "duplicate_percentage": duplicate_percentage,
        "constant_columns": constant_columns,
        "column_details": column_details,
        "missing_values": missing_values,
        "categorical_inconsistencies": (
            categorical_inconsistencies
        ),
        "outliers": outliers,
        "recommendations": recommendations
    }

def get_advanced_analytics(file_path: str):
    """
    Generate advanced analytical summaries for an uploaded dataset.

    Includes:
    - Pearson correlations between numeric columns
    - Numeric distribution statistics and quartiles
    - Categorical value distributions
    - Strongest positive and negative correlations
    """

    df = load_dataset(file_path)

    numeric_df = df.select_dtypes(include="number")

    numeric_distributions = {}

    for column in numeric_df.columns:
        series = numeric_df[column].dropna()

        if len(series) == 0:
            numeric_distributions[column] = {
                "count": 0,
                "mean": None,
                "median": None,
                "min": None,
                "max": None,
                "q1": None,
                "q3": None,
                "skewness": None,
            }
            continue

        numeric_distributions[column] = {
            "count": int(series.count()),
            "mean": _safe_float(series.mean()),
            "median": _safe_float(series.median()),
            "min": _safe_float(series.min()),
            "max": _safe_float(series.max()),
            "q1": _safe_float(series.quantile(0.25)),
            "q3": _safe_float(series.quantile(0.75)),
            "skewness": _safe_float(series.skew()) if len(series) > 2 else 0.0,
        }

    correlations = []

    if len(numeric_df.columns) >= 2:
        correlation_matrix = numeric_df.corr(numeric_only=True)

        for index, first_column in enumerate(correlation_matrix.columns):
            for second_column in correlation_matrix.columns[index + 1:]:
                value = correlation_matrix.loc[first_column, second_column]

                if pd.isna(value):
                    continue

                correlations.append({
                    "column_a": first_column,
                    "column_b": second_column,
                    "correlation": round(float(value), 4),
                    "absolute_correlation": round(abs(float(value)), 4),
                })

        correlations.sort(
            key=lambda item: item["absolute_correlation"],
            reverse=True
        )

    categorical_distributions = {}

    categorical_columns = df.select_dtypes(
        include=["object", "category"]
    ).columns

    for column in categorical_columns:
        unique_count = int(df[column].nunique(dropna=True))

        if unique_count > 50:
            continue

        counts = (
            df[column]
            .fillna("Missing")
            .astype(str)
            .value_counts()
            .head(10)
        )

        categorical_distributions[column] = [
            {
                "category": str(category),
                "count": int(count),
                "percentage": round(
                    (int(count) / len(df)) * 100,
                    2
                ) if len(df) > 0 else 0.0,
            }
            for category, count in counts.items()
        ]

    return {
        "numeric_distributions": numeric_distributions,
        "correlations": correlations,
        "strongest_correlations": correlations[:10],
        "categorical_distributions": categorical_distributions,
    }