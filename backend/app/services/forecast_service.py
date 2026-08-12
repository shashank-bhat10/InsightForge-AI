from __future__ import annotations

import math
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.linear_model import LinearRegression


def _load_dataset(file_path: str) -> pd.DataFrame:
    """
    Load CSV, Excel, or JSON dataset.
    Handles relative paths and Windows-style separators.
    """
    normalized_path = str(file_path).replace("\\", "/")
    path = Path(normalized_path)

    if not path.is_absolute():
        # Try path relative to current working directory.
        if not path.exists():
            project_root = Path(__file__).resolve().parents[2]
            path = project_root / path

    if not path.exists():
        raise ValueError(f"Dataset file not found: {file_path}")

    suffix = path.suffix.lower()

    if suffix == ".csv":
        return pd.read_csv(path)

    if suffix in {".xlsx", ".xls"}:
        return pd.read_excel(path)

    if suffix == ".json":
        return pd.read_json(path)

    raise ValueError("Unsupported dataset format.")


def _safe_float(value):
    if value is None:
        return None

    try:
        value = float(value)
    except (TypeError, ValueError):
        return None

    if not math.isfinite(value):
        return None

    return round(value, 4)


def _looks_like_date_column(column_name: str) -> bool:
    """
    Detect common date/time column names.
    """
    name = str(column_name).strip().lower()

    date_keywords = [
        "date",
        "datetime",
        "date_time",
        "timestamp",
        "time",
        "month",
        "year",
        "day",
        "period",
    ]

    return any(keyword in name for keyword in date_keywords)


def _parse_date_column(series: pd.Series, column_name: str):
    """
    Try several strategies to determine whether a column contains dates.
    Returns parsed datetime values or None.
    """

    # Already datetime
    if pd.api.types.is_datetime64_any_dtype(series):
        parsed = pd.to_datetime(series, errors="coerce")
        return parsed

    # Normal string/object date values
    if pd.api.types.is_object_dtype(series) or pd.api.types.is_string_dtype(series):
        cleaned = series.astype(str).str.strip()

        parsed = pd.to_datetime(
            cleaned,
            errors="coerce",
            format="mixed",
        )

        if parsed.notna().mean() >= 0.80:
            return parsed

    # Numeric timestamps
    if pd.api.types.is_numeric_dtype(series):
        non_null = series.dropna()

        if len(non_null) > 0:
            # Unix seconds
            parsed_seconds = pd.to_datetime(
                non_null,
                unit="s",
                errors="coerce",
            )

            if parsed_seconds.notna().mean() >= 0.80:
                result = pd.Series(
                    pd.NaT,
                    index=series.index,
                    dtype="datetime64[ns]",
                )

                result.loc[non_null.index] = parsed_seconds
                return result

            # Unix milliseconds
            parsed_milliseconds = pd.to_datetime(
                non_null,
                unit="ms",
                errors="coerce",
            )

            if parsed_milliseconds.notna().mean() >= 0.80:
                result = pd.Series(
                    pd.NaT,
                    index=series.index,
                    dtype="datetime64[ns]",
                )

                result.loc[non_null.index] = parsed_milliseconds
                return result

    return None


def _detect_frequency(dates: pd.Series) -> str:
    ordered = pd.Series(
        dates.dropna().sort_values().unique()
    )

    if len(ordered) < 2:
        return "MS"

    differences = ordered.diff().dropna().dt.days

    if differences.empty:
        return "MS"

    median_days = float(differences.median())

    if median_days <= 2:
        return "D"

    if median_days <= 10:
        return "W"

    if median_days <= 45:
        return "MS"

    return "YS"


def get_forecast_columns(file_path: str):
    """
    Detect date/time and numeric columns in a dataset.
    """

    df = _load_dataset(file_path)

    date_columns = []
    numeric_columns = []

    for column in df.columns:
        column_name = str(column)
        series = df[column]

        # Numeric columns
        if pd.api.types.is_numeric_dtype(series):
            numeric_columns.append(column_name)

        # Date/time detection
        parsed = _parse_date_column(series, column_name)

        if parsed is not None:
            valid_ratio = parsed.notna().mean()

            if valid_ratio >= 0.80:
                date_columns.append(column_name)

    return {
        "date_columns": date_columns,
        "numeric_columns": numeric_columns,
    }


def generate_forecast(
    file_path: str,
    date_column: str,
    target_column: str,
    periods: int = 12,
    frequency: str = "auto",
):
    if periods < 1 or periods > 60:
        raise ValueError(
            "Forecast periods must be between 1 and 60."
        )

    df = _load_dataset(file_path)

    if date_column not in df.columns:
        raise ValueError(
            f"Date column '{date_column}' was not found."
        )

    if target_column not in df.columns:
        raise ValueError(
            f"Target column '{target_column}' was not found."
        )

    dates = _parse_date_column(
        df[date_column],
        date_column,
    )

    if dates is None:
        raise ValueError(
            f"Column '{date_column}' could not be interpreted as a date/time column."
        )

    target = pd.to_numeric(
        df[target_column],
        errors="coerce",
    )

    data = pd.DataFrame(
        {
            "date": dates,
            "value": target,
        }
    ).dropna()

    if len(data) < 8:
        raise ValueError(
            "At least 8 valid date/target observations are required for forecasting."
        )

    data = data.sort_values("date")

    if frequency == "auto":
        frequency = _detect_frequency(data["date"])

    allowed_frequencies = {
        "D",
        "W",
        "MS",
        "M",
        "QS",
        "YS",
    }

    if frequency not in allowed_frequencies:
        raise ValueError(
            f"Unsupported frequency '{frequency}'. "
            f"Use one of: {', '.join(sorted(allowed_frequencies))}."
        )

    # Aggregate observations into regular time periods.
    series = (
        data.set_index("date")["value"]
        .resample(frequency)
        .sum()
        .dropna()
    )

    if len(series) < 6:
        raise ValueError(
            "Not enough regular time periods were found after aggregation."
        )

    x = np.arange(
        len(series),
        dtype=float,
    ).reshape(-1, 1)

    y = series.values.astype(float)

    model = LinearRegression()
    model.fit(x, y)

    fitted = model.predict(x)

    residuals = y - fitted

    degrees_of_freedom = max(
        len(y) - 2,
        1,
    )

    residual_std = float(
        np.sqrt(
            np.sum(residuals ** 2)
            / degrees_of_freedom
        )
    )

    future_x = np.arange(
        len(series),
        len(series) + periods,
        dtype=float,
    ).reshape(-1, 1)

    predictions = model.predict(future_x)

    last_date = series.index[-1]

    future_index = pd.date_range(
        start=last_date,
        periods=periods + 1,
        freq=frequency,
    )[1:]

    historical = [
        {
            "date": index.strftime("%Y-%m-%d"),
            "actual": _safe_float(value),
        }
        for index, value in series.items()
    ]

    forecast = []

    for index, prediction in zip(
        future_index,
        predictions,
    ):
        lower = max(
            0.0,
            prediction - (1.96 * residual_std),
        )

        upper = prediction + (
            1.96 * residual_std
        )

        forecast.append(
            {
                "date": index.strftime("%Y-%m-%d"),
                "predicted": _safe_float(prediction),
                "lower_bound": _safe_float(lower),
                "upper_bound": _safe_float(upper),
            }
        )

    return {
        "success": True,
        "date_column": date_column,
        "target_column": target_column,
        "frequency": frequency,
        "historical_periods": len(historical),
        "forecast_periods": periods,
        "model": "Linear Trend",
        "trend_slope": _safe_float(
            model.coef_[0]
        ),
        "historical": historical,
        "forecast": forecast,
    }