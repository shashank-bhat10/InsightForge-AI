import pandas as pd
import numpy as np
from pathlib import Path


def load_dataset(file_path: str):
    """
    Load a CSV or Excel file into a pandas DataFrame.
    """

    file_path = str(file_path)
    if not Path(file_path).is_file():
        raise ValueError("Dataset file is unavailable. Upload it again.")
    try:
        df = _read_dataset(file_path)
    except Exception as error:
        raise ValueError("Could not parse dataset. Supply a valid CSV or Excel file.") from error
    if df.empty:
        raise ValueError("Dataset must contain at least one data row.")
    df.columns = df.columns.map(str)
    return df.replace([np.inf, -np.inf], np.nan)


def _read_dataset(file_path):
    if file_path.lower().endswith(".csv"):
        df = pd.read_csv(file_path)

    elif file_path.lower().endswith(".xlsx"):
        df = pd.read_excel(file_path)

    elif file_path.lower().endswith(".xls"):
        df = pd.read_excel(file_path)

    else:
        raise ValueError("Unsupported file type")

    return df


def get_dataset_preview(file_path: str, rows: int = 10):
    """
    Return the first few rows of the dataset.

    Missing values are converted to None so the result
    can be safely serialized as JSON by FastAPI.
    """

    df = load_dataset(file_path)

    preview_df = df.head(rows).copy()

    # Replace all NaN, NaT and other missing values with None
    preview_df = preview_df.astype(object)
    preview_df = preview_df.where(pd.notna(preview_df), None)

    # Convert the DataFrame to records
    records = preview_df.to_dict(orient="records")

    return records
