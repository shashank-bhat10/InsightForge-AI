from __future__ import annotations

import math
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.linear_model import LinearRegression


def _load_dataset(file_path: str) -> pd.DataFrame:
    path = Path(file_path)

    if not path.exists():
        raise ValueError("Dataset file not found.")

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

    value = float(value)

    if not math.isfinite(value):
        return None

    return round(value, 4)


def _detect_frequency(dates: pd.Series) -> str:
    ordered = pd.Series(dates.dropna().sort_values().unique())

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
    df = _load_dataset(file_path)

    date_columns = []
    numeric_columns = []

    for column in df.columns:
        series = df[column]

        if pd.api.types.is_numeric_dtype(series):
            numeric_columns.append(str(column))

        if pd.api.types.is_datetime64_any_dtype(series):
            date_columns.append(str(column))
            continue

        if series.dtype == "object":
            parsed = pd.to_datetime(series, errors="coerce")

            if parsed.notna().mean() >= 0.8:
                date_columns.append(str(column))

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
        raise ValueError("Forecast periods must be between 1 and 60.")

    df = _load_dataset(file_path)

    if date_column not in df.columns:
        raise ValueError(f"Date column '{date_column}' was not found.")

    if target_column not in df.columns:
        raise ValueError(f"Target column '{target_column}' was not found.")

    dates = pd.to_datetime(df[date_column], errors="coerce")
    target = pd.to_numeric(df[target_column], errors="coerce")

    data = pd.DataFrame({
        "date": dates,
        "value": target,
    }).dropna()

    if len(data) < 8:
        raise ValueError(
            "At least 8 valid date/target observations are required for forecasting."
        )

    data = data.sort_values("date")

    if frequency == "auto":
        frequency = _detect_frequency(data["date"])

    allowed_frequencies = {"D", "W", "MS", "M", "QS", "YS"}
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

    x = np.arange(len(series), dtype=float).reshape(-1, 1)
    y = series.values.astype(float)

    model = LinearRegression()
    model.fit(x, y)

    fitted = model.predict(x)

    residuals = y - fitted
    degrees_of_freedom = max(len(y) - 2, 1)
    residual_std = float(
        np.sqrt(np.sum(residuals ** 2) / degrees_of_freedom)
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

    for index, prediction in zip(future_index, predictions):
        lower = max(0.0, prediction - (1.96 * residual_std))
        upper = prediction + (1.96 * residual_std)

        forecast.append({
            "date": index.strftime("%Y-%m-%d"),
            "predicted": _safe_float(prediction),
            "lower_bound": _safe_float(lower),
            "upper_bound": _safe_float(upper),
        })

    return {
        "success": True,
        "date_column": date_column,
        "target_column": target_column,
        "frequency": frequency,
        "historical_periods": len(historical),
        "forecast_periods": periods,
        "model": "Linear Trend",
        "trend_slope": _safe_float(model.coef_[0]),
        "historical": historical,
        "forecast": forecast,
    }