import pandas as pd

from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer

from sklearn.linear_model import LinearRegression, LogisticRegression

from sklearn.metrics import (
    accuracy_score,
    f1_score,
    mean_absolute_error,
    mean_squared_error,
    precision_score,
    r2_score,
    recall_score,
)

from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder

from sklearn.ensemble import (
    GradientBoostingClassifier,
    GradientBoostingRegressor,
    RandomForestClassifier,
    RandomForestRegressor,
)

from sklearn.tree import DecisionTreeClassifier, DecisionTreeRegressor

from sklearn.inspection import permutation_importance

from app.services.dataset_service import load_dataset


def _detect_problem_type(series: pd.Series) -> str:
    """
    Automatically determine whether the target is
    classification or regression.
    """

    if pd.api.types.is_numeric_dtype(series):

        unique_values = series.dropna().nunique()

        if unique_values <= 10:
            return "classification"

        return "regression"

    return "classification"


def _prepare_features(df: pd.DataFrame, target_column: str):
    """
    Prepare feature and target data.
    """

    if target_column not in df.columns:
        raise ValueError(
            f"Target column '{target_column}' was not found in the dataset."
        )

    data = df.copy()

    # Remove rows where target is missing.
    data = data.dropna(subset=[target_column])

    if data.empty:
        raise ValueError(
            "No usable rows remain after removing missing target values."
        )

    X = data.drop(columns=[target_column])
    y = data[target_column]

    # Remove columns with only one unique value.
    constant_columns = [
        column
        for column in X.columns
        if X[column].nunique(dropna=False) <= 1
    ]

    if constant_columns:
        X = X.drop(columns=constant_columns)

    # Remove very high-cardinality text columns such as identifiers.
    columns_to_remove = []

    for column in X.select_dtypes(
        include=["object", "category"]
    ).columns:

        unique_ratio = (
            X[column].nunique(dropna=True)
            / max(len(X), 1)
        )

        if unique_ratio > 0.90:
            columns_to_remove.append(column)

    if columns_to_remove:
        X = X.drop(columns=columns_to_remove)

    if X.shape[1] == 0:
        raise ValueError(
            "No usable feature columns were found after preprocessing."
        )

    return X, y


def _build_preprocessor(X: pd.DataFrame):
    """
    Build preprocessing for numeric and categorical columns.
    """

    numeric_columns = X.select_dtypes(
        include=["number"]
    ).columns.tolist()

    categorical_columns = X.select_dtypes(
        include=["object", "category", "bool"]
    ).columns.tolist()

    transformers = []

    if numeric_columns:

        numeric_pipeline = Pipeline(
            steps=[
                (
                    "imputer",
                    SimpleImputer(strategy="median")
                )
            ]
        )

        transformers.append(
            (
                "numeric",
                numeric_pipeline,
                numeric_columns
            )
        )

    if categorical_columns:

        categorical_pipeline = Pipeline(
            steps=[
                (
                    "imputer",
                    SimpleImputer(
                        strategy="most_frequent"
                    )
                ),
                (
                    "encoder",
                    OneHotEncoder(
                        handle_unknown="ignore"
                    )
                )
            ]
        )

        transformers.append(
            (
                "categorical",
                categorical_pipeline,
                categorical_columns
            )
        )

    if not transformers:
        raise ValueError(
            "The dataset does not contain usable feature columns."
        )

    return ColumnTransformer(
        transformers=transformers
    )


def _get_models(problem_type: str):
    """
    Return the models used for comparison.
    """

    if problem_type == "classification":

        return {
            "Logistic Regression": LogisticRegression(
                max_iter=1000
            ),

            "Decision Tree": DecisionTreeClassifier(
                random_state=42
            ),

            "Random Forest": RandomForestClassifier(
                n_estimators=100,
                random_state=42,
                n_jobs=-1
            ),

            "Gradient Boosting": GradientBoostingClassifier(
                random_state=42
            ),
        }

    return {
        "Linear Regression": LinearRegression(),

        "Decision Tree": DecisionTreeRegressor(
            random_state=42
        ),

        "Random Forest": RandomForestRegressor(
            n_estimators=100,
            random_state=42,
            n_jobs=-1
        ),

        "Gradient Boosting": GradientBoostingRegressor(
            random_state=42
        ),
    }


def _get_stratify_target(y, problem_type):
    """
    Use stratification when classification classes are suitable.
    """

    if problem_type != "classification":
        return None

    value_counts = y.value_counts()

    if (
        len(value_counts) > 1
        and value_counts.min() >= 2
    ):
        return y

    return None


def _build_pipeline(preprocessor, model):
    """
    Create the complete preprocessing + model pipeline.
    """

    return Pipeline(
        steps=[
            (
                "preprocessor",
                preprocessor
            ),
            (
                "model",
                model
            )
        ]
    )


def _calculate_explainability(
    pipeline,
    X_test,
    y_test,
    problem_type,
):
    """
    Calculate permutation feature importance
    using the complete preprocessing + model pipeline.

    This keeps feature names at their original dataset level,
    making the explanation easier for users to understand.
    """

    if problem_type == "classification":

        scoring = "f1_weighted"

    else:

        scoring = "r2"

    importance_result = permutation_importance(
        pipeline,
        X_test,
        y_test,
        scoring=scoring,
        n_repeats=5,
        random_state=42,
        n_jobs=-1,
    )

    feature_importances = []

    for feature, importance, std in zip(
        X_test.columns,
        importance_result.importances_mean,
        importance_result.importances_std,
    ):

        feature_importances.append(
            {
                "feature": str(feature),
                "importance": round(
                    float(importance),
                    6
                ),
                "std": round(
                    float(std),
                    6
                ),
            }
        )

    feature_importances.sort(
        key=lambda item: item["importance"],
        reverse=True
    )

    # Keep the top 10 features for the UI.
    top_features = feature_importances[:10]

    return {
        "method": "Permutation Feature Importance",
        "metric": scoring,
        "features": top_features,
    }


def train_and_compare_models(
    file_path: str,
    target_column: str,
    problem_type: str = "auto"
):
    """
    Train multiple machine-learning models,
    compare their performance, select the best model,
    and generate explainability information.
    """

    df = load_dataset(file_path)

    if df.empty:
        raise ValueError(
            "The dataset is empty."
        )

    if problem_type not in {
        "auto",
        "classification",
        "regression"
    }:

        raise ValueError(
            "Problem type must be auto, classification, or regression."
        )

    X, y = _prepare_features(
        df,
        target_column
    )

    if problem_type == "auto":
        problem_type = _detect_problem_type(y)

    if problem_type == "classification":

        if y.nunique() < 2:
            raise ValueError(
                "Classification requires at least two target classes."
            )

        if y.nunique() > 50:
            raise ValueError(
                "The target has too many unique classes for automatic classification."
            )

    if problem_type == "regression":

        if not pd.api.types.is_numeric_dtype(y):
            raise ValueError(
                "Regression requires a numeric target column."
            )

    stratify = _get_stratify_target(
        y,
        problem_type
    )

    X_train, X_test, y_train, y_test = train_test_split(
        X,
        y,
        test_size=0.20,
        random_state=42,
        stratify=stratify
    )

    preprocessor = _build_preprocessor(X)

    models = _get_models(problem_type)

    results = []

    trained_pipelines = {}

    for model_name, model in models.items():

        try:

            pipeline = _build_pipeline(
                preprocessor,
                model
            )

            pipeline.fit(
                X_train,
                y_train
            )

            predictions = pipeline.predict(
                X_test
            )

            trained_pipelines[model_name] = pipeline

            if problem_type == "classification":

                accuracy = accuracy_score(
                    y_test,
                    predictions
                )

                precision = precision_score(
                    y_test,
                    predictions,
                    average="weighted",
                    zero_division=0
                )

                recall = recall_score(
                    y_test,
                    predictions,
                    average="weighted",
                    zero_division=0
                )

                f1 = f1_score(
                    y_test,
                    predictions,
                    average="weighted",
                    zero_division=0
                )

                results.append(
                    {
                        "model": model_name,
                        "accuracy": round(
                            float(accuracy),
                            4
                        ),
                        "precision": round(
                            float(precision),
                            4
                        ),
                        "recall": round(
                            float(recall),
                            4
                        ),
                        "f1_score": round(
                            float(f1),
                            4
                        )
                    }
                )

            else:

                mae = mean_absolute_error(
                    y_test,
                    predictions
                )

                mse = mean_squared_error(
                    y_test,
                    predictions
                )

                rmse = mse ** 0.5

                r2 = r2_score(
                    y_test,
                    predictions
                )

                results.append(
                    {
                        "model": model_name,
                        "mae": round(
                            float(mae),
                            4
                        ),
                        "mse": round(
                            float(mse),
                            4
                        ),
                        "rmse": round(
                            float(rmse),
                            4
                        ),
                        "r2_score": round(
                            float(r2),
                            4
                        )
                    }
                )

        except Exception as error:

            results.append(
                {
                    "model": model_name,
                    "error": str(error)
                }
            )

    successful_results = [
        result
        for result in results
        if "error" not in result
    ]

    if not successful_results:

        raise ValueError(
            "All machine-learning models failed during training."
        )

    if problem_type == "classification":

        best_result = max(
            successful_results,
            key=lambda result: result["f1_score"]
        )

        best_metric = "f1_score"

    else:

        best_result = max(
            successful_results,
            key=lambda result: result["r2_score"]
        )

        best_metric = "r2_score"

    best_model_name = best_result["model"]

    best_pipeline = trained_pipelines.get(
        best_model_name
    )

    explainability = None

    if best_pipeline is not None:

        explainability = _calculate_explainability(
            pipeline=best_pipeline,
            X_test=X_test,
            y_test=y_test,
            problem_type=problem_type,
        )

    return {
        "success": True,
        "problem_type": problem_type,
        "target_column": target_column,
        "rows_used": len(df),
        "features_used": list(X.columns),
        "train_rows": len(X_train),
        "test_rows": len(X_test),
        "models": results,
        "best_model": best_model_name,
        "best_metric": best_metric,
        "best_score": best_result[best_metric],
        "explainability": explainability,
    }