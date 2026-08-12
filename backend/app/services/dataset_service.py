import pandas as pd


def load_dataset(file_path: str):
    """
    Load a CSV or Excel file into a pandas DataFrame.
    """

    if file_path.endswith(".csv"):
        df = pd.read_csv(file_path)

    elif file_path.endswith(".xlsx"):
        df = pd.read_excel(file_path)

    elif file_path.endswith(".xls"):
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